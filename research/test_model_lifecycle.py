"""Periodic organs keep their model residency within the measured hardware budget."""
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import local_models as lm  # noqa: E402
import organ_mind as mind  # noqa: E402
import organ_news as news  # noqa: E402


class ModelLifecycle(unittest.TestCase):
    def test_mind_keeps_its_model_warm_only_for_the_voice_call(self):
        # C-071: one minute covers the Serbian rendering of the same thought; nothing longer.
        answer = {"message": {"content": "{}"}, "done": True, "done_reason": "stop"}
        with patch.object(mind.local_models, "request", return_value=answer) as request:
            mind.ollama_chat("fixture:1b", "prompt")
        self.assertEqual(request.call_args.args[2]["keep_alive"], "60s")
        self.assertEqual(request.call_args.kwargs.get("timeout"), 210)

    def test_news_uses_cpu_and_only_short_bounded_warmth(self):
        answer = {"message": {"content": "{}"}, "done": True}
        with patch.object(news.local_models, "request", return_value=answer) as request:
            news.ollama_chat("fixture:1b", "prompt")
        payload = request.call_args.args[2]
        self.assertEqual(payload["keep_alive"], "2m")
        self.assertEqual(payload["options"]["num_gpu"], 0)

    def test_embedding_model_is_released_too(self):
        with patch.object(mind.local_models, "request", return_value={"embeddings": []}) as request:
            mind.ollama_embed("fixture-embed", ["tekst"])
        self.assertEqual(request.call_args.args[2]["keep_alive"], "0s")

    def test_busy_shared_capacity_is_not_queued(self):
        with patch.object(lm, "model_slot") as slot, patch.object(lm, "_request_locked", return_value={}):
            lm.request("http://127.0.0.1:11434", "/api/tags", verify_model=False)
        self.assertEqual(slot.call_args.args[0], 0.0)


if __name__ == "__main__":
    unittest.main()
