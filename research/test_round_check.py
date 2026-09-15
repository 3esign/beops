"""The round check is the thing that says a repair is done, so it is tested for the ways it could lie."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import round_check as rc  # noqa: E402


def task(i, status, commit="abc", ev=("x",), closed="2026-09-14T10:00:00Z", deps=()):
    return {"id": i, "status": status, "source_commit": commit, "local_evidence": list(ev),
            "closed_at": closed, "depends_on": list(deps)}


class Register(unittest.TestCase):
    def check(self, *tasks, commits=("abc",), files=("x",)):
        return rc.register_findings({"tasks": list(tasks)}, lambda c: c in commits, lambda p: p in files)

    def test_a_closed_task_without_commit_evidence_or_time_is_named(self):
        p = self.check(task("R06", "closed", commit=None, ev=(), closed=None))
        self.assertEqual(p[0]["id"], "R06")
        self.assertEqual(set(p[0]["why"]), {"no source commit", "no evidence", "no closing time"})

    def test_a_commit_that_does_not_exist_is_not_proof(self):
        self.assertIn("source commit not in the repository", self.check(task("R07", "closed", commit="zzz"))[0]["why"])

    def test_closed_on_top_of_open_work_is_not_closed(self):
        p = self.check(task("R02", "in_progress"), task("R11", "closed", deps=("R02",)))
        self.assertEqual(p[0]["why"], ["depends on open R02"])

    def test_open_tasks_and_proven_ones_pass(self):
        self.assertEqual(self.check(task("R00", "verified"), task("R12", "planned", commit=None)), [])


class Decision(unittest.TestCase):
    def test_d003_must_name_every_model_inside_its_own_section(self):
        full = "## D-003 — x\n" + " ".join(rc.D003_NAMES) + "\n## D-004 — y\n"
        self.assertEqual(rc.d003_ok(full), [])
        self.assertEqual(rc.d003_ok("## D-003 — x\nGemini\n## D-004 — Codex Claude"), [n for n in rc.D003_NAMES if n != "Gemini"])
        self.assertEqual(rc.d003_ok("## D-001"), ["D-003 missing"])


class Honesty(unittest.TestCase):
    def test_an_unreadable_artefact_is_unknown_never_pass(self):
        @rc.guarded
        def broken():
            raise FileNotFoundError("gone")
        self.assertEqual(broken()[0]["state"], rc.UNKNOWN)

    def test_the_counter_examples_are_real_and_complete(self):
        self.assertTrue(any("85 to 63" in s for s in rc.MUST_REFUSE))
        self.assertTrue(rc.MUST_ACCEPT)


if __name__ == "__main__":
    unittest.main()
