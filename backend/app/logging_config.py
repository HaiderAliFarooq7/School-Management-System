import logging
from logging.handlers import RotatingFileHandler

from app.config import LOG_DIR

_CONFIGURED = False


def configure_logging() -> logging.Logger:
    """App logger that writes to a size-capped, rotating file (1 MB x 3
    backups) so logs can never grow unbounded on small/free hosting, plus the
    console. Safe to call more than once."""
    global _CONFIGURED
    logger = logging.getLogger("sms")
    if _CONFIGURED:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    _CONFIGURED = True
    return logger


logger = configure_logging()
