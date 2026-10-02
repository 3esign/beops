"""Independent calendar/context publication, policy and atomicity regression gate."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class ImpulseGroups(unittest.TestCase):
    def test_independent_groups(self):
        run = subprocess.run(['node', '--test', 'research/test_impulse_groups_node.js'],
                             cwd=ROOT, capture_output=True, text=True,
                             encoding='utf-8', timeout=90)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
