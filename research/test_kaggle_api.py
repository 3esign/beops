#!/usr/bin/env python3
"""test_kaggle_api.py - the Kaggle client, offline. No network, no credential, no key ever printed."""
import contextlib
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import kaggle_api as ka  # noqa: E402

FAKE = "k" * 40


class Credential(unittest.TestCase):
    def setUp(self):
        self.saved = {k: os.environ.get(k) for k in ("KAGGLE_USERNAME", "KAGGLE_KEY", "KAGGLE_CONFIG_DIR", "HOME", "USERPROFILE")}

    def tearDown(self):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_the_environment_comes_first(self):
        os.environ["KAGGLE_USERNAME"], os.environ["KAGGLE_KEY"] = "someone", FAKE
        self.assertEqual(ka.credential(), ("someone", FAKE))

    def test_the_file_kaggle_downloads_is_read_as_it_comes(self):
        for k in ("KAGGLE_USERNAME", "KAGGLE_KEY"):
            os.environ.pop(k, None)
        with tempfile.TemporaryDirectory() as d:
            os.environ["KAGGLE_CONFIG_DIR"] = d
            (pathlib.Path(d) / "kaggle.json").write_text(json.dumps({"username": "someone", "key": FAKE}), encoding="utf-8")
            self.assertEqual(ka.credential(), ("someone", FAKE))

    def test_no_credential_says_what_to_do_and_does_not_crash_the_caller(self):
        for k in ("KAGGLE_USERNAME", "KAGGLE_KEY", "KAGGLE_CONFIG_DIR"):
            os.environ.pop(k, None)
        with tempfile.TemporaryDirectory() as d:
            os.environ["HOME"] = d
            os.environ["USERPROFILE"] = d
            with self.assertRaises(ka.NoCredential) as cm:
                ka.credential()
            self.assertIn("Create New Token", str(cm.exception))
            # main() prints; the suite's stdout is redirected into runtime/tests.txt, which the run
            # script greps for a line starting with OK to decide whether anything may be committed.
            # A test that writes to that file is a test that can vote on its own gate. Capture it.
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = ka.main(["kaggle_api.py", "whoami"])
            self.assertEqual(rc, 3)
            self.assertIn("no credential", buf.getvalue())
            self.assertNotIn(FAKE, buf.getvalue())

    def test_whoami_never_returns_the_key(self):
        os.environ["KAGGLE_USERNAME"], os.environ["KAGGLE_KEY"] = "someone", FAKE
        calls = []
        real = ka._req
        ka._req = lambda *a, **k: calls.append(a) or {}
        try:
            out = ka.whoami()
        finally:
            ka._req = real
        self.assertEqual(out["key_length"], 40)
        self.assertEqual(out["key"], "not shown")
        self.assertNotIn(FAKE, json.dumps(out))
        self.assertTrue(out["authenticated"])


class Pack(unittest.TestCase):
    """The observatory's rule is that the record and the evidence never leave this body. The bench
    sends digests. That is enforced here, so the sentence in the register is a property of the code."""

    def test_a_pack_of_digests_is_clean(self):
        pack = {"schema": "beops-bench-pack/v1", "made_at": "2026-09-10T00:00:00Z", "window_hours": 6,
                "digests": [{"as_of": "x", "numbers": ["41"], "clock": ["22:00"], "sids": {"S146": "SEPA"},
                             "facts": [{"id": "F1", "sr": "a", "en": "b", "kind": "spread", "sid": "S146",
                                        "parameter": "PM10", "lo": 18, "hi": 41}]}]}
        ok, bad = ka.pack_is_clean(pack)
        self.assertTrue(ok, bad)

    def test_a_pack_that_smuggles_evidence_is_refused_by_name(self):
        for leak in ({"receipts": [{"body": "..."}]}, {"digests": [{"permission": "captured"}]},
                     {"digests": [{"facts": [{"id": "F1", "article_body": "the whole text"}]}]},
                     {"notebook": ["what the entity said"]}):
            pack = {"schema": "beops-bench-pack/v1", **leak}
            ok, bad = ka.pack_is_clean(pack)
            self.assertFalse(ok, leak)
            self.assertTrue(bad, leak)


if __name__ == "__main__":
    unittest.main()
