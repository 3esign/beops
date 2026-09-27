# Impulse map, v2 — location estimates and geographic scope

`tools/build_impulses.js` reads retained collector headline rows, official schedule cache and
accepted AI entries plus their immutable contexts. `--output` creates a new JSON artifact inside
the C workspace; it refuses overwriting an existing artifact. No model, paid geocoder or network
call is needed. `tools/impulse_model.js` contains the independently tested transformation.

The day/week/month views are trailing 24/168/720 hours, not calendar periods. Daily buckets
use Europe/Belgrade. Publication day without a clock is an interval; its overlap is disclosed,
not replaced with invented event time. Missing publication time uses the first retained receipt.
Official schedules use their scheduled start and never prove occurrence. AI interpretations use
the output time and remain a separate kind of signal.

Repeated source URLs and title revisions count once per source, retaining first clock, latest
title, revision count and first/last receipt. Different sources can cover the same story;
cross-source deduplication into actual events is not claimed. National/world headlines remain
in the retained-source denominator and must not be presented as Belgrade activity.

The original 28-label matcher remains a list of unverified name candidates. A separate offline
resolver (`tools/headline_geo.js`) now looks for event-place cues and uses a sourced gazetteer.
Accepted estimates carry the matched text, rule, source, named place, spatial precision and radius
in meters. A city receives a broader circle than a neighborhood or venue. These circles are
disclosed place-scale buffers; they are not administrative boundaries, calibrated probability
intervals or proof of the event's exact location. No percentage confidence is invented.

The source title alone supplies geographic cues: publisher headquarters and publisher URLs never
locate an event. Shared names, conflicting places, route endpoints and institution/team names can
remain unresolved. Belgrade, broader/other Serbia, outside Serbia and unknown are separate scopes.
Scope recognition alone does not establish a mappable event location. Unknown titles remain in
the denominator and available for inspection.

`location_estimate` and window `estimates` are separate from `point` and `points`. The latter are
reserved for exactly cited AI anchors in hash-verified contexts. Two AI texts at one instrument
remain two interpretations at one spatial anchor; an estimated center never becomes an exact
event point. Day/week/month counts still refer to retained source URLs, not deduplicated events.

The public headline/PM section requires local geographic evidence and a recent publication clock,
and still keeps the current measurements separate: a local title is not proof that a specific
station measured the described event. Water pollution and unrelated word fragments are not
air-quality topics. Historical or unresolved headlines remain accessible in the archive.

## Next useful increase in geographic coverage

1. Create a reviewed venue register with official address, sourced coordinates and precision;
   Kolarac's seven current schedules are the first concrete candidate.
2. Extract actual time intervals and street segments from permitted official transport/utility
   notices. A street name in a headline is not yet an affected segment or event time.
3. Expand the sourced place register and evaluate the resolver against independently labeled
   headlines. Radius policy and confidence in headline interpretation need separate validation.
4. Process new or changed source identities once; retain the result and proof. Reprocessing the
   entire archive through a model each cycle would add cost without new source information.

## Honest verdict

This implements a local data model and a reviewed local study, not a new public map release.
The v1 snapshot had only a very small number of AI anchors and name matches in a minority of
headlines. V2 adds explicitly estimated areas; its coverage is measured separately in the new
artifact. It is a map of evidence coverage and source signals, not a heatmap of all city life.
The existing public instrument map remains a different view with different evidence semantics.
