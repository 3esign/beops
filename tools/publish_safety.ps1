# Safety helpers for tools\publish_github.ps1.
# Kept separate so tests can execute the hard boundaries without running a real publish.

function Get-BeopsFullPath {
  param([Parameter(Mandatory=$true)][string]$Path)
  $candidate = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path (Get-Location).Path $Path }
  return ([System.IO.Path]::GetFullPath($candidate)).TrimEnd('\', '/')
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
  if ($pub.Equals($driveRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
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
    if ($origin -and -not (Test-BeopsExpectedRemote -Actual $origin -Expected $ExpectedRemote)) {
      throw "unsafe public root '$pub': origin '$origin' is not the expected public remote"
    }
  }
  return $pub
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

function Invoke-BeopsNative {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$FilePath,
    [string[]]$ArgumentList = @(),
    [switch]$Quiet
  )
  if ($Quiet) {
    & $FilePath @ArgumentList | Out-Null
  } else {
    & $FilePath @ArgumentList
  }
  $rc = if ($LASTEXITCODE -ne $null) { [int]$LASTEXITCODE } else { 0 }
  if ($rc -ne 0) {
    throw "$Name failed with exit code $rc"
  }
}

function Get-BeopsNativeOutput {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$FilePath,
    [string[]]$ArgumentList = @()
  )
  $out = & $FilePath @ArgumentList 2>&1
  $rc = if ($LASTEXITCODE -ne $null) { [int]$LASTEXITCODE } else { 0 }
  if ($rc -ne 0) {
    $text = (($out | Out-String).Trim())
    throw "$Name failed with exit code ${rc}: $text"
  }
  return (($out | Out-String).Trim())
}
