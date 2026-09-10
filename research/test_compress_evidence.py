#!/usr/bin/env python3
"""test_compress_evidence.py - the tool that gzips stored evidence had no test, and three defects.

Evidence is the thing this project cannot replace. A capture is the bytes a publisher actually served
on a day that will not come again; if it is lost, the permission it evidences is gone with it.

The tool that compresses those files deleted the original **before anything read the compressed copy
back**. A gzip written to a full disk, or interrupted, would have destroyed the only copy. It also
rewrote manifests in directories where nothing had changed, and it was top-level code that did its
work on import, which is why nothing tested it.
"""
import gzip
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import compress_large_evidence as C  # noqa: E402

BIG = (b'{"served": "' + b"x" * 60000 + b'", "diakritika": "\xc4\x8d\xc4\x87\xc5\xbe\xc5\xa1\xc4\x91"}')
SMALL = b'{"served": "short"}'


def tree(files: dict, manifest=True):
    d = pathlib.Path(tempfile.mkdtemp())
    for name, body in files.items():
        (d / name).write_bytes(body)
    if manifest:
        (d / "MANIFEST.json").write_text(json.dumps({
            "files": [{"file": n, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
                      for n, b in files.items()]}, indent=1), encoding="utf-8")
    return d


class Compress(unittest.TestCase):
    def test_the_original_is_only_removed_after_the_copy_reads_back_identical(self):
        d = tree({"capture.json": BIG})
        want = hashlib.sha256(BIG).hexdigest()
        r = C.run(d, threshold=1000)
        self.assertEqual(len(r["compressed"]), 1)
        self.assertFalse((d / "capture.json").exists(), "the original was not removed")
        gz = d / "capture.json.gz"
        self.assertTrue(gz.exists())
        with gzip.open(gz, "rb") as fh:
            back = fh.read()
        self.assertEqual(hashlib.sha256(back).hexdigest(), want,
                         "what comes out of the archive is not what went in")
        self.assertEqual(back, BIG)

    def test_a_failed_round_trip_keeps_both_copies_and_reports(self):
        """The defect this whole file exists for. If the archive cannot be read back, the original
        must still be there afterwards."""
        d = tree({"capture.json": BIG})
        real = C.sha256_of_gz

        def broken(_path):
            return "0" * 64

        C.sha256_of_gz = broken
        try:
            r = C.run(d, threshold=1000)
        finally:
            C.sha256_of_gz = real
        self.assertEqual(r["compressed"], [])
        self.assertEqual(len(r["failed"]), 1)
        self.assertIn("round trip", r["failed"][0])
        self.assertTrue((d / "capture.json").exists(),
                        "the original was deleted although the copy could not be verified")

    def test_a_file_below_the_threshold_is_untouched(self):
        d = tree({"small.json": SMALL})
        r = C.run(d, threshold=1000)
        self.assertEqual(r["compressed"], [])
        self.assertTrue((d / "small.json").exists())
        self.assertFalse((d / "small.json.gz").exists())

    def test_the_manifest_keeps_the_original_hash_and_length(self):
        """A reader verifies against what was served, not against what is on disk now."""
        d = tree({"capture.json": BIG})
        before = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))["files"][0]
        C.run(d, threshold=1000)
        after = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))["files"][0]
        self.assertEqual(after["sha256"], before["sha256"], "the manifest's hash changed")
        self.assertEqual(after["bytes"], before["bytes"], "the manifest's length changed")
        self.assertEqual(after["stored_compression"], "gzip")
        self.assertEqual(after["stored_as"], "capture.json.gz")
        self.assertIn("ORIGINAL", after["note"])
        self.assertLess(after["stored_bytes"], before["bytes"])

    def test_a_manifest_is_not_rewritten_when_nothing_in_its_directory_changed(self):
        """The counter used to be global, so one compression anywhere rewrote every manifest
        everywhere - a modification to an immutable record for no reason."""
        d = pathlib.Path(tempfile.mkdtemp())
        (d / "a").mkdir()
        (d / "b").mkdir()
        (d / "a" / "big.json").write_bytes(BIG)
        (d / "a" / "MANIFEST.json").write_text(json.dumps(
            {"files": [{"file": "big.json", "bytes": len(BIG),
                        "sha256": hashlib.sha256(BIG).hexdigest()}]}, indent=1), encoding="utf-8")
        (d / "b" / "small.json").write_bytes(SMALL)
        quiet = d / "b" / "MANIFEST.json"
        quiet.write_text('{"files": [{"file": "small.json"}]}', encoding="utf-8")
        untouched = quiet.read_bytes()
        r = C.run(d, threshold=1000)
        self.assertEqual(len(r["compressed"]), 1)
        self.assertEqual(quiet.read_bytes(), untouched,
                         "a manifest was rewritten in a directory where nothing was compressed")
        self.assertEqual(r["manifests_written"], [str(d / "a" / "MANIFEST.json")])

    def test_running_it_twice_changes_nothing_the_second_time(self):
        d = tree({"capture.json": BIG})
        C.run(d, threshold=1000)
        man_after_first = (d / "MANIFEST.json").read_bytes()
        r = C.run(d, threshold=1000)
        self.assertEqual(r["compressed"], [], "an already-compressed file was compressed again")
        self.assertEqual((d / "MANIFEST.json").read_bytes(), man_after_first)

    def test_a_dry_run_touches_nothing(self):
        d = tree({"capture.json": BIG})
        before = sorted(p.name for p in d.iterdir())
        r = C.run(d, threshold=1000, dry_run=True)
        self.assertEqual(len(r["compressed"]), 1, "a dry run did not say what it would do")
        self.assertEqual(sorted(p.name for p in d.iterdir()), before,
                         "a dry run changed the directory")
        self.assertEqual(r["manifests_written"], [])

    def test_importing_the_tool_does_not_compress_anything(self):
        """It used to be top-level code: importing it did the work. That is why nothing tested it."""
        self.assertTrue(hasattr(C, "run"))
        self.assertTrue(hasattr(C, "main"))
        d = tree({"capture.json": BIG})
        import importlib
        importlib.reload(C)
        sys.path.insert(0, str(ROOT / "tools"))
        self.assertTrue((d / "capture.json").exists(), "importing the module compressed a file")


if __name__ == "__main__":
    unittest.main()
