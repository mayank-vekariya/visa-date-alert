$ErrorActionPreference = "Stop"

$TaskNames = "Visa Date Alert Monitor", "Visa Date Alert Watchdog"
foreach ($TaskName in $TaskNames) {
    $Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -eq $Task) {
        Write-Host "Windows task is not installed: $TaskName"
        continue
    }

    if ($Task.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName
    }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed Windows task: $TaskName"
}
Write-Host "The project files, .env, Telegram session, database, and logs were not deleted."
