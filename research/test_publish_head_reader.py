"""Exercise the publisher's bounded scalar reader without starting a release."""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which('powershell')


@unittest.skipUnless(os.name == 'nt' and POWERSHELL, 'Windows publisher contract')
class PublishHeadReader(unittest.TestCase):
    def test_actual_gate_summary_preserves_fast_full_and_failed_results(self):
        with tempfile.TemporaryDirectory() as folder:
            script = pathlib.Path(folder) / 'summary.ps1'
            script.write_text(r'''
param([string]$Source)
$ErrorActionPreference='Stop'
$text=Get-Content -LiteralPath $Source -Raw -Encoding UTF8
$start=$text.IndexOf("`$summary = ''")
$end=$text.IndexOf('$receipt.tests_ok =', $start)
if($start -lt 0 -or $end -le $start){throw 'Actual summary block not found'}
$code=[scriptblock]::Create($text.Substring($start,$end-$start))
$script:publishTestsOutRun=Join-Path $PSScriptRoot 'run.txt'
$testsOut=Join-Path $PSScriptRoot 'shared.txt'
$cases=@(
  @{text='DATA INTEGRITY GATE OK: all core JSONs and HTML pages verified (< 1s).';rc=0;want='DATA INTEGRITY GATE OK:'},
  @{text='DATA INTEGRITY GATE FAILED:';rc=1;want='DATA INTEGRITY GATE FAILED:'},
  @{text="Ran 13 tests in 0.1s`n`nOK";rc=0;want='OK'},
  @{text='OK (skipped=1)';rc=0;want='OK (skipped=1)'},
  @{text='Full research gate passed: all discovery groups completed.';rc=0;want='Full research gate passed:'},
  @{text='';rc=0;want='test runner exited 0 without a completion marker'},
  @{text='interrupted';rc=1;want='test runner exited 1 without a completion marker'}
)
foreach($case in $cases){
  Set-Content -LiteralPath $script:publishTestsOutRun -Value $case.text -Encoding Unicode
  $testsRc=$case.rc
  . $code
  if(-not $summary.Contains($case.want)){throw ('Wrong publisher summary: '+$summary)}
  if($testsRc -ne $case.rc){throw 'Summary altered the test exit code'}
}
Write-Output 'gate summary contract passed: 7 cases'
''', encoding='utf-8')
            result = subprocess.run([POWERSHELL, '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-File', str(script), str(ROOT / 'tools/publish_github.ps1')],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('gate summary contract passed: 7 cases', result.stdout)

    def test_bounded_header_values_and_missing_file(self):
        # A real function extracted through the PowerShell AST: no publisher side
        # effects and no alternate test implementation of its reading logic.
        with tempfile.TemporaryDirectory() as folder:
            work = pathlib.Path(folder)
            script = work / 'check.ps1'
            script.write_text(r'''
param([string]$Source)
$ErrorActionPreference = 'Stop'
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($Source,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Publisher parse failed'}
$fn=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-BeopsJsonHeadValue'},$true)
if(-not $fn){throw 'Missing actual publisher reader'}
. ([scriptblock]::Create($fn.Extent.Text))
$file=Join-Path $PSScriptRoot 'input.json'
$utf8=[System.Text.UTF8Encoding]::new($false)
foreach($offset in @(0,65524,1048564)) {
  $body=(' '*$offset)+'{"as_of":"2026-09-27T09:00:00Z","hours":720,"fraction":1.25,"available":true,"absent":null}'
  [IO.File]::WriteAllText($file,$body,$utf8)
  if((Get-BeopsJsonHeadValue $file 'as_of') -ne '2026-09-27T09:00:00Z'){throw "Bad string at $offset"}
  if((Get-BeopsJsonHeadValue $file 'hours') -ne 720){throw "Bad integer at $offset"}
  if((Get-BeopsJsonHeadValue $file 'fraction') -ne 1.25){throw "Bad number at $offset"}
  if((Get-BeopsJsonHeadValue $file 'available') -ne $true){throw "Bad boolean at $offset"}
  if($null -ne (Get-BeopsJsonHeadValue $file 'absent')){throw 'Bad null'}
}
[IO.File]::WriteAllText($file,(' '*4194304)+'{"outside":"not-readable"}',$utf8)
if($null -ne (Get-BeopsJsonHeadValue $file 'outside')){throw 'Reader exceeded 4 MiB character budget'}
if($null -ne (Get-BeopsJsonHeadValue (Join-Path $PSScriptRoot 'missing.json') 'as_of')){throw 'Missing file not null'}
Write-Output 'bounded scalar contract passed'
''', encoding='utf-8')
            result = subprocess.run([POWERSHELL, '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-File', str(script), str(ROOT / 'tools/publish_github.ps1')],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('bounded scalar contract passed', result.stdout)


if __name__ == '__main__':
    unittest.main()
