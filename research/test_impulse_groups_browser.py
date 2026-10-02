"""Browser group loading: integrity, independent clocks, and visible failures."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class ImpulseGroupsBrowser(unittest.TestCase):
    def test_group_browser_contract(self):
        run = subprocess.run(['node', '--test', 'research/test_impulse_groups_browser_node.js'],
                             cwd=ROOT, capture_output=True, text=True,
                             encoding='utf-8', timeout=45)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
