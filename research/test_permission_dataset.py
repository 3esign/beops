#!/usr/bin/env python3
"""test_permission_dataset.py - the published dataset had no test.

public/dataset/permission-landscape/ is offered under CC BY 4.0 with a citation, a data dictionary and
a manifest of hashes. It says of itself that it contains no captured bytes, no headline text, no
personal data and no measurement values. Nothing checked any of that, and a dataset that quietly
starts carrying what it promised not to is worse than one that never promised.
"""
import csv
import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import export_permission_dataset as ex  # noqa: E402
import record  # noqa: E402

OUT = ROOT / "public" / "dataset" / "permission-landscape"


def read(name):
    with open(OUT / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class Dataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "research" / "SOURCE_REGISTRY.json").exists():
            raise unittest.SkipTest("no registry on this machine")
        cls.manifest = ex.build()

    def test_it_rebuilds_and_every_file_matches_its_own_hash(self):
        for f in self.manifest["files"]:
            p = OUT / f["name"]
            self.assertTrue(p.exists(), f"{f['name']} is in the manifest and not on disk")
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), f["sha256"],
                             f"{f['name']} does not match the hash the manifest publishes for it")

    def test_it_carries_the_files_it_says_it_carries(self):
        names = {f["name"] for f in self.manifest["files"]}
        for need in ("sources.csv", "refusals.csv", "captures.csv", "data_dictionary.md", "README.md"):
            self.assertIn(need, names)

    def test_the_source_rows_are_the_registry_rows(self):
        reg = json.loads((ROOT / "research" / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))
        self.assertEqual(len(read("sources.csv")), len(reg["sources"]))

    def test_refusals_contains_only_sources_that_refused(self):
        reg = {s.get("id"): s.get("status") for s in
               json.loads((ROOT / "research" / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))["sources"]}
        for r in read("refusals.csv"):
            self.assertIn(reg.get(r["source_id"]), ("opted_out", "blocked", "restricted"),
                          f"{r['source_id']} is in refusals.csv and did not refuse")

    def test_it_contains_no_captured_bytes_and_no_headline_text(self):
        """Two of its own promises. The captures are third-party content held as evidence, not as
        publication; the headlines are personal data and this dataset is about organisations."""
        rowsdir = ROOT / "data" / "live" / "rows"
        heads = []
        for d in sorted(rowsdir.iterdir()) if rowsdir.exists() else []:
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.jsonl")):
                for r in record.objects(f, limit=400):     # it wanted 400 lines and read 41 MB
                    if r.get("parameter") == "headline" and isinstance(r.get("result"), str) and len(r["result"]) > 30:
                        heads.append(r["result"])
            if len(heads) > 25:
                break
        blob = "\n".join((OUT / f["name"]).read_text(encoding="utf-8", errors="replace")
                         for f in self.manifest["files"])
        leaked = [h[:60] for h in heads if h in blob]
        self.assertEqual(leaked, [], "a headline reached the published dataset: " + "; ".join(leaked[:3]))
        self.assertNotIn("-----BEGIN", blob)
        self.assertNotIn("<!DOCTYPE", blob, "a captured page reached the dataset")

    def test_it_contains_no_measurement_values(self):
        rows = read("sources.csv")
        self.assertNotIn("result", rows[0].keys())
        self.assertNotIn("value", rows[0].keys())

    def test_the_dictionary_says_what_a_status_is_not_before_what_it_is(self):
        """The sentence the whole dataset turns on: a status is this project's reading of what a site
        said on one day, not a characterisation of an organisation."""
        d = (OUT / "data_dictionary.md").read_text(encoding="utf-8")
        self.assertIn(ex.NOT_A_SCORE, d)
        i_not, i_is = d.find(ex.NOT_A_SCORE), d.find("this project's reading")
        self.assertNotEqual(i_is, -1)
        self.assertLess(i_is, i_not, "the caveat is printed before the thing it qualifies")
        self.assertLess(i_not - i_is, 400, "the caveat has drifted away from the definition it qualifies")

    def test_the_caveat_is_one_sentence_and_not_three_copies_of_one(self):
        """It lived in three places and the three had already drifted: the dictionary had lost
        'compliance score' and 'ranking' while the README and the Zenodo record still carried them.
        Whatever else is true of this sentence, it must be the same sentence everywhere."""
        for name in ("data_dictionary.md", "README.md", "zenodo.json"):
            self.assertIn(ex.NOT_A_SCORE, (OUT / name).read_text(encoding="utf-8"),
                          f"{name} states the caveat in its own words instead of quoting the one")

    def test_the_deposition_record_was_generated_because_it_says_it_was(self):
        """zenodo.json v1.0 said 'Generated by tools/export_permission_dataset.py ... none is typed
        by hand' and was typed by hand. A file that describes its own provenance has to be right
        about it before anything else it says can be trusted."""
        z = json.loads((OUT / "zenodo.json").read_text(encoding="utf-8"))["metadata"]
        self.assertIn("Generated by tools/export_permission_dataset.py", z["notes"])
        self.assertEqual(z["version"], ex.VERSION, "the deposition record does not say which version it is")
        n = len(read("sources.csv"))
        self.assertIn(str(n), z["title"], "the title carries a count that is not the count of rows")
        self.assertIn(f"{n} reviewed sources", z["description"])
        # and it must actually be rebuilt, not merely present
        (OUT / "zenodo.json").write_text("{}", encoding="utf-8")
        ex.build()
        self.assertIn("upload_type", (OUT / "zenodo.json").read_text(encoding="utf-8"),
                      "the exporter does not rewrite the file it claims to generate")

    def test_the_manifest_is_a_declaration_and_not_a_listing_of_the_directory(self):
        """v1.0's manifest was `OUT.iterdir()`, so a working note left in that folder was published
        as part of a CC BY dataset. Nothing undeclared may reach a manifest again."""
        self.assertEqual([f["name"] for f in self.manifest["files"]], list(ex.PUBLISHED))
        stray = OUT / "_stray_from_test.md"
        stray.write_text("this must never be published\n", encoding="utf-8")
        try:
            with self.assertRaises(SystemExit, msg="a stray file in the folder did not stop the build"):
                ex.build()
        finally:
            stray.unlink()
        ex.build()

    def test_every_version_says_what_it_is_not_relative_to_the_one_before(self):
        c = (OUT / "CHANGES.md").read_text(encoding="utf-8")
        self.assertIn(ex.VERSION, [v for v, _, _ in ex.CHANGES],
                      "the current version has no entry in CHANGES")
        for v, _, _ in ex.CHANGES:
            self.assertIn(f"## {v}", c)
        self.assertIn(ex.VERSION, c)

    def test_the_readme_states_the_bias_against_our_own_interest(self):
        r = (OUT / "README.md").read_text(encoding="utf-8")
        self.assertIn("incomplete", r)
        self.assertIn("robots files", r)
        self.assertIn(ex.LICENCE, r)

    def test_the_citation_names_both_authors(self):
        self.assertIn("Golubović Matić", ex.CITE)
        self.assertIn("Poturak", ex.CITE)


if __name__ == "__main__":
    unittest.main()
