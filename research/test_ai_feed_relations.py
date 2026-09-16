"""C-074: the AI panel connects facts only through named relations (offline contract)."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Relations(unittest.TestCase):
    def test_relation_contracts(self):
        r = subprocess.run(['node', str(ROOT / 'research/test_ai_feed_relations_node.js')], capture_output=True,
                           text=True, encoding='utf-8', timeout=25,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(r.returncode, 0, r.stdout + '\n' + r.stderr)
        self.assertIn('relation contracts passed', r.stdout)


if __name__ == '__main__':
    unittest.main()
