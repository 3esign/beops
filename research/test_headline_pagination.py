"""Exercise the actual archive browser script against a bounded offline DOM."""
import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class HeadlinePagination(unittest.TestCase):
    def test_archive_search_paging_and_reader_position_survive_refresh(self):
        run = subprocess.run(
            ['node', str(ROOT / 'research/headline_pagination_contract.test.cjs')],
            capture_output=True, text=True, encoding='utf-8', timeout=20,
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
