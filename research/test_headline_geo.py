"""Offline place inference contract and evidence provenance."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class HeadlineGeography(unittest.TestCase):
    def test_node_contract(self):
        result = subprocess.run(['node', '--test', 'research/test_headline_geo_node.js'], cwd=ROOT,
                                capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
