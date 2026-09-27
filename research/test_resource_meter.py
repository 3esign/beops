"""Resource accounting must keep incomplete work and missing measurements visible."""
import json
import ast
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import resource_meter as resources
import transport


class ResourceAccounting(unittest.TestCase):
    def setUp(self):
        (ROOT / "runtime").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="resource-test-", dir=ROOT / "runtime")
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)

    def receipts(self, phase):
        return [json.loads(p.read_text(encoding="utf-8")) for p in
                (self.root / "runtime/resources/receipts").glob("*-" + phase + ".json")]

    def test_finished_cycle_and_unreported_transport(self):
        with resources.Meter(self.root, "collection"):
            resources.observe_http(123)
            resources.observe_http(None)
        finish = self.receipts("finish")[0]
        self.assertEqual(finish["http"], {"request_attempts": 2, "response_body_bytes": 123,
                                         "body_reports": 1, "unreported_bodies": 1})
        self.assertGreaterEqual(finish["cpu_seconds"], 0)
        self.assertGreaterEqual(finish["wall_seconds"], 0)
        self.assertIsNone(finish["electricity_wh"])
        self.assertIsNone(finish["money"])

    def test_exception_preserves_start_and_failure_without_exception_text(self):
        with self.assertRaises(ValueError):
            with resources.Meter(self.root, "news"):
                raise ValueError("do not retain sensitive exception text")
        finish = self.receipts("finish")[0]
        self.assertEqual(len(self.receipts("start")), 1)
        self.assertEqual(finish["outcome"], "failed")
        self.assertEqual(finish["tokens"]["state"], "not_instrumented")
        self.assertNotIn("sensitive", json.dumps(finish))

    def test_return_code_not_misreported(self):
        self.assertEqual(resources.run_main(self.root, "collection", lambda: 1), 1)
        self.assertEqual(self.receipts("finish")[0]["outcome"], "failed")

    def test_real_transport_path_records_response_and_timeout(self):
        completed = subprocess.CompletedProcess([], 0, stdout=json.dumps({"status": 200,
            "headers": {}, "body": "YWJj", "body_bytes": 3}))
        with resources.Meter(self.root, "collection"):
            with mock.patch.object(transport.subprocess, "run", return_value=completed):
                self.assertEqual(transport.fetch("https://example.invalid")["body"], b"abc")
            with mock.patch.object(transport.subprocess, "run", side_effect=subprocess.TimeoutExpired("node", 2)):
                self.assertIsNone(transport.fetch("https://example.invalid")["body"])
        self.assertEqual(self.receipts("finish")[0]["http"]["request_attempts"], 2)
        self.assertEqual(self.receipts("finish")[0]["http"]["unreported_bodies"], 1)

    def test_node_meter_summary_and_historical_nonduplication(self):
        result = subprocess.run(["node", str(ROOT / "research/resource_meter.test.cjs")],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("resource meter offline contracts passed", result.stdout)

    def test_actual_scheduler_commands_enter_meter(self):
        for batch, script, activity in [("collect_tick.bat", "collect_daemon.py", "collection"),
                ("collect_tick.bat", "collect_events.py", "calendar"),
                ("organ_tick.bat", "organ_news.py", "news"), ("mind_tick.bat", "organ_mind.py", "mind"),
                ("watch_tick.bat", "watchman.py", "watch"), ("guard_tick.bat", "guard.py", "guard"),
                ("legal_tick.bat", "legal_capture.py", "legal")]:
            with self.subTest(script=script):
                command = (ROOT / "tools" / batch).read_text(encoding="utf-8")
                match = re.search(re.escape("tools\\" + script) + r"\s*(.*?)\s*>>", command)
                self.assertIsNotNone(match)
                file = ROOT / "tools" / script
                tree = ast.parse(file.read_text(encoding="utf-8-sig"))
                self.assertIsInstance(tree.body[-1], ast.If)
                entry = ast.Module(body=[tree.body[-1]], type_ignores=[])
                module = ast.Module(body=tree.body[:-1], type_ignores=tree.type_ignores)
                # Load the real top-level imports and definitions. Supplying sys/ROOT
                # here used to conceal watchman's missing sys import (G-3100).
                namespace = {"__name__": "_resource_cli_probe", "__file__": str(file)}
                scheduled_main = mock.Mock(return_value=0)
                real_run_main = resources.run_main
                def isolated_meter(root, name, fn):
                    self.assertEqual(pathlib.Path(root).resolve(), ROOT)
                    return real_run_main(self.root, name, fn)
                with mock.patch.object(sys, "path", list(sys.path)), \
                        mock.patch.object(sys, "argv", [script, *match[1].split()]), \
                        mock.patch.object(resources, "run_main", side_effect=isolated_meter) as run:
                    exec(compile(module, str(file), "exec"), namespace)
                    namespace.update(__name__="__main__", main=scheduled_main)
                    with self.assertRaises(SystemExit) as stopped:
                        exec(compile(entry, str(file), "exec"), namespace)
                    self.assertEqual(stopped.exception.code, 0)
                    self.assertEqual(run.call_args.args[1], activity)
                    scheduled_main.assert_called_once_with()
                    self.assertEqual(self.receipts("finish")[-1]["outcome"], "completed")
        self.assertEqual({r["activity"] for r in self.receipts("finish")},
                         {"collection", "calendar", "news", "mind", "watch", "guard", "legal"})

    def test_watchman_export_cli_loads_real_module_and_exits_help_without_work(self):
        # --help really exits inside argparse before reading inputs or writing a
        # monitoring receipt, while still traversing the export-argument branch.
        result = subprocess.run([sys.executable, "-X", "utf8", "-B",
                                 str(ROOT / "tools/watchman.py"), "--export", "--help"],
                                cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--export", result.stdout)

    def test_persistence_failure_does_not_stop_collection(self):
        with mock.patch.object(resources, "_immutable", side_effect=OSError("disk failure")), \
                mock.patch.object(sys, "stderr"):
            self.assertEqual(resources.run_main(self.root, "collection", lambda: 7), 7)


if __name__ == "__main__":
    unittest.main()
