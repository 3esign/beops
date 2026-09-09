Set-Location 'D:\Svemir\!Projekti\Beops'
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
C:\Svemir\python.cmd -B tools/build_provenance_index.py
cmd /c "npm test 2>&1" | Select-Object -Last 5
git add -A
git -c user.name="Svemir" -c user.email="svemir@local" commit -q -m "The verdict engine must never clear us when we are not clear

urllib.robotparser returns the first matching rule; RFC 9309 requires the
longest. transit.land publishes Allow: /feeds before Disallow: /feeds/, so the
standard library answered allowed where the standard answers disallowed - a
failure in the only direction this tool must never fail in. legal_capture.py
now implements RFC 9309 itself, runs both engines, takes the stricter of the
two always, and records which engine said what so a disagreement is visible
rather than resolved silently.

Content-Signal was being read only from HTTP headers. It lives inside
robots.txt, which is where UNESCO and transit.land both carry it, and it is
per purpose rather than yes or no: UNESCO publishes search=yes, ai-train=no,
use=reference. BEOPS reads and does not train, so ai-input=no or search=no
forbids collection while ai-train=no is honoured, recorded on the source, and
travels with the data to anyone the archive is passed to.

Adds --refused, for a refusal the parser cannot see. Pleiades disallows
anthropic-ai, ClaudeBot and Claude-Web by name while User-agent: * permits
everything, so a collector under any other name reads as allowed; choosing a
name the ban does not mention is circumvention. Adds --needs-decision, which
holds a verdict open. There is deliberately no flag that can force a
permission: the machine may stop us, it may never clear us when we know better.

Wikidata and Overpass both disallow the path that is their API. The evident
target is crawlers - Overpass publishes a sitemap under the path it disallows -
but the letter covers us, so both are held under Decision required and no
collector is built on either. EDGE_CASES.md E-009 and E-010 write up both
questions. CORRECTIONS.md C-002 through C-004 record that ids were allocated
to already-registered sources, that data was taken from those two endpoints
before their permission was captured, and that the verdict engine
over-permitted by standard.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01L8NfE9kz5DBpWDL6cYpeKP" 2>&1 | Select-Object -Last 6
git log --oneline -2
