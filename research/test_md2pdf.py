#!/usr/bin/env python3
"""test_md2pdf.py - the tool that makes the working documents into PDFs had never run on this machine.

It named one font directory, the Debian one, and this project runs on Windows. The failure surfaced
only when a document was handed to it, four versions of the pre-paper after it was written. It was on
the C-050 list of tools nothing tests.

The font is not cosmetic. Without DejaVu the Serbian diacritics render as boxes, and a document whose
subject is a Serbian city becomes unreadable in the language it is about - so the tool refuses to
write a PDF at all rather than write a wrong one.
"""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import md2pdf  # noqa: E402

SAMPLE = """# Naslov sa dijakritikom: čćžšđ

Prvi pasus, sa **podebljanim** i *kosim* tekstom i jednim `code` isečkom.

- prva stavka
- druga stavka

| kolona | vrednost |
|---|---|
| merenje | 41 |
| stanje | nedostupno |

> Citat koji mora da preživi konverziju.

---

Poslednji pasus.
"""


class Fonts(unittest.TestCase):
    def test_a_font_with_the_serbian_letters_is_found_on_this_machine(self):
        found = md2pdf.register_fonts(verbose=False)
        self.assertIn("DJ", found)
        self.assertTrue(md2pdf.has_letters(found["DJ"]),
                        "the registered font does not contain the Serbian letters")

    def test_every_face_is_registered_or_deliberately_substituted(self):
        found = md2pdf.register_fonts(verbose=False)
        for name in md2pdf.FACES:
            self.assertIn(name, found, f"{name} is neither present nor substituted")

    def test_a_font_is_never_trusted_because_of_its_name(self):
        """The check reads the font's own character map. A font that lacks a letter draws a box and
        reportlab says nothing, so the name is not evidence."""
        self.assertFalse(md2pdf.has_letters(__file__), "a Python file was accepted as a font")
        wingding = md2pdf.find_font("wingding.ttf") or md2pdf.find_font("Wingdings.ttf")
        if wingding:
            self.assertFalse(md2pdf.has_letters(wingding),
                             "a symbol font passed the Serbian-letter check")

    def test_the_search_does_not_depend_on_one_operating_system(self):
        dirs = md2pdf.font_dirs()
        self.assertGreaterEqual(len(dirs), 4)
        self.assertTrue(any("/usr/share" in d for d in dirs), "no Linux location is searched")
        self.assertTrue(any("Fonts" in d for d in dirs), "no Windows location is searched")

    def test_the_family_chosen_is_the_one_that_can_draw_the_most_faces(self):
        """Preferring DejaVu unconditionally produced a document with no bold at all, because only
        its regular face is on this machine. Bold carries the load-bearing sentence of every section
        in these documents, so 'has the letters' is the admission test and 'draws the most faces' is
        the choice."""
        admissible = [(len(u), f) for f, _, u in md2pdf.survey() if "DJ" in u]
        self.assertTrue(admissible, "no font family on this machine has the Serbian letters")
        best = max(n for n, _ in admissible)
        found = md2pdf.register_fonts(verbose=False)
        chosen = [n for n, f in admissible if f == found["_family"]][0]
        self.assertEqual(chosen, best,
                         f"chose {found['_family']} with {chosen} faces when {best} were available")

    def test_a_substitution_is_named_rather_than_silent(self):
        """A converter that swaps a face without saying so changes a document quietly."""
        found = md2pdf.register_fonts(verbose=False)
        self.assertIn("_substituted", found)
        self.assertIsInstance(found["_substituted"], list)
        for name in found["_substituted"]:
            self.assertIn(name, md2pdf.FACES)


class Render(unittest.TestCase):
    def test_it_writes_a_pdf_that_is_a_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            src = pathlib.Path(d) / "sample.md"
            dst = pathlib.Path(d) / "sample.pdf"
            src.write_text(SAMPLE, encoding="utf-8")
            md2pdf.render(src, dst, "test")
            self.assertTrue(dst.exists(), "no PDF was written")
            raw = dst.read_bytes()
            self.assertTrue(raw.startswith(b"%PDF-"), "the file is not a PDF")
            self.assertGreater(len(raw), 2000, "the PDF is too small to contain the document")

    def test_a_document_with_diacritics_does_not_lose_them_to_a_missing_glyph(self):
        """The whole reason the font is named. reportlab draws a box for a glyph a font lacks and
        says nothing, so this checks the font that will be used actually has the letters."""
        found = md2pdf.register_fonts(verbose=False)
        for ch in md2pdf.SERBIAN:
            self.assertTrue(md2pdf.has_letters(found["DJ"], ch),
                            f"the registered font has no glyph for {ch!r}")


if __name__ == "__main__":
    unittest.main()
