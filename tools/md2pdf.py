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
import re
import sys
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

FD = "/usr/share/fonts/truetype/dejavu"
for name, file in (("DJ", "DejaVuSans.ttf"), ("DJ-B", "DejaVuSans-Bold.ttf"),
                   ("DJ-I", "DejaVuSans-Oblique.ttf"), ("DJ-BI", "DejaVuSans-BoldOblique.ttf"),
                   ("DJM", "DejaVuSansMono.ttf"), ("DJS", "DejaVuSerif.ttf"),
                   ("DJS-B", "DejaVuSerif-Bold.ttf")):
    pdfmetrics.registerFont(TTFont(name, f"{FD}/{file}"))
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

INLINE = [
    (re.compile(r"`([^`]+)`"), r'<font face="DJM" size="8">\1</font>'),
    (re.compile(r"\*\*\*(.+?)\*\*\*"), r"<b><i>\1</i></b>"),
    (re.compile(r"\*\*(.+?)\*\*"), r"<b>\1</b>"),
    (re.compile(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])"), r"<i>\1</i>"),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"), r'<link href="\2" color="#3a5f8a">\1</link>'),
]


def inline(t: str) -> str:
    t = html.escape(t, quote=False)
    for rx, rep in INLINE:
        t = rx.sub(rep, t)
    return t


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
    doc.build(build(src.read_text(encoding="utf-8"), doc.width))


if __name__ == "__main__":
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    foot = sys.argv[3] if len(sys.argv) > 3 else src.stem
    render(src, dst, foot)
    print(f"{dst} {dst.stat().st_size} bytes")
