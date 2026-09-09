#!/usr/bin/env python3
"""
make_layers.py - the axonometric scheme of BEOPS's layers: what the observatory is made of, from the
ground the map stands on to the voice that speaks, with the live counts read from the registries.

    python -B tools/make_layers.py            writes research/05-design/studies/slojevi.svg (and docs/ copy if --out docs)

One SVG, bilingual (every label exists twice, class sr-only / en-only, so the page's language toggle
works inside it), themed by the page's CSS variables (currentColor and var(--signal)). The plates are
drawn in a 2:1 isometric projection; the vertical order is the order of dependence: nothing above a
plate exists without the plate below it.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "research" / "05-design" / "studies" / "slojevi.svg"


def counts() -> dict:
    reg = json.loads((ROOT / "research" / "SOURCE_REGISTRY.json").read_text(encoding="utf-8"))["sources"]
    col = json.loads((ROOT / "research" / "COLLECTORS.json").read_text(encoding="utf-8"))["sources"]
    st = json.loads((ROOT / "research" / "STATIC_LAYERS.json").read_text(encoding="utf-8")) if (ROOT / "research" / "STATIC_LAYERS.json").exists() else {}
    stat = st.get("layers", st) if isinstance(st, dict) else []
    n_static = len(stat) if isinstance(stat, list) else len([k for k in stat.keys()]) if isinstance(stat, dict) else 0
    return {
        "records": len(reg), "refused": sum(1 for s in reg if s.get("status") == "opted_out"),
        "polled": sum(1 for s in col if s.get("enabled", True)),
        "live": sum(1 for s in col if s.get("enabled", True) and s.get("cadence_seconds", 0) <= 900),
        "periodic": sum(1 for s in col if s.get("enabled", True) and s.get("cadence_seconds", 0) > 900),
        "static": len(stat) if isinstance(stat, list) else 1,
        "static_live": 1,   # Kontur is on the map; the rest of the static register is registered, not yet fetched
    }


def plate(x, y, w, d, h, cls):
    """An isometric plate: top face (parallelogram) + two visible sides. (x,y) is the front-left corner of the top."""
    # iso axes: right = (0.866, 0.5) scaled, back = (-0.866, 0.5) -> we use a 2:1 projection for legibility
    ax, ay = 1.0, 0.5   # right vector
    bx, by = -1.0, 0.5  # back-left vector? (use standard: back = (1,-0.5))
    # corners of the top face
    p0 = (x, y)
    p1 = (x + w, y - w * 0.5)
    p2 = (x + w - d, y - w * 0.5 - d * 0.5)
    p3 = (x - d, y - d * 0.5)
    top = " ".join(f"{px:.1f},{py:.1f}" for px, py in (p0, p1, p2, p3))
    right = " ".join(f"{px:.1f},{py:.1f}" for px, py in (p0, p1, (p1[0], p1[1] + h), (p0[0], p0[1] + h)))
    left = " ".join(f"{px:.1f},{py:.1f}" for px, py in (p3, p0, (p0[0], p0[1] + h), (p3[0], p3[1] + h)))
    return (f'<polygon class="side {cls}" points="{left}"/><polygon class="side2 {cls}" points="{right}"/>'
            f'<polygon class="top {cls}" points="{top}"/>'), (p0, p1, p2, p3)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, sr, en, cls="", size=13, anchor="start", weight=""):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text class="sr-only {cls}" x="{x:.0f}" y="{y:.0f}" font-size="{size}" text-anchor="{anchor}"{w}>{esc(sr)}</text>'
            f'<text class="en-only {cls}" x="{x:.0f}" y="{y:.0f}" font-size="{size}" text-anchor="{anchor}"{w}>{esc(en)}</text>')


def build(c: dict) -> str:
    W, H = 1320, 1030
    # plates from the ground up; each: (key, sr title, en title, sr items, en items, accent)
    layers = [
        ("ground", "0 · Podloga", "0 · Ground",
         ["Natural Earth 1:10 mil. (javno vlasništvo): reke, jezera, izgrađeno tkivo", "orijentacija, ne merenje · bez granica opština (svi putevi odbijeni)"],
         ["Natural Earth 1:10m (public domain): rivers, lakes, built-up footprint", "orientation, not measurement · no municipality boundaries (every route refused)"], False),
        ("static", "1 · Statični i polustatični slojevi", "1 · Static and semi-static layers",
         [f"Kontur stanovništvo 2022 (CC BY) na mapi · {c['static']} slojeva u registru statičnih slojeva", "traju mesecima i godinama: popis, putevi, GHSL, poplavne zone, službeni list (sledeći)"],
         [f"Kontur population 2022 (CC BY) on the map · {c['static']} layers in the static register", "they last months and years: census, roads, GHSL, flood zones, the gazette (next)"], False),
        ("periodic", "2 · Periodični izvori (sati – dani)", "2 · Periodic sources (hours – days)",
         [f"{c['periodic']} izvora: SEPA satne srednje vrednosti (32 stanice), planirana isključenja struje, obaveštenja grada, Vodovod, Elektrane, Vlada RS", "objavljuju u taktu izvora; svaka vrednost nosi sat merenja ili dan objave"],
         [f"{c['periodic']} sources: SEPA hourly means (32 stations), planned power outages, City notices, water utility, heating operator, Government RS", "published on the source's own beat; every value carries its measurement hour or publication day"], False),
        ("live", "3 · Živa čula (minuti)", "3 · Live senses (minutes)",
         [f"{c['live']} izvora na 5–15 min: RHMZ stanice, građanski senzori, parking, {c['live'] - 3 if c['live'] > 3 else 0} feed(ova) vesti", "život, živost, novost, promena — stalno pribavljanje; prijem nije merenje"],
         [f"{c['live']} sources at 5–15 min: RHMZ stations, citizen sensors, parking, {c['live'] - 3 if c['live'] > 3 else 0} news feeds", "life, liveliness, novelty, change — a constant pull; a reception is not a measurement"], True),
        ("legal", "4 · Pravni okvir i dozvole (kapija)", "4 · Legal frame and permissions (the gate)",
         [f"{c['records']} zapisa u registru · {c['polled']} se čita · {c['refused']} imenovanih odbijanja koja se ne zaobilaze", "zahvat dozvole pre svakog čitanja; knjiga zahvata; nedeljna ponovna provera; ivični slučajevi E-001–E-013"],
         [f"{c['records']} registry records · {c['polled']} polled · {c['refused']} named refusals never circumvented", "a permission capture before any reading; the ledger; a weekly re-check; edge cases E-001–E-013"], False),
        ("organize", "5 · Sistem koji organizuje", "5 · The system that organizes",
         ["sakupljač: kapija → prijem → red → dedupe → izvoz (svakih 5 min) · potvrde i za neuspehe", "pet stanja: izmereno / bez vremena / procenjeno / prognoza / nedostupno · ispravke se dopisuju, ništa se ne briše"],
         ["the collector: gate → reception → row → dedupe → export (every 5 min) · receipts even for failures", "five states: observed / untimed / estimated / forecast / unavailable · corrections appended, nothing deleted"], False),
        ("mind", "6 · Sistem koji misli i govori", "6 · The system that thinks and speaks",
         ["organele (povezivač istih događaja, ocena iznenađenja) · tri entiteta: Posmatrač, Sumnjalo, Povezivač · glas na ekavici", "svaka rečenica proverena kodom (brojevi samo iz digesta, citati, bez budućnosti kao činjenice, ekavica) · tvrdnje se boduju"],
         ["organelles (same-event linker, surprise ranker) · three entities: Observer, Skeptic, Connector · a voice in ekavian Serbian", "every sentence checked by code (numbers only from the digest, citations, no future as fact, ekavica) · claims are scored"], True),
        ("express", "7 · Izraz", "7 · Expression",
         ["scena: monolog + puls (mapa kruži samo kad je instrument stvarno pročitan) · podaci po stanici i na mapi · četiri mape", "sajt objavljen na 10 min · dvojezično · ai_generated=true na svakoj misli"],
         ["the stage: monologue + pulse (the map rings only when an instrument was really read) · data per station and on the map · four maps", "site published every 10 min · bilingual · ai_generated=true on every thought"], False),
    ]
    w, d, h = 430, 200, 20   # plate width, depth, thickness
    x0, y0 = 560, 965        # front-left corner of the ground plate
    step = 98                # vertical distance between plates
    parts = []
    # knowledge column on the right: literature, papers, this document
    parts.append(f'<g class="know">')
    kx, ky = 1050, 610
    parts.append(f'<rect x="{kx}" y="{ky}" width="250" height="330" rx="4" class="knowbox"/>')
    parts.append(text(kx + 14, ky + 28, "Znanje pored slojeva", "Knowledge beside the layers", size=13, weight="600"))
    kitems = [("naučna literatura: 2024–26 u šest tema (urbani LLM agenti, senzori, halucinacije, ontologije)", "the literature: 2024–26 in six themes (urban LLM agents, sensing, hallucination, ontologies)"),
              ("radni dokument v1.1 · pre-paper za konferenciju", "working document v1.1 · pre-paper for the conference"),
              ("registar izvora S01–S214 · registar organa · ivični slučajevi · ispravke", "source register S01–S214 · organ register · edge cases · corrections"),
              ("dnevnik rada · mapa projekta · ovaj crtež", "the work log · the project map · this drawing")]
    yy = ky + 54
    for sr, en in kitems:
        for i, (line_sr, line_en) in enumerate(zip(_wrap(sr, 34), _wrap(en, 34))):
            parts.append(text(kx + 14, yy, line_sr, line_en, size=11.5, cls="dim"))
            yy += 15
        yy += 8
    parts.append('</g>')
    # plates
    tops = []
    for i, (key, tsr, ten, isr, ien, accent) in enumerate(layers):
        y = y0 - i * step
        poly, corners = plate(x0, y, w, d, h, ("accent" if accent else "plain") + " " + key)
        parts.append(f'<g class="layer {key}">{poly}</g>')
        tops.append((key, corners, tsr, ten, isr, ien, accent))
    # labels: to the left of each plate, aligned with its front-left corner
    for key, corners, tsr, ten, isr, ien, accent in tops:
        p3 = corners[3]
        lx, ly = p3[0] - 14, p3[1] + 6
        parts.append(text(lx, ly, tsr, ten, size=14, anchor="end", weight="600", cls=("accent-text" if accent else "")))
        yy = ly + 16
        for sr, en in zip(isr, ien):
            for line_sr, line_en in zip(_wrap(sr, 54), _wrap(en, 54)):
                parts.append(text(lx, yy, line_sr, line_en, size=10.5, anchor="end", cls="dim"))
                yy += 12.5
    # flows: arrows along the right edge from senses up through the gate to expression
    ax = x0 + w + 30
    parts.append(f'<g class="flow">')
    for i in range(2, len(layers) - 1):
        y_from = y0 - i * step - w * 0.5 + 10
        y_to = y0 - (i + 1) * step - w * 0.5 + 10 + h + 6
        parts.append(f'<line x1="{ax}" y1="{y_from:.0f}" x2="{ax}" y2="{y_to:.0f}" marker-end="url(#arrow)"/>')
    parts.append(text(ax + 10, y0 - 3 * step - w * 0.5 + 6, "prijem", "reception", size=11, cls="dim"))
    parts.append(text(ax + 10, y0 - 4 * step - w * 0.5 + 6, "dozvola", "permission", size=11, cls="dim"))
    parts.append(text(ax + 10, y0 - 5 * step - w * 0.5 + 6, "red, potvrda", "row, receipt", size=11, cls="dim"))
    parts.append(text(ax + 10, y0 - 6 * step - w * 0.5 + 6, "digest → misao", "digest → thought", size=11, cls="dim"))
    parts.append('</g>')
    # a note on the ground plate about what the map may not do
    parts.append(text(x0 + 40, y0 - 8, "mapa ne meri: ona samo kruži tamo gde je instrument stvarno pročitan", "the map measures nothing: it only rings where an instrument was actually read", size=10.5, cls="dim"))
    # title
    parts.insert(0, text(40, 44, "BEOPS — slojevi opservatorije, aksonometrija", "BEOPS — the layers of the observatory, axonometric", size=18, weight="600"))
    parts.insert(1, text(40, 66, "od tla na kome mapa stoji do glasa koji govori; ništa iznad ne postoji bez onoga ispod", "from the ground the map stands on to the voice that speaks; nothing above exists without what is below", size=12, cls="dim"))
    style = """
<style>
.top.plain{fill:var(--field,#FBFAF7);stroke:currentColor;stroke-width:1.1}
.side.plain,.side2.plain{fill:currentColor;fill-opacity:.08;stroke:currentColor;stroke-width:.8;stroke-opacity:.5}
.top.accent{fill:var(--signal,#D93A16);fill-opacity:.10;stroke:var(--signal,#D93A16);stroke-width:1.2}
.side.accent,.side2.accent{fill:var(--signal,#D93A16);fill-opacity:.22;stroke:var(--signal,#D93A16);stroke-width:.8;stroke-opacity:.6}
.top.legal{stroke-dasharray:4 3}
text{font-family:"Source Sans 3","Segoe UI",system-ui,sans-serif;fill:currentColor}
text.dim{fill:currentColor;fill-opacity:.62}
text.accent-text{fill:var(--signal,#D93A16)}
.flow line{stroke:currentColor;stroke-opacity:.5;stroke-width:1.2}
.knowbox{fill:none;stroke:currentColor;stroke-opacity:.35;stroke-dasharray:3 3}
</style>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" fill-opacity=".6"/></marker></defs>
"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" '
            f'aria-label="BEOPS layers, axonometric" class="layers-svg">{style}' + "".join(parts) + '</svg>')


def _wrap(s: str, n: int) -> list[str]:
    words, lines, cur = s.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > n and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    return lines


def main() -> int:
    out = OUT
    if "--out" in sys.argv:
        out = ROOT / sys.argv[sys.argv.index("--out") + 1] / "slojevi.svg"
    svg = build(counts())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
