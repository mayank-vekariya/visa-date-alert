$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -e .

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
}

Write-Host ""
Write-Host "Setup complete. Next steps:"
Write-Host "  1. Fill in .env"
Write-Host "  2. .\.venv\Scripts\visa-alert.exe doctor"
Write-Host "  3. .\.venv\Scripts\visa-alert.exe list-chats"
Write-Host "  4. powershell -ExecutionPolicy Bypass -File .\install-startup.ps1"
Write-Host "  5. powershell -ExecutionPolicy Bypass -File .\status.ps1"
