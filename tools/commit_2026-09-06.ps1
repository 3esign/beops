Set-Location 'D:\Svemir\!Projekti\Beops'
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
C:\Svemir\python.cmd -B tools/build_provenance_index.py
Write-Output "--- npm test ---"
cmd /c "npm test 2>&1" | Select-Object -Last 12
Write-Output "--- git ---"
git add -A
git -c user.name="Svemir" -c user.email="svemir@local" commit -m "Provenance: store the proof, not the claim; collect S57 and count how much of Serbia's traffic data is measured

Adds research/08-provenance/, where a source may not be collected until the
permission evidence is captured: the site's own robots.txt as served, the
response headers of the exact URLs we read with X-Robots-Tag and Content-Signal
pulled out by name, the licence page as served, and a SHA-256 of each. INDEX.md
is generated from those captures, so it cannot state a permission the stored
bytes do not support.

EDGE_CASES.md is the section the law does not settle: text and data mining with
no verified Serbian transposition, robots.txt binding us without binding anyone,
absence of a licence not being a grant, repeated small extractions adding up
under the sui generis right, the ArcGIS door we stopped at, archived copies
versus a live opt-out, the word measurement for sound, and the question nobody
regulates - what obligations lawful aggregation acquires that its parts did not.

CORRECTIONS.md records two failures of the day, both by the author of the rules
they broke. C-001: the capture tool's first run reported seven total TLS
failures as allowed_for_us true, because None is not False. Fixed to three
states, with unknown never rendering as permitted and no insecure mode. C-002
in effect: ids were allocated to sources already registered. Both rules now
live in the tool, which refuses the work, rather than in a document.

S57 collected. 44 workbooks from JP Putevi Srbije, 2018-2024, four road
categories, stored immutably with a manifest. Each file defines its own legend
and the parser reads it per file - the asterisk means data borrowed from the
neighbouring counter in one publication and unbuilt interchange in another.

Across 6940 section-years: 36.7 percent observed, 36.0 percent interpolated,
21.9 percent unavailable with a stated reason. The observed share fell from
46.3 percent in 2019 to 27.0 percent in 2024. Belgrade is 45.7 percent
interpolated against 36.7 percent observed, and the largest figure Serbia
publishes for the ring road - 55545 vehicles on Bubanj Potok to Transped - was
interpolated, not measured. This is not our inference; it is the publisher's
own per-row label, which every reader discards by taking only the Total column.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01L8NfE9kz5DBpWDL6cYpeKP" 2>&1 | Select-Object -Last 12
git log --oneline -3
