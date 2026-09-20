# Serialize the two baseline builders with outer publish preparation.  The
# batch wrapper may avoid obvious contention, but this atomic lock is the
# boundary that prevents a race with publish_github.ps1.
param(
  [string]$ProjectRoot = '',
  [string]$PythonPath = '',
  [ValidateRange(1, 86400)][int]$TimeoutSeconds = 1200
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'publish_safety.ps1')

if (-not $ProjectRoot) { $ProjectRoot = Join-Path $PSScriptRoot '..' }
$project = (Resolve-Path -LiteralPath $ProjectRoot).Path
$runtime = Join-Path $project 'runtime'
$preparationLockFile = Join-Path $runtime 'publish-preparation.lock'
$preparationLock = Enter-BeopsPublishLock -Path $preparationLockFile -MaxAgeMinutes 15

# Contention is normal: the scheduled baseline quietly yields to publication.
if (-not $preparationLock.Acquired) { exit 0 }

$previousLocation = (Get-Location).Path
$exitCode = 125
try {
  if (-not $PythonPath) { $PythonPath = $env:BEOPS_PYTHON }
  if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw 'baseline Python executable is unavailable'
  }
  $boundedRunner = Join-Path $PSScriptRoot 'run_bounded.ps1'
  if (-not (Test-Path -LiteralPath $boundedRunner -PathType Leaf)) {
    throw 'bounded baseline runner is unavailable'
  }

  $logPath = Join-Path $runtime 'baseline-tick.log'
  $statusPath = Join-Path $runtime 'baseline-bounded-status.json'
  $stamp = '---- ' + [DateTimeOffset]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ') + "`r`n"
  [IO.File]::AppendAllText($logPath, $stamp, (New-Object Text.UTF8Encoding($false)))
  Set-Location -LiteralPath $project

  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $boundedRunner `
    -Name 'history qualification' -FilePath $PythonPath `
    -Arguments '-X utf8 -B tools\history_qualification.py build' `
    -LogPath $logPath -StatusPath $statusPath -TimeoutSeconds $TimeoutSeconds `
    -AllowedRoot $project
  $exitCode = if ($LASTEXITCODE -ne $null) { [int]$LASTEXITCODE } else { 125 }

  if ($exitCode -eq 0) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $boundedRunner `
      -Name 'baseline build' -FilePath $PythonPath `
      -Arguments '-X utf8 -B tools\baseline.py build' `
      -LogPath $logPath -StatusPath $statusPath -TimeoutSeconds $TimeoutSeconds `
      -AllowedRoot $project
    $exitCode = if ($LASTEXITCODE -ne $null) { [int]$LASTEXITCODE } else { 125 }
  }
} finally {
  Set-Location -LiteralPath $previousLocation
  if ((Test-Path -LiteralPath $preparationLockFile) -and
      (Test-BeopsPublishLockOwnedByCurrentProcess -Path $preparationLockFile)) {
    Remove-Item -LiteralPath $preparationLockFile -Force -ErrorAction SilentlyContinue
  }
}

exit $exitCode
