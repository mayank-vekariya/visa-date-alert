$ErrorActionPreference = "Stop"

$TaskName = "Visa Date Alert Monitor"
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -eq $Task) {
    Write-Host "Windows task is not installed: $TaskName"
    exit 0
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Removed Windows task: $TaskName"
Write-Host "The project files, .env, Telegram session, database, and logs were not deleted."
