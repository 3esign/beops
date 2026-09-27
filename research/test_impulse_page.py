"""Public impulse projection: frozen clock, privacy, and resource accounting."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class ImpulsePage(unittest.TestCase):
    def test_public_projection(self):
        run = subprocess.run(['node', '--test', 'research/test_impulse_page_node.js'],
                             cwd=ROOT, capture_output=True, text=True,
                             encoding='utf-8', timeout=45)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
