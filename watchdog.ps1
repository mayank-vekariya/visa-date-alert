param(
    [ValidateRange(2, 60)]
    [int]$MaxHeartbeatAgeMinutes = 10
)

$ErrorActionPreference = "Stop"
$MonitorTaskName = "Visa Date Alert Monitor"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$HeartbeatPath = Join-Path $ProjectRoot "data\monitor.heartbeat"
$LogPath = Join-Path $ProjectRoot "logs\watchdog.log"

function Write-WatchdogLog {
    param([string]$Message)

    $LogDirectory = Split-Path -Parent $LogPath
    New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    $Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
    Add-Content -LiteralPath $LogPath -Value "$Timestamp $Message" -Encoding UTF8
}

function Get-MonitorHealth {
    $Task = Get-ScheduledTask -TaskName $MonitorTaskName -ErrorAction SilentlyContinue
    if ($null -eq $Task) {
        return [pscustomobject]@{ Healthy = $false; Reason = "monitor task is not installed" }
    }
    if ($Task.State -ne "Running") {
        return [pscustomobject]@{ Healthy = $false; Reason = "monitor task state is $($Task.State)" }
    }
    if (-not (Test-Path -LiteralPath $HeartbeatPath)) {
        return [pscustomobject]@{ Healthy = $false; Reason = "heartbeat file is missing" }
    }

    $Heartbeat = Get-Item -LiteralPath $HeartbeatPath
    $Age = (Get-Date).ToUniversalTime() - $Heartbeat.LastWriteTimeUtc
    if ($Age.TotalMinutes -gt $MaxHeartbeatAgeMinutes) {
        $RoundedAge = [math]::Round($Age.TotalMinutes, 1)
        return [pscustomobject]@{ Healthy = $false; Reason = "heartbeat is $RoundedAge minutes old" }
    }
    return [pscustomobject]@{ Healthy = $true; Reason = "heartbeat is fresh" }
}

try {
    $Health = Get-MonitorHealth
    if ($Health.Healthy) {
        Write-WatchdogLog "HEALTHY: $($Health.Reason)."
        exit 0
    }

    Write-WatchdogLog "RECOVERY: $($Health.Reason); restarting the monitor."
    $Task = Get-ScheduledTask -TaskName $MonitorTaskName -ErrorAction SilentlyContinue
    if ($null -eq $Task) {
        throw "The monitor task is not installed. Run install-startup.ps1 first."
    }

    if ($Task.State -eq "Running") {
        Stop-ScheduledTask -TaskName $MonitorTaskName
        Start-Sleep -Seconds 2
    }

    $ProjectProcesses = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and
        $_.CommandLine.Contains($ProjectRoot) -and
        ($_.CommandLine -match "visa-alert\.exe.*\brun\b" -or
            $_.CommandLine -match "visa_alert_bot.*\brun\b")
    }
    foreach ($Process in $ProjectProcesses) {
        Stop-Process -Id $Process.ProcessId -Force -ErrorAction SilentlyContinue
    }

    Remove-Item -LiteralPath $HeartbeatPath -Force -ErrorAction SilentlyContinue
    Start-ScheduledTask -TaskName $MonitorTaskName

    for ($Attempt = 1; $Attempt -le 15; $Attempt++) {
        Start-Sleep -Seconds 2
        $Health = Get-MonitorHealth
        if ($Health.Healthy) {
            Write-WatchdogLog "RECOVERED: monitor is running and $($Health.Reason)."
            exit 0
        }
    }

    throw "Monitor did not produce a fresh heartbeat within 30 seconds."
}
catch {
    Write-WatchdogLog "FAILED: $($_.Exception.Message)"
    exit 1
}
