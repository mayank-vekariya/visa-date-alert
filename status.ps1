$ErrorActionPreference = "Continue"
$MonitorTaskName = "Visa Date Alert Monitor"
$WatchdogTaskName = "Visa Date Alert Watchdog"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$HeartbeatPath = Join-Path $ProjectRoot "data\monitor.heartbeat"
$WatchdogLogPath = Join-Path $ProjectRoot "logs\watchdog.log"
$Healthy = $true

Write-Host "Visa Date Alert status"
Write-Host ""

$MonitorTask = Get-ScheduledTask -TaskName $MonitorTaskName -ErrorAction SilentlyContinue
if ($null -eq $MonitorTask) {
    Write-Host "[DOWN] Monitor task is not installed."
    $Healthy = $false
}
else {
    $MonitorInfo = Get-ScheduledTaskInfo -TaskName $MonitorTaskName
    Write-Host "[$($MonitorTask.State)] Monitor task"
    Write-Host "       Last run: $($MonitorInfo.LastRunTime)"
    Write-Host "       Last result: $($MonitorInfo.LastTaskResult)"
    if ($MonitorTask.State -ne "Running") {
        $Healthy = $false
    }
}

$WatchdogTask = Get-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction SilentlyContinue
if ($null -eq $WatchdogTask) {
    Write-Host "[DOWN] Hourly watchdog task is not installed."
    $Healthy = $false
}
else {
    $WatchdogInfo = Get-ScheduledTaskInfo -TaskName $WatchdogTaskName
    Write-Host "[$($WatchdogTask.State)] Hourly watchdog task"
    Write-Host "       Last run: $($WatchdogInfo.LastRunTime)"
    Write-Host "       Next run: $($WatchdogInfo.NextRunTime)"
    Write-Host "       Last result: $($WatchdogInfo.LastTaskResult)"
}

if (Test-Path -LiteralPath $HeartbeatPath) {
    $Heartbeat = Get-Item -LiteralPath $HeartbeatPath
    $Age = (Get-Date).ToUniversalTime() - $Heartbeat.LastWriteTimeUtc
    $RoundedAge = [math]::Round($Age.TotalMinutes, 1)
    if ($Age.TotalMinutes -le 10) {
        Write-Host "[FRESH] Monitor heartbeat is $RoundedAge minutes old."
    }
    else {
        Write-Host "[STALE] Monitor heartbeat is $RoundedAge minutes old."
        $Healthy = $false
    }
}
else {
    Write-Host "[DOWN] Monitor heartbeat is missing."
    $Healthy = $false
}

if (Test-Path -LiteralPath $WatchdogLogPath) {
    Write-Host ""
    Write-Host "Recent watchdog checks:"
    Get-Content -LiteralPath $WatchdogLogPath -Tail 5
}

if ($Healthy) {
    Write-Host ""
    Write-Host "Overall: HEALTHY"
    exit 0
}

Write-Host ""
Write-Host "Overall: NEEDS ATTENTION"
exit 1
