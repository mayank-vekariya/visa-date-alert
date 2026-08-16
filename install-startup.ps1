$ErrorActionPreference = "Stop"

$MonitorTaskName = "Visa Date Alert Monitor"
$WatchdogTaskName = "Visa Date Alert Watchdog"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunScript = Join-Path $ProjectRoot "run.ps1"
$WatchdogScript = Join-Path $ProjectRoot "watchdog.ps1"
$Executable = (Get-Command powershell.exe).Source

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".env"))) {
    throw "Missing .env. Run setup.ps1 and configure the project first."
}

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".venv\Scripts\visa-alert.exe"))) {
    throw "Missing virtual environment. Run setup.ps1 first."
}

$MonitorAction = New-ScheduledTaskAction `
    -Execute $Executable `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunScript`"" `
    -WorkingDirectory $ProjectRoot
$MonitorTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$WatchdogAction = New-ScheduledTaskAction `
    -Execute $Executable `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$WatchdogScript`"" `
    -WorkingDirectory $ProjectRoot
$WatchdogTrigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited
$MonitorSettings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries
$WatchdogSettings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

foreach ($TaskName in ($MonitorTaskName, $WatchdogTaskName)) {
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $ExistingTask -and $ExistingTask.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName
    }
}

Register-ScheduledTask `
    -TaskName $MonitorTaskName `
    -Action $MonitorAction `
    -Trigger $MonitorTrigger `
    -Principal $Principal `
    -Settings $MonitorSettings `
    -Description "Start the Telegram visa appointment alert monitor at sign-in." `
    -Force | Out-Null

Register-ScheduledTask `
    -TaskName $WatchdogTaskName `
    -Action $WatchdogAction `
    -Trigger $WatchdogTrigger `
    -Principal $Principal `
    -Settings $WatchdogSettings `
    -Description "Check Visa Date Alert hourly and restart it if its heartbeat is stale." `
    -Force | Out-Null

Start-ScheduledTask -TaskName $MonitorTaskName
Write-Host "Installed and started Windows task: $MonitorTaskName"
Write-Host "Installed hourly health check: $WatchdogTaskName"
Write-Host "Status: powershell -ExecutionPolicy Bypass -File .\status.ps1"
