# Lightweight cadence gate for a legacy scheduler registration. A successful
# publication starts a quiet window; failed attempts remain immediately eligible
# so a transient gate failure is retried by the next scheduled tick.
param(
  [string]$ReceiptPath = '',
  [DateTimeOffset]$NowUtc = [DateTimeOffset]::UtcNow,
  [double]$MinimumMinutes = 29
)
$ErrorActionPreference = 'Stop'

if (-not $ReceiptPath) {
  $root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
  $ReceiptPath = Join-Path $root 'data\live\publish-last-success.json'
}

if (-not (Test-Path -LiteralPath $ReceiptPath)) {
  Write-Output 'publish due: no successful receipt'
  exit 0
}

try {
  $receipt = Get-Content -LiteralPath $ReceiptPath -Raw | ConvertFrom-Json
  if (-not $receipt.published -or -not $receipt.at) {
    Write-Output 'publish due: last receipt is not a successful publication'
    exit 0
  }
  $publishedAt = [DateTimeOffset]::Parse(
    [string]$receipt.at,
    [System.Globalization.CultureInfo]::InvariantCulture,
    [System.Globalization.DateTimeStyles]::AssumeUniversal
  ).ToUniversalTime()
} catch {
  Write-Output 'publish due: successful receipt is unreadable'
  exit 0
}

$ageMinutes = ($NowUtc.ToUniversalTime() - $publishedAt).TotalMinutes
if ($ageMinutes -ge 0 -and $ageMinutes -lt $MinimumMinutes) {
  Write-Output ('publish quiet: last success was {0:N1} minutes ago' -f $ageMinutes)
  exit 75
}

Write-Output ('publish due: last success was {0:N1} minutes ago' -f $ageMinutes)
exit 0
