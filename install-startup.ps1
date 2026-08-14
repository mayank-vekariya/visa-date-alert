$ErrorActionPreference = "Stop"

$TaskName = "Visa Date Alert Monitor"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunScript = Join-Path $ProjectRoot "run.ps1"
$Executable = (Get-Command powershell.exe).Source

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".env"))) {
    throw "Missing .env. Run setup.ps1 and configure the project first."
}

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".venv\Scripts\visa-alert.exe"))) {
    throw "Missing virtual environment. Run setup.ps1 first."
}

$Action = New-ScheduledTaskAction `
    -Execute $Executable `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunScript`"" `
    -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "Start the Telegram visa appointment alert monitor at sign-in." `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName
Write-Host "Installed and started Windows task: $TaskName"
Write-Host "Status: Get-ScheduledTask -TaskName '$TaskName'"
