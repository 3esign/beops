# Makes the BEOPS scheduled tasks survive the things that actually stop them: a sleeping machine, a
# missed window, a battery, a run that hangs, and a logon that never re-armed them. It changes only
# SETTINGS and TRIGGERS - never the action, never the account, and it never stores a password, so the
# tasks still run in the user's session. That is the honest limit: they run while this user is logged
# on, and they resume by themselves the moment that is true again.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\harden_tasks.ps1
$ErrorActionPreference = 'Stop'
$names = @('Beops_Collect','Beops_Mind','Beops_Organ','Beops_Publish','Beops_Watch','Beops_Legal','Beops_Guard','Beops_Baseline')
foreach ($n in $names) {
  $t = Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue
  if (-not $t) { Write-Output "$n : not registered - skipped"; continue }
  $s = $t.Settings
  $s.StartWhenAvailable          = $true    # a window missed while asleep is taken as soon as possible
  $s.DisallowStartIfOnBatteries  = $false   # a laptop on battery is still a laptop that is running
  $s.StopIfGoingOnBatteries      = $false
  $s.ExecutionTimeLimit          = 'PT1H'   # a hung run is killed within the hour, not left forever
  $s.MultipleInstances           = 'IgnoreNew'
  $s.RestartCount                = 3        # a failed run is retried three times, ten minutes apart
  $s.RestartInterval             = 'PT10M'
  $s.RunOnlyIfNetworkAvailable   = $false   # "no network" is an observation to record, not a reason not to ask
  $s.WakeToRun                   = $false   # never wake the machine: the record says silence, honestly
  $s.Enabled                     = $true
  # An AtLogOn trigger is what brings everything back after a restart without storing a password.
  $trg = @($t.Triggers)
  if (-not ($trg | Where-Object { $_.CimClass.CimClassName -eq 'MSFT_TaskLogonTrigger' })) {
    $trg += New-ScheduledTaskTrigger -AtLogOn
  }
  Set-ScheduledTask -TaskName $n -Settings $s -Trigger $trg | Out-Null
  $t2 = Get-ScheduledTask -TaskName $n
  $i  = Get-ScheduledTaskInfo -TaskName $n
  Write-Output ("{0,-15} state={1,-8} triggers={2} startWhenAvailable={3} battery_ok={4} next={5}" -f `
    $n, $t2.State, $t2.Triggers.Count, $t2.Settings.StartWhenAvailable, (-not $t2.Settings.DisallowStartIfOnBatteries), $i.NextRunTime)
}
