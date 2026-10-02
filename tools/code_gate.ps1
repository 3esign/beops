# BEOPS code gate - the complete research suite, once per source commit, outside any release.
# Scheduled task Beops_CodeGate wakes every 30 minutes; it does work only when the current commit has
# no passing receipt younger than 20 h. A release then reads the receipt instead of carrying the
# 3-8 minute suite inside its own budget (tools/publish_github.ps1, "code gate receipt").
#
# Why (2026-10-01): the full suite ran inside the release whenever the source changed, the last
# publication failed, or 24 h had passed. On an 8 GB body under load it consumed the cycle budget
# and a release that had already spent 90 minutes freezing inputs was thrown away.
#
# Rules: publication has priority (no run while a release preparation holds its lock); the receipt
# binds the commit only when tracked code equals that commit (uncommitted code -> no receipt);
# a failing suite writes passed=false, so the release falls back to its own full gate, as before.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\code_gate.ps1          # scheduled
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\code_gate.ps1 -Force   # run now
param([switch]$Force)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
$dir = Join-Path $root 'runtime\code-gate'
New-Item -ItemType Directory -Force $dir | Out-Null
$log = Join-Path $root 'runtime\code-gate.log'
function Log([string]$m) { Add-Content -LiteralPath $log -Value ([DateTimeOffset]::UtcNow.ToString('o') + ' ' + $m) -Encoding UTF8 }
if (Test-Path -LiteralPath (Join-Path $root 'runtime\publish-preparation.lock')) { Log 'quiet: a release preparation holds the lock (publication has priority)'; exit 0 }
$head = (git rev-parse HEAD).Trim()
$tree = (git rev-parse 'HEAD^{tree}').Trim()
$receiptPath = Join-Path $dir ($head + '.json')
if (-not $Force -and (Test-Path -LiteralPath $receiptPath)) {
  try {
    $old = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    $age = ([DateTimeOffset]::UtcNow - [DateTimeOffset]::Parse([string]$old.finished_at)).TotalHours
    if ($old.passed -and $age -ge 0 -and $age -lt 20) { exit 0 }
  } catch {}
}
# Code only: data written by organs (research/observations, data/live, runtime) is not code.
$dirty = git status --porcelain --untracked-files=no -- tools research/*.py research/*.js research/*.json public/*.js public/*.html src package.json
if ($dirty) { Log ('skip: tracked code differs from ' + $head.Substring(0,7) + ': ' + (($dirty | Select-Object -First 3) -join '; ')); exit 0 }
$lock = Join-Path $dir '.running'
if (Test-Path -LiteralPath $lock) {
  $age = ((Get-Date) - (Get-Item -LiteralPath $lock).LastWriteTime).TotalMinutes
  if ($age -lt 60) { exit 0 }
}
Set-Content -LiteralPath $lock -Value $PID -Encoding ASCII
try {
  $runtimeJson = Join-Path $root 'runtime\test-python.json'
  if (Test-Path -LiteralPath $runtimeJson) {
    $rt = Get-Content -LiteralPath $runtimeJson -Raw | ConvertFrom-Json
    if ($rt.python) { $env:BEOPS_TEST_PYTHON = [string]$rt.python; $env:BEOPS_PYTHON = [string]$rt.python }
    if ($rt.pythonpath) { $env:BEOPS_TEST_PYTHONPATH = [string]$rt.pythonpath }
  }
  Remove-Item Env:BEOPS_CYCLE_DEADLINE -ErrorAction SilentlyContinue
  $started = [DateTimeOffset]::UtcNow
  Log ('start ' + $head.Substring(0,7))
  $out = Join-Path $dir ($head + '.txt')
  $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  & node tools\test-research.js *> $out
  $rc = $LASTEXITCODE
  $ErrorActionPreference = $prev
  $finished = [DateTimeOffset]::UtcNow
  $tail = @(Get-Content -LiteralPath $out -Tail 12 -ErrorAction SilentlyContinue | ForEach-Object { [string]$_ }) -join "`n"
  $receipt = [ordered]@{
    schema = 'beops-code-gate/v1'; source_oid = $head; source_tree = $tree; passed = ($rc -eq 0); exit_code = $rc
    started_at = $started.ToString('o'); finished_at = $finished.ToString('o')
    seconds = [Math]::Round(($finished - $started).TotalSeconds, 1)
    python = [string]$env:BEOPS_TEST_PYTHON; output_tail = $tail
  }
  $tmp = $receiptPath + '.tmp'
  [IO.File]::WriteAllText($tmp, ($receipt | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding($false)))
  Move-Item -LiteralPath $tmp -Destination $receiptPath -Force
  Log ('done ' + $head.Substring(0,7) + ' passed=' + ($rc -eq 0) + ' ' + $receipt.seconds + ' s')
  exit $rc
} finally { Remove-Item -LiteralPath $lock -Force -ErrorAction SilentlyContinue }
