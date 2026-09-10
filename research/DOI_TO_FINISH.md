# The permission dataset: what is ready, and the one step that needs your hands

**Status 2026-09-10, dataset v1.1.** The dataset is complete, licensed and citable in form. It is not
citable in fact, because it has no DOI, and a DOI is the one thing here I will not obtain on your
behalf — it needs an account and a token, and this project's standing rule is that credentials are
yours.

This note is a working document. It is not part of the dataset and is not published with it; v1.0
published it by accident, because the dataset's manifest was a listing of its folder rather than a
declaration of its contents. That is fixed: a file that is not declared now stops the build.

## What exists now

`public/dataset/permission-landscape/`, rebuilt by the exporter on every run:

| file | what it is |
|---|---|
| `sources.csv` | 215 reviewed sources: id, theme, kind, status, polled or not, whether stored permission evidence exists, host, and the reason in the reviewer's own words |
| `refusals.csv` | the 16 that declined, on their own, because they are the finding |
| `captures.csv` | 313 stored permission captures with their hashes |
| `data_dictionary.md` | every column — and what a status is **not**, before what it is |
| `README.md` | the counts, the citation, and the bias in the source list stated against our own interest |
| `CHANGES.md` | what each version is, relative to the one before it |
| `zenodo.json` | the deposition record, generated from the same registry as the rest |
| `MANIFEST.json` | sha256 and byte length of each file above |

Licence **CC BY 4.0**. No captured bytes, no headline text, no personal data, no measurement values.

## The metadata a deposit needs, already written

`zenodo.json` is a complete Zenodo deposition record: title, authors with affiliation, description,
version, licence, keywords, language, and the related-identifier link back to the source repository.
It is generated from the record, so its counts cannot drift from the CSVs. Nothing in it needs editing.

## The step that needs you

One of these, whichever you prefer:

1. **Zenodo** — sign in at zenodo.org, *New upload*, add the files, then *Import metadata* and paste
   `zenodo.json`. It mints the DOI on publish. Zenodo also links a GitHub repository directly:
   switching the `3esign/beops` repository on in Zenodo's GitHub settings mints a DOI for every future
   release automatically, which would suit a record that publishes itself every ten minutes.
2. **Kaggle** — the client is already written and reads a key from the place the Kaggle tools expect.
   Once a key is in place on this machine I can create and push the dataset without you touching it
   again. Kaggle gives a stable URL and a citation block but not a DOI, so it is the weaker of the two
   for a paper.

**My recommendation:** Zenodo, and turn on the GitHub link while you are there. The DOI then belongs to
the repository rather than to one export, which matches what this record actually is.

## Then

Tell me the DOI and I will put it into the dataset README, the manifest, the citation line in the
exporter, and the pre-paper — as a new version, in one pass.
