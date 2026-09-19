# Lightweight cadence gate for a legacy scheduler registration. A successful
# publication starts a quiet window; failed attempts remain immediately eligible
# so a transient gate failure is retried by the next scheduled tick.
param(
  [string]$ReceiptPath = '',
  [string]$StatusPath = '',
  [DateTimeOffset]$NowUtc = [DateTimeOffset]::UtcNow,
  [double]$MinimumMinutes = 29
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
    age_minutes = if ($AgeMinutes -ne $null) { [Math]::Round([double]$AgeMinutes, 3) } else { $null }
    receipt_path = $ReceiptPath
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

if (-not (Test-Path -LiteralPath $ReceiptPath)) {
  Write-PublishDueStatus -Decision 'due' -ExitCode 0 -Reason 'no_successful_receipt'
  Write-Output 'publish due: no successful receipt'
  exit 0
}

try {
  $receipt = Get-Content -LiteralPath $ReceiptPath -Raw | ConvertFrom-Json
  if (-not $receipt.published -or -not $receipt.at) {
    Write-PublishDueStatus -Decision 'due' -ExitCode 0 -Reason 'last_receipt_not_successful' -Receipt $receipt
    Write-Output 'publish due: last receipt is not a successful publication'
    exit 0
  }
  $finishedAt = [DateTimeOffset]::Parse([string]$receipt.at).ToUniversalTime()
  # A release can take longer than the cadence itself on the observatory disk. The
  # quiet window begins only after the verified release finishes; measuring from
  # cycle_started_at otherwise creates an almost continuous publish loop.
  $publishedAt = $finishedAt
} catch {
  Write-PublishDueStatus -Decision 'due' -ExitCode 0 -Reason 'successful_receipt_unreadable'
  Write-Output 'publish due: successful receipt is unreadable'
  exit 0
}

$ageMinutes = ($NowUtc.ToUniversalTime() - $publishedAt).TotalMinutes
if ($ageMinutes -ge 0 -and $ageMinutes -lt $MinimumMinutes) {
  Write-PublishDueStatus -Decision 'quiet' -ExitCode 75 -Reason 'recent_success' -Receipt $receipt -AgeMinutes $ageMinutes
  Write-Output ('publish quiet: last success was {0:N1} minutes ago' -f $ageMinutes)
  exit 75
}

Write-PublishDueStatus -Decision 'due' -ExitCode 0 -Reason 'minimum_elapsed' -Receipt $receipt -AgeMinutes $ageMinutes
Write-Output ('publish due: last success was {0:N1} minutes ago' -f $ageMinutes)
exit 0
