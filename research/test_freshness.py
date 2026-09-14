import pathlib
import subprocess
import unittest

class FreshnessContract(unittest.TestCase):
    def test_browser_clock_and_embedded_scripts(self):
        script = pathlib.Path(__file__).with_name('freshness_contract.test.cjs')
        run = subprocess.run(['node', str(script)], capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
