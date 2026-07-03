# Windows Task Scheduler Setup for Anime Refresher
# Schedules execution at 06:00, 12:00, and 22:00 daily

$TaskName = "AnimeRefresher"
$Action = New-ScheduledTaskAction -Execute "C:\shortcuts\anime-refresher.bat"
$Trigger1 = New-ScheduledTaskTrigger -Daily -At 6:00AM
$Trigger2 = New-ScheduledTaskTrigger -Daily -At 12:00PM
$Trigger3 = New-ScheduledTaskTrigger -Daily -At 10:00PM

# Unregister if already exists
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Register the new task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger @($Trigger1, $Trigger2, $Trigger3) -Description "Automated Anime Refresher Downloader & Episode Tracker"

Write-Host "Successfully registered scheduled task: $TaskName (Triggers: 06:00, 12:00, 22:00 daily)" -ForegroundColor Green
