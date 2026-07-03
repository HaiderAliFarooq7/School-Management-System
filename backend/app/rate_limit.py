"""In-memory sliding-window rate limiting for login attempts.

This app deploys as a single Render instance, so process-local state is the
whole picture — no Redis needed. State resets on restart/redeploy, which is
an acceptable trade-off for brute-force protection (an attacker cannot force
a restart, and losing a few counters on deploy is harmless).
"""
import threading
import time
from collections import defaultdict, deque

# Per (client IP + username): stops targeted brute force on one account.
MAX_ATTEMPTS_PER_ACCOUNT = 5
# Per client IP across all usernames: slows credential stuffing.
MAX_ATTEMPTS_PER_IP = 20
WINDOW_SECONDS = 15 * 60


class LoginRateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_account: dict[str, deque[float]] = defaultdict(deque)
        self._by_ip: dict[str, deque[float]] = defaultdict(deque)

    @staticmethod
    def _prune(attempts: deque[float], now: float) -> None:
        while attempts and attempts[0] <= now - WINDOW_SECONDS:
            attempts.popleft()

    def retry_after(self, ip: str, username: str) -> int | None:
        """Seconds until another attempt is allowed, or None if not limited."""
        now = time.time()
        with self._lock:
            account = self._by_account[self._account_key(ip, username)]
            per_ip = self._by_ip[ip]
            self._prune(account, now)
            self._prune(per_ip, now)
            oldest = None
            if len(account) >= MAX_ATTEMPTS_PER_ACCOUNT:
                oldest = account[0]
            if len(per_ip) >= MAX_ATTEMPTS_PER_IP:
                oldest = per_ip[0] if oldest is None else min(oldest, per_ip[0])
            if oldest is None:
                return None
            return max(int(oldest + WINDOW_SECONDS - now), 1)

    def record_failure(self, ip: str, username: str) -> None:
        now = time.time()
        with self._lock:
            self._by_account[self._account_key(ip, username)].append(now)
            self._by_ip[ip].append(now)
            # Opportunistic cleanup so the maps can't grow unbounded under a
            # scan that sprays thousands of usernames/IPs.
            if len(self._by_account) > 10_000:
                self._by_account = defaultdict(
                    deque,
                    {k: v for k, v in self._by_account.items() if v and v[-1] > now - WINDOW_SECONDS},
                )
            if len(self._by_ip) > 10_000:
                self._by_ip = defaultdict(
                    deque,
                    {k: v for k, v in self._by_ip.items() if v and v[-1] > now - WINDOW_SECONDS},
                )

    def reset(self, ip: str, username: str) -> None:
        """A successful login clears the account counter (not the IP one)."""
        with self._lock:
            self._by_account.pop(self._account_key(ip, username), None)

    @staticmethod
    def _account_key(ip: str, username: str) -> str:
        return f"{ip}|{username.strip().lower()}"


login_rate_limiter = LoginRateLimiter()


def client_ip(request) -> str:
    """Real client IP behind Render's proxy (first X-Forwarded-For hop),
    falling back to the direct peer address."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
