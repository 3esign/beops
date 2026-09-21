"""Offline tests for tools/organ_news.py - a fake model, never the daemon."""
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
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

    def test_transport_failure_never_spends_a_headline_quality_attempt(self):
        seed(on.LIVE, H)

        def timeout(_model, _prompt):
            raise TimeoutError("fixture timeout")

        rec = on.run(NOW, chat=timeout, tags=lambda: ["qwen2.5:1.5b"])
        self.assertEqual(rec["state"], "waiting_model")
        self.assertEqual(rec["reason"], "no alternate local model after transport failure")
        attempts = json.loads((on.LIVE / "derived/news/attempts.json").read_text(encoding="utf-8"))
        retry = json.loads((on.LIVE / "derived/news/retry.json").read_text(encoding="utf-8"))
        self.assertEqual(attempts, {})
        self.assertTrue(all(row["state"] == "failed" and row["transport_failures"] == 1
                            for row in retry.values()))

    def test_only_transport_failures_are_waiting_model_even_when_last_fallback_is_untried(self):
        seed(on.LIVE, H)
        calls = []

        def tags():
            return ["qwen2.5:1.5b", "qwen3.5:4b"] if not calls else ["qwen3.5:4b"]

        def timeout(model, _prompt):
            calls.append(model)
            raise RuntimeError("CLI returned no output")

        rec = on.run(NOW, chat=timeout, tags=tags, batch_size=1, limit=1)
        self.assertEqual(calls, ["qwen2.5:1.5b"])
        self.assertEqual(rec["fallbacks"], [{"from": "qwen2.5:1.5b", "to": "qwen3.5:4b",
                                             "after": "RuntimeError"}])
        self.assertEqual(rec["state"], "waiting_model")
        self.assertEqual(rec["reason"], "local model transport failed before a complete answer")

    def test_non_transport_model_error_remains_organ_failed(self):
        seed(on.LIVE, H[:1])

        def malformed(_model, _prompt):
            raise json.JSONDecodeError("bad model json", "x", 0)

        rec = on.run(NOW, chat=malformed, tags=lambda: ["qwen2.5:1.5b"])
        self.assertEqual(rec["state"], "organ_failed")

    def test_transport_failure_falls_back_to_next_local_model(self):
        seed(on.LIVE, H)
        calls = []

        def tags():
            return ["qwen2.5:1.5b", "qwen3.5:4b"] if not calls else ["qwen3.5:4b"]

        def chat(model, _prompt):
            calls.append(model)
            if model == "qwen2.5:1.5b":
                raise RuntimeError("CLI returned no output")
            return {"items": [{"i": 0, "headline": H[1]["result"], "category": "nije_beograd",
                               "belgrade": False, "zones": [], "event_time_text": None}]}

        rec = on.run(NOW, chat=chat, tags=tags, batch_size=1, limit=2)
        self.assertEqual(calls, ["qwen2.5:1.5b", "qwen3.5:4b"])
        self.assertEqual(rec["state"], "derived")
        self.assertEqual(rec["derived"], 1)
        self.assertEqual(rec["fallbacks"], [{"from": "qwen2.5:1.5b", "to": "qwen3.5:4b",
                                             "after": "RuntimeError"}])

    def test_reconcile_rebuilds_attempt_budget_from_retained_rows(self):
        seed(on.LIVE, H[:1])
        answer = {"items": [{"i": 0, "headline": H[0]["result"], "category": "radovi",
                             "belgrade": True, "zones": [], "event_time_text": "od ponedeljka"}]}
        on.run(NOW, chat=lambda _m, _p: answer, tags=lambda: ["qwen2.5:1.5b"])
        attempts_path = on.LIVE / "derived/news/attempts.json"
        attempts_path.write_text(json.dumps({"S68|a": 3}), encoding="utf-8")
        result = on.reconcile_completion()
        repaired = json.loads(attempts_path.read_text(encoding="utf-8"))
        self.assertEqual(repaired, {"S68|a": 1})
        self.assertEqual(result["unsupported_attempts_removed"], 2)
        self.assertEqual(result["supported_attempts_recovered"], 0)
        self.assertEqual(result["pending_keys_reopened"], 0)

    def test_attempt_cache_delta_separates_recovery_from_removal(self):
        delta = on.news_state.attempt_cache_delta(
            {"transport-only": 3, "old-row": 0, "still-semantic": 3},
            {"old-row": 2, "still-semantic": 3},
            set(),
        )
        self.assertEqual(delta, {
            "unsupported_attempts_removed": 3,
            "supported_attempts_recovered": 2,
            "pending_keys_reopened": 1,
            "pending_semantic_exhausted": 1,
        })

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

    def test_cli_file_model_names_match_ollama_style_preferences(self):
        self.assertEqual(on.pick_model(["qwen3.5-4b", "qwen2.5-1.5b-hf"], ["qwen3.5:4b"]), "qwen3.5-4b")

    def test_cold_model_has_time_to_load_and_stays_warm_between_batches(self):
        captured = {}
        original = on.local_models.request

        def fake_request(base, path, payload, timeout):
            captured.update(base=base, path=path, payload=payload, timeout=timeout)
            return {"message": {"content": '```json\n{"ok": true}\n```'}, "done": True}

        on.local_models.request = fake_request
        try:
            self.assertEqual(on.ollama_chat("qwen2.5:1.5b", "test"), {"ok": True})
        finally:
            on.local_models.request = original

        self.assertEqual(captured["timeout"], 210)
        self.assertEqual(captured["payload"]["keep_alive"], "2m")
        self.assertFalse(captured["payload"]["stream"])
        self.assertNotIn("format", captured["payload"])
        self.assertEqual(captured["payload"]["options"]["num_gpu"], 0)

    def test_partial_ollama_stream_is_rejected(self):
        original = on.local_models.request
        on.local_models.request = lambda *_args, **_kwargs: {
            "message": {"content": "@@@@@@@@"}, "done": False
        }
        try:
            with self.assertRaisesRegex(ValueError, "incomplete Ollama response"):
                on.ollama_chat("qwen2.5:1.5b", "test")
        finally:
            on.local_models.request = original

    def test_length_limited_ollama_response_is_rejected_even_when_json_is_valid(self):
        original = on.local_models.request
        on.local_models.request = lambda *_args, **_kwargs: {
            "message": {"content": '{"items": []}'}, "done": True, "done_reason": "length"
        }
        try:
            with self.assertRaisesRegex(ValueError, "incomplete Ollama response"):
                on.ollama_chat("qwen2.5:1.5b", "test")
        finally:
            on.local_models.request = original

    def test_registry_lists_the_organ_with_editor(self):
        c = on.check()
        self.assertEqual(c["organ"], "news-sorter")
        self.assertTrue(c["editor_of_record"])
        self.assertGreater(c["gazetteer"], 40)


if __name__ == "__main__":
    unittest.main()
