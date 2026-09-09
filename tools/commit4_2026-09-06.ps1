Set-Location 'D:\Svemir\!Projekti\Beops'
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
cmd /c "npm test 2>&1" | Select-Object -Last 4
git add -A
git -c user.name="Svemir" -c user.email="svemir@local" commit -q -m "A plan built from where the surprises came from, and a place register that is adopted rather than invented

Part A of the hypotheses note asks how each find was actually made, and gets
seven mechanisms. The strongest is that catalogues leak endpoints on domains
nobody would guess: the best source in the registry lives at
opendata.kosava.cloud, which says nothing about being the environment agency.
Extracting distinct hosts from the 7064 already-harvested resource URLs cost no
network and produced six new leads.

Confirmed from that extraction: the Ministry of Culture publishes the official
immovable cultural property register through the national spatial
infrastructure, which is what Wikidata could not supply since none of its 219
Belgrade monuments carried the official register number. RATEL publishes EMF
drive tests as GPS tracks carrying field strength and height, which is this
project's first moving sensor and its first line geometry. The Ministry of
Education publishes every institution with its rooms and floor area, by address
and not by coordinate, which is exactly why the address register matters. The
pollen API returns stations with coordinates, three of them in Belgrade.

Two negative findings, re-derived from the stored harvest after a Latin-script
query against Cyrillic organisation names nearly produced a false negative:
the national meteorological service has zero datasets on the national portal,
and exactly four datasets carry a high-value-dataset marker. Serbia has
implemented two of the six HVD categories, companies and environment.

The place register note argues the join between maps and data has to be held
in our own code, because six sources address space in six mutually
unintelligible ways and no publisher will ever adopt another's key. The
addendum then corrects that note twice from the literature. A benchmark
published in May 2026 shows pre-computed grid equi-joins beating geometric
intersects by 13 to 457 times, with ten-million-point joins under 200 ms, so
the join becomes an integer equality. The S2 knowledge-graph paper makes the
sharper point that places are mutable and cells are not, so places should
attach to immutable cells rather than carry geometry as identity. And the
register itself already exists as a standard: Linked Places Format has
per-element temporal validity and a certainty on geometry, which were the two
things called the hard parts, so it is adopted and extended with the one field
it leaves to the implementer, the binding method.

The choice of grid is settled by measurement rather than preference. Across the
Belgrade bounding box H3 cell area varies by 0.61 percent at every working
resolution, far inside the uncertainty of any value the project holds, against
a 154-fold covering cost for strict equal area. Nationally the same spread is
6.93 percent, and that caveat travels with the decision.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01L8NfE9kz5DBpWDL6cYpeKP" 2>&1 | Select-Object -Last 4
git log --oneline -2
