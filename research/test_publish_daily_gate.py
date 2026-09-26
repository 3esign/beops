"""Execute the publisher's gate selection with isolated runners and no publication."""
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'Windows publishing entry point')
class DailyGate(unittest.TestCase):
    def test_full_checks_expire_even_when_data_only_releases_keep_succeeding(self):
        source = (ROOT / 'tools/publish_github.ps1').read_text(encoding='utf-8-sig')
        start = source.index('$gatePy = Resolve-BeopsTestPython', source.index("$receipt.built = $true"))
        gate = source[start:source.index("$summary = ''", start)]
        scratch = ROOT / 'runtime/tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            work = pathlib.Path(folder)
            script = work / 'gate-cases.ps1'
            prefix = r'''
$ErrorActionPreference = 'Stop'
$StateRoot = $PSScriptRoot
$src = $PSScriptRoot
$head = 'source-unchanged'
New-Item -ItemType Directory -Path (Join-Path $StateRoot 'data/live') -Force | Out-Null
$script:publishTestsOutRun = Join-Path $StateRoot 'gate-output.txt'
function Resolve-BeopsTestPython { return 'Invoke-FixturePython' }
function Write-BeopsPhase { param($Name, $Clock, $ExitCode) }
function Invoke-FixturePython { Write-Output 'FAST-RUNNER'; $global:LASTEXITCODE = 0 }
function node { Write-Output 'FULL-RUNNER'; $global:LASTEXITCODE = $script:fullExitCode }
$results = @()
foreach ($case in @('recent', 'stale', 'exactly24h', 'future', 'legacy', 'malformed', 'changed', 'unverified', 'unpublished', 'failedtests', 'fullfailure')) {
  $fullStamp = [DateTimeOffset]::UtcNow.AddHours(-3).ToString('o')
  $previous = @{tests_ok=$true;published=$true;site_verified=$true;source_head=$head;last_full_gate_at=$fullStamp}
  switch ($case) {
    'stale' { $previous.last_full_gate_at = [DateTimeOffset]::UtcNow.AddHours(-25).ToString('o') }
    'exactly24h' { $previous.last_full_gate_at = [DateTimeOffset]::UtcNow.AddHours(-24).ToString('o') }
    'future' { $previous.last_full_gate_at = [DateTimeOffset]::UtcNow.AddHours(1).ToString('o') }
    'legacy' { $previous.Remove('last_full_gate_at') }
    'malformed' { $previous.last_full_gate_at = 'not-a-clock' }
    'changed' { $previous.source_head = 'previous-source' }
    'unverified' { $previous.site_verified = $false }
    'unpublished' { $previous.published = $false }
    'failedtests' { $previous.tests_ok = $false }
    'fullfailure' { $previous.Remove('last_full_gate_at') }
  }
  $script:fullExitCode = if ($case -eq 'fullfailure') { 1 } else { 0 }
  $previous | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $StateRoot 'data/live/publish-last-success.json') -Encoding UTF8
  $receipt = [ordered]@{gate_mode='full';last_full_gate_at=''}
'''
            suffix = r'''
  $results += @{case=$case;mode=$receipt.gate_mode;full_at=$receipt.last_full_gate_at;previous_full_at=$previous.last_full_gate_at;rc=$testsRc;runner=(Get-Content -LiteralPath $script:publishTestsOutRun -Raw).Trim()}
}
$results | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $StateRoot 'result.json') -Encoding UTF8
'''
            script.write_text(prefix + gate + suffix, encoding='utf-8-sig')
            process = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                      '-File', str(script)], cwd=work, capture_output=True,
                                     text=True, timeout=30)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            rows = json.loads((work / 'result.json').read_text(encoding='utf-8-sig'))
        for row in rows:
            with self.subTest(case=row['case']):
                fast = row['case'] == 'recent'
                self.assertEqual(row['mode'], 'fast' if fast else 'full')
                self.assertEqual(row['runner'], 'FAST-RUNNER' if fast else 'FULL-RUNNER')
                if fast:
                    self.assertEqual(row['full_at'], row['previous_full_at'])
                elif row['case'] == 'fullfailure':
                    self.assertEqual(row['full_at'], '')
                    self.assertEqual(row['rc'], 1)
                else:
                    self.assertTrue(row['full_at'])
                    self.assertEqual(row['rc'], 0)


if __name__ == '__main__':
    unittest.main()
