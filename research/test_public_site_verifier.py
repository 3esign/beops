#!/usr/bin/env python3
"""The live GitHub Pages interface has a named verifier.

The normal suite is offline and protects the artefact before publish. The public site check is
networked by nature, so it is a separate command, but it must remain discoverable and tied to the
same public-surface contract.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "verify_public_site.js"


class PublicSiteVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    def test_the_site_check_has_a_named_npm_command(self):
        self.assertEqual(
            self.package["scripts"].get("test:site"),
            "node tools/verify_public_site.js",
            "the live public interface check is no longer a named command",
        )
        self.assertEqual(self.package["scripts"].get("test"), "node tools/test-research.js")

    def test_the_verifier_checks_the_real_public_surface(self):
        self.assertIn("https://3esign.github.io/beops/", self.script)
        self.assertIn("BEOPS_SITE_URL", self.script)
        self.assertIn("beops_site_check", self.script)
        self.assertIn("Beops-public", self.script)

    def test_the_verifier_compares_the_live_site_to_the_public_export(self):
        self.assertIn("docs', 'index.html'", self.script)
        self.assertIn("sha256(live.text)", self.script)
        self.assertIn("does not match", self.script)
        self.assertIn("replace(/\\r\\n/g, '\\n')", self.script)

    def test_the_verifier_allows_a_short_pages_propagation_window(self):
        self.assertIn("BEOPS_SITE_WAIT_SECONDS", self.script)
        self.assertIn("BEOPS_SITE_POLL_MS", self.script)
        self.assertIn("attempts.push", self.script)
        self.assertIn("await sleep(POLL_MS)", self.script)
        self.assertIn("raw_check", self.script)

    def test_the_verifier_treats_stale_public_words_as_failures(self):
        for marker in ("Claude, Anthropic", "Claude Fable", "Svemir (Claude"):
            self.assertIn(marker, self.script)
        self.assertIn("local AI infrastructure", self.script)

    def test_raw_github_comparison_is_opt_in(self):
        self.assertIn("BEOPS_CHECK_RAW === '1'", self.script)

    def test_the_verifier_checks_the_embedded_interface_routes(self):
        for rel in ("podaci.html", "monolog.html", "sada.html", "traka.html", "svedoci.html"):
            self.assertIn(rel, self.script)

    def test_the_verifier_uses_the_svemir_incognito_gate_when_available(self):
        self.assertIn("incognito.js", self.script)
        self.assertIn("incognito.headers", self.script)


if __name__ == "__main__":
    unittest.main()
