"""Run the isolated publisher: an actual failing suite cannot mutate the mirror."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'Windows publishing entry point')
class FailedPublish(unittest.TestCase):
    def test_real_failed_gate_preserves_public_commit_and_payload(self):
        self.run_case(False)

    def test_deadline_during_real_public_copy_restores_previous_tree(self):
        self.run_case(True)

    def run_case(self, expire_copy):
        with tempfile.TemporaryDirectory() as folder:
            base=pathlib.Path(folder);source=base/'source';mirror=base/'Beops-public'
            (source/'tools').mkdir(parents=True);(source/'research').mkdir()
            (source/'runtime').mkdir();(source/'data/live').mkdir(parents=True)
            for name in ('publish_github.ps1','publish_safety.ps1','test-research.js','incognito_user_agent.js','mirror_transaction.py','published_editions.py'):
                shutil.copyfile(ROOT/'tools'/name,source/'tools'/name)
            for name in ('baseline','latency','agreement','export_permission_dataset','collect_daemon',
                         'build_history','watchman','build_site','make_maps'):
                (source/'tools'/f'{name}.py').write_text('print("fixture build completed")\n')
            (source/'tools/ai_feed.js').write_text('process.exit(0);\n')
            (source/'tools/validate_public_tree.py').write_text('print("minimal fixture export")\n')
            (source/'docs').mkdir()
            (source/'docs/index.html').write_text('<!doctype html><html><head><title>Local fixture</title></head><body>test</body></html>')
            (source/'research/test_failure.py').write_text(
                'import unittest\nclass Refusal(unittest.TestCase):\n def test_failure(self): '+('self.assertTrue(True)' if expire_copy else 'self.fail("deliberate gate failure")')+'\n')
            def git(root,*args):
                return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE,text=True,timeout=10).strip()
            for root in (source,mirror):
                root.mkdir(exist_ok=True);git(root,'init','-q')
                (root/'.gitattributes').write_text('* -text\n')
                (root/'sentinel.txt').write_bytes(b'new candidate\n' if root==source else b'previous published generation\n')
                git(root,'add','.')
                git(root,'-c','user.name=Semir Poturak','-c','user.email=scumutator@gmail.com','commit','-qm','fixture')
            git(mirror,'remote','add','origin','https://github.com/3esign/beops.git')
            # Even if fault injection regresses, a fixture can never push online.
            git(mirror,'remote','set-url','--push','origin',str(base/'no-remote-allowed'))
            public_oid=git(mirror,'rev-parse','HEAD');source_oid=git(source,'rev-parse','HEAD')
            (mirror/'.git/beops-export-owner.json').write_text(json.dumps({
                'schema':'beops-public-owner/v1','path':str(mirror.resolve()),'remote':'https://github.com/3esign/beops.git'}))
            (source/'runtime/release-inputs.json').write_text(json.dumps({
                'schema':'beops-release-inputs/v1','source_oid':source_oid,'files':[]}))
            env=dict(os.environ,BEOPS_PYTHON=sys.executable,BEOPS_TEST_PYTHON=sys.executable,
                     BEOPS_PUBLIC_ROOT=str(mirror),PSModulePath=str(pathlib.Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/Modules'))
            for key in ('BEOPS_PHASE_TRACE','BEOPS_FROZEN_ROOT','BEOPS_FROZEN_MANIFEST_SHA256','BEOPS_FROZEN_SOURCE_OID'):
                env.pop(key,None)
            command=['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(source/'tools/publish_github.ps1'),'-Isolated','-SourceOid',source_oid]
            if expire_copy:
                env.update(BEO_TEST_MIRROR=str(mirror),BEO_TEST_MARKER=str(source/'runtime/expired.txt'),
                           BEO_TEST_PUBLISH=str(source/'tools/publish_github.ps1'),BEO_TEST_SOURCE_OID=source_oid)
                wrapper=source/'runtime/expire-copy.ps1'
                wrapper.write_text('''function Copy-Item {
  [CmdletBinding()]param([string]$LiteralPath,[string]$Destination,[switch]$Recurse,[switch]$Force)
  Microsoft.PowerShell.Management\\Copy-Item @PSBoundParameters
  if ([IO.Path]::GetFullPath($Destination).StartsWith($env:BEO_TEST_MIRROR+'\\',[StringComparison]::OrdinalIgnoreCase)) {
    $env:BEOPS_CYCLE_DEADLINE=[DateTimeOffset]::UtcNow.AddSeconds(-1).ToString('o')
    [IO.File]::WriteAllText($env:BEO_TEST_MARKER,'expired during real copy')
  }
}
& $env:BEO_TEST_PUBLISH -Isolated -SourceOid $env:BEO_TEST_SOURCE_OID
exit $LASTEXITCODE
''')
                command=['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(wrapper)]
            run=subprocess.run(command,
                cwd=source,env=env,capture_output=True,text=True,timeout=45)
            self.assertEqual(run.returncode,5 if expire_copy else 3,run.stdout+'\n'+run.stderr)
            receipt=json.loads((source/'data/live/publish-receipt.json').read_text(encoding='utf-8-sig'))
            self.assertTrue(receipt['built'])
            self.assertEqual(receipt['tests_ok'],expire_copy)
            for key in ('committed','pushed','published','site_verified'):
                self.assertFalse(receipt[key],key)
            if expire_copy:
                self.assertTrue((source/'runtime/expired.txt').exists(),run.stdout+'\n'+run.stderr)
                self.assertIn('budget exhausted',receipt['why'])
                self.assertIn('previous public working tree restored',receipt['why'])
            else:
                self.assertIn('FAIL: test_failure',receipt['why'])
                transcript=(source/'runtime/publish-tests.txt').read_text(encoding='utf-16')
                self.assertIn('deliberate gate failure',transcript)
            self.assertEqual(git(mirror,'rev-parse','HEAD'),public_oid)
            self.assertEqual(git(mirror,'status','--porcelain'),'')
            self.assertEqual((mirror/'sentinel.txt').read_bytes(),b'previous published generation\n')
            self.assertFalse((source/'runtime/publish.lock').exists())


if __name__ == '__main__': unittest.main()
