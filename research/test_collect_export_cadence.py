"""C-076: a collector tick refreshes the local snapshot at most every ten minutes.

Under a publish the export waited for the release lock and reread the rows for over 100 s,
which pushed the tick past its next five-minute slot; Windows skips a slot while a run is
still going. Collection itself must not wait for a view that is only minutes old.
"""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location("collect_daemon_cadence", ROOT / "tools" / "collect_daemon.py")
cd = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cd)


class ExportCadence(unittest.TestCase):
    def run_tick(self, root):
        calls = []
        out = io.StringIO()
        with mock.patch.object(cd, "ROOT", root), \
                mock.patch.object(cd, "tick", lambda only="": {"schema": "beops-live-tick/v1", "results": []}), \
                mock.patch.object(cd, "export", lambda: calls.append(1) or root / "public" / "live-snapshot.json"), \
                mock.patch.object(sys, "argv", ["collect_daemon.py", "tick"]), \
                contextlib.redirect_stdout(out):
            code = cd.main()
        return code, calls, json.loads(out.getvalue())

    def test_a_fresh_snapshot_is_kept_and_an_old_one_is_rebuilt(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            snap = root / "public" / "live-snapshot.json"
            snap.parent.mkdir(parents=True)
            snap.write_text("{}", encoding="utf-8")
            code, calls, result = self.run_tick(root)
            self.assertEqual((code, calls), (0, []))
            self.assertTrue(result["snapshot"].startswith("kept"))
            self.assertIn("timing", result)
            old = time.time() - cd.EXPORT_EVERY_SECONDS - 5
            os.utime(snap, (old, old))
            code, calls, result = self.run_tick(root)
            self.assertEqual((code, calls), (0, [1]))

    def test_a_missing_snapshot_is_built(self):
        with tempfile.TemporaryDirectory() as td:
            code, calls, _ = self.run_tick(pathlib.Path(td))
            self.assertEqual(calls, [1])

    def test_the_interval_stays_inside_what_the_readers_accept(self):
        # The watch calls counts older than 30 min unknown; the AI panel refuses a snapshot older than 60 min.
        self.assertLessEqual(cd.EXPORT_EVERY_SECONDS, 15 * 60)


if __name__ == "__main__":
    unittest.main()
