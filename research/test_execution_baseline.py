"""The G0 snapshot keeps operational axes separate and counts durable evidence."""
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import execution_baseline as baseline


class ExecutionBaseline(unittest.TestCase):
    def test_axes_do_not_turn_collection_red_for_safe_policy_blocks_or_ai_lateness(self):
        commands = {name: {"exit_code": 0, "stdout": ""} for name in ("tests", "doctor", "tasks", "guard", "watch", "site")}
        commands["guard"]["stdout"] = "guard now verdict: ok"
        commands["site"]["stdout"] = json.dumps({"ok": True, "operational_verdict": "CURRENT_AND_VERIFIED"})
        watch = {"checks": [{"check": "rows", "state": "ok"}, {"check": "published", "state": "ok"},
                            {"check": "AI observations", "state": "late"},
                            {"check": "source S1", "state": "ok"}, {"check": "source S2", "state": "blocked"}]}
        axes = baseline.summarize_axes(commands, watch, {"expected": 9, "ok": 9, "drift": 0})
        self.assertEqual(axes["collection"]["state"], "ok")
        self.assertEqual(axes["collection"]["policy_blocked_sources"], 1)
        self.assertEqual(axes["publishing"]["state"], "ok")
        self.assertEqual(axes["ai"]["state"], "late")

    def test_aliases_are_matching_tasks_and_npm_preamble_does_not_hide_json(self):
        parsed = baseline.parse_json_output({"stdout": "> beops test:site\n\n{\"ok\":true,\"nested\":{\"ok\":false}}\n"})
        self.assertEqual(parsed, {"ok": True, "nested": {"ok": False}})
        commands = {name: {"exit_code": 0, "stdout": ""} for name in ("tests", "doctor", "tasks", "guard", "watch", "site")}
        commands["guard"]["stdout"] = "guard now verdict: ok"
        commands["site"]["stdout"] = '> beops test:site\n{"ok":true,"operational_verdict":"CURRENT_AND_VERIFIED"}'
        watch = {"checks": [{"check": "rows", "state": "ok"}, {"check": "published", "state": "ok"},
                            {"check": "AI observations", "state": "ok"}]}
        axes = baseline.summarize_axes(commands, watch, {"expected": 9, "ok": 0, "alias": 9, "drift": 0})
        self.assertEqual(axes["scheduler"]["state"], "ok")
        self.assertEqual(axes["publishing"]["state"], "ok")

    def test_inventory_separates_responses_from_attempts_without_text(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            feed = root / "runtime" / "ai-feed"
            for name in ("receipts", "responses", "entries"):
                (feed / name).mkdir(parents=True)
            for key, state, response in (("a", "accepted", True), ("b", "failed", True), ("c", "failed", False)):
                row = {"id": key, "state": state, "reason": "validation_rejected" if key == "b" else None}
                (feed / "receipts" / f"{key}-finish.json").write_text(json.dumps(row), encoding="utf-8")
                if response:
                    (feed / "responses" / f"{key}.json").write_text("{}", encoding="utf-8")
                if state == "accepted":
                    (feed / "entries" / f"{key}.json").write_text("{}", encoding="utf-8")
            got = baseline.ai_inventory(root)
            self.assertEqual(got["terminal_attempts"], 3)
            self.assertEqual(got["evaluable_responses"], 2)
            self.assertEqual(got["operational_without_response"], 1)

    def test_snapshot_and_row_inventory_are_hashed_and_counted(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            rows = root / "data" / "live" / "rows" / "S1"
            rows.mkdir(parents=True)
            (rows / "2026-09.jsonl").write_text('{"x":1}\n{"x":2}\n', encoding="utf-8")
            public = root / "public"
            public.mkdir()
            snapshot = {"as_of": "2026-09-12T12:00:00Z", "sources": [{"sid": "S1"}]}
            path = public / "live-snapshot.json"
            path.write_text(json.dumps(snapshot), encoding="utf-8")
            self.assertEqual(baseline.row_inventory(root)["rows"], 2)
            got = baseline.snapshot_inventory(root, datetime(2026, 9, 12, 12, 30, tzinfo=timezone.utc))
            self.assertEqual(got["age_minutes"], 30)
            self.assertEqual(got["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
