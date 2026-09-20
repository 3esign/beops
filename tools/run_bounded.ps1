# Run one trusted BEOPS phase below the outer Task Scheduler deadline.
# If the phase times out, kill only the process tree created here and leave a receipt.
param(
  [Parameter(Mandatory=$true)][string]$Name,
  [Parameter(Mandatory=$true)][string]$FilePath,
  [string]$Arguments = '',
  [Parameter(Mandatory=$true)][string]$LogPath,
  [string]$StatusPath = '',
  [ValidateRange(1, 86400)][int]$TimeoutSeconds = 1200,
  [string]$AllowedRoot = ''
)
$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $AllowedRoot) { $AllowedRoot = $projectRoot }
$allowed = [IO.Path]::GetFullPath($AllowedRoot).TrimEnd('\', '/')
if (-not (Test-Path -LiteralPath $allowed -PathType Container)) {
  throw "bounded phase root does not exist: $allowed"
}

function Resolve-BoundedOutput([string]$Path) {
  $candidate = if ([IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $allowed $Path }
  $full = [IO.Path]::GetFullPath($candidate)
  $prefix = $allowed + [IO.Path]::DirectorySeparatorChar
  if (-not $full.Equals($allowed, [StringComparison]::OrdinalIgnoreCase) -and
      -not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "bounded phase output escapes its allowed root: $full"
  }
  return $full
}

$LogPath = Resolve-BoundedOutput $LogPath
if (-not $StatusPath) { $StatusPath = Join-Path $allowed 'runtime\bounded-last.json' }
$StatusPath = Resolve-BoundedOutput $StatusPath
$logDir = Split-Path $LogPath -Parent
$statusDir = Split-Path $StatusPath -Parent
foreach ($dir in @($logDir, $statusDir, (Join-Path $allowed 'runtime\tmp'))) {
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
}

if (-not (Test-Path -LiteralPath $FilePath)) { throw "bounded phase executable does not exist: $FilePath" }
if ($FilePath -match '[\r\n"]' -or $Arguments -match '[\r\n]') { throw 'unsafe newline or quote in bounded phase command' }

$token = "$PID-" + [guid]::NewGuid().ToString('N')
$tmpDir = Join-Path $allowed 'runtime\tmp'
$runner = Join-Path $tmpDir ("bounded-$token.cmd")
$stdout = Join-Path $tmpDir ("bounded-$token.stdout")
$stderr = Join-Path $tmpDir ("bounded-$token.stderr")
$started = [DateTimeOffset]::UtcNow
$clock = [Diagnostics.Stopwatch]::StartNew()
$child = $null
$timedOut = $false
$exitCode = 125
$failure = $null
$containment = 'not_required'

function Append-Bytes([string]$Source, [string]$Destination) {
  if (-not (Test-Path -LiteralPath $Source)) { return }
  $input = [IO.File]::Open($Source, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
  try {
    $output = [IO.File]::Open($Destination, [IO.FileMode]::Append, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try { $input.CopyTo($output) } finally { $output.Dispose() }
  } finally { $input.Dispose() }
}

try {
  [IO.File]::WriteAllText(
    $runner,
    "@echo off`r`ncall `"$FilePath`" $Arguments 1>`"$stdout`" 2>`"$stderr`"`r`nset `"BEOPS_BOUNDED_RC=%ERRORLEVEL%`"`r`nexit /b %BEOPS_BOUNDED_RC%`r`n",
    [Text.Encoding]::ASCII
  )
  $child = Start-Process -FilePath $env:ComSpec -ArgumentList @('/d', '/s', '/c', "`"$runner`"") `
    -WorkingDirectory $allowed -PassThru -WindowStyle Hidden
  if (-not $child.WaitForExit($TimeoutSeconds * 1000)) {
    $timedOut = $true
    & (Join-Path $env:SystemRoot 'System32\taskkill.exe') /PID $child.Id /T /F 2>$null | Out-Null
    $killExit = $LASTEXITCODE
    $wrapperExited = $child.WaitForExit(10000)
    if ($killExit -eq 0 -and $wrapperExited) {
      $containment = 'tree_terminated'
      $exitCode = 124
    } else {
      $containment = 'containment_failed'
      $failure = "taskkill exit $killExit; wrapper_exited=$wrapperExited"
      $exitCode = 125
    }
  } else {
    $child.WaitForExit()
    $containment = 'process_exited'
    $exitCode = $child.ExitCode
  }
} catch {
  $failure = $_.Exception.Message
  if ($child -and -not $child.HasExited) {
    & (Join-Path $env:SystemRoot 'System32\taskkill.exe') /PID $child.Id /T /F 2>$null | Out-Null
  }
  $exitCode = 125
} finally {
  $clock.Stop()
  Append-Bytes $stdout $LogPath
  Append-Bytes $stderr $LogPath
  if ($timedOut) {
    [IO.File]::AppendAllText($LogPath, "bounded phase timed out: $Name after $TimeoutSeconds seconds`r`n", [Text.Encoding]::UTF8)
  } elseif ($failure) {
    [IO.File]::AppendAllText($LogPath, "bounded phase failed to run: $Name ($failure)`r`n", [Text.Encoding]::UTF8)
  }
  $receipt = [ordered]@{
    schema = 'beops-bounded-phase/v1'
    at = [DateTimeOffset]::UtcNow.ToString('o')
    started_at = $started.ToString('o')
    name = $Name
    pid = if ($child) { $child.Id } else { $null }
    timeout_seconds = $TimeoutSeconds
    elapsed_seconds = [Math]::Round($clock.Elapsed.TotalSeconds, 3)
    timed_out = $timedOut
    containment = $containment
    exit_code = $exitCode
    failure = $failure
  }
  $statusTmp = "$StatusPath.$PID.tmp"
  $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statusTmp -Encoding UTF8
  Move-Item -LiteralPath $statusTmp -Destination $StatusPath -Force
  foreach ($owned in @($runner, $stdout, $stderr)) {
    if (Test-Path -LiteralPath $owned) { Remove-Item -LiteralPath $owned -Force }
  }
}
exit $exitCode
