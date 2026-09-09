# Registers (or replaces) the scheduled task Beops_Collect: every 5 minutes, S4U logon so it
# runs whether or not a user is logged in (G-289: Interactive-only tasks silently skip).
# Verify afterwards with:  schtasks /query /tn Beops_Collect /v /fo list
$ErrorActionPreference = 'Stop'
$name = 'Beops_Collect'
$bat  = 'D:\Svemir\!Projekti\Beops\tools\collect_tick.bat'
$action  = New-ScheduledTaskAction -Execute $bat -WorkingDirectory 'D:\Svemir\!Projekti\Beops'
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $name -Confirm:$false }
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'BEOPS live collector: one bounded pass over permitted sources every 5 minutes (tools/collect_daemon.py tick)' | Out-Null
Get-ScheduledTask -TaskName $name | Select-Object TaskName, State | Format-List
