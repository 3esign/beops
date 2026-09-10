#!/usr/bin/env python3
"""md2pdf.py - a small, deliberate Markdown-to-PDF renderer for this project's working documents.

It is not a general converter. It handles exactly what these documents use - headings, paragraphs,
bullet and numbered lists, pipe tables, block quotes, rules, and inline bold/italic/code/links - and
it uses DejaVu so that Serbian diacritics render as letters rather than as boxes. Anything it does
not understand is printed as plain text rather than silently dropped, because a converter that
quietly loses a sentence is worse than one that prints it badly.
"""
from __future__ import annotations

import html
import os
import re
import sys
import pathlib
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, KeepTogether, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

# Where the font actually is. The first version of this file named one directory - the Debian one -
# and this project runs on Windows, so the tool could never have produced a PDF on the machine that
# holds the record. It was one of the tools nothing tested, and the failure surfaced only when a
# document was handed to it, four pre-paper versions after it was written.
#
# The font is not cosmetic. Serbian is written with c-caron, c-acute, z-caron, s-caron and d-stroke,
# and a font without those letters draws boxes. So the rule here is: prefer DejaVu; accept any other
# family that PROVABLY has the letters, checked against the font's own character map rather than
# assumed from its name; and refuse to write a PDF at all if nothing does.

SERBIAN = "\u010d\u0107\u017e\u0161\u0111\u010c\u0106\u017d\u0160\u0110"   # čćžšđ ČĆŽŠĐ

FACES = ("DJ", "DJ-B", "DJ-I", "DJ-BI", "DJM", "DJS", "DJS-B")

# family -> the file for each of the seven roles, in the order of FACES. A None means the family has
# no such face and the chain below substitutes one it does have.
FAMILIES = [
    ("DejaVu", ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf",
                "DejaVuSans-BoldOblique.ttf", "DejaVuSansMono.ttf", "DejaVuSerif.ttf",
                "DejaVuSerif-Bold.ttf")),
    ("Calibri/Consolas/Times", ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf",
                                "consola.ttf", "times.ttf", "timesbd.ttf")),
    ("Segoe UI/Consolas/Times", ("segoeui.ttf", "segoeuib.ttf", "segoeuii.ttf", "segoeuiz.ttf",
                                 "consola.ttf", "times.ttf", "timesbd.ttf")),
    ("Verdana/Courier/Times", ("verdana.ttf", "verdanab.ttf", "verdanai.ttf", "verdanaz.ttf",
                               "cour.ttf", "times.ttf", "timesbd.ttf")),
]

# When a face is missing, use one that is present: an upright italic is a cosmetic loss, a missing
# letter is a wrong document.
SUBSTITUTE = {"DJ-B": "DJ", "DJ-I": "DJ", "DJ-BI": "DJ-B", "DJM": "DJ", "DJS": "DJ", "DJS-B": "DJS"}


def font_dirs() -> list:
    d = [os.environ.get("BEOPS_FONT_DIR"),                  # an explicit answer beats any search
         "/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu",
         "/usr/local/share/fonts/dejavu", "/Library/Fonts",
         os.path.expanduser("~/Library/Fonts")]
    try:                                                    # matplotlib ships DejaVu when it is here
        import matplotlib
        d.append(str(pathlib.Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"))
    except Exception:                                       # noqa: BLE001 - a missing library is not an error
        pass
    home = pathlib.Path(os.path.expanduser("~"))
    d += [str(q) for q in sorted(home.glob(".cache/codex-runtimes/*/dependencies/native/*/Library/share/fonts"))]
    d += [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
          str(home / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts")]
    return [x for x in d if x]


def find_font(file: str) -> str | None:
    for d in font_dirs():
        q = pathlib.Path(d) / file
        if q.is_file():
            return str(q)
    return None


def has_letters(path: str, letters: str = SERBIAN) -> bool:
    """Whether a font actually contains the letters, read from its own character map. A font is not
    trusted because of its name: reportlab draws a box for a glyph a font lacks and says nothing."""
    try:
        f = TTFont("probe", path)
        m = getattr(f.face, "charToGlyph", None)
        if not m:
            return False
        return all(ord(c) in m for c in letters)
    except Exception:                                       # noqa: BLE001 - unreadable is not usable
        return False


def survey() -> list:
    """Every family, with the faces it can actually supply. Read once, so the choice below is made
    on what is on this machine rather than on what a name suggests."""
    out = []
    for family, files in FAMILIES:
        paths = {name: find_font(f) for name, f in zip(FACES, files)}
        usable = {n: p for n, p in paths.items() if p and has_letters(p)}
        out.append((family, paths, usable))
    return out


def register_fonts(verbose: bool = True) -> dict:
    """Register the seven roles from the family that can supply the most of them.

    Not simply the first family that has the letters. DejaVu is the preference, but on this machine
    only its regular face exists - it arrives bundled with a PDF utility rather than installed - so
    preferring it unconditionally produced a document with no bold at all, in a set of documents where
    the load-bearing sentence of every section is bold. The rule is therefore: any family that has the
    Serbian letters is admissible, and among the admissible ones the one that can draw the most of the
    seven roles wins, with the order of FAMILIES breaking ties. What is chosen is printed, so a
    document that came out in a different face says so rather than looking like a design decision.
    """
    tried = []
    ranked = []
    for family, paths, usable in survey():
        if "DJ" not in usable:
            tried.append("%s (%s)" % (family, "not installed" if not paths.get("DJ")
                                      else "installed, no Serbian letters"))
            continue
        ranked.append((len(usable), family, paths, usable))
    ranked.sort(key=lambda r: (-r[0], [f for f, _ in FAMILIES].index(r[1])))
    for _, family, paths, usable in ranked:
        found, substituted = dict(usable), []
        for name, path in usable.items():
            pdfmetrics.registerFont(TTFont(name, path))
        for name in FACES:                                  # resolve the chain, DJ is always present
            if name in found:
                continue
            src = name
            while src in SUBSTITUTE and SUBSTITUTE[src] not in found:
                src = SUBSTITUTE[src]
            src = SUBSTITUTE.get(src, "DJ") if src not in found else src
            pdfmetrics.registerFont(TTFont(name, found.get(src, found["DJ"])))
            found[name] = found.get(src, found["DJ"])
            substituted.append(name)
        if verbose:
            print("fonts: %s (%d of %d faces) from %s"
                  % (family, len(usable), len(FACES), pathlib.Path(found["DJ"]).parent))
            if substituted:
                print("  substituted (the face is not on this machine): %s" % ", ".join(substituted))
            if family != "DejaVu":
                print("  NOTE: DejaVu is not complete on this machine; %s was chosen because its "
                      "character map contains the Serbian letters and it supplies more of the seven "
                      "faces." % family)
        found["_family"], found["_substituted"] = family, substituted
        return found
    raise SystemExit(
        "md2pdf: no font with the Serbian letters was found. Tried: %s. Looked in: %s. Set "
        "BEOPS_FONT_DIR to a directory holding DejaVuSans.ttf. This tool refuses to write a PDF "
        "rather than write one in which cccc, zz, ss and d-stroke are boxes."
        % ("; ".join(tried), "; ".join(font_dirs())))


register_fonts()
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B", italic="DJ-I", boldItalic="DJ-BI")

INK = colors.HexColor("#1a1a1a")
MUTE = colors.HexColor("#5a5a5a")
LINE = colors.HexColor("#c9c6bf")
BAND = colors.HexColor("#f2f0ea")

S = {
    "h1": ParagraphStyle("h1", fontName="DJS-B", fontSize=17, leading=21, textColor=INK,
                         spaceBefore=2, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="DJS-B", fontSize=12.5, leading=16, textColor=INK,
                         spaceBefore=14, spaceAfter=5),
    "h3": ParagraphStyle("h3", fontName="DJ-B", fontSize=10.5, leading=14, textColor=INK,
                         spaceBefore=10, spaceAfter=3),
    "h4": ParagraphStyle("h4", fontName="DJ-B", fontSize=9.5, leading=13, textColor=MUTE,
                         spaceBefore=8, spaceAfter=2),
    "p": ParagraphStyle("p", fontName="DJ", fontSize=9, leading=13.2, textColor=INK,
                        alignment=TA_JUSTIFY, spaceAfter=6),
    "li": ParagraphStyle("li", fontName="DJ", fontSize=9, leading=13.2, textColor=INK,
                         alignment=TA_LEFT, leftIndent=11, bulletIndent=2, spaceAfter=2.5),
    "q": ParagraphStyle("q", fontName="DJ-I", fontSize=9, leading=13.2, textColor=MUTE,
                        leftIndent=10, rightIndent=6, spaceBefore=3, spaceAfter=7,
                        borderPadding=(0, 0, 0, 6)),
    "td": ParagraphStyle("td", fontName="DJ", fontSize=7.8, leading=10.4, textColor=INK),
    "th": ParagraphStyle("th", fontName="DJ-B", fontSize=7.8, leading=10.4, textColor=INK),
}

ITALIC_PATTERN = r"(?<![\w*])\*([^*\n]+)\*(?![\w*])"

INLINE = [
    (re.compile(r"`([^`]+)`"), r'<font face="DJM" size="8">\1</font>'),
    (re.compile(r"\*\*\*(.+?)\*\*\*"), r"<b><i>\1</i></b>"),
    # bold whose last words are italic: **A *B***. Without this the bold rule takes two of the three
    # trailing stars and the italic rule then reaches across the closing tag, which reportlab refuses.
    (re.compile(r"\*\*([^*]*?)\*([^*]+)\*\*\*"), r"<b>\1<i>\2</i></b>"),
    (re.compile(r"\*\*\*([^*]+)\*([^*]*?)\*\*"), r"<b><i>\1</i>\2</b>"),
    (re.compile(r"\*\*(.+?)\*\*"), r"<b>\1</b>"),
    (re.compile(ITALIC_PATTERN), r"<i>\1</i>"),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"), r'<link href="\2" color="#3a5f8a">\1</link>'),
]


TAG = re.compile(r"<(/?)(b|i|font|link|super|sub)\b[^>]*>")

DEGRADED = []          # paragraphs whose markup could not be made well-formed, for the run to report


def markup_ok(t: str) -> bool:
    """Whether the tags in a rendered paragraph nest properly.

    reportlab's paragraph parser raises on overlapping tags, and the markdown these documents use can
    produce them: `**bold with *italic inside***` closes the bold before the italic, because the
    bold rule takes two of the three trailing stars and the italic rule then reaches across the
    closing tag. That crashed the whole conversion on pre-paper v5, in a tool whose own docstring
    promises that anything it does not understand is printed as plain text rather than dropped.
    """
    stack = []
    for m in TAG.finditer(t):
        closing, name = m.group(1), m.group(2)
        if not closing:
            stack.append(name)
        elif not stack or stack.pop() != name:
            return False
    return not stack


def inline(t: str, rules=None) -> str:
    """Markdown inline markup, degrading rather than crashing.

    Three attempts: everything; then without italics, since bold-inside-italic is the construct that
    overlaps; then the plain escaped text. The last is a loss of emphasis and never a loss of a
    sentence, which is the trade this tool's docstring promises and did not keep.
    """
    escaped = html.escape(t, quote=False)
    for attempt in (rules or INLINE, [r for r in INLINE if r[0].pattern != ITALIC_PATTERN]):
        out = escaped
        for rx, rep in attempt:
            out = rx.sub(rep, out)
        if markup_ok(out):
            return out
    DEGRADED.append(t.strip()[:90])
    return escaped


def is_table_row(s: str) -> bool:
    return s.startswith("|") and s.count("|") >= 2


def split_row(s: str) -> list[str]:
    return [c.strip() for c in s.strip().strip("|").split("|")]


def build(md: str, width: float) -> list:
    flow: list = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            flow.append(Paragraph('<font face="DJM" size="8">' +
                                  html.escape("\n".join(buf)).replace("\n", "<br/>") + "</font>", S["p"]))
            continue
        if re.fullmatch(r"-{3,}|_{3,}|\*{3,}", s):
            flow.append(Spacer(1, 3))
            flow.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceAfter=7))
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            lvl = min(len(m.group(1)), 4)
            flow.append(Paragraph(inline(m.group(2)), S[f"h{lvl}"]))
            i += 1
            continue
        if is_table_row(s) and i + 1 < len(lines) and re.fullmatch(r"[\s|:-]+", lines[i + 1].strip()):
            head = split_row(s)
            i += 2
            body = []
            while i < len(lines) and is_table_row(lines[i].strip()):
                body.append(split_row(lines[i].strip())); i += 1
            n = max(len(head), max((len(r) for r in body), default=0))
            def pad(r):
                return (r + [""] * n)[:n]
            data = [[Paragraph(inline(c), S["th"]) for c in pad(head)]] + \
                   [[Paragraph(inline(c), S["td"]) for c in pad(r)] for r in body]
            first = max(0.16 * width, min(0.34 * width, width / n))
            rest = (width - first) / max(n - 1, 1)
            cols = [first] + [rest] * (n - 1) if n > 1 else [width]
            t = Table(data, colWidths=cols, repeatRows=1, hAlign="LEFT")
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BAND),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
                ("LINEBELOW", (0, 1), (-1, -2), 0.25, colors.HexColor("#e6e3dc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ]))
            flow.append(t)
            flow.append(Spacer(1, 8))
            continue
        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            flow.append(Paragraph(inline(" ".join(x for x in buf if x)), S["q"]))
            continue
        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            flow.append(Paragraph(inline(m.group(1)), S["li"], bulletText="•"))
            i += 1
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
            flow.append(Paragraph(inline(m.group(2)), S["li"], bulletText=m.group(1) + "."))
            i += 1
            continue
        buf = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,6}\s|[-*]\s|\d+\.\s|>|\||```|-{3,}$)", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        flow.append(Paragraph(inline(" ".join(buf)), S["p"]))
    return flow


def render(src: Path, dst: Path, footer: str) -> None:
    doc = BaseDocTemplate(str(dst), pagesize=A4,
                          leftMargin=20 * mm, rightMargin=18 * mm,
                          topMargin=16 * mm, bottomMargin=16 * mm,
                          title=src.stem, author="Darinka Golubovic Matic; Semir Poturak")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")

    def page(canvas, d):
        canvas.saveState()
        canvas.setFont("DJ", 7)
        canvas.setFillColor(MUTE)
        canvas.drawString(doc.leftMargin, 10 * mm, footer)
        canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, str(canvas.getPageNumber()))
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.4)
        canvas.line(doc.leftMargin, 13 * mm, A4[0] - doc.rightMargin, 13 * mm)
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=page)])
    DEGRADED.clear()
    doc.build(build(src.read_text(encoding="utf-8"), doc.width))
    if DEGRADED:
        print("%d paragraph(s) printed without emphasis because their markup could not be made "
              "well-formed; no text was dropped:" % len(DEGRADED))
        for x in DEGRADED[:6]:
            print("   " + x)


if __name__ == "__main__":
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    foot = sys.argv[3] if len(sys.argv) > 3 else src.stem
    render(src, dst, foot)
    print(f"{dst} {dst.stat().st_size} bytes")
