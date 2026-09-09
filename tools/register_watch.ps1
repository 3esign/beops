# Registers (or replaces) ONLY the watchman task, so registering it never disturbs the five tasks it
# watches. The full set lives in tools/register_tasks.ps1, which now includes this one as well.
# Verify with: schtasks /query /tn Beops_Watch /v /fo list
$ErrorActionPreference = 'Stop'
$root = 'D:\Svemir\!Projekti\Beops'
$name = 'Beops_Watch'
$action    = New-ScheduledTaskAction -Execute (Join-Path $root 'tools\watch_tick.bat') -WorkingDirectory $root
$trigger   = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
               -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -MultipleInstances IgnoreNew
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $name -Confirm:$false }
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Settings $settings `
  -Description 'BEOPS: the watchman - reads the artefacts (rows, receipts, history, the published commit) and never a task status' | Out-Null
Write-Output 'registered Beops_Watch every 10 min'
Get-ScheduledTask -TaskName 'Beops_*' | Select-Object TaskName, State | Format-Table -AutoSize
