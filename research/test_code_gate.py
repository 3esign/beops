"""2026-10-01: the complete suite runs once per source commit (tools/code_gate.ps1), outside any
release, and a release reads its receipt instead of carrying the suite inside its own budget.

What must stay true: the receipt binds one exact commit and is accepted only when it passed and is
younger than 24 h; the gate yields to a running release preparation (publication has priority);
uncommitted code never produces a receipt; a failed or missing receipt leaves the release on its
own complete gate, exactly as before."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = (ROOT / 'tools/code_gate.ps1').read_text(encoding='utf-8')
PUBLISH = (ROOT / 'tools/publish_github.ps1').read_text(encoding='utf-8')


class CodeGate(unittest.TestCase):
    def test_receipt_names_one_commit_and_its_verdict(self):
        self.assertIn("schema = 'beops-code-gate/v1'", GATE)
        for field in ('source_oid = $head', 'source_tree = $tree', 'passed = ($rc -eq 0)', 'finished_at'):
            self.assertIn(field, GATE)
        self.assertIn("node tools\\test-research.js", GATE)

    def test_publication_has_priority(self):
        self.assertIn("runtime\\publish-preparation.lock", GATE)
        lock_check = GATE.index('publish-preparation.lock')
        self.assertLess(lock_check, GATE.index('test-research.js'), 'the gate yields before it starts the suite')

    def test_uncommitted_code_gets_no_receipt(self):
        self.assertRegex(GATE, r"git status --porcelain --untracked-files=no -- tools")
        self.assertLess(GATE.index('$dirty'), GATE.index('test-research.js'))

    def test_release_accepts_only_a_passing_fresh_receipt_for_its_own_commit(self):
        block = PUBLISH[PUBLISH.index('Code gate receipt'):PUBLISH.index('if ($canFastGate) {')]
        self.assertIn("'runtime\\code-gate\\' + $head + '.json'", block)
        self.assertIn("$codeGate.passed -eq $true", block)
        self.assertIn("$codeGate.source_oid -eq $head", block)
        self.assertIn("$codeGate.schema -eq 'beops-code-gate/v1'", block)
        self.assertRegex(block, r"\$codeGateAge -ge 0 -and \$codeGateAge -lt 24")

    def test_without_a_receipt_the_complete_gate_still_runs(self):
        self.assertIn('complete research gate: running full suite', PUBLISH)
        self.assertTrue(re.search(r"if \(\$canFastGate\) \{[\s\S]*?\} else \{[\s\S]*?test-research\.js", PUBLISH))


if __name__ == '__main__':
    unittest.main()
