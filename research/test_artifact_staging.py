"""G-593: durable artifacts keep project access after their build is published."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from artifact_staging import create_artifact_staging

REPAIR = Path(__file__).resolve().parents[1]/'tools/repair_evidence_permissions.ps1'
ACL_TIMEOUT_SECONDS = 60


def acl(path):
    env = os.environ.copy()
    env['BEOPS_ACL_TEST_PATH'] = str(path)
    result = subprocess.run(['powershell', '-NoProfile', '-Command',
        "$ErrorActionPreference='Stop'; $env:PSModulePath=Join-Path $PSHOME 'Modules'; "
        "$a=Get-Acl -LiteralPath $env:BEOPS_ACL_TEST_PATH -ErrorAction Stop; "
        "@{protected=$a.AreAccessRulesProtected; inherited=@($a.Access | Where-Object IsInherited).Count} | ConvertTo-Json -Compress"],
        env=env, capture_output=True, text=True, check=True, timeout=ACL_TIMEOUT_SECONDS)
    return json.loads(result.stdout)


class ArtifactStaging(unittest.TestCase):
    def test_unique_sibling_and_complete_bytes_survive_rename(self):
        with tempfile.TemporaryDirectory() as folder:
            parent = Path(folder)
            first = create_artifact_staging(parent, '.packet-')
            second = create_artifact_staging(parent, '.packet-')
            self.assertNotEqual(first, second)
            self.assertEqual(first.parent, parent.resolve())
            (first/'proof.json').write_bytes(b'{"known":true}\r\n')
            os.replace(first, parent/'final')
            self.assertEqual((parent/'final/proof.json').read_bytes(), b'{"known":true}\r\n')

    def test_collision_does_not_reuse_or_modify_an_existing_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            parent = Path(folder)
            old = parent/('.packet-'+UUID(int=1).hex)
            old.mkdir()
            (old/'keep').write_text('original')
            with patch('artifact_staging.uuid.uuid4', side_effect=[UUID(int=1), UUID(int=2)]):
                fresh = create_artifact_staging(parent, '.packet-')
            self.assertEqual(fresh.name, '.packet-'+UUID(int=2).hex)
            self.assertEqual((old/'keep').read_text(), 'original')

    def test_unsafe_prefix_and_missing_parent_are_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            for value in ('../escape', r'..\escape', '.', '..', ''):
                with self.subTest(prefix=value), self.assertRaises(ValueError):
                    create_artifact_staging(folder, value)
            with self.assertRaises(FileNotFoundError):
                create_artifact_staging(Path(folder)/'missing')

    @unittest.skipUnless(os.name == 'nt', 'Windows ACL regression')
    def test_published_stage_inherits_acl_while_python_private_temp_does_not(self):
        with tempfile.TemporaryDirectory() as folder:
            parent = Path(folder)
            old = Path(tempfile.mkdtemp(dir=parent))
            os.replace(old, parent/'old-published')
            old_acl = acl(parent/'old-published')
            self.assertTrue(old_acl['protected'], 'reproduction requires modern Python Windows mkdir 0700')
            self.assertEqual(old_acl['inherited'], 0)
            fresh = create_artifact_staging(parent)
            (fresh/'proof').write_text('proof')
            os.replace(fresh, parent/'new-published')
            for path in (parent/'new-published', parent/'new-published/proof'):
                current = acl(path)
                self.assertFalse(current['protected'], path)
                self.assertGreater(current['inherited'], 0, path)


@unittest.skipUnless(os.name == 'nt', 'Windows ACL repair integration')
class EvidencePermissionRepair(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.trail = self.root/'research/_trail'
        self.trail.mkdir(parents=True)
        self.names = ['ai-quality-20260912','ai-quality-20260913','execution-baseline-20260912T212944Z','execution-baseline-20260912T213239Z']
        self.files = []
        for index, name in enumerate(self.names):
            stage = Path(tempfile.mkdtemp(dir=self.trail))
            for n in range(8 if index < 2 else 7):
                raw = ('immutable '+name+' '+str(n)).encode()
                (stage/f'proof-{n}.json').write_bytes(raw)
                self.files.append({'path':f'research/_trail/{name}/proof-{n}.json','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            os.replace(stage, self.trail/name)
        self.manifest = self.trail/'remediation-20260914/r01-recovery.json'
        self.manifest.parent.mkdir()
        self.write_manifest()

    def write_manifest(self):
        self.manifest.write_text(json.dumps({'schema':'beops-evidence-recovery/v1','files':self.files}))

    def repair(self, mode, *extra, succeeds=True):
        result = subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(REPAIR),'-ProjectRoot',str(self.root),'-Mode',mode,*extra],
                                capture_output=True,text=True,timeout=30)
        if succeeds:
            self.assertEqual(result.returncode,0,result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode,0)
        return result

    def test_scoped_repair_is_idempotent_reversible_and_keeps_all_payloads(self):
        applied = self.repair('Apply')
        self.assertEqual(applied['changed'],4)
        self.assertEqual(applied['files_verified'],30)
        for name in self.names:
            self.assertFalse(acl(self.trail/name)['protected'])
        self.assertEqual(self.repair('Apply')['changed'],0)
        for f in self.files:
            self.assertEqual(hashlib.sha256((self.root/f['path']).read_bytes()).hexdigest(),f['sha256'])
        self.assertEqual(self.repair('Rollback','-JournalPath',applied['journal'])['state'],'rolled_back')
        for name in self.names:
            self.assertTrue(acl(self.trail/name)['protected'])

    def test_changed_payload_refuses_before_any_acl_write(self):
        (self.root/self.files[-1]['path']).write_bytes(b'different payload')
        result = self.repair('Apply', succeeds=False)
        self.assertIn('Payload differs',result.stderr)
        for name in self.names:
            self.assertTrue(acl(self.trail/name)['protected'])

    def test_manifest_cannot_escape_the_four_directories(self):
        self.files[0]['path']='research/_trail/../../outside'
        self.write_manifest()
        result = self.repair('Apply', succeeds=False)
        self.assertIn('Unsafe evidence manifest',result.stderr)


if __name__ == '__main__':
    unittest.main()
