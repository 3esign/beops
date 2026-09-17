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


class BuiltPage(unittest.TestCase):
    """C-084: the working copy's docs/ is never rebuilt by the publisher; the published mirror is."""

    def run_step(self, local, mirror):
        import tempfile, os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            pages = []
            for name, body in (("local", local), ("mirror", mirror)):
                f = d / name / "docs" / "index.html"
                f.parent.mkdir(parents=True)
                if body is not None:
                    f.write_text(body, encoding="utf-8")
                pages.append((name, f))
            with patch.object(rc, "built_pages", lambda: pages):
                return {r["check"][:3]: r for r in rc.step2()}["2.3"]

    FOOT = "<footer>Where this runs ... Google Gemini ...</footer>"
    OLD = "<footer>Where this runs ... local models only</footer>"

    def test_a_stale_working_copy_with_a_current_mirror_passes_and_says_which(self):
        r = self.run_step(self.OLD, self.FOOT)
        self.assertEqual(r["state"], rc.PASS)
        self.assertIn("mirror", r["said"])

    def test_neither_page_carrying_it_is_not_a_pass(self):
        self.assertNotEqual(self.run_step(self.OLD, self.OLD)["state"], rc.PASS)

    def test_a_missing_mirror_is_not_a_pass(self):
        self.assertNotEqual(self.run_step(self.OLD, None)["state"], rc.PASS)

    def test_the_mirror_is_the_publisher_default_or_its_override(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BEOPS_PUBLIC_ROOT", None)
            self.assertEqual(rc.public_mirror(), rc.ROOT.parent / "Beops-public")
        with patch.dict(os.environ, {"BEOPS_PUBLIC_ROOT": "X:/pub"}):
            self.assertEqual(rc.public_mirror(), pathlib.Path("X:/pub"))


class IdentityClock(unittest.TestCase):
    def test_the_identity_check_counts_from_the_first_commit_carrying_the_name(self):
        from unittest.mock import patch
        calls = []

        def fake_git(*args):
            calls.append(args)
            return "2026-09-15T10:00:00+02:00\n2026-09-17T09:30:00+02:00"
        with patch.object(rc, "git", fake_git):
            self.assertEqual(rc.identity_since().isoformat(), "2026-09-15T10:00:00+02:00")
        self.assertIn("--reverse", calls[0])
        self.assertIn(rc.TOKEN, calls[0])

    def test_step0_does_not_use_the_newest_transport_commit(self):
        src = (rc.ROOT / "tools" / "round_check.py").read_text(encoding="utf-8")
        self.assertNotIn('since = commit_time("tools/net_fetch.js")', src)


if __name__ == "__main__":
    unittest.main()
