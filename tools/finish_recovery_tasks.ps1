# Final administrator-only step. Preserves disabled tasks through register_tasks.ps1.
# Run only after the reviewed recovery source has been applied.
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw 'Windows administrator confirmation is required to update the existing BEOPS tasks. No task has been changed.'
}
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backup = Join-Path $root ('runtime\tasks-before-reconcile-' + (Get-Date -Format 'yyyyMMddTHHmmss'))
New-Item -ItemType Directory -Path $backup -ErrorAction Stop | Out-Null
foreach ($task in Get-ScheduledTask -TaskName 'Beops_*') {
  Export-ScheduledTask -TaskName $task.TaskName | Set-Content -LiteralPath (Join-Path $backup ($task.TaskName + '.xml')) -Encoding UTF8
}
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'register_tasks.ps1')
if ($LASTEXITCODE -ne 0) { throw "Task registration failed; original definitions remain in $backup" }
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'audit_tasks.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Task registration completed but audit still reports drift' }
Write-Output 'BEOPS task definitions reconciled and verified; prior disabled states preserved.'
