"""Offline tests for tools/organ_news.py - a fake model, never the daemon."""
import importlib.util
import json
import pathlib
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("organ_news", ROOT / "tools" / "organ_news.py")
on = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(on)
NOW = datetime(2026, 9, 9, 10, 0, tzinfo=timezone.utc)


def seed(live, rows):
    p = live / "rows" / "S68" / "2026-09.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


H = [{"sid": "S68", "kind": "text", "result": "Radovi na Brankovom mostu od ponedeljka", "resultTime": "2026-09-09T08:00:00Z",
      "receivedTime": "2026-09-09T09:00:00Z", "dedupe_key": "S68|a"},
     {"sid": "S68", "kind": "text", "result": "Vlada usvojila budzet", "resultTime": "2026-09-09T08:10:00Z",
      "receivedTime": "2026-09-09T09:00:00Z", "dedupe_key": "S68|b"}]


class OrganTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._live = on.LIVE
        on.LIVE = pathlib.Path(self.tmp.name) / "live"
        on.utcnow = lambda: NOW

    def tearDown(self):
        on.LIVE = self._live
        self.tmp.cleanup()

    def test_silent_when_daemon_down(self):
        seed(on.LIVE, H)
        rec = on.run(NOW, chat=lambda m, p: (_ for _ in ()).throw(AssertionError("must not be called")), tags=lambda: None)
        self.assertEqual(rec["state"], "organ_silent")
        self.assertEqual(rec["waiting"], 2)
        self.assertFalse((on.LIVE / "derived" / "news" / "2026-09.jsonl").exists())
        self.assertTrue((on.LIVE / "derived" / "news" / "receipts" / (on.stamp(NOW) + ".json")).exists())

    def test_derived_rows_are_estimates_with_provenance_and_gazetteer_only(self):
        seed(on.LIVE, H)
        answer = {"items": [
            {"i": 1, "headline": "Radovi na Brankovom mostu", "category": "radovi", "belgrade": True, "zones": [{"name": "Brankov most", "score": 0.9}, {"name": "Ulica Kneza Milosa", "score": 0.4}], "event_time_text": "od ponedeljka"},
            {"i": 2, "headline": "Vlada usvojila budzet", "category": "nije_beograd", "belgrade": False, "zones": [], "event_time_text": None}]}  # indices shifted by one on purpose: the echo must win
        rec = on.run(NOW, chat=lambda m, p: answer, tags=lambda: ["qwen3.5:cloud", "qwen2.5:3b", "other"])
        self.assertEqual(rec["state"], "derived")
        self.assertEqual(rec["model"], "qwen2.5:3b")
        lines = (on.LIVE / "derived" / "news" / "2026-09.jsonl").read_text(encoding="utf-8").strip().split("\n")
        a, b = (json.loads(x) for x in lines)
        self.assertEqual(a["state"], "estimated")
        self.assertTrue(a["ai_generated"])
        self.assertEqual(a["category"], "radovi")
        self.assertEqual(a["zones"][0], {"name": "Brankov most", "score": 0.9})
        self.assertIsNone(a["zones"][1]["name"])            # not in gazetteer -> kept as a rejection
        self.assertEqual(a["zones"][1]["rejected"], "Ulica Kneza Milosa")
        self.assertEqual(a["binding"], "inferred_from_content")
        self.assertEqual(a["bound_by"], "echo")
        self.assertEqual(len(a["prompt_sha256"]), 64)
        self.assertEqual(a["input_key"], "S68|a")
        self.assertFalse(b["belgrade"])
        # second run: nothing left to do, no call
        rec2 = on.run(NOW + __import__("datetime").timedelta(minutes=1), chat=lambda m, p: (_ for _ in ()).throw(AssertionError("must not be called")), tags=lambda: ["qwen2.5:3b"])
        self.assertEqual(rec2["state"], "nothing_to_do")

    def test_unknown_category_and_missing_item_are_null_not_guessed(self):
        seed(on.LIVE, H)
        answer = {"items": [{"i": 0, "category": "nesto_novo", "belgrade": "yes", "zones": [], "event_time_text": None}]}
        on.run(NOW, chat=lambda m, p: answer, tags=lambda: ["lfm2.5:1.2b"])
        lines = (on.LIVE / "derived" / "news" / "2026-09.jsonl").read_text(encoding="utf-8").strip().split("\n")
        a, b = (json.loads(x) for x in lines)
        self.assertIsNone(a["category"])
        self.assertIsNone(a["belgrade"])
        self.assertIsNone(b["category"])
        self.assertIn("no item", b["note"])

    def test_cloud_models_are_skipped_unless_allowed(self):
        self.assertIsNone(on.pick_model(["qwen3.5:cloud", "gemma4:cloud"], ["qwen3.5", "gemma4"]))
        self.assertEqual(on.pick_model(["qwen3.5:cloud", "qwen2.5:3b"], ["qwen3.5", "qwen2.5:3b"]), "qwen2.5:3b")
        self.assertEqual(on.pick_model(["qwen3.5:cloud"], ["qwen3.5"], allow_cloud=True), "qwen3.5:cloud")

    def test_registry_lists_the_organ_with_editor(self):
        c = on.check()
        self.assertEqual(c["organ"], "news-sorter")
        self.assertTrue(c["editor_of_record"])
        self.assertGreater(c["gazetteer"], 40)


if __name__ == "__main__":
    unittest.main()
