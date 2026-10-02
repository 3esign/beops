# One small calendar/context transaction sharing BOTH locks with full publication.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'publish_safety.ps1')
$root=Split-Path $PSScriptRoot -Parent
if (Test-Path -LiteralPath (Join-Path $root 'runtime\PUBLISH_PAUSED')) { exit 75 }
if (Test-Path -LiteralPath (Join-Path $root 'runtime\MAINTENANCE')) { exit 75 }
$locks=@()
try {
  foreach($name in @('publish-preparation.lock','publish.lock')) {
    $file=Join-Path $root ('runtime\'+$name)
    $lock=Enter-BeopsPublishLock -Path $file -MaxAgeMinutes 15
    if(-not $lock.Acquired){exit 75}
    $locks+=,$file
  }
  $memory=Get-CimInstance Win32_OperatingSystem
  $disk=Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
  # Group build has bounded inputs and no whole-observation copies. Keep the same
  # two GiB reserve, plus 128 MiB for stage, rollback and Git delta.
  if([int64]$memory.FreePhysicalMemory*1024 -lt 256MB -or [int64]$disk.FreeSpace -lt (2GB+128MB)){exit 75}
  $receipt=Join-Path $root 'data\live\publish-last-success.json'
  if(-not (Test-Path -LiteralPath $receipt)){exit 75}
  $last=Get-Content -Raw -LiteralPath $receipt|ConvertFrom-Json
  $head=(& git -C $root rev-parse HEAD).Trim()
  if($LASTEXITCODE -ne 0){throw 'cannot resolve group source HEAD'}
  if($last.source_head -ne $head -or -not $last.site_verified){exit 75}
  $env:BEOPS_ROOT=$root
  $env:BEOPS_GROUP_LOCKED='1'
  $env:GIT_HTTP_USER_AGENT=(& node (Join-Path $root 'tools\incognito_user_agent.js')).Trim()
  if($LASTEXITCODE -ne 0){throw 'transport identity unavailable'}
  Push-Location $root
  try {
    & node --test research/test_impulse_groups_node.js research/test_impulse_groups_browser_node.js research/test_group_publication_node.js
    if($LASTEXITCODE -ne 0){throw 'group publication gate failed'}
    & node tools/publish_groups.js
    $code=$LASTEXITCODE
  } finally {Pop-Location}
  exit $code
} finally {
  foreach($file in $locks){if(Test-BeopsPublishLockOwnedByCurrentProcess -Path $file){Remove-Item -LiteralPath $file -Force}}
}
