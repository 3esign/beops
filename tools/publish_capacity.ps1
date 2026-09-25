# Refuse an expensive public release when the observatory body is already under
# memory pressure. The publish tick treats exit 75 as a quiet skip.
param(
  [string]$StatusPath = '',
  [double]$MinimumFreeMB = -1,
  [object]$ObservedFreeMB = $null,
  [object]$ObservedTotalMB = $null,
  [DateTimeOffset]$NowUtc = [DateTimeOffset]::UtcNow
)
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $StatusPath) {
  $StatusPath = Join-Path $root 'data\live\publish-capacity-status.json'
}

if ($MinimumFreeMB -lt 0) {
  if ($env:BEOPS_PUBLISH_MIN_FREE_MB) {
    $MinimumFreeMB = [double]$env:BEOPS_PUBLISH_MIN_FREE_MB
  } else {
    $MinimumFreeMB = 256
  }
}

function Write-CapacityStatus {
  param(
    [string]$Decision,
    [int]$ExitCode,
    [string]$Reason,
    [object]$FreeMB,
    [object]$TotalMB
  )
  $dir = Split-Path $StatusPath -Parent
  if ($dir -and -not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
  $row = [ordered]@{
    schema = 'beops-publish-capacity-status/v1'
    at = $NowUtc.ToUniversalTime().ToString('o')
    decision = $Decision
    exit_code = $ExitCode
    reason = $Reason
    free_mb = if ($FreeMB -ne $null) { [Math]::Round([double]$FreeMB, 1) } else { $null }
    total_mb = if ($TotalMB -ne $null) { [Math]::Round([double]$TotalMB, 1) } else { $null }
    minimum_free_mb = [Math]::Round([double]$MinimumFreeMB, 1)
  }
  $tmp = $StatusPath + '.' + $PID + '.tmp'
  $row | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $tmp -Encoding UTF8
  Move-Item -LiteralPath $tmp -Destination $StatusPath -Force
}

if ($ObservedFreeMB -eq $null) {
  try {
    $os = Get-CimInstance Win32_OperatingSystem
    $ObservedFreeMB = [double]$os.FreePhysicalMemory / 1024
    $ObservedTotalMB = [double]$os.TotalVisibleMemorySize / 1024
  } catch {
    Write-CapacityStatus -Decision 'quiet' -ExitCode 75 -Reason 'capacity_unknown' -FreeMB $null -TotalMB $null
    Write-Output 'publish quiet: memory capacity could not be measured'
    exit 75
  }
}

if ([double]$ObservedFreeMB -lt $MinimumFreeMB) {
  Write-CapacityStatus -Decision 'quiet' -ExitCode 75 -Reason 'low_memory' -FreeMB $ObservedFreeMB -TotalMB $ObservedTotalMB
  Write-Output ('publish quiet: free memory {0:N1} MB is below {1:N1} MB' -f [double]$ObservedFreeMB, [double]$MinimumFreeMB)
  exit 75
}

Write-CapacityStatus -Decision 'ready' -ExitCode 0 -Reason 'capacity_ok' -FreeMB $ObservedFreeMB -TotalMB $ObservedTotalMB
Write-Output ('publish capacity ok: free memory {0:N1} MB' -f [double]$ObservedFreeMB)
exit 0
