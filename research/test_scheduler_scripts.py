#!/usr/bin/env python3
"""Scheduler scripts are infrastructure: a bad replacement can stop the observatory."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTER = ROOT / "tools" / "register_tasks.ps1"
AUDIT = ROOT / "tools" / "audit_tasks.ps1"
SPECS = ROOT / "tools" / "beops_tasks.ps1"


class RegisterTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = REGISTER.read_text(encoding="utf-8")
        cls.audit = AUDIT.read_text(encoding="utf-8")
        cls.specs = SPECS.read_text(encoding="utf-8")

    def test_the_registry_resolves_the_project_from_its_own_location(self):
        self.assertIn("$PSScriptRoot", self.s)
        for s in (self.s, self.audit, self.specs):
            self.assertNotIn("D:\\Svemir\\!Projekti\\Beops", s)

    def test_the_registry_knows_all_eight_clocks(self):
        spec_names = []
        for name in ("Beops_Collect", "Beops_Mind", "Beops_Organ", "Beops_Publish",
                     "Beops_Watch", "Beops_Legal", "Beops_Guard", "Beops_Baseline"):
            self.assertIn(name, self.specs)
            spec_names.append(name)
        self.assertEqual(len(spec_names), 8)

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
        self.assertNotIn("Register-ScheduledTask", self.audit)
        self.assertNotIn("Set-ScheduledTask", self.audit)


if __name__ == "__main__":
    unittest.main()
