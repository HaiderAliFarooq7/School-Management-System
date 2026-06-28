# Launches the School Management System web app for LAN use.
# Run this from PowerShell in the SMS_Web folder: .\start.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host "Checking PostgreSQL service..."
$pg = Get-Service -Name "postgresql-x64-*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pg -and $pg.Status -ne "Running") {
    Start-Service $pg.Name
    Write-Host "Started PostgreSQL service: $($pg.Name)"
} elseif (-not $pg) {
    Write-Warning "No PostgreSQL service found. Make sure PostgreSQL is installed and running."
}

Set-Location $backend
& ".\.venv\Scripts\python.exe" -m alembic upgrade head
Write-Host "Database migrations applied."

if (-not (Test-Path (Join-Path $frontend "dist"))) {
    Write-Host "Building frontend (first run)..."
    Set-Location $frontend
    npm install
    npm run build
    Set-Location $backend
}

$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } | Select-Object -First 1).IPAddress
Write-Host ""
Write-Host "Starting server..."
Write-Host "  On this computer:  http://localhost:8000"
if ($ip) {
    Write-Host "  On other devices on this WiFi/LAN:  http://$ip:8000"
}
Write-Host ""
Write-Host "First time on this machine? Allow the port through Windows Firewall:"
Write-Host '  netsh advfirewall firewall add rule name="SMS Web" dir=in action=allow protocol=TCP localport=8000'
Write-Host ""

& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
