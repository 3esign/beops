#!/usr/bin/env python3
"""The public signature names the durable contributor, not a transient model/provider."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

PUBLIC_HTML = (
    ROOT / "docs" / "index.html",
    ROOT / "docs" / "podaci.html",
    ROOT / "docs" / "monolog.html",
)
SOURCE_HTML = (
    ROOT / "tools" / "build_site.py",
    ROOT / "research" / "05-design" / "studies" / "podaci.html",
    ROOT / "research" / "05-design" / "studies" / "monolog-puls.html",
)
PROVIDER_WORDS = ("Claude", "Anthropic", "Fable")


def author_blocks(text: str):
    return re.findall(r"<(?:p|div) class=\"authors\".*?</(?:p|div)>", text, flags=re.S)


class PublicAttributionTests(unittest.TestCase):
    def test_public_author_blocks_do_not_name_transient_provider(self):
        for path in PUBLIC_HTML:
            blocks = author_blocks(path.read_text(encoding="utf-8"))
            self.assertTrue(blocks, f"no public author block found in {path}")
            for word in PROVIDER_WORDS:
                hits = [b for b in blocks if word in b]
                self.assertEqual(hits, [], f"{word} appears in public author block in {path}")

    def test_public_author_blocks_still_name_svemir(self):
        for path in PUBLIC_HTML:
            joined = "\n".join(author_blocks(path.read_text(encoding="utf-8")))
            self.assertIn("Svemir", joined)
            self.assertIn("verified contributor", joined)

    def test_public_sources_do_not_reintroduce_provider_signature(self):
        for path in SOURCE_HTML:
            blocks = author_blocks(path.read_text(encoding="utf-8"))
            self.assertTrue(blocks, f"no source author block found in {path}")
            for word in PROVIDER_WORDS:
                hits = [b for b in blocks if word in b]
                self.assertEqual(hits, [], f"{word} appears in source author block in {path}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
