# Safety helpers for tools\publish_github.ps1.
# Kept separate so tests can execute the hard boundaries without running a real publish.

if (-not ('BeopsPhysicalPath' -as [type])) {
  Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class BeopsPhysicalPath {
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern SafeFileHandle CreateFile(string name, uint access, uint share, IntPtr security, uint mode, uint flags, IntPtr template);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern uint GetFinalPathNameByHandle(SafeFileHandle file, StringBuilder path, uint size, uint flags);
  public static string Resolve(string name) {
    using (var handle=CreateFile(name,0,7,IntPtr.Zero,3,0x02000000,IntPtr.Zero)) {
      if(handle.IsInvalid) throw new System.IO.IOException("Cannot resolve physical path: "+name);
      var text=new StringBuilder(32768);
      uint size=GetFinalPathNameByHandle(handle,text,(uint)text.Capacity,0);
      if(size==0||size>=text.Capacity) throw new System.IO.IOException("Cannot resolve physical path: "+name);
      var result=text.ToString();
      if(result.StartsWith(@"\\?\UNC\")) return @"\\"+result.Substring(8);
      return result.StartsWith(@"\\?\") ? result.Substring(4) : result;
    }
  }
}
'@
}

function Get-BeopsFullPath {
  param([Parameter(Mandatory=$true)][string]$Path)
  $candidate = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path (Get-Location).Path $Path }
  $full = [System.IO.Path]::GetFullPath($candidate)
  if (Test-Path -LiteralPath $full) {
    $resolved = [BeopsPhysicalPath]::Resolve($full)
    if ($resolved -eq [System.IO.Path]::GetPathRoot($resolved)) { return $resolved }
    return $resolved.TrimEnd('\', '/')
  }
  $parent = Split-Path -Parent $full
  if ($parent -and $parent -ne $full) { return Join-Path (Get-BeopsFullPath $parent) (Split-Path -Leaf $full) }
  return $full
}

function Test-BeopsSameOrInside {
  param(
    [Parameter(Mandatory=$true)][string]$Parent,
    [Parameter(Mandatory=$true)][string]$Child
  )
  $p = Get-BeopsFullPath $Parent
  $c = Get-BeopsFullPath $Child
  $cmp = [System.StringComparison]::OrdinalIgnoreCase
  return $c.Equals($p, $cmp) -or $c.StartsWith($p + [System.IO.Path]::DirectorySeparatorChar, $cmp)
}

function Get-BeopsGitOrigin {
  param([Parameter(Mandatory=$true)][string]$Repo)
  if (-not (Test-Path -LiteralPath (Join-Path $Repo '.git'))) { return '' }
  $origin = git -C $Repo remote get-url origin 2>$null
  if ($LASTEXITCODE -ne 0) { return '' }
  return (($origin -join "`n").Trim())
}

function Test-BeopsExpectedRemote {
  param(
    [string]$Actual,
    [string]$Expected
  )
  if (-not $Actual) { return $false }
  if ($Actual -eq $Expected) { return $true }
  $norm = $Actual -replace '^git@github.com:', 'https://github.com/' -replace '\.git$', ''
  $want = $Expected -replace '\.git$', ''
  return $norm -eq $want
}

function Assert-BeopsPublicRootSafe {
  param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$PublicRoot,
    [string]$ExpectedRemote = 'https://github.com/3esign/beops.git'
  )
  $src = Get-BeopsFullPath $SourceRoot
  $pub = Get-BeopsFullPath $PublicRoot
  $driveRoot = ([System.IO.Path]::GetPathRoot($pub)).TrimEnd('\', '/')
  if ($pub.TrimEnd('\', '/').Equals($driveRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "unsafe public root '$pub': drive root cannot be an export target"
  }
  if (Test-BeopsSameOrInside -Parent $src -Child $pub) {
    throw "unsafe public root '$pub': it is the source repository or inside it"
  }
  if (Test-BeopsSameOrInside -Parent $pub -Child $src) {
    throw "unsafe public root '$pub': it contains the source repository"
  }
  $leaf = Split-Path -Leaf $pub
  if ($leaf -ne 'Beops-public') {
    $origin = Get-BeopsGitOrigin $pub
    if (-not (Test-BeopsExpectedRemote -Actual $origin -Expected $ExpectedRemote)) {
      throw "unsafe public root '$pub': custom target must be the expected public remote"
    }
  } else {
    $origin = Get-BeopsGitOrigin $pub
    $nonempty = (Test-Path -LiteralPath $pub) -and @(Get-ChildItem -LiteralPath $pub -Force).Count -gt 0
    if ($nonempty -and -not (Test-BeopsExpectedRemote -Actual $origin -Expected $ExpectedRemote)) {
      throw "unsafe public root '$pub': origin '$origin' is not the expected public remote"
    }
  }
  if (Test-Path -LiteralPath (Join-Path $pub '.git')) {
    $dirty = git -C $pub status --porcelain --untracked-files=all 2>&1
    if ($LASTEXITCODE -ne 0 -or ($dirty -join '').Trim()) { throw "unsafe public root '$pub': mirror has uncommitted or unreadable state" }
    $head = git -C $pub rev-parse --verify --quiet HEAD
    if ($LASTEXITCODE -eq 0) {
      $marker = Join-Path $pub '.git\beops-export-owner.json'
      if (-not (Test-Path -LiteralPath $marker)) { throw "public mirror needs explicit ownership registration: $pub" }
      $owner = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
      if ($owner.schema -ne 'beops-public-owner/v1' -or $owner.path -ne $pub -or -not (Test-BeopsExpectedRemote -Actual $owner.remote -Expected $ExpectedRemote)) { throw 'invalid public mirror ownership marker' }
    }
  }
  return $pub
}

function Register-BeopsPublicOwnership {
  param([Parameter(Mandatory=$true)][string]$PublicRoot)
  $pub = Get-BeopsFullPath $PublicRoot
  $origin = Get-BeopsGitOrigin $pub
  if (-not (Test-BeopsExpectedRemote -Actual $origin -Expected 'https://github.com/3esign/beops.git')) { throw 'ownership registration requires the BEOPS public remote' }
  $dirty = git -C $pub status --porcelain --untracked-files=all
  if ($LASTEXITCODE -ne 0 -or ($dirty -join '').Trim()) { throw 'ownership registration requires a clean mirror' }
  [ordered]@{schema='beops-public-owner/v1';path=$pub;remote=$origin;registered_at=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $pub '.git\beops-export-owner.json') -Encoding UTF8
}

function Assert-BeopsDeletionTarget {
  param(
    [Parameter(Mandatory=$true)][string]$PublicRoot,
    [Parameter(Mandatory=$true)][string]$Target
  )
  $pub = Get-BeopsFullPath $PublicRoot
  $targetPath = Get-BeopsFullPath $Target
  if ($targetPath.Equals($pub, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "refusing to delete export root '$targetPath'"
  }
  if (-not (Test-BeopsSameOrInside -Parent $pub -Child $targetPath)) {
    throw "refusing to delete '$targetPath': not inside export root '$pub'"
  }
  return $targetPath
}

function Get-BeopsPublishLockInfo {
  param([Parameter(Mandatory=$true)][string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    return [pscustomobject]@{ Exists = $false; Path = $Path; Pid = $null; AgeMinutes = $null; Text = '' }
  }
  $item = Get-Item -LiteralPath $Path
  $text = ''
  try { $text = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop } catch {}
  $pidValue = $null
  if ($text -match '\bpid\s+([0-9]+)\b') { $pidValue = [int]$Matches[1] }
  $age = ((Get-Date) - $item.LastWriteTime).TotalMinutes
  return [pscustomobject]@{ Exists = $true; Path = $item.FullName; Pid = $pidValue; AgeMinutes = $age; Text = $text }
}

function Test-BeopsProcessAlive {
  param([Nullable[int]]$ProcessId)
  if (-not $ProcessId) { return $false }
  try {
    $null = Get-Process -Id $ProcessId -ErrorAction Stop
    return $true
  } catch {
    return $false
  }
}

function Test-BeopsPublishLockOwnedByCurrentProcess {
  param([Parameter(Mandatory=$true)][string]$Path)
  $info = Get-BeopsPublishLockInfo $Path
  return $info.Exists -and $info.Pid -eq $PID
}

function New-BeopsPublishLock {
  param([Parameter(Mandatory=$true)][string]$Path)
  $dir = Split-Path $Path -Parent
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  try {
    $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    try {
      $bytes = [System.Text.Encoding]::UTF8.GetBytes("pid $PID at " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))
      $fs.Write($bytes, 0, $bytes.Length)
    } finally {
      $fs.Close()
    }
    return $true
  } catch [System.IO.IOException] {
    return $false
  }
}

function Clear-BeopsAbandonedPublishLock {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [double]$MaxAgeMinutes = 15
  )
  $info = Get-BeopsPublishLockInfo $Path
  if (-not $info.Exists) {
    return [pscustomobject]@{ Removed = $false; Reason = 'missing'; Info = $info }
  }
  if ($info.AgeMinutes -lt $MaxAgeMinutes) {
    return [pscustomobject]@{ Removed = $false; Reason = 'recent'; Info = $info }
  }
  if ($info.Pid -and (Test-BeopsProcessAlive -ProcessId $info.Pid)) {
    return [pscustomobject]@{ Removed = $false; Reason = 'owner-running'; Info = $info }
  }
  Remove-Item -LiteralPath $Path -Force -ErrorAction Stop
  return [pscustomobject]@{ Removed = $true; Reason = 'abandoned'; Info = $info }
}

function Enter-BeopsPublishLock {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [double]$MaxAgeMinutes = 15
  )
  $recovered = $false
  if (Test-Path -LiteralPath $Path) {
    $clear = Clear-BeopsAbandonedPublishLock -Path $Path -MaxAgeMinutes $MaxAgeMinutes
    if (-not $clear.Removed -and $clear.Reason -ne 'missing') {
      $age = if ($clear.Info.AgeMinutes -ne $null) { "{0:N1}" -f $clear.Info.AgeMinutes } else { "unknown" }
      return [pscustomobject]@{ Acquired = $false; Recovered = $false; Reason = $clear.Reason; AgeMinutes = $clear.Info.AgeMinutes; Message = "another publish holds the lock ($($clear.Reason), age $age min)" }
    }
    $recovered = $clear.Removed
  }
  if (New-BeopsPublishLock -Path $Path) {
    $msg = if ($recovered) { 'an abandoned publish lock was removed and retaken' } else { 'publish lock acquired' }
    return [pscustomobject]@{ Acquired = $true; Recovered = $recovered; Reason = 'acquired'; AgeMinutes = 0; Message = $msg }
  }
  return [pscustomobject]@{ Acquired = $false; Recovered = $false; Reason = 'race'; AgeMinutes = 0; Message = 'another publish took the lock first' }
}

function Save-BeopsReleaseDiagnostic {
  param([string]$SourceRoot, [string]$RunRoot, [string]$SourceOid, [string]$Outcome)
  $folder = Join-Path $SourceRoot 'runtime\release-diagnostics'
  New-Item -ItemType Directory -Path $folder -Force | Out-Null
  $run = Split-Path $RunRoot -Leaf
  if ($run -notmatch '^beops-release-[a-f0-9]{32}$') { throw 'unexpected release diagnostic name' }
  $receiptFile = Join-Path $SourceRoot 'data\live\publish-receipt.json'
  $lastReceipt = $null
  $receiptNote = 'no receipt exists'
  if (Test-Path -LiteralPath $receiptFile) {
    try {
      $candidate = Get-Content -LiteralPath $receiptFile -Raw | ConvertFrom-Json
      if ($candidate.source_head -eq $SourceOid) {
        $lastReceipt = $candidate
        $receiptNote = 'matching receipt attached'
      } else {
        $receiptNote = 'existing receipt belongs to another source OID'
      }
    } catch {
      $receiptNote = 'existing receipt is unreadable'
    }
  }
  $transcript = Get-ChildItem -LiteralPath (Join-Path $RunRoot 'runtime') -File -Filter 'publish-tests-*.txt' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  # The child deletes its PID-specific transcript after writing this completed copy.
  # Preserve it before the outer publisher removes the generated workspace.
  if (-not $transcript) {
    $transcript = Get-Item -LiteralPath (Join-Path $RunRoot 'runtime\publish-tests.txt') -ErrorAction SilentlyContinue
  }
  $transcriptName = $null
  if ($transcript) {
    $transcriptName = $run + '-tests.txt'
    Copy-Item -LiteralPath $transcript.FullName -Destination (Join-Path $folder $transcriptName) -Force
  }
  $phaseName = $null
  if ($env:BEOPS_PHASE_TRACE -and (Test-Path -LiteralPath $env:BEOPS_PHASE_TRACE)) {
    $phaseName = $run + '-phases.jsonl'
    Copy-Item -LiteralPath $env:BEOPS_PHASE_TRACE -Destination (Join-Path $folder $phaseName) -Force
  }
  @{schema='beops-release-diagnostic/v1'; at=(Get-Date).ToUniversalTime().ToString('o'); source_oid=$SourceOid; workspace=$RunRoot; outcome=$Outcome; receipt_note=$receiptNote; receipt=$lastReceipt; test_transcript=$transcriptName; phase_transcript=$phaseName} |
    ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $folder ($run + '.json')) -Encoding UTF8
  # This directory contains our diagnostics, not source/evidence. Keep ten runs.
  $older = Get-ChildItem -LiteralPath $folder -File -Filter 'beops-release-*.json' | Sort-Object LastWriteTime -Descending | Select-Object -Skip 10
  foreach ($item in $older) {
    $record = Get-Content -LiteralPath $item.FullName -Raw | ConvertFrom-Json
    if ($record.schema -eq 'beops-release-diagnostic/v1' -and $item.Name -match '^beops-release-[a-f0-9]{32}\.json$') {
      $oldTranscript = Join-Path $folder ($item.BaseName + '-tests.txt')
      if (Test-Path -LiteralPath $oldTranscript) { Remove-Item -LiteralPath $oldTranscript -Force }
      $oldPhases = Join-Path $folder ($item.BaseName + '-phases.jsonl')
      if (Test-Path -LiteralPath $oldPhases) { Remove-Item -LiteralPath $oldPhases -Force }
      Remove-Item -LiteralPath $item.FullName -Force
    }
  }
}

function Remove-BeopsGeneratedRelease {
  param([string]$Path, [string]$SourceRoot, [string]$BaseRoot)
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $full = Get-BeopsFullPath $Path
  $base = Get-BeopsFullPath $BaseRoot
  $source = Get-BeopsFullPath $SourceRoot
  if ((Split-Path $full -Parent) -ne $base -or (Split-Path $full -Leaf) -notmatch '^beops-release-[a-f0-9]{32}$' -or (Test-BeopsSameOrInside -Parent $full -Child $source)) {
    throw 'release cleanup boundary refused'
  }
  $marker = Join-Path $full '.beops-generated-workspace.json'
  if (-not (Test-Path -LiteralPath $marker)) { return } # never touch an unowned directory
  $owned = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
  if ((Get-BeopsFullPath $owned.destination) -ne $full -or (Get-BeopsFullPath $owned.source) -ne $source) { throw 'release owner marker mismatch' }
  if (Get-ChildItem -LiteralPath $full -Force -Recurse -Attributes ReparsePoint | Select-Object -First 1) { throw 'release cleanup contains a link' }
  Remove-Item -LiteralPath $full -Recurse -Force -ErrorAction Stop
}

function Clear-BeopsAbandonedReleases {
  param([string]$SourceRoot, [string]$BaseRoot)
  if (-not (Test-Path -LiteralPath $BaseRoot)) { return }
  foreach ($item in Get-ChildItem -LiteralPath $BaseRoot -Directory -Filter 'beops-release-*') {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
    if ($item.Name -notmatch '^beops-release-[a-f0-9]{32}$') { continue }
    $marker = Join-Path $item.FullName '.beops-generated-workspace.json'
    if (-not (Test-Path -LiteralPath $marker)) { continue }
    try {
      $owner = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
      if ($owner.schema -ne 'beops-generated-workspace/v2' -or $owner.retained -ne $false -or [int]$owner.owner_pid -le 0) { continue }
      if ((Get-BeopsFullPath $owner.source) -ne (Get-BeopsFullPath $SourceRoot)) { continue }
      if (([DateTimeOffset]::UtcNow - [DateTimeOffset]::Parse($owner.created_at)).TotalHours -lt 2) { continue }
      if (Test-BeopsProcessAlive -ProcessId ([int]$owner.owner_pid)) { continue }
      Save-BeopsReleaseDiagnostic -SourceRoot $SourceRoot -RunRoot $item.FullName -SourceOid $owner.source_oid -Outcome 'abandoned-cleanup'
      Remove-BeopsGeneratedRelease -Path $item.FullName -SourceRoot $SourceRoot -BaseRoot $BaseRoot
      Write-Output ('Removed owned abandoned release: ' + $item.Name)
    } catch { Write-Warning ('Release preserved: ' + $item.Name + ': ' + $_.Exception.Message) }
  }
}

function Write-BeopsPhase {
  param([string]$Name, [System.Diagnostics.Stopwatch]$Clock, [object]$ExitCode)
  if (-not $env:BEOPS_PHASE_TRACE) { return }
  $row = @{schema='beops-phase/v1';at=[DateTime]::UtcNow.ToString('o');name=$Name;
    seconds=[Math]::Round($Clock.Elapsed.TotalSeconds,3);exit_code=$ExitCode;pid=$PID}
  $line = ($row | ConvertTo-Json -Compress) + [Environment]::NewLine
  [IO.File]::AppendAllText($env:BEOPS_PHASE_TRACE, $line, (New-Object Text.UTF8Encoding($false)))
}

function Invoke-BeopsTimedProcess {
  param([string]$FilePath, [string[]]$ArgumentList, [int]$TimeoutMilliseconds = 120000)
  if ($env:BEOPS_CYCLE_DEADLINE) {
    $remaining = ([DateTimeOffset]::Parse($env:BEOPS_CYCLE_DEADLINE)-[DateTimeOffset]::UtcNow).TotalMilliseconds
    if ($remaining -le 0) { throw 'publication cycle budget exhausted before next phase' }
    $TimeoutMilliseconds = [int][Math]::Min($remaining, [int]::MaxValue)
  }
  $command = (Get-Command $FilePath -ErrorAction Stop).Source
  $quote = {
    param([string]$value)
    '"' + [regex]::Replace([regex]::Replace($value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
  }
  $arguments = @($ArgumentList | ForEach-Object { & $quote $_ }) -join ' '
  $info = New-Object Diagnostics.ProcessStartInfo
  if ($command -match '\.(cmd|bat)$') {
    foreach ($value in (@($command)+$ArgumentList)) {
      if ($value -match '[%"\r\n]') { throw 'unsafe batch argument; use a direct interpreter executable' }
    }
    $info.FileName = $env:ComSpec
    $info.Arguments = '/d /s /v:off /c "' + (& $quote $command) + ' ' + $arguments + '"'
  } else {
    $info.FileName = $command
    $info.Arguments = $arguments
  }
  $info.WorkingDirectory = (Get-Location).Path
  $info.UseShellExecute = $false
  $info.CreateNoWindow = $true
  $info.RedirectStandardOutput = $true
  $info.RedirectStandardError = $true
  $info.StandardOutputEncoding = New-Object Text.UTF8Encoding($false)
  $info.StandardErrorEncoding = New-Object Text.UTF8Encoding($false)
  $process = New-Object Diagnostics.Process
  $process.StartInfo = $info
  try {
    if (-not $process.Start()) { throw 'native phase did not start' }
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit($TimeoutMilliseconds)) {
      # Only the process tree created above belongs to this phase.
      & "$env:SystemRoot\System32\taskkill.exe" /PID $process.Id /T /F 2>&1 | Out-Null
      $null = $process.WaitForExit(5000)
      throw 'publication phase exceeded the remaining cycle budget'
    }
    return @{code=$process.ExitCode;stdout=$stdout.GetAwaiter().GetResult();stderr=$stderr.GetAwaiter().GetResult()}
  } finally { $process.Dispose() }
}

function Assert-BeopsCycleRemaining {
  if ($env:BEOPS_CYCLE_DEADLINE -and [DateTimeOffset]::UtcNow -ge [DateTimeOffset]::Parse($env:BEOPS_CYCLE_DEADLINE)) {
    throw 'publication cycle budget exhausted before next copy operation'
  }
}

function Invoke-BeopsRecovery {
  param([string]$Name, [string]$FilePath, [string[]]$ArgumentList = @())
  $processingDeadline = $env:BEOPS_CYCLE_DEADLINE
  try {
    # Recovery uses only the existing five-minute reserve after processing.
    # Never renew the processing budget or continue publication in this scope.
    $limit = if ($processingDeadline) { [DateTimeOffset]::Parse($processingDeadline).AddMinutes(5) } else { [DateTimeOffset]::UtcNow.AddMinutes(5) }
    $env:BEOPS_CYCLE_DEADLINE = $limit.ToString('o')
    Invoke-BeopsNative -Name $Name -FilePath $FilePath -ArgumentList $ArgumentList -Quiet
  } finally { $env:BEOPS_CYCLE_DEADLINE = $processingDeadline }
}

function Invoke-BeopsNative {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$FilePath,
    [string[]]$ArgumentList = @(),
    [switch]$Quiet
  )
  $clock = [Diagnostics.Stopwatch]::StartNew()
  $rc = $null
  try {
  if ($env:BEOPS_CYCLE_DEADLINE) {
    $result = Invoke-BeopsTimedProcess -FilePath $FilePath -ArgumentList $ArgumentList
    $rc = $result.code
    if ($rc -ne 0) { throw "$Name failed with exit code ${rc}: $($result.stderr.Trim())" }
    if (-not $Quiet -and $result.stdout) { Write-Output $result.stdout.TrimEnd() }
    return
  }
  if ($Quiet) {
    & $FilePath @ArgumentList | Out-Null
  } else {
    & $FilePath @ArgumentList
  }
  $rc = if ($LASTEXITCODE -ne $null) { [int]$LASTEXITCODE } else { 0 }
  if ($rc -ne 0) {
    throw "$Name failed with exit code $rc"
  }
  } finally { Write-BeopsPhase -Name $Name -Clock $clock -ExitCode $rc }
}

function Get-BeopsNativeOutput {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$FilePath,
    [string[]]$ArgumentList = @()
  )
  if ($env:BEOPS_CYCLE_DEADLINE) {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $rc = $null
    try {
      $result = Invoke-BeopsTimedProcess -FilePath $FilePath -ArgumentList $ArgumentList
      $rc = $result.code
      if ($rc -ne 0) { throw "$Name failed with exit code ${rc}: $($result.stdout.Trim())`n$($result.stderr.Trim())" }
      return $result.stdout.Trim()
    } finally { Write-BeopsPhase -Name $Name -Clock $clock -ExitCode $rc }
  }
  # Windows PowerShell 5 turns native stderr into ErrorRecord objects. With
  # Stop it can interrupt at the first traceback line, before the exit code.
  # Keep streams separate: a successful command may warn and still emit JSON.
  $null = Get-Command $FilePath -ErrorAction Stop
  $capture = Join-Path ([IO.Path]::GetTempPath()) ('beops-native-' + [guid]::NewGuid())
  $null = New-Item -ItemType Directory -Path $capture -ErrorAction Stop
  $priorPreference = $ErrorActionPreference
  $clock = [Diagnostics.Stopwatch]::StartNew()
  $rc = $null
  try {
    $stdout = Join-Path $capture 'stdout.txt'
    $stderr = Join-Path $capture 'stderr.txt'
    $ErrorActionPreference = 'Continue'
    & $FilePath @ArgumentList 1> $stdout 2> $stderr
    $rc = [int]$LASTEXITCODE
    $ErrorActionPreference = $priorPreference
    $text = [IO.File]::ReadAllText($stdout)
    $errors = [IO.File]::ReadAllText($stderr)
    if ($rc -ne 0) {
      throw "$Name failed with exit code ${rc}: $($text.Trim())`n$($errors.Trim())"
    }
    return $text.Trim()
  } finally {
    Write-BeopsPhase -Name $Name -Clock $clock -ExitCode $rc
    $ErrorActionPreference = $priorPreference
    # This GUID directory and its two files were created by this invocation.
    Remove-Item -LiteralPath $capture -Recurse -Force -ErrorAction SilentlyContinue
  }
}
