# Publishes a clean export of this repository to GitHub (3esign/beops) as open source.
# Internal working documents (research/06-paper, research/_trail, research/01-programme) stay local: the
# public repository carries the registry, the provenance index, the corrections, the collectors, the organs,
# the tools and the site - the observatory, not its drafts.
# Why an export and not `git push`: the local history carries a 141 MB evidence blob that GitHub
# refuses (>100 MB), and research/evidence/ (585 MB of captured third-party pages) stays local by
# rule - it is proof, not publication. The public repository therefore receives the current tree
# minus evidence, scratch, archives, runtime and live data, as ONE commit per publish, with the
# local commit hash in the message. Tracked source bytes are archived from HEAD, not copied from the
# moving working tree; generated public artefacts are overlaid after the build and named in the
# manifest. Local history is never rewritten.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_github.ps1            # publish
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_github.ps1 -DryRun    # show what would go
param([switch]$DryRun, [switch]$Isolated, [switch]$PrepareOnly, [string]$SourceOid, [string]$StateRoot)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'publish_safety.ps1')
function Resolve-BeopsBundledPython {
  $bundled = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (Test-Path $bundled) { return $bundled }
  return $null
}
function Resolve-BeopsPython {
  if ($env:BEOPS_PYTHON -and (Test-Path $env:BEOPS_PYTHON)) { return $env:BEOPS_PYTHON }
  $svemirPython = 'C:\Svemir\python.cmd'
  if (Test-Path $svemirPython) { return $svemirPython }
  $bundled = Resolve-BeopsBundledPython
  if ($bundled -and (Test-Path $bundled)) { return $bundled }
  return 'python'
}
function Resolve-BeopsTestPython {
  if ($env:BEOPS_TEST_PYTHON -and (Test-Path $env:BEOPS_TEST_PYTHON)) { return $env:BEOPS_TEST_PYTHON }
  $bundled = Resolve-BeopsBundledPython
  if ($bundled -and (Test-Path $bundled)) { return $bundled }
  return (Resolve-BeopsPython)
}
$remote = 'https://github.com/3esign/beops.git'
$src = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $Isolated -and (Test-Path -LiteralPath (Join-Path $src 'runtime\PUBLISH_PAUSED'))) {
  Write-Output 'Publication is explicitly paused by runtime/PUBLISH_PAUSED. Collectors are unaffected.'
  exit 75
}
$projectParent = Split-Path $src -Parent
$pub = if ($env:BEOPS_PUBLIC_ROOT) { $env:BEOPS_PUBLIC_ROOT } else { Join-Path $projectParent 'Beops-public' }
$pub = Assert-BeopsPublicRootSafe -SourceRoot $src -PublicRoot $pub -ExpectedRemote $remote
$py = Resolve-BeopsPython
$env:GIT_HTTP_USER_AGENT = (Get-BeopsNativeOutput 'workspace Git transport identity' 'node' @('-e', "const fs=require('node:fs');const p=[process.env.BEOPS_INCOGNITO,'C:/Svemir/lib/incognito.js','D:/Svemir/lib/incognito.js'].filter(Boolean).find(p=>fs.existsSync(p));if(!p)throw Error('Incognito provider missing');process.stdout.write(require(p).headers('https://github.com/3esign/beops.git')['User-Agent']);")).Trim()
if (-not $Isolated -and -not $DryRun) {
  # The export lock below protects the mirror, but taking it only after preparing a
  # 600+ MB workspace still lets two callers duplicate all capture work. Serialize
  # the outer lifecycle before allocating a release; the inner process keeps the
  # separate mirror lock because it may also be invoked directly in tests/review.
  $preparationLockFile = Join-Path $src 'runtime\publish-preparation.lock'
  $preparationLock = Enter-BeopsPublishLock -Path $preparationLockFile -MaxAgeMinutes 15
  if (-not $preparationLock.Acquired) {
    Write-Output ("STOP: {0}. NO RELEASE WAS PREPARED." -f $preparationLock.Message)
    exit 75
  }
  $publishExit = 1
  try {
    $oid = (Get-BeopsNativeOutput 'resolve release OID' 'git' @('-C', $src, 'rev-parse', '--verify', 'HEAD^{commit}')).Trim()
    $releaseBase = if ($env:BEOPS_RELEASE_ROOT) { Get-BeopsFullPath $env:BEOPS_RELEASE_ROOT } else { Join-Path (Split-Path (Get-BeopsFullPath $src) -Parent) '_runtime\beops-releases' }
    $runRoot = Join-Path $releaseBase ('beops-release-' + [guid]::NewGuid().ToString('N'))
    try {
      $prepared = Get-BeopsNativeOutput 'prepare isolated release' $py @('-X', 'utf8', '-B', (Join-Path $src 'tools\prepare_release.py'), '--source', $src, '--destination', $runRoot, '--oid', $oid)
    } catch {
      $failurePath = Join-Path $src 'data\live\publish-receipt.json'
      $failureTmp = $failurePath + '.' + $PID + '.tmp'
      New-Item -ItemType Directory -Path (Split-Path $failurePath -Parent) -Force | Out-Null
      @{schema='beops-publish-receipt/v1';at=(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ');source_head=$oid;built=$false;tests_ok=$false;pushed=$false;site_verified=$false;published=$false;why=('release preparation failed: '+$_.Exception.Message)} | ConvertTo-Json | Set-Content -LiteralPath $failureTmp -Encoding UTF8
      Move-Item -LiteralPath $failureTmp -Destination $failurePath -Force
      Save-BeopsReleaseDiagnostic -SourceRoot $src -RunRoot $runRoot -SourceOid $oid -Outcome 'preparation-failed'
      Remove-BeopsGeneratedRelease -Path $runRoot -SourceRoot $src -BaseRoot $releaseBase
      throw
    }
    $capture = $prepared | ConvertFrom-Json
    $env:BEOPS_PUBLIC_ROOT = $pub
    $env:TEMP = Join-Path $runRoot 'runtime\tmp'
    $env:TMP = $env:TEMP
    New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
    $args = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $capture.workspace 'tools\publish_github.ps1'), '-Isolated', '-SourceOid', $oid, '-StateRoot', $src)
    if ($PrepareOnly) { $args += '-PrepareOnly' }
    try {
      & powershell @args
      $publishExit = $LASTEXITCODE
      $manifest = Join-Path $runRoot 'runtime\release-inputs.json'
      if (Test-Path -LiteralPath $manifest) { Copy-Item -LiteralPath $manifest -Destination (Join-Path $src 'runtime\release-inputs-last.json') -Force }
    } finally {
      Save-BeopsReleaseDiagnostic -SourceRoot $src -RunRoot $runRoot -SourceOid $oid -Outcome $(if ($PrepareOnly) { 'prepared-retained' } else { 'publish-finished' })
      if ($PrepareOnly) {
        Write-Output ('Prepared release retained for review: ' + $runRoot)
      } else {
        Remove-BeopsGeneratedRelease -Path $runRoot -SourceRoot $src -BaseRoot $releaseBase
      }
    }
  } finally {
    if ((Test-Path -LiteralPath $preparationLockFile) -and
        (Test-BeopsPublishLockOwnedByCurrentProcess -Path $preparationLockFile)) {
      Remove-Item -LiteralPath $preparationLockFile -Force -ErrorAction SilentlyContinue
    }
  }
  exit $publishExit
}
if (-not $StateRoot) { $StateRoot = $src }

$exclude = @('research/evidence','research/_scratch','research/06-paper','research/_trail','research/01-programme','archive','runtime','data/live','node_modules',
             'research/06-paper/conference/Prvi-poziv-2026.pdf','research/06-paper/conference/Uputstvo-za-autore3.pdf',
             'research/06-paper/conference/call-1.png','research/06-paper/conference/call-2.png','research/06-paper/conference/call-3.png',
             'research/evidence/S158')
Set-Location $src
$null = New-Item -ItemType Directory -Path (Join-Path $src 'runtime') -Force
$head = (Get-BeopsNativeOutput 'git source short HEAD' 'git' @('-C', $src, 'rev-parse', '--verify', $(if ($SourceOid) { $SourceOid } else { 'HEAD' }))).Trim()
$sourceTree = (Get-BeopsNativeOutput 'git source tree' 'git' @('-C', $src, 'rev-parse', ($head + '^{tree}'))).Trim()
$files = (Get-BeopsNativeOutput 'git source HEAD file list' 'git' @('-C', $src, 'ls-tree', '-r', '--name-only', $head)) -split '\r?\n' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
$keep = $files | Where-Object { $f = $_; -not ($exclude | Where-Object { $f -eq $_ -or $f.StartsWith($_ + '/') }) }
# C-020, second occurrence. The folder list above excludes research/06-paper, so pre-papers and
# working documents never reach the export - but research/07-legal is exported whole, and the letters
# live there. The site build calls letters internal by name (NOT_PUBLIC in tools/build_site.py) while
# this export published them, which is the same policy answering two different ways depending on which
# door a document walks through. The categories are named here too, by FILENAME, so a new document of
# an internal kind is excluded by being that kind rather than by someone remembering to list it.
$notPublic = @('PISMA','LETTER','WORKING_DOCUMENT','INTERNAL','DRAFT','PRESEK','PRE_PAPER','PREPAPER','PRED_RAD')
$keep = $keep | Where-Object { $n = (Split-Path $_ -Leaf).ToUpper(); -not ($notPublic | Where-Object { $n.Contains($_) }) }
Write-Output ("source commit {0}: {1} HEAD files, {2} exported" -f $head, $files.Count, $keep.Count)
if ($DryRun) { $keep | Select-Object -First 40; exit 0 }
# C-045 left this open: two publish paths - the scheduled tick and any ship batch - run against one
# export repository with no coordination, and the loser of a race for git's index.lock read exactly
# like a clean tree. The race is now refused rather than lost silently. A lock older than fifteen
# minutes is treated as abandoned, because a publish that takes that long has died.
$lockFile = Join-Path $StateRoot 'runtime\publish.lock'
$script:publishTestsOutRun = $null
$script:sourceArchivePath = $null
$script:siteCheckOutRun = $null
$script:copyRecovery = $null
$receiptPath = Join-Path $StateRoot 'data\live\publish-receipt.json'
$generatedPublicPaths = @('public/history.json', 'public/headlines.json',
                          'public/watch.json',
                          'public/dataset/permission-landscape',
                          'research/08-provenance/CORRECTION_TIMES.json',
                          'research/observations/live')
$receipt = [ordered]@{
  schema            = 'beops-publish-receipt/v1'
  at                = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  source_head       = $head
  source_tree       = $sourceTree
  source_files_from = 'git archive fixed source OID'
  source_file_count = $keep.Count
  generated_as_of   = ''
  built             = $false
  tests_ok          = $false
  tests             = ''
  export_manifest   = 'docs/export-manifest.json'
  export_changed    = $false
  committed         = $false
  pushed            = $false
  remote_head       = ''
  site_verified     = $false
  site_live_hash    = ''
  site_local_hash   = ''
  site_route_count  = 0
  site_checked_at   = ''
  verified_history  = $null
  published         = $false
  why               = ''
}
function Write-BeopsPublishReceipt {
  $receipt.at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  $tempReceipt = $receiptPath + '.' + $PID + '.tmp'
  $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $tempReceipt -Encoding UTF8
  Move-Item -LiteralPath $tempReceipt -Destination $receiptPath -Force
  if ($receipt.published -and $receipt.pushed -and $receipt.site_verified) {
    $success = Join-Path $StateRoot 'data\live\publish-last-success.json'
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($success + '.' + $PID + '.tmp') -Encoding UTF8
    Move-Item -LiteralPath ($success + '.' + $PID + '.tmp') -Destination $success -Force
  }
}
function Release-BeopsPublishRun {
  if ($receipt.published -and $script:copyRecovery -and (Test-Path -LiteralPath $script:copyRecovery)) {
    Remove-Item -LiteralPath $script:copyRecovery -Force -ErrorAction SilentlyContinue
  }
  if ($script:publishTestsOutRun -and (Test-Path $script:publishTestsOutRun)) {
    Remove-Item -LiteralPath $script:publishTestsOutRun -Force -ErrorAction SilentlyContinue
  }
  if ($script:siteCheckOutRun -and (Test-Path $script:siteCheckOutRun)) {
    Remove-Item -LiteralPath $script:siteCheckOutRun -Force -ErrorAction SilentlyContinue
  }
  if ($script:sourceArchivePath -and (Test-Path -LiteralPath $script:sourceArchivePath)) {
    Remove-Item -LiteralPath $script:sourceArchivePath -Force -ErrorAction SilentlyContinue
  }
  if ($lockFile -and (Test-Path $lockFile) -and (Test-BeopsPublishLockOwnedByCurrentProcess -Path $lockFile)) {
    Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
  }
}
function Get-BeopsTrackedDirtyStatus {
  $dirty = Get-BeopsNativeOutput 'git tracked source status' 'git' @('-C', $src, 'status', '--porcelain', '--untracked-files=no', '--', 'tools', 'research/*.py', 'research/05-design/studies', 'public/*.html', 'package.json', ':(exclude)research/_scratch', ':(exclude)research/evidence')
  return ($dirty.Trim())
}
function Assert-BeopsTrackedSourceClean {
  param([string]$Moment)
  $dirty = Get-BeopsTrackedDirtyStatus
  if ($dirty) {
    throw "tracked source working tree is dirty $Moment; commit or move those changes before publish: $dirty"
  }
}
function Invoke-BeopsSiteCheck {
  $script:siteCheckOutRun = Join-Path $src ("runtime\publish-site-check-{0}.json" -f $PID)
  $prevEAP = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  & node tools\verify_public_site.js *> $script:siteCheckOutRun
  $siteRc = $LASTEXITCODE
  $ErrorActionPreference = $prevEAP
  $raw = if (Test-Path -LiteralPath $script:siteCheckOutRun) { Get-Content -LiteralPath $script:siteCheckOutRun -Raw } else { '' }
  if (Test-Path -LiteralPath $script:siteCheckOutRun) { Copy-Item -LiteralPath $script:siteCheckOutRun -Destination (Join-Path $StateRoot 'runtime\publish-site-check-last.json') -Force }
  $site = $null
  try { if ($raw.Trim()) { $site = $raw | ConvertFrom-Json } } catch {}
  $receipt.site_checked_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  if ($site) {
    $receipt.site_verified = [bool]$site.ok
    $receipt.site_live_hash = [string]($site.live_hash)
    $receipt.site_local_hash = [string]($site.local_hash)
    $receipt.site_route_count = @($site.routes).Count
  }
  if ($siteRc -ne 0 -or -not $site -or -not $site.ok) {
    $detail = if ($raw.Trim()) { $raw.Trim() } else { 'no site verifier output' }
    if ($site -and $site.errors) { $detail = @($site.errors) -join '; ' }
    throw "site verification failed after push with exit code ${siteRc}: $($detail.Substring(0, [Math]::Min(500, $detail.Length)))"
  }
  $history = Get-Content -LiteralPath (Join-Path $pub 'docs\history.json') -Raw | ConvertFrom-Json
  $receipt.verified_history = @{history_ends=$history.history_ends;hours_of_history=$history.hours_of_history}
}
$lock = Enter-BeopsPublishLock -Path $lockFile -MaxAgeMinutes 15
if (-not $lock.Acquired) {
  Write-Output ("STOP: {0}. NOTHING WAS PUBLISHED." -f $lock.Message)
  exit 4
}
if ($lock.Recovered) { Write-Output ("note: {0}" -f $lock.Message) }
try {
Assert-BeopsTrackedSourceClean 'before build'
Invoke-BeopsNative 'rebuild frozen baseline' $py @('-X', 'utf8', '-B', 'tools\baseline.py', 'build') -Quiet
Invoke-BeopsNative 'rebuild frozen latency' $py @('-X', 'utf8', '-B', 'tools\latency.py', 'build') -Quiet
Invoke-BeopsNative 'rebuild frozen agreement' $py @('-X', 'utf8', '-B', 'tools\agreement.py', 'build') -Quiet
Invoke-BeopsNative 'build versioned permission dataset' $py @('-X', 'utf8', '-B', 'tools\export_permission_dataset.py') -Quiet
Invoke-BeopsNative 'export frozen rows' $py @('-X', 'utf8', '-B', 'tools\collect_daemon.py', 'export')
Invoke-BeopsNative 'report frozen rows' $py @('-X', 'utf8', '-B', 'tools\collect_daemon.py', 'report')
Invoke-BeopsNative 'build frozen history' $py @('-X', 'utf8', '-B', 'tools\build_history.py')
Invoke-BeopsNative 'build frozen watch view' $py @('-X', 'utf8', '-B', 'tools\watchman.py', '--export') -Quiet


# the site: docs/ is what GitHub Pages serves (main branch, /docs). It is GENERATED by
# tools/build_site.py from the registry, the provenance index, the corrections and the last export,
# so the public page cannot state a number the files do not support.
  Invoke-BeopsNative 'build_site.py' $py @('-X', 'utf8', '-B', 'tools\build_site.py')
  Invoke-BeopsNative 'export frozen experimental AI feed' 'node' @('tools\ai_feed.js', 'export')
# the three maps of the document, regenerated from the snapshot the site is about to serve
Invoke-BeopsNative 'make_maps.py' $py @('-X', 'utf8', '-B', 'tools\make_maps.py', '--out', 'docs') -Quiet
$receipt.built = $true

# ---------------------------------------------------------------- PUBLISH GATE
# Every ship batch ran the full suite and refused to commit when it failed. The scheduled publish
# fired every ten minutes, rebuilt the site and pushed it without running a single test - so the gate
# protected the rare path and not the common one, and the common one is how the public site actually
# updates. The gate lives here, after the site is built and before anything is copied, committed or
# pushed, so that THE THING THAT PUBLISHES IS THE THING THAT CHECKS and no future caller can publish
# by forgetting.
#
# On failure nothing is copied into the export, nothing is committed and nothing is pushed: the
# published site stays exactly as it was. The export working tree may be left half-rebuilt, which is
# harmless because every publish clears and rebuilds it from scratch - but the LAST PUBLISHED COMMIT
# is untouched, which is the part that matters.
#
# A frozen site must not be a quiet site. Every run writes data/live/publish-receipt.json and
# tools/guard.py reads it, so a suite that has been failing for half an hour becomes a STOP rather
# than a silence - the lesson C-036 bought for the organs, applied to the publisher.
$testsOut = Join-Path $src 'runtime\publish-tests.txt'
$script:publishTestsOutRun = Join-Path $src ("runtime\publish-tests-{0}.txt" -f $PID)
$gatePy = Resolve-BeopsTestPython
$prevEAP = $ErrorActionPreference
$previousGatePython = $env:BEOPS_PYTHON
try {
  $ErrorActionPreference = 'Continue'
  $env:BEOPS_PYTHON = $gatePy
  # Use the same bounded suite runner as local verification (120 s maximum).
  & node tools\test-research.js *> $script:publishTestsOutRun
  $testsRc = $LASTEXITCODE
} finally {
  $ErrorActionPreference = $prevEAP
  $env:BEOPS_PYTHON = $previousGatePython
}
$summary = ''
if (Test-Path $script:publishTestsOutRun) {
  try {
    Copy-Item -LiteralPath $script:publishTestsOutRun -Destination $testsOut -Force -ErrorAction Stop
  } catch {
    Write-Output ("note: could not update shared publish test transcript: {0}" -f $_.Exception.Message)
  }
  $summary = ((Get-Content $script:publishTestsOutRun | Select-String -CaseSensitive -Pattern '^Ran |^OK$|^FAILED') -join ' ').Trim()
}
$receipt.tests_ok = ($testsRc -eq 0)
$receipt.tests = $summary
$receipt | Add-Member -NotePropertyName tests_exit_code -NotePropertyValue $testsRc -Force
$receipt | Add-Member -NotePropertyName tests_transcript_bytes -NotePropertyValue $(if (Test-Path $script:publishTestsOutRun) { (Get-Item $script:publishTestsOutRun).Length } else { 0 }) -Force
if ($testsRc -ne 0) {
  $first = ''
  if (Test-Path $script:publishTestsOutRun) {
    $raw = Get-Content $script:publishTestsOutRun -Raw
    $i = $raw.IndexOf('FAIL:'); if ($i -lt 0) { $i = $raw.IndexOf('ERROR:') }
    if ($i -ge 0) { $first = $raw.Substring($i, [Math]::Min(400, $raw.Length - $i)) }
  }
  $receipt.why = "the suite did not pass, so nothing was published. $first"
  Write-BeopsPublishReceipt
  Write-Output "STOP: the suite did not pass ($summary). NOTHING WAS PUBLISHED and the site stays as it was."
  Write-Output $first
  # PowerShell does not run a finally block on `exit`, and a lock left behind by a failing gate would
  # block every publish for the next fifteen minutes - a second outage caused by the first.
  Release-BeopsPublishRun
  exit 3
}
Write-Output "gate: $summary"
Assert-BeopsTrackedSourceClean 'after gate'
# ------------------------------------------------------------ END PUBLISH GATE

function New-BeopsTrackedHeadArchive {
  param([string[]]$Paths)
  if (-not $Paths -or $Paths.Count -eq 0) { return }
  $script:sourceArchivePath = Join-Path $src ("runtime\publish-source-{0}.tar" -f $PID)
  if (Test-Path -LiteralPath $script:sourceArchivePath) {
    Remove-Item -LiteralPath $script:sourceArchivePath -Force
  }
  Invoke-BeopsNative 'git archive source HEAD' 'git' (@('-C', $src, 'archive', '--format=tar', '-o', $script:sourceArchivePath, $head, '--') + $Paths)
}
function Expand-BeopsTrackedHeadArchive {
  if (-not $script:sourceArchivePath -or -not (Test-Path -LiteralPath $script:sourceArchivePath)) {
    throw 'source archive was not created'
  }
  Invoke-BeopsNative 'extract source HEAD archive' 'tar' @('-xf', $script:sourceArchivePath, '-C', $pub)
}
New-BeopsTrackedHeadArchive $keep
# Build the complete export beside the live mirror. No public file is cleared.
$mirror = $pub
$pub = Join-Path $src 'runtime\export-stage'
New-Item -ItemType Directory -Path $pub -ErrorAction Stop | Out-Null
Expand-BeopsTrackedHeadArchive
function Copy-BeopsGeneratedPublic {
  param([string]$Rel)
  $from = Join-Path $src $Rel
  if (-not (Test-Path $from)) { return }
  $to = Join-Path $pub $Rel
  $item = Get-Item -LiteralPath $from
  if ($item.PSIsContainer) {
    New-Item -ItemType Directory -Path $to -Force | Out-Null
    Get-ChildItem -LiteralPath $from -Force | ForEach-Object {
      Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $to $_.Name) -Recurse -Force
    }
    return
  }
  $d = Split-Path $to
  if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
  Copy-Item -LiteralPath $from -Destination $to -Force
}
# These are live/generated public artefacts. They are ignored in the private source repo so that the
# working tree can stay readable, but the public site and public mirror still receive them explicitly.
# Keep every already published immutable dataset edition at its original URL.
$priorEditions = Join-Path $mirror 'public\dataset\permission-landscape\releases'
$releaseEditions = Join-Path $src 'public\dataset\permission-landscape\releases'
if (Test-Path -LiteralPath $priorEditions) {
  foreach ($edition in Get-ChildItem -LiteralPath $priorEditions -Directory) {
    $targetEdition = Join-Path $releaseEditions $edition.Name
    if (Test-Path -LiteralPath $targetEdition) {
      # Same content id: retain the originally published edition bytes.
      foreach ($file in Get-ChildItem -LiteralPath $edition.FullName -File) { Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $targetEdition $file.Name) -Force }
    } else { Copy-Item -LiteralPath $edition.FullName -Destination $targetEdition -Recurse }
  }
}
foreach ($f in $generatedPublicPaths) {
  Copy-BeopsGeneratedPublic $f
}
if (Test-Path (Join-Path $src 'docs')) { Copy-Item -LiteralPath (Join-Path $src 'docs') -Destination $pub -Recurse -Force }
# evidence placeholder so links in the index explain themselves
$note = @'
# research/evidence

The captured pages, headers, robots.txt files and hashes (585 MB) that prove each permission live on the authors' own machine and are not republished: they are third-party content kept as evidence, not as publication. Every capture is listed with its SHA-256 in `research/08-provenance/INDEX.md` and `LEDGER.jsonl`; a reviewer may request any capture by id.
'@
New-Item -ItemType Directory -Path (Join-Path $pub 'research/evidence') -Force | Out-Null
Set-Content -Path (Join-Path $pub 'research/evidence/README.md') -Value $note -Encoding UTF8
$note2 = @'
# research/06-paper, research/_trail, research/01-programme

The working documents, pre-papers, research trails and programme notes are internal and stay on the authors' own machine. The public repository carries the observatory itself: the source registry, the provenance index and ledger, the corrections, the collectors, the organ register, the tools, the tests and the generated site. Links into these folders from the research index are therefore not resolvable here.
'@
foreach ($d in @('research/06-paper','research/_trail','research/01-programme')) { New-Item -ItemType Directory -Path (Join-Path $pub $d) -Force | Out-Null; Set-Content -Path (Join-Path $pub "$d/README.md") -Value $note2 -Encoding UTF8 }
function Write-BeopsExportManifest {
  param([string]$GeneratedAsOf)
  $manifestRel = 'docs/export-manifest.json'
  $manifestPath = Join-Path $pub $manifestRel
  $gitDir = Join-Path $pub '.git'
  $base = (Get-BeopsFullPath $pub) + [System.IO.Path]::DirectorySeparatorChar
  $items = @()
  $exportedFiles = Get-ChildItem -LiteralPath $pub -File -Recurse -Force | Sort-Object FullName
  foreach ($item in $exportedFiles) {
    $full = Get-BeopsFullPath $item.FullName
    if (Test-BeopsSameOrInside -Parent $gitDir -Child $full) { continue }
    $rel = $full.Substring($base.Length).Replace('\', '/')
    if ($rel -eq $manifestRel) { continue }
    $hash = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
    $items += [ordered]@{ path = $rel; bytes = $item.Length; sha256 = $hash }
  }
  $manifest = [ordered]@{
    schema            = 'beops-export-manifest/v1'
    source_head       = $head
    source_tree       = $sourceTree
    source_files_from = 'git archive fixed source OID'
    source_file_count = $keep.Count
    generated_as_of   = $GeneratedAsOf
    generated_paths   = $generatedPublicPaths
    inputs_manifest_sha256 = if (Test-Path 'runtime/release-inputs.json') { (Get-FileHash 'runtime/release-inputs.json' -Algorithm SHA256).Hash.ToLowerInvariant() } else { '' }
    file_count        = $items.Count
    files             = $items
  }
  New-Item -ItemType Directory -Path (Split-Path $manifestPath -Parent) -Force | Out-Null
  $manifestText = ($manifest | ConvertTo-Json -Depth 8) -replace "`r`n", "`n"
  [System.IO.File]::WriteAllText($manifestPath, $manifestText, (New-Object System.Text.UTF8Encoding($false)))
}
# One commit per publish: the public history becomes a free archive of what the observatory held at
# each moment - the "git scraping" pattern - and a second, independent record against our own receipts.
$snap = Join-Path $src 'public\live-snapshot.json'
$asof = if (Test-Path $snap) { try { (Get-Content $snap -Raw | ConvertFrom-Json).as_of } catch { '' } } else { '' }
$receipt.generated_as_of = $asof
$msg = if ($asof) { "Live snapshot $asof (export of $head)" } else { "Publish export of local commit $head ($(Get-Date -Format 'yyyy-MM-dd HH:mm') local)" }
Invoke-BeopsNative 'validate exported public links' $py @('-X', 'utf8', '-B', 'tools\validate_public_tree.py', $pub)
Write-BeopsExportManifest $asof
if ($PrepareOnly) {
  $receipt.why = 'prepared and tested; no mirror mutation or push requested'
  Write-BeopsPublishReceipt
  Write-Output ('PREPARED ' + $pub)
  Release-BeopsPublishRun
  exit 0
}
$stage = $pub
$pub = Assert-BeopsPublicRootSafe -SourceRoot $src -PublicRoot $mirror -ExpectedRemote $remote
if (-not (Test-Path -LiteralPath (Join-Path $pub '.git'))) {
  New-Item -ItemType Directory -Path $pub -Force | Out-Null
  Invoke-BeopsNative 'git init public export' 'git' @('-C', $pub, 'init', '-q', '-b', 'main')
  Invoke-BeopsNative 'git origin public export' 'git' @('-C', $pub, 'remote', 'add', 'origin', $remote)
  Register-BeopsPublicOwnership -PublicRoot $pub
}
# Validate every existing physical target before the first mutation.
$existing = @(Get-ChildItem -LiteralPath $pub -File -Recurse -Force | Where-Object { $_.FullName -notlike ((Join-Path $pub '.git') + '\*') })
foreach ($item in $existing) { $null = Assert-BeopsDeletionTarget -PublicRoot $pub -Target $item.FullName }
$priorHead = & git -C $pub rev-parse --verify --quiet HEAD
if ($LASTEXITCODE -eq 0) {
  $script:copyRecovery = (Get-BeopsNativeOutput 'capture public copy rollback' $py @('-X', 'utf8', '-B', 'tools\mirror_transaction.py', 'capture', $pub) | ConvertFrom-Json).archive
}
$backup = Join-Path (Split-Path $pub -Parent) ('_to_delete\beops-obsolete-' + [guid]::NewGuid().ToString('N'))
foreach ($item in $existing) {
  $rel = $item.FullName.Substring($pub.Length + 1)
  if (-not (Test-Path -LiteralPath (Join-Path $stage $rel))) {
    $to = Join-Path $backup $rel
    New-Item -ItemType Directory -Path (Split-Path $to -Parent) -Force | Out-Null
    Move-Item -LiteralPath $item.FullName -Destination $to
  }
}
foreach ($file in Get-ChildItem -LiteralPath $stage -File -Recurse -Force) {
  $rel = $file.FullName.Substring($stage.Length + 1)
  $to = Join-Path $pub $rel
  New-Item -ItemType Directory -Path (Split-Path $to -Parent) -Force | Out-Null
  Copy-Item -LiteralPath $file.FullName -Destination $to -Force
}
Invoke-BeopsNative 'git add public export' 'git' @('-C', $pub, 'add', '-A')
# The source .gitignore travels with the export and lists docs/ (generated locally, never committed
# in the source repo). In the EXPORT repo docs/ is the published site, so it must be forced in.
# Without -f, only the files added before that ignore rule existed stayed tracked, and every page
# added later - monolog.html, basemap-belgrade.json - was silently dropped and served as 404.
foreach ($f in @('docs') + $generatedPublicPaths) {
  if (Test-Path -LiteralPath (Join-Path $pub $f)) {
    Invoke-BeopsNative "git force-add $f" 'git' @('-C', $pub, 'add', '-A', '-f', $f)
  }
}
Invoke-BeopsNative 'verify staged export bytes against manifest' $py @('-X', 'utf8', '-B', 'tools\verify_staged_export.py', $pub)
# On 2026-09-10 this said "nothing changed since the last publish" and exited 0 while seventeen
# files sat staged in the export, so the site stayed a commit behind until somebody ran it by hand.
# The check could not tell an EMPTY status from an UNREADABLE one - git returning nothing because
# there is nothing to say, and git returning nothing because it failed (an index.lock held by the
# scheduled publish running at the same moment reads exactly like a clean tree). That is the
# watchman's second lie - calling blindness success - committed by the publish path.
# So the exit code is consulted, and a status that could not be read is never reported as clean.
$status = git -C $pub status --porcelain 2>&1
$rc = $LASTEXITCODE
if ($rc -ne 0) {
  throw "could not read the export status (git exit $rc)"
}
$changed = @($status | Where-Object { $_ -ne $null -and "$_".Trim() -ne '' }).Count -gt 0
if (-not $changed) {
  $publicHead = Get-BeopsNativeOutput 'git public HEAD' 'git' @('-C', $pub, 'rev-parse', 'HEAD')
  $remoteLine = Get-BeopsNativeOutput 'git remote main HEAD' 'git' @('-C', $pub, 'ls-remote', 'origin', 'refs/heads/main')
  $remoteHead = (($remoteLine -split '\s+')[0])
  if ($remoteHead -eq $publicHead) {
    $receipt.remote_head = $remoteHead
    Invoke-BeopsSiteCheck
    $receipt.pushed = $true; $receipt.published = $true
    $receipt.why = 'nothing changed since the last publish; live site verified'
    Write-BeopsPublishReceipt
    Write-Output 'nothing changed since the last publish'
    Release-BeopsPublishRun
    exit 0
  }
  Write-Output 'export is clean locally but remote is behind; pushing the existing export commit'
  Invoke-BeopsNative 'git push public export' 'git' @('-C', $pub, 'push', '-u', 'origin', 'main')
  $remoteLine = Get-BeopsNativeOutput 'git remote main HEAD after push' 'git' @('-C', $pub, 'ls-remote', 'origin', 'refs/heads/main')
  $remoteHead = (($remoteLine -split '\s+')[0])
  $receipt.pushed = $true
  $receipt.remote_head = $remoteHead
  if ($remoteHead -ne $publicHead) {
    $receipt.why = "push returned success but remote head is $remoteHead, expected $publicHead"
    Write-BeopsPublishReceipt
    Write-Output ("STOP: {0}. NOTHING WAS PUBLISHED." -f $receipt.why)
    Release-BeopsPublishRun
    exit 6
  }
  Invoke-BeopsSiteCheck
  $receipt.published = $true
  $receipt.why = "Pushed existing export commit $publicHead for source $head"
  Write-BeopsPublishReceipt
  Write-Output ("published: {0}" -f $receipt.why)
  Release-BeopsPublishRun
  exit 0
}
$receipt.export_changed = $true
Invoke-BeopsNative 'git commit public export' 'git' @('-C', $pub, '-c', 'user.name=Semir Poturak', '-c', 'user.email=scumutator@gmail.com', 'commit', '-q', '-m', $msg)
$receipt.committed = $true
$remotes = Get-BeopsNativeOutput 'git remote list' 'git' @('-C', $pub, 'remote')
if (-not (($remotes -split "`n") | Where-Object { $_ -eq 'origin' })) {
  Invoke-BeopsNative 'git add public remote' 'git' @('-C', $pub, 'remote', 'add', 'origin', $remote)
}
$publicHead = Get-BeopsNativeOutput 'git public HEAD' 'git' @('-C', $pub, 'rev-parse', 'HEAD')
Invoke-BeopsNative 'git push public export' 'git' @('-C', $pub, 'push', '-u', 'origin', 'main')
$receipt.pushed = $true
$remoteLine = Get-BeopsNativeOutput 'git remote main HEAD after push' 'git' @('-C', $pub, 'ls-remote', 'origin', 'refs/heads/main')
$remoteHead = (($remoteLine -split '\s+')[0])
$receipt.remote_head = $remoteHead
if ($remoteHead -ne $publicHead) {
  $receipt.why = "push returned success but remote head is $remoteHead, expected $publicHead"
  Write-BeopsPublishReceipt
  Write-Output ("STOP: {0}. NOTHING WAS PUBLISHED." -f $receipt.why)
  Release-BeopsPublishRun
  exit 6
}
Invoke-BeopsSiteCheck
$receipt.published = $true
$receipt.why = $msg
Write-BeopsPublishReceipt
Write-Output "published: $msg"

} catch {
  $receipt.why = "publish failed before final confirmation: " + $_.Exception.Message
  if ($script:copyRecovery -and -not $receipt.committed -and -not $receipt.pushed) {
    try {
      Invoke-BeopsNative 'restore failed pre-commit public copy' $py @('-X', 'utf8', '-B', 'tools\mirror_transaction.py', 'restore', $pub, $script:copyRecovery) -Quiet
      $receipt.why += '; previous public working tree restored'
    } catch { $receipt.why += '; public copy rollback requires review: ' + $_.Exception.Message }
  }
  Write-BeopsPublishReceipt
  if ($receipt.pushed) {
    Write-Output ("STOP: {0}. REMOTE PUSH COMPLETED BUT LIVE SITE WAS NOT VERIFIED." -f $receipt.why)
  } else {
    Write-Output ("STOP: {0}. NOTHING WAS PUBLISHED." -f $receipt.why)
  }
  Release-BeopsPublishRun
  exit 5
} finally { Release-BeopsPublishRun }
