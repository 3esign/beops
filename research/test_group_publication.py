"""Small group delta transaction, rollback and preserved observation contract."""
import pathlib
import subprocess
import unittest

class GroupPublicationTests(unittest.TestCase):
    def test_node_contract(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        run = subprocess.run(['node', '--test', 'research/test_group_publication_node.js'], cwd=root,
                             capture_output=True, text=True, encoding='utf-8', timeout=120)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
