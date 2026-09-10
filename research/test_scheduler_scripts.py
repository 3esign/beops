#!/usr/bin/env python3
"""Scheduler scripts are infrastructure: a bad replacement can stop the observatory."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTER = ROOT / "tools" / "register_tasks.ps1"


class RegisterTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = REGISTER.read_text(encoding="utf-8")

    def test_the_registry_resolves_the_project_from_its_own_location(self):
        self.assertIn("$PSScriptRoot", self.s)
        self.assertNotIn("D:\\Svemir\\!Projekti\\Beops", self.s)

    def test_the_registry_knows_all_eight_clocks(self):
        for name in ("Beops_Collect", "Beops_Mind", "Beops_Organ", "Beops_Publish",
                     "Beops_Watch", "Beops_Legal", "Beops_Guard", "Beops_Baseline"):
            self.assertIn(name, self.s)

    def test_replacing_a_task_does_not_delete_it_first(self):
        self.assertIn("-Force", self.s)
        self.assertNotIn("Unregister-ScheduledTask", self.s)


if __name__ == "__main__":
    unittest.main()
