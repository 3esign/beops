# Registers (or replaces) the four BEOPS scheduled tasks. S4U logon so they run whether or not a
# user is signed in (an Interactive-only task silently skips and leaves the previous Last Result).
# Verify afterwards with: schtasks /query /tn Beops_Collect /tn Beops_Organ /tn Beops_Publish /tn Beops_Mind /v /fo list
$ErrorActionPreference = 'Stop'
$root = 'D:\Svemir\!Projekti\Beops'
$tasks = @(
  @{ name='Beops_Collect'; bat='tools\collect_tick.bat'; minutes=5;  limit=10; desc='BEOPS: one bounded pass over permitted sources' },
  @{ name='Beops_Organ';   bat='tools\organ_tick.bat';   minutes=10; limit=9;  desc='BEOPS: one bounded pass of the news-sorter organ on a local model' },
  @{ name='Beops_Publish'; bat='tools\publish_tick.bat'; minutes=30; limit=20; desc='BEOPS: export and push the public site (github.com/3esign/beops)' },
  @{ name='Beops_Mind';    bat='tools\mind_tick.bat';    minutes=4;  limit=12; desc='BEOPS: one drop of the mind - one step of the endless conversation on local models' }
)
foreach ($t in $tasks) {
  $action    = New-ScheduledTaskAction -Execute (Join-Path $root $t.bat) -WorkingDirectory $root
  $trigger   = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $t.minutes)
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited
  $settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
                 -ExecutionTimeLimit (New-TimeSpan -Minutes $t.limit) -MultipleInstances IgnoreNew
  if (Get-ScheduledTask -TaskName $t.name -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $t.name -Confirm:$false }
  Register-ScheduledTask -TaskName $t.name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description $t.desc | Out-Null
  Write-Output ("registered {0} every {1} min" -f $t.name, $t.minutes)
}
Get-ScheduledTask -TaskName 'Beops_*' | Select-Object TaskName, State | Format-Table -AutoSize
