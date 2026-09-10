# Read-only audit of the BEOPS scheduled tasks against the canonical task spec.
# It reports C:/D: root aliases separately from real action drift.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_tasks.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\audit_tasks.ps1 -WarnOnly
param(
  [switch]$WarnOnly
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'beops_tasks.ps1')

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
    if (-not (Ends-WithTaskPath $execute $spec.Bat)) {
      $issues += 'action drift'
    } elseif ((Normalize-TaskPath $execute) -ne (Normalize-TaskPath $expectedExecute)) {
      $issues += 'root alias'
    }
    if (-not $workingDirectory) {
      $issues += 'missing working directory'
    } elseif (-not (Test-Path -LiteralPath $workingDirectory)) {
      $issues += 'working directory missing on disk'
    } elseif ((Normalize-TaskPath $workingDirectory) -ne (Normalize-TaskPath $root)) {
      $issues += 'working directory alias'
    }
    if ($triggerCount -lt 2) {
      $issues += 'missing repeat or logon trigger'
    }
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

$rows | Format-Table Task,Status,Issues,TriggerCount,Execute -AutoSize
$drift = @($rows | Where-Object { $_.Status -eq 'DRIFT' })
if ($drift.Count -gt 0 -and -not $WarnOnly) { exit 1 }
