Set-Location 'D:\Svemir\!Projekti\Beops'
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
Write-Output "--- stage 1: documents, registry, tools ---"
git add CLAIMS.md CONTRIBUTING.md README.md research/README.md research/SOURCE_REGISTRY.json research/COLLECTION_PLAN.json research/01-programme research/02-senses research/03-models research/08-provenance/*.md research/08-provenance/LEDGER.jsonl research/collect_permitted.py research/putevi_parse.py tools data/ca-bundle-windows.pem 2>&1 | Select-Object -Last 3
git -c user.name="Svemir" -c user.email="svemir@local" commit -q -F tools/commitmsg8.txt 2>&1 | Select-Object -Last 3
git log --oneline -1
Write-Output "--- stage 2: the collected evidence ---"
git add research/evidence 2>&1 | Select-Object -Last 3
git -c user.name="Svemir" -c user.email="svemir@local" commit -q -m "Evidence: 218 collected files and 121 permission captures, compressed" -m "Raw bytes as served for thirteen sources, each with a manifest carrying sha256, byte length, HTTP status, response headers and fetch time, plus the provenance capture the collection was gated on. Files above 8 MB are stored gzipped; the sha256 in every manifest still describes the ORIGINAL bytes, verifiable with gunzip -c FILE | sha256sum. 1.5 GB became 332 MB." -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" 2>&1 | Select-Object -Last 3
git log --oneline -2
git count-objects -vH | Select-String "size-pack|count"
