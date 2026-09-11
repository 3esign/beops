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
. (Join-Path $PSScriptRoot 'beops_tasks.ps1')
$root = Get-BeopsRoot
$tasks = @(Get-BeopsTaskSpecs)
if ($Only.Count -gt 0) {
  $known = @($tasks | ForEach-Object { $_.Name })
  $missing = @($Only | Where-Object { $known -notcontains $_ })
  if ($missing.Count -gt 0) { throw ("unknown BEOPS task(s): " + ($missing -join ', ')) }
  $tasks = @($tasks | Where-Object { $Only -contains $_.Name })
}
foreach ($t in $tasks) {
  $prior = Get-ScheduledTask -TaskName $t.Name -ErrorAction SilentlyContinue
  $wasDisabled = $prior -and -not $prior.Settings.Enabled
  $bat = Join-Path $root $t.Bat
  if (-not (Test-Path $bat)) { throw ("task action is missing: " + $bat) }
  $action = New-ScheduledTaskAction -Execute $bat -WorkingDirectory $root
  $repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $t.Minutes)
  $user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
  $logon = New-ScheduledTaskTrigger -AtLogOn -User $user
  $principal = New-ScheduledTaskPrincipal -UserId $user -LogonType S4U -RunLevel Limited
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes $t.Limit) -MultipleInstances IgnoreNew
  Register-ScheduledTask -TaskName $t.Name -Action $action -Trigger @($repeat, $logon) -Principal $principal -Settings $settings -Description $t.Desc -Force | Out-Null
  if ($wasDisabled) { Disable-ScheduledTask -TaskName $t.Name | Out-Null }
  Write-Output ("registered {0} every {1} min" -f $t.Name, $t.Minutes)
}
Get-ScheduledTask -TaskName 'Beops_*' | Select-Object TaskName, State | Format-Table -AutoSize
