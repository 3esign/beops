# Data dictionary — the permission landscape of a European capital

Version 1.1, generated 2026-09-10T23:07:46.596982Z.

## sources.csv

| column | meaning |
|---|---|
| `source_id` | this project's internal identifier, stable across versions |
| `theme` | the subject the source concerns, as this project classified it |
| `kind` | what sort of thing the source is (a feed, a register, a catalogue, a refusal) |
| `status` | **this project's reading of what the publisher's site said on the day it was read.** It is not a legal characterisation of any organisation, not a compliance score, and not a ranking. `probe_ok` the endpoint answered and nothing forbade us; `primary_page` the site was read but the specific local feed was not validated; `lead` recorded but not independently verified in this pass; `opted_out` the publisher declined; `no_coverage` the source exists but holds nothing for Belgrade; `needs_decision` an unresolved conflict, and therefore not collected; `collected` in the record |
| `is_polled` | whether a collector actually asks this source on a schedule |
| `has_stored_permission_evidence` | whether the bytes served when permission was checked are held on file with a hash |
| `host` | the hostname, so rows can be grouped by publisher |
| `reviewer_reason` | **the reviewer's own words, unedited except for whitespace.** Where they are uncomfortable — "not independently verified", "the actual local feed was not validated" — that is deliberate: the vocabulary exists so an unverified thing cannot quietly become a verified one |

## refusals.csv

The subset that said no, on its own, because it is the finding rather than a footnote to it.
**A refusal is a decision not to be a source for this project.** It is not evidence that an
organisation is closed or obstructive, and several are routine terms-of-use statements that were
never addressed to us. No refusal in this file was contacted, argued with, or worked around.

## captures.csv

One row per stored permission capture. The captured bytes themselves are **not** in this dataset:
they are third-party content held as evidence, not as publication. `manifest_sha256` identifies each
capture, and a reviewer may request any of them by source id and hash.

## What this dataset cannot tell you

- **Whether the list is complete.** It is not. It was assembled by two people reading sites, and a
  later review found that the strongest-licensed sources available — the City's official gazette and
  most of its seventeen municipalities — were missing from it, because the list was built by reading
  robots files rather than by reading the statute.
- **Anything about the publishers' intentions.** A `Disallow` line is a machine instruction, not a
  refusal addressed to a person, and this dataset does not distinguish the two.
- **Anything about Belgrade.** It measures this project's access to signals about Belgrade. Those are
  different things, and conflating them is the error the whole record is built against.
