"""AI quality review must remain blind, immutable and separate from provider availability."""
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ai_feed_review as review


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class FeedReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.feed = self.root / "runtime" / "ai-feed"
        for name in ("receipts", "responses", "contexts", "prompts", "entries"):
            (self.feed / name).mkdir(parents=True)
        self.context = {"schema": "beops-ai-context/v1", "as_of": "2026-09-12T12:00:00Z",
                        "facts": [{"id": "F1", "kind": "observation", "source": "Izvor",
                                   "place": "Zemun", "metric": "temperatura", "value": 20,
                                   "unit": "C", "clock": "measurement", "time": "2026-09-12T11:00:00Z",
                                   "received_at": "2026-09-12T11:01:00Z"}],
                        "coverage": [{"sid": "S1", "usable_streams": 1, "observed_streams": 2}]}
        context_raw = compact(self.context).encode()
        self.context_hash = hashlib.sha256(context_raw).hexdigest()
        (self.feed / "contexts" / f"{self.context_hash}.json").write_bytes(context_raw)
        prompt_raw = "Samo dokaz.".encode()
        self.prompt_hash = hashlib.sha256(prompt_raw).hexdigest()
        (self.feed / "prompts" / f"{self.prompt_hash}.txt").write_bytes(prompt_raw)
        self._attempt("a" * 32, "accepted", True, "gemini-test", None)
        self._attempt("b" * 32, "failed", True, "local-test", "validation_rejected")
        self._attempt("c" * 32, "failed", False, "transport-test", "provider_http_429")

    def tearDown(self):
        self.temp.cleanup()

    def _attempt(self, attempt, state, response, model, reason):
        finish = {"schema": "beops-ai-attempt/v1", "id": attempt, "at": "2026-09-12T12:00:00Z",
                  "provider": "fixture", "model": model, "context_hash": self.context_hash,
                  "prompt_hash": self.prompt_hash, "state": state}
        if reason:
            finish["reason"] = reason
        (self.feed / "receipts" / f"2026-{attempt}-finish.json").write_text(compact(finish), encoding="utf-8")
        if response:
            payload = {"text": '{"title":"Primer","paragraphs":[],"question":"?","limitations":"Granica"}',
                       "model": model, "transport": "fixture"}
            (self.feed / "responses" / f"{attempt}.json").write_text(compact(payload), encoding="utf-8")
        if state == "accepted":
            entry = {"id": attempt, "context_hash": self.context_hash, "prompt_hash": self.prompt_hash}
            (self.feed / "entries" / f"{attempt}.json").write_text(compact(entry), encoding="utf-8")

    def test_prepare_counts_only_durable_text_as_quality_population_and_stays_blind(self):
        output = self.root / "review"
        result = review.prepare(self.root, output, target=3, seed="fixture")
        self.assertEqual(result["items"], 2)
        self.assertEqual(result["shortage"], 1)
        self.assertEqual(result["population"]["terminal_attempts"], 3)
        self.assertEqual(result["population"]["accepted_responses"], 1)
        self.assertEqual(result["population"]["rejected_responses"], 1)
        self.assertEqual(result["population"]["excluded"]["no_response:failed"], 1)
        blind = json.loads((output / "packet-blind.json").read_text(encoding="utf-8"))
        rendered = json.dumps(blind)
        self.assertNotIn("gemini-test", rendered)
        self.assertNotIn("validation_rejected", rendered)
        self.assertEqual(blind["rows"][0]["deterministic_control"]["missing"], ["S1: upotrebljivo 1/2 tokova"])
        with self.assertRaises(FileExistsError):
            review.prepare(self.root, output, target=3)

    def test_human_score_and_two_reviewer_agreement_do_not_infer_missing_labels(self):
        output = self.root / "review"
        review.prepare(self.root, output, target=2, seed="fixture")
        packet = json.loads((output / "packet-private.json").read_text(encoding="utf-8"))
        ratings = {criterion: "no" if criterion == "causal_error" else "yes" for criterion in review.CRITERIA}
        first = {"packet_id": packet["packet_id"], "reviewer": "Čovek A", "reviewer_type": "human",
                 "independent_before_reveal": True, "rows": [{"id": packet["rows"][0]["id"], "ratings": ratings}]}
        scored = review.score(packet, first)
        self.assertEqual(scored["state"], "partial")
        self.assertEqual(scored["annotated"], 1)
        bad = dict(first, reviewer_type="model")
        with self.assertRaises(ValueError):
            review.score(packet, bad)
        second = dict(first, reviewer="Čovek B")
        agreement = review.compare(packet, first, second)
        self.assertEqual(agreement["overlap"], 1)
        self.assertEqual(agreement["state"], "insufficient_overlap")
        self.assertEqual(agreement["metrics"]["evidence_support"]["kappa"], 1.0)


if __name__ == "__main__":
    unittest.main()
