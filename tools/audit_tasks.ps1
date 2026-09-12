# Read-only audit of the BEOPS scheduled tasks against the canonical task spec.
# It reports C:/D: root aliases separately from real action drift.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_tasks.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_tasks.ps1 -WarnOnly
param(
  [switch]$WarnOnly,
  [switch]$Json
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'beops_tasks.ps1')
. (Join-Path $PSScriptRoot 'publish_safety.ps1')

function Normalize-TaskPath([string]$PathText) {
  if (-not $PathText) { return '' }
  return (($PathText -replace '/', '\').TrimEnd('\')).ToLowerInvariant()
}

function Ends-WithTaskPath([string]$PathText, [string]$Suffix) {
  $a = Normalize-TaskPath $PathText
  $s = Normalize-TaskPath $Suffix
  return ($a -ne '' -and $a.EndsWith($s))
}

$root = Get-BeopsRoot
$rows = foreach ($spec in Get-BeopsTaskSpecs) {
  $task = Get-ScheduledTask -TaskName $spec.Name -ErrorAction SilentlyContinue
  $expectedExecute = Join-Path $root $spec.Bat
  $issues = @()
  $execute = ''
  $workingDirectory = ''
  $triggerCount = 0
  if (-not $task) {
    $issues += 'missing task'
  } else {
    $execute = [string]$task.Actions.Execute
    $workingDirectory = [string]$task.Actions.WorkingDirectory
    $triggerCount = @($task.Triggers).Count
    if (@($task.Actions).Count -ne 1) { $issues += 'action count drift' }
    if (-not (Ends-WithTaskPath $execute $spec.Bat)) {
      $issues += 'action drift'
    } elseif ((Normalize-TaskPath $execute) -ne (Normalize-TaskPath $expectedExecute)) {
      if ((Normalize-TaskPath (Get-BeopsFullPath $execute)) -eq (Normalize-TaskPath (Get-BeopsFullPath $expectedExecute))) {
        $issues += 'root alias'
      } else { $issues += 'action physical target drift' }
    }
    if ([string]$task.Actions.Arguments) { $issues += 'action arguments drift' }
    if (-not $workingDirectory) {
      $issues += 'missing working directory'
    } elseif (-not (Test-Path -LiteralPath $workingDirectory)) {
      $issues += 'working directory missing on disk'
    } elseif ((Normalize-TaskPath $workingDirectory) -ne (Normalize-TaskPath $root)) {
      if ((Normalize-TaskPath (Get-BeopsFullPath $workingDirectory)) -eq (Normalize-TaskPath (Get-BeopsFullPath $root))) {
        $issues += 'working directory alias'
      } else { $issues += 'working directory physical target drift' }
    }
    if ($triggerCount -lt 2) {
      $issues += 'missing repeat or logon trigger'
    }
    if ([string]$task.Settings.ExecutionTimeLimit -ne [System.Xml.XmlConvert]::ToString([TimeSpan]::FromMinutes($spec.Limit))) { $issues += 'execution limit drift' }
    if ([string]$task.Settings.MultipleInstances -ne 'IgnoreNew') { $issues += 'overlap policy drift' }
    $interval = [System.Xml.XmlConvert]::ToString([TimeSpan]::FromMinutes($spec.Minutes))
    if (-not @($task.Triggers | Where-Object { $_.Repetition.Interval -eq $interval }).Count) { $issues += 'repeat interval drift' }
    $expectedLogon = if ($spec.LogonType) { $spec.LogonType } else { 'S4U' }
    if ([string]$task.Principal.LogonType -ne $expectedLogon -or [string]$task.Principal.RunLevel -ne 'Limited') { $issues += 'principal drift' }
    $expectedUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    function Get-UserSid([string]$Identity) {
      try { return ([System.Security.Principal.NTAccount]$Identity).Translate([System.Security.Principal.SecurityIdentifier]).Value }
      catch { return $Identity }
    }
    if ((Get-UserSid ([string]$task.Principal.UserId)) -ne (Get-UserSid $expectedUser)) { $issues += 'principal user drift' }
    $logs = @($task.Triggers | Where-Object { $_.CimClass.CimClassName -eq 'MSFT_TaskLogonTrigger' })
    if (-not $logs.Count -or @($logs | Where-Object { -not $_.UserId }).Count) { $issues += 'unscoped logon trigger' }
    if (@($logs | Where-Object { $_.UserId -and (Get-UserSid ([string]$_.UserId)) -ne (Get-UserSid $expectedUser) }).Count) { $issues += 'logon user drift' }
  }
  $bad = @($issues | Where-Object { $_ -notlike '*alias' })
  $status = if ($bad.Count -gt 0) { 'DRIFT' } elseif ($issues.Count -gt 0) { 'ALIAS' } else { 'OK' }
  [pscustomobject]@{
    Task = $spec.Name
    Status = $status
    Issues = if ($issues.Count) { $issues -join '; ' } else { '' }
    Execute = $execute
    Expected = $expectedExecute
    WorkingDirectory = $workingDirectory
    TriggerCount = $triggerCount
  }
}

$summary = [pscustomobject]@{
  schema = 'beops-task-audit/v1'
  at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  root = $root
  expected = @(Get-BeopsTaskSpecs).Count
  ok = @($rows | Where-Object { $_.Status -eq 'OK' }).Count
  alias = @($rows | Where-Object { $_.Status -eq 'ALIAS' }).Count
  drift = @($rows | Where-Object { $_.Status -eq 'DRIFT' }).Count
  tasks = @($rows)
}
if ($Json) { $summary | ConvertTo-Json -Depth 6 }
else { $rows | Format-Table Task,Status,Issues,TriggerCount,Execute -AutoSize }
$drift = @($rows | Where-Object { $_.Status -eq 'DRIFT' })
if ($drift.Count -gt 0 -and -not $WarnOnly) { exit 1 }
