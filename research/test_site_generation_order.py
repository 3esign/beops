"""Run real publisher build commands; generation pins must survive the last writer."""
import copy
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mirror_transaction as M
import verify_staged_export as V


@unittest.skipUnless(shutil.which('powershell.exe'), 'Windows publisher requires PowerShell')
class SiteGenerationOrder(unittest.TestCase):
    def test_actual_publish_build_order_pins_fresh_citizen_output(self):
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder)
            for directory in ('tools', 'research', 'docs', 'public', 'runtime'):
                (base / directory).mkdir()
            for name in ('build_site', 'build_public_page', 'build_city_view', 'build_headlines',
                         'collect_events', 'contracts', 'prose', 'headline_geo'):
                shutil.copyfile(ROOT / 'tools' / (name + '.py'), base / 'tools' / (name + '.py'))
            # The actual citizen builder imports the shared offline geography
            # adapter. Keep its complete runtime closure inside this fixture.
            for name in ('headline_geo.js', 'headline_places.json'):
                shutil.copyfile(ROOT / 'tools' / name, base / 'tools' / name)
            (base / 'research/COLLECTORS.json').write_text('{"sources":[]}', encoding='utf-8')
            captured = b'{"schema":"fixture-release-inputs"}\n'
            (base / 'runtime/release-inputs.json').write_bytes(captured)
            generation_id = hashlib.sha256(captured).hexdigest()
            asof = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
            generation = {'id': generation_id, 'schema': 'beops-input-generation/v1',
                          'observation_prefix': 'complete-lf-lines/v1', 'captured_at': asof}
            snapshot = {'as_of': asof, 'input_generation': generation, 'sources': [{
                'sid': 'S146', 'name': 'fixture station', 'datastreams': [{
                    'station': 'A', 'datastream': 'A-PM25', 'parameter': 'PM2.5', 'unit': 'ug/m3',
                    'points': [{'t': asof, 'v': 17.0}]}]}]}
            (base / 'public/live-snapshot.json').write_text(json.dumps(snapshot), encoding='utf-8')
            (base / 'public/history.json').write_text(json.dumps({
                'as_of': asof, 'input_generation': generation, 'series': []}), encoding='utf-8')
            stale = copy.deepcopy(snapshot)
            stale['sources'][0]['datastreams'][0]['points'][0]['v'] = 999.0
            # A previous docs view must never supply the new citizen page's content.
            (base / 'docs/city-overview.json').write_text(json.dumps({'snapshot': stale}), encoding='utf-8')
            (base / '.gitattributes').write_bytes(b'* -text\n')
            runner = base / 'build.ps1'
            runner.write_text(r'''
param([string]$Publisher,[string]$Safety,[string]$Fixture,[string]$Python,[string]$AsOf)
$ErrorActionPreference='Stop'
. $Safety
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($Publisher,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Publisher syntax is invalid'}
$commands=@($ast.FindAll({param($item)
  $item -is [System.Management.Automation.Language.CommandAst] -and
  $item.GetCommandName() -eq 'Invoke-BeopsNative' -and
  $item.CommandElements[1].Value -in @('build_site.py','build_public_page.py')
},$true) | Sort-Object {$_.Extent.StartOffset})
if(-not $commands.Count){throw 'No actual site build commands found'}
$py=$Python
Set-Location $Fixture
foreach($command in $commands){Invoke-Expression $command.Extent.Text}
$function=$ast.Find({param($item)
  $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
  $item.Name -eq 'Write-BeopsExportManifest'
},$true)
if(-not $function){throw 'Missing real manifest producer'}
Invoke-Expression $function.Extent.Text
$pub=$Fixture;$head='a'*40;$sourceTree='b'*40
$keep=@();$generatedPublicPaths=@('docs')
Write-BeopsExportManifest $AsOf
''', encoding='utf-8')
            env = dict(os.environ)
            # Fixture subprocesses must use only their copied tools, never live roots.
            env.pop('PYTHONPATH', None)
            for key in ('BEOPS_FROZEN_ROOT', 'BEOPS_FROZEN_SOURCE_OID', 'BEOPS_FROZEN_MANIFEST_SHA256',
                        'BEOPS_PHASE_TRACE', 'BEOPS_CYCLE_DEADLINE'):
                env.pop(key, None)
            run = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                  '-File', str(runner), '-Publisher', str(ROOT / 'tools/publish_github.ps1'),
                                  '-Safety', str(ROOT / 'tools/publish_safety.ps1'), '-Fixture', str(base),
                                  '-Python', sys.executable, '-AsOf', asof],
                                 env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            tag = '<meta name="beops-input-generation" content="' + generation_id + '">'
            for name in ('index.html', 'instrument.html'):
                html = (base / 'docs' / name).read_text(encoding='utf-8')
                self.assertEqual(html.count(tag), 1, name)
            citizen = (base / 'docs/index.html').read_text(encoding='utf-8')
            self.assertIn('prosek 17.0', citizen)
            self.assertNotIn('prosek 999.0', citizen)
            M.git(base, 'init', '-q')
            # The real manifest lists every fixture file; stage that exact inventory.
            M.git(base, 'add', '--', '.')
            manifest = json.loads((base / 'docs/export-manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['inputs_manifest_sha256'], generation_id)
            self.assertEqual(V.verify(base)['staged_files_verified'], len(manifest['files']))


class StagedHtmlGeneration(unittest.TestCase):
    def test_semantically_wrong_html_is_refused_even_with_matching_staged_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            (root / 'docs').mkdir()
            (root / '.gitattributes').write_bytes(b'* -text\n')
            M.git(root, 'init', '-q')
            generation_id = 'a' * 64
            pin = '<meta name="beops-input-generation" content="' + generation_id + '">'
            wrong = pin.replace(generation_id, 'b' * 64)
            for label, pins, valid in [('right', pin, True), ('missing', '', False),
                                       ('wrong', wrong, False), ('duplicate', pin + wrong, False)]:
                with self.subTest(label=label):
                    raw = ('<html><head>' + pins + '</head><body>fixture</body></html>').encode()
                    (root / 'docs/index.html').write_bytes(raw)
                    manifest = {'inputs_manifest_sha256': generation_id, 'files': [{
                        'path': 'docs/index.html', 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}]}
                    (root / 'docs/export-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                    M.git(root, 'add', '--', '.gitattributes', 'docs')
                    # Worktree is deliberately repaired after staging; only the staged bytes count.
                    (root / 'docs/index.html').write_text('<html><head>' + pin + '</head></html>', encoding='utf-8')
                    if valid:
                        self.assertEqual(V.verify(root)['staged_files_verified'], 1)
                    else:
                        with self.assertRaisesRegex(ValueError, 'staged HTML generation differs'):
                            V.verify(root)


if __name__ == '__main__':
    unittest.main()
