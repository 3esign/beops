#!/usr/bin/env python3
"""
Beops research/ restructure with link rewriting.

Principle applied:
  - DOCUMENTS (.md) move into numbered subfolders.
  - CODE (.py, .ps1) and REGISTRIES (.json) stay flat in research/, because
    `tools/test-research.js` discovers tests with `unittest discover -s research
    -p test_*.py`, `audit_model_cards.py` reads MODEL_CANDIDATES.json from its own
    directory, and `observe_10k.py` writes into research/observations. Moving those
    would break the test chain and the live recorder for no navigational gain.
  - EVIDENCE folders (observations/, evidence/) never move.

Every local markdown link in the whole project is resolved against its host file's
OLD location, mapped, and rewritten relative to the host's NEW location. Anything
that cannot be resolved is reported, not silently left.
"""
import os, re, sys, shutil

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."

# old (root-relative, posix) -> new (root-relative, posix)
MOVES = {}

def add(folder, names):
    for n in names:
        MOVES[f"research/{n}"] = f"research/{folder}/{n}"

add("01-programme", [
    "RADNI_PROGRAM.md",
    "PLAN_CULA_MODELI_2026-09-05.md",
    "PULSE_RESEARCH_PROTOCOL.md",
    "ZONE_I_POVEZIVANJE.md",
    "PRETRAGA_KEYWORDS_2026-09-05.md",
])
add("02-senses", [
    "ZIVI_OTISAK_BEOGRADA.md",
    "VISE_DOMENA_2026-09-05.md",
    "NOVA_CULA_I_USPAVANA_TEHNOLOGIJA_2026-09-05.md",
    "NOVA_CULA_RUNDA2_2026-09-05.md",
    "ZAHTEVI_JP_AGREGATI.md",
    "DRUGI_GRADOVI_CULA_I_ORGANI.md",
])
add("03-models", [
    "KATALOG_MODELA_I_PROVAJDERA_2026-09-05.md",
    "MODELI_I_LITERATURA.md",
])
add("04-bibliography", [
    "BIBLIOGRAPHY_2026-09-05.md",
    "BIBLIOGRAFIJA_2026-09-05.md",
])
add("05-design", [
    "UI_CONCEPTS_AND_COMPOSITION.md",
])
add("06-paper", [
    "rad_draft.md",
])
add("_trail", [
    "INTAKE_2026-09-05.md",
    "PLAN_IZVRSENJA_2026-09-05.md",
    "AUDIT_V1_2026-09-05.md",
    "AUDIT_V2_2026-09-05.md",
    "MERGE_2026-09-05.md",
    "revise-1788619136912.md",
    "PRESEK_2026-09-05_POPODNE.md",
    "VERIFICATION_2026-09-05.md",
    "PAZARAC_TRANSFER_AUDIT.md",
])

# whole directories that move
DIR_MOVES = {
    "research/studies": "research/05-design/studies",
    "research/conference": "research/06-paper/conference",
}

LINK = re.compile(r'\]\(([^)\s]+)\)')

def norm(p):
    return os.path.normpath(p).replace(os.sep, "/")

def map_target(old_rootrel):
    """Map a root-relative path through file moves and directory moves."""
    if old_rootrel in MOVES:
        return MOVES[old_rootrel]
    for od, nd in DIR_MOVES.items():
        if old_rootrel == od or old_rootrel.startswith(od + "/"):
            return nd + old_rootrel[len(od):]
    return old_rootrel

def do_moves(dry):
    done = []
    for old, new in sorted(MOVES.items()):
        src, dst = os.path.join(ROOT, old), os.path.join(ROOT, new)
        if not os.path.exists(src):
            print(f"  SKIP missing: {old}")
            continue
        if not dry:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
        done.append((old, new))
    for od, nd in sorted(DIR_MOVES.items()):
        src, dst = os.path.join(ROOT, od), os.path.join(ROOT, nd)
        if not os.path.isdir(src):
            print(f"  SKIP missing dir: {od}")
            continue
        if not dry:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
        done.append((od + "/", nd + "/"))
    return done

def all_md():
    out = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in (".git", "node_modules", "archive", "runtime")]
        for f in fns:
            if f.endswith(".md"):
                out.append(norm(os.path.relpath(os.path.join(dp, f), ROOT)))
    return sorted(out)

def rewrite(dry):
    """Rewrite links BEFORE anything moves.

    Each file is read at its OLD location; every local link is resolved against the
    OLD tree (so existence can actually be checked) and re-expressed relative to the
    host's NEW location. Files are moved afterwards, carrying correct links with them.
    Doing this in the other order silently leaves every moved file's links untouched,
    because after the move a file's old and new directory look identical.
    """
    hosts = {h: map_target(h) for h in all_md()}

    changed, unresolved, kept = 0, [], 0
    for host_old, host_new in sorted(hosts.items()):
        path = os.path.join(ROOT, host_old)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        old_dir = os.path.dirname(host_old)
        new_dir = os.path.dirname(host_new)

        def sub(m):
            nonlocal changed, kept
            raw = m.group(1)
            if re.match(r'^[a-zA-Z]+:', raw) or raw.startswith("#") or raw.startswith("//"):
                return m.group(0)
            link, frag = (raw.split("#", 1) + [""])[:2]
            frag = "#" + frag if frag else ""
            trailing = "/" if link.endswith("/") else ""
            target_old = norm(os.path.join(old_dir, link)) if old_dir else norm(link)
            target_old = target_old.rstrip("/")
            if not (os.path.exists(os.path.join(ROOT, target_old))):
                unresolved.append((host_old, raw, target_old))
                return m.group(0)
            target_new = map_target(target_old)
            rel = os.path.relpath(os.path.join(ROOT, target_new),
                                  os.path.join(ROOT, new_dir) if new_dir else ROOT)
            rel = rel.replace(os.sep, "/") + trailing + frag
            if rel == raw:
                kept += 1
                return m.group(0)
            changed += 1
            return "](" + rel + ")"

        new_text = LINK.sub(sub, text)
        if new_text != text and not dry:
            open(path, "w", encoding="utf-8").write(new_text)
    return changed, kept, unresolved

if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    print("DRY RUN" if dry else "APPLYING")
    changed, kept, unresolved = rewrite(dry)     # links first, while the old tree still stands
    moved = do_moves(dry)                        # then move, carrying correct links
    print(f"moves: {len(moved)}")
    print(f"links rewritten: {changed}   links unchanged: {kept}")
    if unresolved:
        print("UNRESOLVED (target does not exist in the tree; left untouched):")
        for h, l, t in unresolved:
            print(f"  {h}  ->  {l}   (mapped to {t})")
    else:
        print("every local link resolves after the move")
