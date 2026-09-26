"""Exercise the real PowerShell manifest producer through its Python/JS consumers."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import mirror_transaction as M
import verify_staged_export as V


@unittest.skipUnless(shutil.which('powershell.exe'), 'Windows publisher requires PowerShell')
class ExportManifestContract(unittest.TestCase):
    def test_real_producer_staged_bytes_and_public_generation_share_canonical_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            base=pathlib.Path(folder);source=base/'source';public=base/'public'
            (source/'runtime').mkdir(parents=True);(public/'docs').mkdir(parents=True)
            captured=b'{"schema":"fixture-release-inputs"}\n'
            (source/'runtime/release-inputs.json').write_bytes(captured)
            generation_id=hashlib.sha256(captured).hexdigest();asof='2026-09-26T21:00:00Z'
            snapshot={'as_of':asof,'input_generation':{'id':generation_id,
                'schema':'beops-input-generation/v1','observation_prefix':'complete-lf-lines/v1',
                'captured_at':asof}}
            (public/'docs/live-snapshot.json').write_text(json.dumps(snapshot),encoding='utf-8')
            (public/'.gitattributes').write_bytes(b'* -text\n')
            binary=public/'docs/file with space.pdf';original=b'%PDF byte fixture\x00\r\n'
            binary.write_bytes(original)
            (public/'source.js').write_bytes(b'exports.fixture=true;\n')
            M.git(public,'init','-q')
            runner=base/'produce.ps1'
            runner.write_text(r'''
param([string]$Publisher,[string]$Safety,[string]$Source,[string]$ExportRoot,[string]$AsOf)
$ErrorActionPreference='Stop'
. $Safety
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($Publisher,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Publisher syntax is invalid'}
$function=$ast.Find({param($item) $item -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $item.Name -eq 'Write-BeopsExportManifest'},$true)
if(-not $function){throw 'Real export manifest producer is missing'}
Invoke-Expression $function.Extent.Text
$pub=$ExportRoot;$head='a'*40;$sourceTree='b'*40
$keep=@('source.txt');$generatedPublicPaths=@('docs')
Set-Location $Source
Write-BeopsExportManifest $AsOf
''',encoding='utf-8')
            proc=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(runner),
                '-Publisher',str(ROOT/'tools/publish_github.ps1'),'-Safety',str(ROOT/'tools/publish_safety.ps1'),
                '-Source',str(source),'-ExportRoot',str(public),'-AsOf',asof],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            manifest=json.loads((public/'docs/export-manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['inputs_manifest_sha256'],generation_id)
            self.assertNotIn('inputs_manifest_SHA256',manifest)
            self.assertEqual(len(manifest['files']),4)
            for row in manifest['files']:
                self.assertEqual(set(row),{'path','bytes','sha256'})
            self.assertEqual(len(M.manifest_files(public)),4)
            M.git(public,'add','--','.gitattributes','source.js','docs')
            self.assertEqual(V.verify(public)['staged_files_verified'],4)
            js=base/'generation.cjs'
            js.write_text(r'''
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {validateGeneration}=require(process.argv[2]);
const docs=process.argv[3],manifest=JSON.parse(fs.readFileSync(path.join(docs,'export-manifest.json')));
const value=JSON.parse(fs.readFileSync(path.join(docs,'live-snapshot.json')));
assert.equal(validateGeneration('live-snapshot.json',value,manifest.inputs_manifest_sha256,manifest.generated_as_of),value.input_generation.id);
''',encoding='utf-8')
            subprocess.run(['node',str(js),str(ROOT/'tools/verify_public_site.js'),str(public/'docs')],
                           check=True,capture_output=True,text=True,timeout=10)
            # The staged blob is the authority, not the subsequently edited worktree.
            binary.write_bytes(b'%'*len(original))
            self.assertEqual(V.verify(public)['staged_files_verified'],4)
            M.git(public,'add','--','docs/file with space.pdf')
            with self.assertRaisesRegex(ValueError,'staged bytes differ from manifest'):
                V.verify(public)


if __name__=='__main__':unittest.main()
