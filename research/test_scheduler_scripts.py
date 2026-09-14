#!/usr/bin/env python3
"""Scheduler scripts are infrastructure: a bad replacement can stop the observatory."""
import pathlib
import json
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTER = ROOT / "tools" / "register_tasks.ps1"
AUDIT = ROOT / "tools" / "audit_tasks.ps1"
SPECS = ROOT / "tools" / "beops_tasks.ps1"
PUBLISH_TICK = ROOT / "tools" / "publish_tick.bat"
PUBLISH_DUE = ROOT / "tools" / "publish_due.ps1"


class RegisterTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = REGISTER.read_text(encoding="utf-8")
        cls.audit = AUDIT.read_text(encoding="utf-8")
        cls.specs = SPECS.read_text(encoding="utf-8")
        cls.publish_tick = PUBLISH_TICK.read_text(encoding="utf-8")

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
        self.assertEqual(specs["Beops_Publish"][2], 30)
        self.assertEqual(len({offset for _, offset, _ in specs.values()}), len(specs))
        self.assertIn("AddMinutes($t.OffsetMinutes)", self.s)
        self.assertNotIn("AddMinutes(1)", self.s)

    def test_publish_entry_enforces_the_cadence_before_expensive_setup(self):
        gate = 'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_due.ps1"'
        self.assertIn(gate, self.publish_tick)
        self.assertLess(self.publish_tick.index(gate), self.publish_tick.index("beops_env.bat"))

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
        self.assertEqual(len(priorities), 8)
        self.assertEqual(set(priorities.values()), {7})
        self.assertIn("-Priority (Get-BeopsTaskPriority $t)", self.s)
        self.assertIn("$priority -ne $expectedPriority", self.audit)

    def test_only_a_recent_success_opens_the_publish_quiet_window(self):
        now = "2026-09-12T06:30:00Z"
        cases = (
            ({"published": True, "at": "2026-09-12T06:20:00Z"}, 75),
            ({"published": True, "at": "2026-09-12T05:59:00Z"}, 0),
            ({"published": False, "at": "2026-09-12T06:29:00Z"}, 0),
        )
        with tempfile.TemporaryDirectory() as td:
            receipt = pathlib.Path(td) / "receipt.json"
            for payload, expected in cases:
                receipt.write_text(json.dumps(payload), encoding="utf-8")
                run = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                     "-File", str(PUBLISH_DUE), "-ReceiptPath", str(receipt),
                     "-NowUtc", now],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(run.returncode, expected, run.stdout + run.stderr)

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
