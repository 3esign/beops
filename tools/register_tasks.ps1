# Registers or replaces the BEOPS scheduled tasks from one source of truth.
# The project root is resolved from this script, so C:\Svemir and D:\Svemir
# entry points do not leak into task actions.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\register_tasks.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\register_tasks.ps1 -Only Beops_Guard
param(
  [string[]]$Only = @()
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$tasks = @(
  [pscustomobject]@{ Name='Beops_Collect';  Bat='tools\collect_tick.bat';  Minutes=5;     Limit=10; Desc='BEOPS: one bounded pass over permitted sources' },
  [pscustomobject]@{ Name='Beops_Organ';    Bat='tools\organ_tick.bat';    Minutes=10;    Limit=9;  Desc='BEOPS: one bounded pass of the news-sorter organ on a local model' },
  [pscustomobject]@{ Name='Beops_Publish';  Bat='tools\publish_tick.bat';  Minutes=10;    Limit=8;  Desc='BEOPS: export and push the public site (github.com/3esign/beops)' },
  [pscustomobject]@{ Name='Beops_Mind';     Bat='tools\mind_tick.bat';     Minutes=4;     Limit=12; Desc='BEOPS: one drop of the mind - one step of the endless conversation on local models' },
  [pscustomobject]@{ Name='Beops_Watch';    Bat='tools\watch_tick.bat';    Minutes=10;    Limit=5;  Desc='BEOPS: the watchman - reads artefacts, never task status as truth' },
  [pscustomobject]@{ Name='Beops_Legal';    Bat='tools\legal_tick.bat';    Minutes=10080; Limit=30; Desc='BEOPS: weekly re-capture of the permission evidence of every polled source' },
  [pscustomobject]@{ Name='Beops_Guard';    Bat='tools\guard_tick.bat';    Minutes=15;    Limit=20; Desc='BEOPS: guard - checks task liveness, permissions, organs and publish gate' },
  [pscustomobject]@{ Name='Beops_Baseline'; Bat='tools\baseline_tick.bat'; Minutes=60;    Limit=60; Desc='BEOPS: hourly baseline build for transport and static comparison layers' }
)
if ($Only.Count -gt 0) {
  $known = @($tasks | ForEach-Object { $_.Name })
  $missing = @($Only | Where-Object { $known -notcontains $_ })
  if ($missing.Count -gt 0) { throw ("unknown BEOPS task(s): " + ($missing -join ', ')) }
  $tasks = @($tasks | Where-Object { $Only -contains $_.Name })
}
foreach ($t in $tasks) {
  $bat = Join-Path $root $t.Bat
  if (-not (Test-Path $bat)) { throw ("task action is missing: " + $bat) }
  $action = New-ScheduledTaskAction -Execute $bat -WorkingDirectory $root
  $repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $t.Minutes)
  $logon = New-ScheduledTaskTrigger -AtLogOn
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes $t.Limit) -MultipleInstances IgnoreNew
  Register-ScheduledTask -TaskName $t.Name -Action $action -Trigger @($repeat, $logon) -Principal $principal -Settings $settings -Description $t.Desc -Force | Out-Null
  Write-Output ("registered {0} every {1} min" -f $t.Name, $t.Minutes)
}
Get-ScheduledTask -TaskName 'Beops_*' | Select-Object TaskName, State | Format-Table -AutoSize
