"""A broken test runtime must leave a failure receipt without preparing or publishing."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'Windows publisher entry point')
class PublishPreflight(unittest.TestCase):
    def test_broken_test_runtime_refuses_release_and_preserves_unrelated_files(self):
        self.run_refusal(broken_runtime=True)

    def test_unindexed_document_refuses_before_capture_and_preserves_other_files(self):
        self.run_refusal(broken_runtime=False)

    def run_refusal(self, broken_runtime):
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder)
            source = base/'source'
            (source/'tools').mkdir(parents=True)
            for name in ('publish_github.ps1', 'publish_safety.ps1', 'test-research.js', 'incognito_user_agent.js'):
                shutil.copyfile(ROOT/'tools'/name, source/'tools'/name)
            (source/'tools/prepare_release.py').write_text(
                'import pathlib\npathlib.Path("PREPARATION_RAN").write_text("unexpected")\nraise SystemExit(99)\n', encoding='utf-8')
            sentinel = base/'unrelated.txt'
            sentinel.write_text('keep', encoding='utf-8')
            broken = base/'broken-python.cmd'
            broken.write_text('@exit /b 1\n', encoding='ascii')
            (source/'research').mkdir()
            shutil.copyfile(ROOT/'research/test_research_index.py',source/'research/test_research_index.py')
            (source/'research/README.md').write_text('Fixture index\n',encoding='utf-8')
            subprocess.run(['git', 'init', '-q', str(source)], check=True, capture_output=True, timeout=10)
            subprocess.run(['git', '-C', str(source), 'add', 'tools'], check=True, capture_output=True, timeout=10)
            subprocess.run(['git', '-C', str(source), '-c', 'user.name=Semir Poturak',
                '-c', 'user.email=scumutator@gmail.com', 'commit', '-qm', 'preflight fixture'],
                check=True, capture_output=True, timeout=10)
            (source/'research/unindexed-study.md').write_text('New unindexed document\n',encoding='utf-8')
            env = dict(os.environ, BEOPS_PYTHON=sys.executable, BEOPS_TEST_PYTHON=str(broken) if broken_runtime else sys.executable,
                       BEOPS_PUBLIC_ROOT=str(base/'Beops-public'), BEOPS_RELEASE_ROOT=str(base/'releases'))
            run = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-File', str(source/'tools/publish_github.ps1')], cwd=source, env=env,
                capture_output=True, text=True, timeout=30)
            self.assertNotEqual(run.returncode, 0, run.stdout)
            receipt = json.loads((source/'data/live/publish-receipt.json').read_text(encoding='utf-8-sig'))
            for name in ('built', 'tests_ok', 'pushed', 'site_verified', 'published'):
                self.assertFalse(receipt[name], name)
            if broken_runtime:
                self.assertIn('research gate prerequisites', receipt['why'])
                self.assertIn('complete installed interpreter', receipt['why'])
            else:
                self.assertIn('research document index',receipt['why'])
                self.assertIn('unindexed-study.md',run.stdout+run.stderr)
            self.assertFalse((source/'PREPARATION_RAN').exists())
            self.assertFalse((source/'runtime/publish-preparation.lock').exists())
            self.assertFalse((base/'Beops-public').exists())
            self.assertEqual(list((base/'releases').glob('beops-release-*')), [])
            diagnostics = list((source/'runtime/release-diagnostics').glob('*.json'))
            self.assertEqual(len(diagnostics), 1)
            self.assertEqual(json.loads(diagnostics[0].read_text(encoding='utf-8-sig'))['receipt'], receipt)
            self.assertEqual(sentinel.read_text(encoding='utf-8'), 'keep')
