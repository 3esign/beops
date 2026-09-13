# Changes

Each version of this dataset says what it is not, relative to the one before it. Older versions are not rewritten.

## 1.2 — 2026-09-11

Capture manifest hashes are read and verified from stored evidence; outcomes are explicit allowed/refused/unknown. Each content edition is preserved under releases/<edition_id>.

## 1.1 — 2026-09-10

Three corrections, none of them to a row. (a) The data dictionary's caveat on `status` was shorter than the README's and had lost "compliance score" and "ranking"; both now quote one sentence held in one place. (b) `zenodo.json` was written by hand while stating that it had been generated from the record; it is now generated from the record, and carries the version it describes, which it did not before. (c) v1.0's manifest was a listing of the directory, so a working note left in that folder was published as part of the dataset; the manifest is now built from a declared list and a file that is not on it stops the build. The CSVs of 1.1 are byte-identical to those of 1.0, verified by hash.

## 1.0 — 2026-09-10

First publication: 215 sources reviewed, the refusals named, the permission captures listed by hash.
