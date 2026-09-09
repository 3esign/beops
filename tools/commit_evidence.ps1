Set-Location 'D:\Svemir\!Projekti\Beops'
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
git add .gitattributes
git -c user.name="Svemir" -c user.email="svemir@local" commit -q -m "Evidence is binary to git, or its hashes stop meaning anything" -m "Git was normalising line endings inside research/evidence. A file committed with LF and checked out on Windows as CRLF is no longer the bytes that were served, so every sha256 in every MANIFEST.json would fail for anyone who cloned the repository on another platform - silently, and only for them. The whole point of storing evidence is that its hash can be checked, so evidence is now declared -text -diff and git never touches it." -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" 2>&1 | Select-Object -Last 2
foreach($d in @('research/evidence/legal','research/evidence/putevi-aadt','research/evidence/S06','research/evidence/S13','research/evidence/S146','research/evidence/S148','research/evidence/S151','research/evidence/S152','research/evidence/S153')){
  if (Test-Path $d) {
    git add $d 2>&1 | Select-Object -Last 1
    git -c user.name="Svemir" -c user.email="svemir@local" commit -q -m ("Evidence: " + $d) -m "Raw bytes as served, with a manifest carrying sha256, byte length, HTTP status, response headers and fetch time, plus the provenance capture the collection was gated on. Files above 8 MB are gzipped; the manifest sha256 describes the ORIGINAL bytes and is verified with: gunzip -c FILE | sha256sum" 2>&1 | Select-Object -Last 1
    Write-Output ("committed " + $d)
  }
}
git log --oneline -3
