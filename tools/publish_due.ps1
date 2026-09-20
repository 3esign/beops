# Lightweight cadence gate for a legacy scheduler registration. A successful
# publication starts a quiet window; a failed attempt gets a bounded cooldown so
# repeated full gates cannot starve collection on a constrained body.
param(
  [string]$ReceiptPath = '',
  [string]$StatusPath = '',
  [string]$AttemptReceiptPath = '',
  [DateTimeOffset]$NowUtc = [DateTimeOffset]::UtcNow,
  [double]$MinimumMinutes = 29,
  [double]$FailureCooldownMinutes = 120
)
$ErrorActionPreference = 'Stop'

if (-not $ReceiptPath) {
  $root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
  $ReceiptPath = Join-Path $root 'data\live\publish-last-success.json'
} else {
  $root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}
if (-not $StatusPath) {
  $StatusPath = Join-Path $root 'data\live\publish-scheduler-status.json'
}
if (-not $AttemptReceiptPath) {
  $AttemptReceiptPath = Join-Path $root 'data\live\publish-receipt.json'
}

function Write-PublishDueStatus {
  param(
    [string]$Decision,
    [int]$ExitCode,
    [string]$Reason,
    [object]$Receipt = $null,
    [Nullable[double]]$AgeMinutes = $null
  )
  $dir = Split-Path $StatusPath -Parent
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  $row = [ordered]@{
    schema = 'beops-publish-scheduler-status/v1'
    at = $NowUtc.ToUniversalTime().ToString('o')
    decision = $Decision
    exit_code = $ExitCode
    reason = $Reason
    minimum_minutes = $MinimumMinutes
    failure_cooldown_minutes = $FailureCooldownMinutes
    age_minutes = if ($AgeMinutes -ne $null) { [Math]::Round([double]$AgeMinutes, 3) } else { $null }
    receipt_path = $ReceiptPath
    attempt_receipt_path = $AttemptReceiptPath
    last_success_at = if ($Receipt) { [string]$Receipt.at } else { $null }
    last_success_cycle_started_at = if ($Receipt) { [string]$Receipt.cycle_started_at } else { $null }
    last_success_generated_as_of = if ($Receipt) { [string]$Receipt.generated_as_of } else { $null }
    last_success_source_head = if ($Receipt) { [string]$Receipt.source_head } else { $null }
    last_success_remote_head = if ($Receipt) { [string]$Receipt.remote_head } else { $null }
  }
  $tmp = $StatusPath + '.' + $PID + '.tmp'
  $row | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $tmp -Encoding UTF8
  Move-Item -LiteralPath $tmp -Destination $StatusPath -Force
}

function Stop-InvalidCadenceState {
  param([string]$Reason, [string]$Message)
  Write-PublishDueStatus -Decision 'error' -ExitCode 9 -Reason $Reason
  [Console]::Error.WriteLine($Message)
  exit 9
}

function Test-RecentFailedAttempt {
  if (-not (Test-Path -LiteralPath $AttemptReceiptPath)) { return $false }
  try {
    $attempt = Get-Content -LiteralPath $AttemptReceiptPath -Raw | ConvertFrom-Json
    if (-not $attempt.at) {
      Stop-InvalidCadenceState -Reason 'attempt_receipt_missing_time' -Message 'publish attempt receipt lacks a completion time'
    }
    $attemptAt = [DateTimeOffset]::Parse([string]$attempt.at).ToUniversalTime()
    $attemptAge = ($NowUtc.ToUniversalTime() - $attemptAt).TotalMinutes
    if ($attemptAge -lt 0) {
      Stop-InvalidCadenceState -Reason 'attempt_receipt_from_future' -Message 'publish attempt receipt is dated in the future'
    }
    if ($attempt.published -eq $true) { return $false }
    if ($attemptAge -ge 0 -and $attemptAge -lt $FailureCooldownMinutes) {
      Write-PublishDueStatus -Decision 'quiet' -ExitCode 75 -Reason 'recent_failed_attempt' -Receipt $null -AgeMinutes $attemptAge
      Write-Output ('publish quiet: last failed attempt was {0:N1} minutes ago' -f $attemptAge)
      return $true
    }
  } catch {
    Write-PublishDueStatus -Decision 'error' -ExitCode 9 -Reason 'attempt_receipt_unreadable'
    [Console]::Error.WriteLine('publish cadence state is unreadable; refusing an expensive retry')
    exit 9
  }
  return $false
}

if (-not (Test-Path -LiteralPath $ReceiptPath)) {
  if (Test-RecentFailedAttempt) { exit 75 }
  Write-PublishDueStatus -Decision 'due' -ExitCode 0 -Reason 'no_successful_receipt'
  Write-Output 'publish due: no successful receipt'
  exit 0
}

try {
  $receipt = Get-Content -LiteralPath $ReceiptPath -Raw | ConvertFrom-Json
  if (-not $receipt.published -or -not $receipt.at) {
    if (Test-RecentFailedAttempt) { exit 75 }
    Write-PublishDueStatus -Decision 'error' -ExitCode 9 -Reason 'last_success_receipt_invalid' -Receipt $receipt
    [Console]::Error.WriteLine('last-success receipt is not a successful publication; refusing an expensive retry')
    exit 9
  }
  $finishedAt = [DateTimeOffset]::Parse([string]$receipt.at).ToUniversalTime()
  # A release can take longer than the cadence itself on the observatory disk. The
  # quiet window begins only after the verified release finishes; measuring from
  # cycle_started_at otherwise creates an almost continuous publish loop.
  $publishedAt = $finishedAt
} catch {
  if (Test-RecentFailedAttempt) { exit 75 }
  Write-PublishDueStatus -Decision 'error' -ExitCode 9 -Reason 'successful_receipt_unreadable'
  [Console]::Error.WriteLine('successful receipt is unreadable; refusing an expensive retry')
  exit 9
}

$ageMinutes = ($NowUtc.ToUniversalTime() - $publishedAt).TotalMinutes
if ($ageMinutes -lt 0) {
  Stop-InvalidCadenceState -Reason 'successful_receipt_from_future' -Message 'successful receipt is dated in the future'
}
if ($ageMinutes -ge 0 -and $ageMinutes -lt $MinimumMinutes) {
  Write-PublishDueStatus -Decision 'quiet' -ExitCode 75 -Reason 'recent_success' -Receipt $receipt -AgeMinutes $ageMinutes
  Write-Output ('publish quiet: last success was {0:N1} minutes ago' -f $ageMinutes)
  exit 75
}

if (Test-RecentFailedAttempt) { exit 75 }

Write-PublishDueStatus -Decision 'due' -ExitCode 0 -Reason 'minimum_elapsed' -Receipt $receipt -AgeMinutes $ageMinutes
Write-Output ('publish due: last success was {0:N1} minutes ago' -f $ageMinutes)
exit 0
