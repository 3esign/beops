# 08 — Provenance

*Where every number came from, and the stored proof that we were allowed to have it.*

This folder answers one question, and it must be able to answer it a year from
now, to someone who is not friendly: **on what basis did you collect this?**

The answer is never a sentence somebody wrote. It is bytes on disk.

## What is here

| file | what it is |
|---|---|
| `INDEX.md` | **Generated.** The table of every source and its permission verdict. Never edit by hand. |
| `LEDGER.jsonl` | Append-only. One line per capture: verdict, evidence path, timestamp. |
| `CORRECTIONS.md` | Every time this system got something wrong, and what the wrong thing said. |
| `EDGE_CASES.md` | Where the law is unsettled, where we are at the edge, and the questions we would put to a regulator. |
| `../evidence/legal/<SID>/<UTC>/` | The captures themselves. Never edited, never deleted. |

## What a capture contains

For one source, at one moment in time:

- `robots.txt` — the site's own file, exactly as served. A `404` is captured
  too: under RFC 9309 the absence of the file is itself the statement *no
  restrictions stated*, and we store the absence rather than assuming it.
- `robots_verdict.json` — the machine verdict of `urllib.robotparser`, run
  **separately for our own user-agent and for `*`**, for each path we intend to
  read. Two agents, because a site may permit everyone and forbid us, or the
  reverse, and we want the record to show which.
- `headers.json` — the response headers of the exact URLs we intend to read,
  with the AI-opt-out signals pulled out by name: `X-Robots-Tag`,
  `Content-Signal`, `Content-Usage`, `TDM-Reservation`, `TDM-Policy`.
- `terms_<n>.*` — the licence or terms page, as served, in its original bytes.
- `MANIFEST.json` — SHA-256 and byte length of every file above, the
  user-agent used, and the UTC time of each fetch.

## The three rules

**1. Evidence before collector.** A source may not enter
`research/SOURCE_REGISTRY.json`, and no collector may be written for it, until
a capture exists. `INDEX.md` lists every registered source with no capture
under *Not yet documented* — that list is the work queue, and it is visible,
not hidden.

**2. An unknown is never a permission.** If TLS could not be verified, if
`robots.txt` could not be read, if the URL was unreachable — the verdict is
`null`, and `null` renders under *Evidence incomplete*, never under
*permitted*. There is deliberately no `--insecure` mode: a capture that cannot
check who it is talking to is not evidence of anything. This rule is written
in blood; see `CORRECTIONS.md`.

**3. We identify honestly.** The collector always sends
`Beops-Research-Capture/1.0`. There is no mode that disguises who is asking,
and no proposal to add one will be accepted. When a site says no — in
`robots.txt`, in a `Content-Signal` header, in its terms — the answer is no,
and the refusal is recorded so that nobody rediscovers the source next year and
quietly starts collecting.

## Running it

```
python -B tools/legal_capture.py --sid S141 --name "<source>" \
    --url  <the exact URL we will read>   \
    --url  <another, repeatable>          \
    --terms <licence or terms page>       \
    --note "<what this source is>"

python -B tools/build_provenance_index.py
```

Commit the capture and the regenerated index **in the same commit**. The index
is generated from the captures, so it can never claim a permission the stored
bytes do not support — but only if the two travel together.

## Re-capture

Terms change. A capture is a statement about a moment, not forever. Re-capture:

- before anything is published,
- when a site is redesigned or its operator changes,
- annually for anything in continuous collection.

Old captures are never deleted. A permission that was true in 2026 stays in the
record even if the site changes its mind in 2027 — and the difference between
the two captures is itself a finding.
