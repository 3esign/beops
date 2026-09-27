# Resource accounting, v1

Measured from 2026-09-26 23:25 UTC onward. Earlier resource cycles are unknown.

`tools/resource_summary.js` exports `buildSummary(projectRoot, asOf)` and prints the same
read-only JSON when invoked with Node. It reports rolling 24-hour, 7-day and 30-day windows
by cycle start, not calendar-day statistics. A complete cycle is counted in full, not prorated.

The normal scheduled commands record an immutable start and a separate immutable finish
under `runtime/resources/receipts`. An interrupted process leaves its start visible without
fabricated CPU, time, energy or token totals. Duplicate/mismatched/orphan receipts are refused
by the summary; incomplete measurements remain visible. I/O failures warn in the normal
process stderr log and do not stop observation. This is deliberately partial accounting.

Instrumented processes: collection plus local snapshot export, official-calendar refresh,
AI feed, news `run`, mind `run`/`step`, scheduled watch, guard and legal recapture.
Each measures wall time, its own CPU time, and process lifetime peak RSS. Peak RSS is not
summed. Child processes, remote inference, model servers/GPU, host baseline, publication,
baseline construction, tests and old OBS001 work are not counted as measured CPU.

HTTP counters cover attempts and decoded body bytes in the shared collector transport and
the AI adapter HTTP function. They exclude opaque CLI traffic, headers, compression on the
wire, TCP/TLS overhead and other processes. Zero means zero observed in these functions.

AI-feed usage is copied from provider reports, including returned-but-rejected responses.
Missing and failed calls keep missing tokens. Input, output, cache read/write, reasoning and
provider total fields stay separate: provider definitions differ, so no billing-equivalent total
is inferred. The historical ledger covers retained attempts with per-field reporting coverage;
it overlaps new cycle totals and must never be added to them. News/mind token counts and
qualification probes remain unavailable in this first version.

The 2026-09-27 continuation corrects normalization of retained Codex CLI and Antigravity CLI
usage fields: `reasoning_output_tokens` / `thinking_tokens`, `cache_read_tokens` and
`cache_write_input_tokens`. These map to their corresponding separate reasoning, cache-read
and cache-creation fields; they are never added to input or output. Existing immutable cycle
receipts retain their original recorded amounts. Rebuilding the separate historical ledger
can recover fields from retained responses, but does not backfill or add them to cycle totals.
Timeout logs can contain intermediate usage without a completed provider response; such
logs are not treated as a complete bill or silently merged into measured cycles.

From the 2026-09-27 thorough audit, new private cycle receipts also retain `provider_calls`:
the immutable AI attempt id, provider/model labels, whether a response returned, terminal
attempt state, a bounded failure classification and the normalized per-call usage. These
identify missing usage without reconstructing a link from timestamps. Rejected output can
have reported usage; a timeout or rate limit without a returned response stays unavailable.
No prompt, answer or free-form diagnostic is copied into this linkage. Existing receipts
remain unchanged, and the public summary still derives its totals from the original aggregate
fields: adding a trace never adds tokens a second time.

Electricity and money are `null`. CPU time is not energy; elapsed time is not energy.
Physical energy readings and a declared allocation of shared host/idle work are required
before reporting Wh. Tariff and provider billing evidence are required before reporting money.

The public account also derives ratios from the same retained window: finished cycles / starts,
mean CPU and elapsed seconds / finished cycles (all recorded outcomes), reported HTTP bodies /
attempts, and mean decoded bytes / reported bodies. Token reporting coverage is reported calls /
counted calls only; cycles whose call count is unknown remain explicitly separate. A missing or
zero denominator yields `null`, never zero or 100%. These are descriptions of recorded work,
not efficiency scores, whole-machine coverage, energy estimates or billable totals. Activity
breakdowns use the same formulas and window, so a calendar refresh is not compared to AI work
as though the two cycles did the same job.

Measurement sources: [Node process CPU and memory](https://nodejs.org/api/process.html),
[Python process time](https://docs.python.org/3/library/time.html#time.process_time).
Recorder overhead includes writing the start receipt, but excludes the finish write and
summary generation. Success checks include the actual scheduler command, not a guessed CLI.
