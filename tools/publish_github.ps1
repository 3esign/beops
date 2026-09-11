# Publishes a clean export of this repository to GitHub (3esign/beops) as open source.
# Internal working documents (research/06-paper, research/_trail, research/01-programme) stay local: the
# public repository carries the registry, the provenance index, the corrections, the collectors, the organs,
# the tools and the site - the observatory, not its drafts.
# Why an export and not `git push`: the local history carries a 141 MB evidence blob that GitHub
# refuses (>100 MB), and research/evidence/ (585 MB of captured third-party pages) stays local by
# rule - it is proof, not publication. The public repository therefore receives the current tree
# minus evidence, scratch, archives, runtime and live data, as ONE commit per publish, with the
# local commit hash in the message. Local history is never rewritten.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_github.ps1            # publish
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_github.ps1 -DryRun    # show what would go
param([switch]$DryRun)
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
$projectParent = Split-Path $src -Parent
$pub = if ($env:BEOPS_PUBLIC_ROOT) { $env:BEOPS_PUBLIC_ROOT } else { Join-Path $projectParent 'Beops-public' }
$pub = Assert-BeopsPublicRootSafe -SourceRoot $src -PublicRoot $pub -ExpectedRemote $remote
$py = Resolve-BeopsPython
$exclude = @('research/evidence','research/_scratch','research/06-paper','research/_trail','research/01-programme','archive','runtime','data/live','node_modules',
             'research/06-paper/conference/Prvi-poziv-2026.pdf','research/06-paper/conference/Uputstvo-za-autore3.pdf',
             'research/06-paper/conference/call-1.png','research/06-paper/conference/call-2.png','research/06-paper/conference/call-3.png',
             'research/evidence/S158')
Set-Location $src
$null = New-Item -ItemType Directory -Path (Join-Path $src 'runtime') -Force
$head = (git rev-parse --short HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or -not $head) { throw "git rev-parse --short HEAD failed" }
$files = (git ls-files) -split "`n" | Where-Object { $_ -ne '' }
if ($LASTEXITCODE -ne 0) { throw "git ls-files failed" }
$keep = $files | Where-Object { $f = $_; -not ($exclude | Where-Object { $f -eq $_ -or $f.StartsWith($_ + '/') }) }
# C-020, second occurrence. The folder list above excludes research/06-paper, so pre-papers and
# working documents never reach the export - but research/07-legal is exported whole, and the letters
# live there. The site build calls letters internal by name (NOT_PUBLIC in tools/build_site.py) while
# this export published them, which is the same policy answering two different ways depending on which
# door a document walks through. The categories are named here too, by FILENAME, so a new document of
# an internal kind is excluded by being that kind rather than by someone remembering to list it.
$notPublic = @('PISMA','LETTER','WORKING_DOCUMENT','INTERNAL','DRAFT','PRESEK','PRE_PAPER','PREPAPER','PRED_RAD')
$keep = $keep | Where-Object { $n = (Split-Path $_ -Leaf).ToUpper(); -not ($notPublic | Where-Object { $n.Contains($_) }) }
Write-Output ("source commit {0}: {1} tracked files, {2} exported" -f $head, $files.Count, $keep.Count)
if ($DryRun) { $keep | Select-Object -First 40; exit 0 }
# C-045 left this open: two publish paths - the scheduled tick and any ship batch - run against one
# export repository with no coordination, and the loser of a race for git's index.lock read exactly
# like a clean tree. The race is now refused rather than lost silently. A lock older than fifteen
# minutes is treated as abandoned, because a publish that takes that long has died.
$lockFile = Join-Path $src 'runtime\publish.lock'
$script:publishTestsOutRun = $null
$receiptPath = Join-Path $src 'data\live\publish-receipt.json'
$receipt = [ordered]@{
  schema        = 'beops-publish-receipt/v1'
  at            = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  source_head   = $head
  built         = $false
  tests_ok      = $false
  tests         = ''
  export_changed = $false
  committed     = $false
  pushed        = $false
  remote_head   = ''
  published     = $false
  why           = ''
}
function Write-BeopsPublishReceipt {
  $receipt.at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  $receipt | ConvertTo-Json -Depth 4 | Set-Content -Path $receiptPath -Encoding UTF8
}
function Release-BeopsPublishRun {
  if ($script:publishTestsOutRun -and (Test-Path $script:publishTestsOutRun)) {
    Remove-Item -LiteralPath $script:publishTestsOutRun -Force -ErrorAction SilentlyContinue
  }
  if ($lockFile -and (Test-Path $lockFile) -and (Test-BeopsPublishLockOwnedByCurrentProcess -Path $lockFile)) {
    Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
  }
}
$lock = Enter-BeopsPublishLock -Path $lockFile -MaxAgeMinutes 15
if (-not $lock.Acquired) {
  Write-Output ("STOP: {0}. NOTHING WAS PUBLISHED." -f $lock.Message)
  exit 4
}
if ($lock.Recovered) { Write-Output ("note: {0}" -f $lock.Message) }
try {

# the site: docs/ is what GitHub Pages serves (main branch, /docs). It is GENERATED by
# tools/build_site.py from the registry, the provenance index, the corrections and the last export,
# so the public page cannot state a number the files do not support.
Invoke-BeopsNative 'build_site.py' $py @('-X', 'utf8', '-B', 'tools\build_site.py')
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
$ErrorActionPreference = 'Continue'
& $gatePy -X utf8 -B -m unittest discover -s research -p "test_*.py" *> $script:publishTestsOutRun
$testsRc = $LASTEXITCODE
$ErrorActionPreference = $prevEAP
$summary = ''
if (Test-Path $script:publishTestsOutRun) {
  try {
    Copy-Item -LiteralPath $script:publishTestsOutRun -Destination $testsOut -Force -ErrorAction Stop
  } catch {
    Write-Output ("note: could not update shared publish test transcript: {0}" -f $_.Exception.Message)
  }
  $summary = ((Get-Content $script:publishTestsOutRun | Select-String -Pattern '^Ran |^OK$|^FAILED') -join ' ').Trim()
}
$receipt.tests_ok = ($testsRc -eq 0)
$receipt.tests = $summary
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
# ------------------------------------------------------------ END PUBLISH GATE

if (-not (Test-Path -LiteralPath $pub)) {
  New-Item -ItemType Directory -Path $pub | Out-Null
  Invoke-BeopsNative 'git init public export' 'git' @('-C', $pub, 'init', '-q', '-b', 'main')
}
# clear the export tree (never the .git of the export repo), after the gate has passed
Get-ChildItem -LiteralPath $pub -Force | Where-Object { $_.Name -ne '.git' } | ForEach-Object {
  $target = Assert-BeopsDeletionTarget -PublicRoot $pub -Target $_.FullName
  Remove-Item -LiteralPath $target -Recurse -Force
}
foreach ($f in $keep) {
  $d = Split-Path (Join-Path $pub $f)
  if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
  Copy-Item -LiteralPath (Join-Path $src $f) -Destination (Join-Path $pub $f) -Force
}
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
foreach ($f in @('public/history.json',
                 'public/watch.json',
                 'public/dataset/permission-landscape',
                 'research/08-provenance/CORRECTION_TIMES.json',
                 'research/observations/live')) {
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
Invoke-BeopsNative 'git add public export' 'git' @('-C', $pub, 'add', '-A')
# The source .gitignore travels with the export and lists docs/ (generated locally, never committed
# in the source repo). In the EXPORT repo docs/ is the published site, so it must be forced in.
# Without -f, only the files added before that ignore rule existed stayed tracked, and every page
# added later - monolog.html, basemap-belgrade.json - was silently dropped and served as 404.
foreach ($f in @('docs',
                 'public/history.json',
                 'public/watch.json',
                 'public/dataset/permission-landscape',
                 'research/08-provenance/CORRECTION_TIMES.json',
                 'research/observations/live')) {
  if (Test-Path -LiteralPath (Join-Path $pub $f)) {
    Invoke-BeopsNative "git force-add $f" 'git' @('-C', $pub, 'add', '-A', '-f', $f)
  }
}
# One commit per publish: the public history becomes a free archive of what the observatory held at
# each moment - the "git scraping" pattern - and a second, independent record against our own receipts.
$snap = Join-Path $src 'public\live-snapshot.json'
$asof = if (Test-Path $snap) { try { (Get-Content $snap -Raw | ConvertFrom-Json).as_of } catch { '' } } else { '' }
$msg = if ($asof) { "Live snapshot $asof (export of $head)" } else { "Publish export of local commit $head ($(Get-Date -Format 'yyyy-MM-dd HH:mm') local)" }
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
  Write-Output "STOP: could not read the export status (git exit $rc). Nothing was published, and this is NOT 'nothing changed'."
  $receipt.why = "could not read the export status (git exit $rc)"
  Write-BeopsPublishReceipt
  Release-BeopsPublishRun
  exit 2
}
$changed = @($status | Where-Object { $_ -ne $null -and "$_".Trim() -ne '' }).Count -gt 0
if (-not $changed) {
  $publicHead = Get-BeopsNativeOutput 'git public HEAD' 'git' @('-C', $pub, 'rev-parse', 'HEAD')
  $remoteLine = Get-BeopsNativeOutput 'git remote main HEAD' 'git' @('-C', $pub, 'ls-remote', 'origin', 'refs/heads/main')
  $remoteHead = (($remoteLine -split '\s+')[0])
  if ($remoteHead -eq $publicHead) {
    $receipt.remote_head = $remoteHead
    $receipt.why = 'nothing changed since the last publish'
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
$receipt.published = $true
$receipt.why = $msg
Write-BeopsPublishReceipt
Write-Output "published: $msg"

} catch {
  $receipt.why = "publish failed before confirmed push: " + $_.Exception.Message
  Write-BeopsPublishReceipt
  Write-Output ("STOP: {0}. NOTHING WAS PUBLISHED." -f $receipt.why)
  Release-BeopsPublishRun
  exit 5
} finally { Release-BeopsPublishRun }
