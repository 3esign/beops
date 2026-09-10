#!/usr/bin/env python3
"""test_migrate_structure.py - a migration that has already run, kept honest.

`migrate_structure.py` moved the research documents into numbered folders and rewrote every local
markdown link to match. It ran once, in early September, and it is the kind of script that is
dangerous precisely because it is finished: it is still in the repository, it still moves files, and
nothing recorded that it has nothing left to do.

This does not re-run it. It checks the two things worth checking about a spent migration: that its
path arithmetic is still correct, and that **running it again would move nothing**, which is the only
safe state for a script like this to sit in.
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import migrate_structure as M  # noqa: E402


class PathArithmetic(unittest.TestCase):
    def test_a_path_nobody_moved_is_returned_unchanged(self):
        for p in ("tools/guard.py", "research/SOURCE_REGISTRY.json", "README.md"):
            self.assertEqual(M.map_target(p), p)

    def test_a_moved_file_maps_to_where_it_went(self):
        if not M.MOVES:
            self.skipTest("this migration declares no file moves")
        for old, new in list(M.MOVES.items())[:8]:
            self.assertEqual(M.map_target(old), new)

    def test_a_directory_move_carries_everything_under_it(self):
        for od, nd in M.DIR_MOVES.items():
            self.assertEqual(M.map_target(od), nd)
            self.assertEqual(M.map_target(od + "/deep/file.md"), nd + "/deep/file.md")

    def test_a_directory_move_does_not_catch_a_name_that_merely_starts_the_same(self):
        """The classic prefix bug: moving `docs` must not move `docs-archive`."""
        for od in M.DIR_MOVES:
            near = od + "-archive/x.md"
            self.assertEqual(M.map_target(near), near,
                             f"{near} was dragged along by the move of {od}")

    def test_normalising_a_path_is_stable_and_uses_forward_slashes(self):
        self.assertEqual(M.norm("a/b/../c"), "a/c")
        self.assertEqual(M.norm("./a/b"), "a/b")
        self.assertNotIn("\\\\", M.norm("a/b"))
        self.assertEqual(M.norm(M.norm("a/b/../c")), M.norm("a/b/../c"))


class AlreadyRun(unittest.TestCase):
    def test_running_it_again_would_move_nothing(self):
        """The safe resting state for a spent migration. If this ever fails, either the migration was
        undone or a file came back under an old name - and either way somebody has to look before the
        script is run, not after."""
        old = M.ROOT
        M.ROOT = str(ROOT)
        try:
            would_move = M.do_moves(dry=True)
        finally:
            M.ROOT = old
        self.assertEqual(would_move, [],
                         "the migration still has work to do: " + "; ".join(f"{a} -> {b}" for a, b in would_move[:5]))

    def test_a_dry_run_is_actually_dry(self):
        """It takes a flag rather than being a separate path, so this asserts the flag is honoured -
        the file listing before and after must be identical."""
        before = sorted(p.name for p in (ROOT / "research").iterdir())
        old = M.ROOT
        M.ROOT = str(ROOT)
        try:
            M.do_moves(dry=True)
        finally:
            M.ROOT = old
        self.assertEqual(sorted(p.name for p in (ROOT / "research").iterdir()), before,
                         "a dry run changed the research directory")


if __name__ == "__main__":
    unittest.main()
