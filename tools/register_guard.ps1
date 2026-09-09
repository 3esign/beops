# Registers Beops_Guard: every 15 minutes, forever, checking that the other tasks are alive and that
# the collection is still permitted. It is the only task allowed to restart another one.
$ErrorActionPreference = 'Stop'
$root = 'D:\Svemir\!Projekti\Beops'
$act  = New-ScheduledTaskAction -Execute "$root\tools\guard_tick.bat" -WorkingDirectory $root
$t1   = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15)
$t2   = New-ScheduledTaskTrigger -AtLogOn
$set  = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'Beops_Guard' -Action $act -Trigger @($t1,$t2) -Settings $set -Force | Out-Null
Write-Output ('Beops_Guard registered; next run ' + (Get-ScheduledTaskInfo -TaskName 'Beops_Guard').NextRunTime)
