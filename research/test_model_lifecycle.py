"""Periodic organs keep their model residency within the measured hardware budget."""
import pathlib
import os
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
        self.assertTrue(request.call_args.kwargs.get("allow_cloud"))

    def test_account_cli_does_not_take_the_local_gpu_slot(self):
        response = {"done": True}
        with patch.dict(os.environ, {"BEOPS_MODEL_BACKEND": "cli"}), \
             patch.object(lm, "model_slot") as slot, \
             patch.object(lm, "_request_bridge", return_value=response) as bridge:
            got = lm.request("http://127.0.0.1:11434", "/api/chat",
                             {"model": "gpt-5.6-luna"}, allow_cloud=True)
        self.assertEqual(got, response)
        slot.assert_not_called()
        bridge.assert_called_once()

    def test_bridge_deadline_precedes_subprocess_guard(self):
        completed = __import__('subprocess').CompletedProcess([], 0, stdout='{}', stderr='')
        with patch.object(lm.subprocess, "run", return_value=completed) as run:
            lm._request_bridge("/api/chat", {"model": "gpt-5.6-luna"}, 75)
        sent = __import__('json').loads(run.call_args.kwargs["input"])
        self.assertEqual(run.call_args.kwargs["timeout"], 75)
        self.assertEqual(sent["timeout"], 60)

    def test_mind_requests_one_bilingual_cloud_object(self):
        content = {"text": "Two stations [F1] reported 41.", "cites": ["F1"],
                   "hypotheses": [], "questions": [], "next_check": "", "claim": {},
                   "sr": "Dve stanice [F1] su javile 41.", "hypotheses_sr": [], "questions_sr": []}
        answer = {"message": {"content": __import__('json').dumps(content)}, "done": True, "done_reason": "stop"}
        with patch.object(mind, "register", return_value={"allow_cloud": True}), \
             patch.object(mind.local_models, "request", return_value=answer) as request:
            got = mind.ollama_chat("gpt-5.6-luna", "prompt")
        self.assertEqual(got["sr"], content["sr"])
        self.assertIn("sr", request.call_args.args[2]["format"]["required"])
        self.assertEqual(request.call_args.kwargs["timeout"], 75)
        self.assertTrue(request.call_args.kwargs["allow_cloud"])

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
        with patch.dict(os.environ, {"BEOPS_MODEL_BACKEND": "ollama"}), \
             patch.object(lm, "model_slot") as slot, \
             patch.object(lm, "_request_locked", return_value={}):
            lm.request("http://127.0.0.1:11434", "/api/tags", verify_model=False)
        self.assertEqual(slot.call_args.args[0], 0.0)


if __name__ == "__main__":
    unittest.main()
