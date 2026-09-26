#!/usr/bin/env python3
"""Scheduler scripts are infrastructure: a bad replacement can stop the observatory."""
import pathlib
import json
import os
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTER = ROOT / "tools" / "register_tasks.ps1"
AUDIT = ROOT / "tools" / "audit_tasks.ps1"
SPECS = ROOT / "tools" / "beops_tasks.ps1"
PUBLISH_TICK = ROOT / "tools" / "publish_tick.bat"
PUBLISH_DUE = ROOT / "tools" / "publish_due.ps1"
PUBLISH_CAPACITY = ROOT / "tools" / "publish_capacity.ps1"
PUBLISHER = ROOT / "tools" / "publish_github.ps1"
BASELINE_TICK = ROOT / "tools" / "baseline_tick.bat"
BASELINE_RUN = ROOT / "tools" / "baseline_run.ps1"
RUN_BOUNDED = ROOT / "tools" / "run_bounded.ps1"


class RegisterTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = REGISTER.read_text(encoding="utf-8")
        cls.audit = AUDIT.read_text(encoding="utf-8")
        cls.specs = SPECS.read_text(encoding="utf-8")
        cls.publish_tick = PUBLISH_TICK.read_text(encoding="utf-8")
        cls.publisher = PUBLISHER.read_text(encoding="utf-8")
        cls.baseline_tick = BASELINE_TICK.read_text(encoding="utf-8")
        cls.baseline_run = BASELINE_RUN.read_text(encoding="utf-8")

    def test_the_registry_resolves_the_project_from_its_own_location(self):
        self.assertIn("$PSScriptRoot", self.s)
        for s in (self.s, self.audit, self.specs):
            self.assertNotIn("D:\\Svemir\\!Projekti\\Beops", s)

    def test_the_registry_knows_all_nine_clocks(self):
        spec_names = []
        for name in ("Beops_AIFeed", "Beops_Collect", "Beops_Mind", "Beops_Organ",
                     "Beops_Publish", "Beops_Watch", "Beops_Legal", "Beops_Guard",
                     "Beops_Baseline"):
            self.assertIn(name, self.specs)
            spec_names.append(name)
        self.assertEqual(len(spec_names), 9)

    def test_heavy_clocks_start_apart_and_publish_at_most_twice_an_hour(self):
        import re
        rows = re.findall(
            r"Name='([^']+)'.*?Minutes=(\d+);\s+OffsetMinutes=(\d+);\s+Limit=(\d+);",
            self.specs,
        )
        self.assertEqual(len(rows), 9)
        specs = {name: (int(minutes), int(offset), int(limit))
                 for name, minutes, offset, limit in rows}
        self.assertEqual(specs["Beops_AIFeed"][0], 5)
        self.assertEqual(specs["Beops_Publish"][0], 30)
        self.assertEqual(specs["Beops_Publish"][2], 45)
        self.assertEqual(len({offset for _, offset, _ in specs.values()}), len(specs))
        self.assertIn("AddMinutes($t.OffsetMinutes)", self.s)
        self.assertNotIn("AddMinutes(1)", self.s)

    def test_publish_entry_loads_cadence_configuration_before_release_setup(self):
        gate = 'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_due.ps1"'
        self.assertIn(gate, self.publish_tick)
        self.assertGreater(self.publish_tick.index(gate), self.publish_tick.index("beops_env.bat"))
        self.assertLess(self.publish_tick.index(gate), self.publish_tick.index('-File tools\\publish_github.ps1'))

    def test_publish_entry_checks_capacity_before_expensive_setup(self):
        cadence = 'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_due.ps1"'
        capacity = 'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_capacity.ps1"'
        self.assertIn(capacity, self.publish_tick)
        self.assertGreater(self.publish_tick.index(capacity), self.publish_tick.index(cadence))
        self.assertGreater(self.publish_tick.index(capacity), self.publish_tick.index("beops_env.bat"))
        self.assertLess(self.publish_tick.index(capacity), self.publish_tick.index('-File tools\\publish_github.ps1'))
        direct = "Join-Path $PSScriptRoot 'publish_capacity.ps1'"
        self.assertIn(direct, self.publisher)
        self.assertLess(self.publisher.index(direct),
                        self.publisher.index("$preparationLock = Enter-BeopsPublishLock"))

    def test_watch_persistence_budget_leaves_scheduler_grace_before_next_cadence(self):
        import re
        watch = (ROOT / 'tools/watchman.py').read_text(encoding='utf-8')
        spec = re.search(r"Name='Beops_Watch'.*?Minutes=(\d+);.*?Limit=(\d+);", self.specs)
        cadence, limit = map(int, spec.groups())
        persistence = int(re.search(r'^PERSIST_BUDGET_SECONDS = (\d+)', watch, re.M).group(1))
        lock_wait = int(re.search(r'^LOCK_WAIT_SECONDS = (\d+)', watch, re.M).group(1))
        self.assertLess(lock_wait, persistence)
        self.assertGreaterEqual(limit * 60 - persistence, 60)
        self.assertLess(limit, cadence)

    def test_low_memory_publish_is_quiet_before_release_setup(self):
        with tempfile.TemporaryDirectory() as td:
            status = pathlib.Path(td) / "capacity.json"
            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(PUBLISH_CAPACITY), "-StatusPath", str(status),
                 "-ObservedFreeMB", "256", "-ObservedTotalMB", "8192",
                 "-MinimumFreeMB", "1024", "-NowUtc", "2026-09-20T07:55:00Z"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 75, run.stdout + run.stderr)
            quiet = json.loads(status.read_text(encoding="utf-8-sig"))
            self.assertEqual(quiet["schema"], "beops-publish-capacity-status/v1")
            self.assertEqual(quiet["decision"], "quiet")
            self.assertEqual(quiet["reason"], "low_memory")
            self.assertEqual(quiet["free_mb"], 256)

            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(PUBLISH_CAPACITY), "-StatusPath", str(status),
                 "-ObservedFreeMB", "2048", "-ObservedTotalMB", "8192",
                 "-MinimumFreeMB", "1024", "-NowUtc", "2026-09-20T07:56:00Z"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            ready = json.loads(status.read_text(encoding="utf-8-sig"))
            self.assertEqual(ready["decision"], "ready")
            self.assertEqual(ready["reason"], "capacity_ok")

    def test_baseline_uses_one_atomic_publish_preparation_lock_for_both_children(self):
        for lock in ("publish-preparation.lock", "publish.lock"):
            self.assertIn(lock, self.baseline_tick)
            self.assertLess(self.baseline_tick.index(lock), self.baseline_tick.index("beops_env.bat"))
        self.assertIn("baseline_run.ps1", self.baseline_tick)
        self.assertNotIn("run_bounded.ps1", self.baseline_tick)
        self.assertIn(". (Join-Path $PSScriptRoot 'publish_safety.ps1')", self.baseline_run)
        acquired = self.baseline_run.index("Enter-BeopsPublishLock")
        history = self.baseline_run.index("-Name 'history qualification'")
        baseline = self.baseline_run.index("-Name 'baseline build'")
        cleanup = self.baseline_run.index("Test-BeopsPublishLockOwnedByCurrentProcess")
        self.assertLess(acquired, history)
        self.assertLess(history, baseline)
        self.assertLess(baseline, cleanup)
        self.assertIn("if (-not $preparationLock.Acquired) { exit 0 }", self.baseline_run)
        self.assertEqual(self.baseline_run.count("-TimeoutSeconds $TimeoutSeconds"), 2)
        self.assertIn("Remove-Item -LiteralPath $preparationLockFile", self.baseline_run)

    @unittest.skipUnless(os.name == "nt", "Windows atomic lock contract")
    def test_baseline_lock_is_held_across_both_steps_and_busy_is_quiet(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "runtime" / "tmp") as td:
            root = pathlib.Path(td)
            runtime = root / "runtime"
            runtime.mkdir()
            fake_python = root / "fake-python.cmd"
            calls = root / "calls.log"
            fake_python.write_text(
                "@echo off\r\n"
                "if not exist \"%~dp0runtime\\publish-preparation.lock\" exit /b 91\r\n"
                ">>\"%~dp0calls.log\" echo %*\r\n"
                "exit /b 0\r\n",
                encoding="ascii",
            )
            command = [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(BASELINE_RUN), "-ProjectRoot", str(root),
                "-PythonPath", str(fake_python), "-TimeoutSeconds", "10",
            ]
            run = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            invoked = calls.read_text(encoding="utf-8-sig").splitlines()
            self.assertEqual(len(invoked), 2)
            self.assertIn("history_qualification.py build", invoked[0])
            self.assertIn("baseline.py build", invoked[1])
            lock = runtime / "publish-preparation.lock"
            self.assertFalse(lock.exists(), "orchestrator did not release its own lock")

            calls.unlink()
            owned_by_other = f"pid {os.getpid()} at 2026-09-20T09:00:00Z"
            lock.write_text(owned_by_other, encoding="utf-8")
            blocked = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
            self.assertEqual(blocked.returncode, 0, blocked.stdout + blocked.stderr)
            self.assertEqual(blocked.stdout, "")
            self.assertEqual(blocked.stderr, "")
            self.assertFalse(calls.exists(), "busy baseline lock still launched a child")
            self.assertEqual(lock.read_text(encoding="utf-8-sig"), owned_by_other)

    @unittest.skipUnless(os.name == "nt", "Windows process-tree contract")
    def test_bounded_runner_kills_its_child_tree_before_outer_task_limit(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "runtime" / "tmp") as td:
            root = pathlib.Path(td)
            child_pid = root / "child.pid"
            grandchild_pid = root / "grandchild.pid"
            grandchild = root / "grandchild.py"
            grandchild.write_text(
                "import os, pathlib, sys, time\n"
                "pathlib.Path(sys.argv[1]).write_text(str(os.getpid()), encoding='ascii')\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            fixture = root / "slow.py"
            fixture.write_text(
                "import os, pathlib, subprocess, sys, time\n"
                f"pathlib.Path({str(child_pid)!r}).write_text(str(os.getpid()), encoding='ascii')\n"
                f"subprocess.Popen([sys.executable, {str(grandchild)!r}, {str(grandchild_pid)!r}])\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            log = root / "bounded.log"
            status = root / "status.json"
            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RUN_BOUNDED),
                 "-Name", "fixture", "-FilePath", os.sys.executable,
                 "-Arguments", str(fixture), "-LogPath", str(log),
                 "-StatusPath", str(status), "-TimeoutSeconds", "3", "-AllowedRoot", str(root)],
                capture_output=True, text=True, timeout=20, check=False,
            )
            self.assertEqual(run.returncode, 124, run.stdout + run.stderr)
            receipt = json.loads(status.read_text(encoding="utf-8-sig"))
            self.assertTrue(receipt["timed_out"])
            self.assertEqual(receipt["containment"], "tree_terminated")
            self.assertEqual(receipt["exit_code"], 124)
            self.assertTrue(child_pid.is_file(), run.stdout + run.stderr)
            self.assertTrue(grandchild_pid.is_file(), run.stdout + run.stderr)
            import ctypes
            def alive(pid):
                handle = ctypes.windll.kernel32.OpenProcess(0x100000, False, pid)
                if not handle:
                    return False
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            for pid_file in (child_pid, grandchild_pid):
                pid = int(pid_file.read_text(encoding="utf-8-sig").strip())
                self.assertFalse(alive(pid), f"bounded descendant PID {pid} survived")

    @unittest.skipUnless(os.name == "nt", "Windows bounded runner contract")
    def test_bounded_runner_preserves_output_and_child_exit_code(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "runtime" / "tmp") as td:
            root = pathlib.Path(td)
            fixture = root / "quick.cmd"
            fixture.write_text(
                "@echo off\r\necho bounded-out\r\necho cwd=%CD%\r\necho bounded-err 1>&2\r\nexit /b 7\r\n",
                encoding="ascii",
            )
            log = root / "bounded.log"
            status = root / "status.json"
            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RUN_BOUNDED),
                 "-Name", "fixture", "-FilePath", str(fixture), "-LogPath", str(log),
                 "-StatusPath", str(status), "-TimeoutSeconds", "5", "-AllowedRoot", str(root)],
                capture_output=True, text=True, timeout=20, check=False,
            )
            self.assertEqual(run.returncode, 7, run.stdout + run.stderr)
            receipt = json.loads(status.read_text(encoding="utf-8-sig"))
            self.assertFalse(receipt["timed_out"])
            self.assertEqual(receipt["containment"], "process_exited")
            self.assertEqual(receipt["exit_code"], 7)
            logged = log.read_text(encoding="utf-8-sig")
            self.assertIn("bounded-out", logged)
            self.assertIn(f"cwd={root}", logged)
            self.assertIn("bounded-err", logged)
            self.assertEqual(list((root / "runtime" / "tmp").glob("bounded-*")), [])

    def test_publish_settings_use_normal_cpu_io_and_memory_priority(self):
        # Construct real Windows settings objects without registering any task.
        script = """$ErrorActionPreference = 'Stop'
. '%s'
@(Get-BeopsTaskSpecs | ForEach-Object {
  $settings = New-ScheduledTaskSettingsSet -Priority (Get-BeopsTaskPriority $_)
  [pscustomobject]@{ name=$_.Name; priority=$settings.Priority }
}) | ConvertTo-Json -Compress
""" % str(SPECS).replace("'", "''")
        run = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        priorities = {row["name"]: row["priority"] for row in json.loads(run.stdout)}
        self.assertEqual(priorities.pop("Beops_Publish"), 4)
        self.assertEqual(priorities.pop("Beops_Collect"), 4, "C-076: collection must not starve behind a publish")
        self.assertEqual(len(priorities), 7)
        self.assertEqual(set(priorities.values()), {7})
        self.assertIn("-Priority (Get-BeopsTaskPriority $t)", self.s)
        self.assertIn("$priority -ne $expectedPriority", self.audit)

    def test_only_a_recent_success_opens_the_publish_quiet_window(self):
        now = "2026-09-12T06:30:00Z"
        cases = (
            ({"published": True, "at": "2026-09-12T06:20:00Z"}, 75),
            ({"published": True, "cycle_started_at": "2026-09-12T05:40:00Z",
              "at": "2026-09-12T06:20:00Z"}, 75),
            ({"published": True, "at": "2026-09-12T05:59:00Z"}, 0),
            ({"published": False, "at": "2026-09-12T06:29:00Z"}, 9),
        )
        with tempfile.TemporaryDirectory() as td:
            receipt = pathlib.Path(td) / "receipt.json"
            attempt = pathlib.Path(td) / "missing-attempt.json"
            status = pathlib.Path(td) / "status.json"
            for payload, expected in cases:
                receipt.write_text(json.dumps(payload), encoding="utf-8")
                run = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                     "-File", str(PUBLISH_DUE), "-ReceiptPath", str(receipt),
                     "-AttemptReceiptPath", str(attempt), "-StatusPath", str(status), "-NowUtc", now],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(run.returncode, expected, run.stdout + run.stderr)

    def test_recent_failed_publish_attempt_opens_a_failure_cooldown(self):
        now = "2026-09-12T06:30:00Z"
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            success = root / "last-success.json"
            attempt = root / "last-attempt.json"
            status = root / "status.json"
            success.write_text(json.dumps({
                "published": True,
                "at": "2026-09-12T01:00:00Z",
            }), encoding="utf-8")
            attempt.write_text(json.dumps({
                "published": False,
                "at": "2026-09-12T06:20:00Z",
                "why": "research gate timed out",
            }), encoding="utf-8")
            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(PUBLISH_DUE), "-ReceiptPath", str(success),
                 "-AttemptReceiptPath", str(attempt), "-StatusPath", str(status),
                 "-NowUtc", now, "-FailureCooldownMinutes", "120"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 75, run.stdout + run.stderr)
            quiet = json.loads(status.read_text(encoding="utf-8-sig"))
            self.assertEqual(quiet["decision"], "quiet")
            self.assertEqual(quiet["reason"], "recent_failed_attempt")
            self.assertEqual(quiet["attempt_receipt_path"], str(attempt))

    def test_unreadable_cadence_receipts_fail_closed(self):
        now = "2026-09-12T06:30:00Z"
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            success = root / "last-success.json"
            attempt = root / "last-attempt.json"
            status = root / "status.json"
            success.write_text("{broken", encoding="utf-8")
            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(PUBLISH_DUE), "-ReceiptPath", str(success),
                 "-AttemptReceiptPath", str(attempt), "-StatusPath", str(status), "-NowUtc", now],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 9, run.stdout + run.stderr)
            self.assertEqual(json.loads(status.read_text(encoding="utf-8-sig"))["decision"], "error")

            success.unlink()
            attempt.write_text("{broken", encoding="utf-8")
            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(PUBLISH_DUE), "-ReceiptPath", str(success),
                 "-AttemptReceiptPath", str(attempt), "-StatusPath", str(status), "-NowUtc", now],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 9, run.stdout + run.stderr)
            self.assertEqual(json.loads(status.read_text(encoding="utf-8-sig"))["reason"],
                             "attempt_receipt_unreadable")

            for payload, reason in (
                ({"published": False}, "attempt_receipt_missing_time"),
                ({"published": False, "at": "2026-09-12T06:31:00Z"}, "attempt_receipt_from_future"),
            ):
                attempt.write_text(json.dumps(payload), encoding="utf-8")
                run = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                     "-File", str(PUBLISH_DUE), "-ReceiptPath", str(success),
                     "-AttemptReceiptPath", str(attempt), "-StatusPath", str(status), "-NowUtc", now],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(run.returncode, 9, run.stdout + run.stderr)
                self.assertEqual(json.loads(status.read_text(encoding="utf-8-sig"))["reason"], reason)

            attempt.unlink()
            success.write_text(json.dumps({"published": True, "at": "2026-09-12T06:31:00Z"}),
                               encoding="utf-8")
            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(PUBLISH_DUE), "-ReceiptPath", str(success),
                 "-AttemptReceiptPath", str(attempt), "-StatusPath", str(status), "-NowUtc", now],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 9, run.stdout + run.stderr)
            self.assertEqual(json.loads(status.read_text(encoding="utf-8-sig"))["reason"],
                             "successful_receipt_from_future")

    def test_publish_cadence_writes_machine_status_for_skip_and_due(self):
        now = "2026-09-12T06:30:00Z"
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            receipt = root / "receipt.json"
            attempt = root / "missing-attempt.json"
            status = root / "status.json"
            receipt.write_text(json.dumps({
                "published": True,
                "at": "2026-09-12T06:20:00Z",
                "cycle_started_at": "2026-09-12T06:20:00Z",
                "generated_as_of": "2026-09-12T06:19:00Z",
                "source_head": "a" * 40,
                "remote_head": "b" * 40,
            }), encoding="utf-8")
            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(PUBLISH_DUE), "-ReceiptPath", str(receipt),
                 "-AttemptReceiptPath", str(attempt), "-StatusPath", str(status), "-NowUtc", now],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 75, run.stdout + run.stderr)
            quiet = json.loads(status.read_text(encoding="utf-8-sig"))
            self.assertEqual(quiet["schema"], "beops-publish-scheduler-status/v1")
            self.assertEqual(quiet["decision"], "quiet")
            self.assertEqual(quiet["reason"], "recent_success")
            self.assertEqual(quiet["last_success_source_head"], "a" * 40)

            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(PUBLISH_DUE), "-ReceiptPath", str(receipt),
                 "-AttemptReceiptPath", str(attempt), "-StatusPath", str(status),
                 "-NowUtc", "2026-09-12T07:01:00Z"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            due = json.loads(status.read_text(encoding="utf-8-sig"))
            self.assertEqual(due["decision"], "due")
            self.assertEqual(due["reason"], "minimum_elapsed")

    def test_replacing_a_task_does_not_delete_it_first(self):
        self.assertIn("-Force", self.s)
        self.assertNotIn("Unregister-ScheduledTask", self.s)

    def test_registry_and_audit_share_the_same_task_spec(self):
        self.assertIn("beops_tasks.ps1", self.s)
        self.assertIn("beops_tasks.ps1", self.audit)
        self.assertIn("Get-BeopsTaskSpecs", self.s)
        self.assertIn("Get-BeopsTaskSpecs", self.audit)

    def test_audit_is_read_only_and_reports_alias_separately(self):
        self.assertIn("root alias", self.audit)
        self.assertIn("action drift", self.audit)
        self.assertIn("beops-task-audit/v1", self.audit)
        self.assertIn("ConvertTo-Json", self.audit)
        self.assertNotIn("Register-ScheduledTask", self.audit)
        self.assertNotIn("Set-ScheduledTask", self.audit)

    def test_every_wrapper_preserves_maintenance_and_starts_no_job(self):
        import shutil
        names = ('ai_feed', 'collect', 'mind', 'organ', 'watch', 'publish', 'guard', 'baseline', 'legal')
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td) / 'paused project'
            (root / 'tools').mkdir(parents=True)
            (root / 'runtime').mkdir()
            (root / 'runtime/MAINTENANCE').write_text('controlled pause', encoding='utf-8')
            for name in ('beops_env.bat', 'publish_due.ps1'):
                shutil.copy2(ROOT / 'tools' / name, root / 'tools' / name)
            for name in names:
                with self.subTest(task=name):
                    target = root / 'tools' / (name + '_tick.bat')
                    shutil.copy2(ROOT / 'tools' / target.name, target)
                    run = subprocess.run(['cmd.exe', '/d', '/c', str(target)],
                        capture_output=True, text=True, timeout=15)
                    self.assertEqual(run.returncode, 75, run.stdout + run.stderr)
            self.assertEqual([p.name for p in (root / 'runtime').iterdir()], ['MAINTENANCE'])
            self.assertFalse((root / 'data').exists())


if __name__ == "__main__":
    unittest.main()
