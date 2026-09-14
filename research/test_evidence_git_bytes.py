"""G-591: Git must preserve the bytes that dated audit manifests hash."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EvidenceGitBytes(unittest.TestCase):
    def check_roundtrip(self, autocrlf):
        payload = b'first evidence line\r\nsecond evidence line\r\n'
        names = [
            'research/_trail/comprehensive-audit-20260914/sample.txt',
            'research/_trail/remediation-plan-20260914/sample.json',
            'research/_trail/remediation-20260914/recovered/sample.html',
        ]
        env = os.environ.copy()
        for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
            env.pop(key, None)
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            def git(*args):
                return subprocess.run(['git', '-C', str(base), '-c', f'core.autocrlf={autocrlf}',
                                       '-c', 'core.safecrlf=false', *args], env=env,
                                      capture_output=True, check=True, timeout=15).stdout
            git('init', '--quiet')
            (base/'.gitattributes').write_bytes((ROOT/'.gitattributes').read_bytes())
            for name in [*names, 'ordinary.txt']:
                target = base/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            git('add', '--', '.gitattributes', *names, 'ordinary.txt')
            for name in names:
                with self.subTest(path=name, autocrlf=autocrlf):
                    self.assertEqual(git('show', ':'+name), payload)
            # Positive control: the fixture really exercises text normalization.
            self.assertEqual(git('show', ':ordinary.txt'), payload.replace(b'\r\n', b'\n'))

    def test_evidence_bytes_with_windows_autocrlf(self):
        self.check_roundtrip('true')

    def test_evidence_bytes_without_autocrlf(self):
        self.check_roundtrip('false')


if __name__ == '__main__':
    unittest.main()
