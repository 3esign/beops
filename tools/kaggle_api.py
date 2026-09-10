#!/usr/bin/env python3
"""kaggle_api.py - the Kaggle API over the standard library, for the model bench only.

Why not the `kaggle` package: this repository has no third-party dependency and is not going to
acquire one for an HTTP call. Installing it here also failed twice on this body (MSYS2 python is
externally managed; then `rpds-py` needed a rust build that does not complete), so the dependency
would have cost more than it saved. The Kaggle API is HTTP with Basic authentication.

Where the credential lives, in this order: `KAGGLE_USERNAME` + `KAGGLE_KEY` in the environment; the
file Kaggle itself hands out (`~/.kaggle/kaggle.json`, what "Create New Token" downloads); or the
secret store this machine already keeps, named by `SVEMIR_SECRETS` (a file) or `SVEMIR_HOME` (whose
`data/secrets.json` is read). The last one exists so a key can arrive through the channel that already
holds every other key on this body, instead of being typed into this repository.

Nothing here ever WRITES a credential and nothing here ever prints one: `whoami()` returns the username
and the key's LENGTH, an HTTP error carries the server's message and never the header, and a store that
holds no pair is reported by the KEY NAMES that were looked for, never by what it contained.

WHAT LEAVES THE MACHINE, EXACTLY. The observatory's own rule is that collection, the record and the
permission evidence never leave this body, and that stays true: this tool is used by the model bench
and sends ONE thing - a pack of digests, which are numbered facts computed from public sources
(counts, spreads, ages, headline titles with their times). It sends no article body, no permission
capture, no receipt, no notebook, no personal data. `pack_is_clean()` refuses a pack that carries any
key outside that list, so the rule is enforced by code rather than by intention.
"""
from __future__ import annotations

import base64
import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://www.kaggle.com/api/v1"
UA = "beops-bench/1.0 (stdlib)"

# A digest pack may carry only these keys. Anything else is a leak, not a bench input.
PACK_KEYS = {"schema", "made_at", "window_hours", "digests", "as_of", "facts", "numbers", "clock",
             "sids", "sid_names", "headlines", "id", "sr", "en", "kind", "sid", "parameter", "lo",
             "hi", "hour", "station", "zone", "n", "delta", "age_min", "untimed", "people_thousands",
             "similarity", "outlet", "title", "t", "prompt", "entity", "role_en", "models"}


class NoCredential(RuntimeError):
    pass


# The shapes a store may use. A key is looked for BY NAME; nothing else in the file is touched, and
# no value from it is ever returned except the pair itself.
FLAT = (("username", "key"), ("kaggle_username", "kaggle_key"), ("KAGGLE_USERNAME", "KAGGLE_KEY"))
NESTED = ((("kaggle", "username"), ("kaggle", "key")),)


def _dig(d: dict, path: tuple):
    cur = d
    for step in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(step)
    return cur if isinstance(cur, str) else None


def _pair_from(d: dict) -> tuple[str, str] | None:
    for un, kn in FLAT:
        u, k = d.get(un), d.get(kn)
        if isinstance(u, str) and isinstance(k, str) and u.strip() and k.strip():
            return u.strip(), k.strip()
    for upath, kpath in NESTED:
        u, k = _dig(d, upath), _dig(d, kpath)
        if u and k and u.strip() and k.strip():
            return u.strip(), k.strip()
    return None


def stores() -> list[pathlib.Path]:
    """Every place a credential may be kept, in the order it is trusted. Paths only - this list is
    printable, and printing it reveals nothing."""
    out: list[pathlib.Path] = []
    cfg = os.environ.get("KAGGLE_CONFIG_DIR")
    if cfg:
        out.append(pathlib.Path(cfg) / "kaggle.json")
    out.append(pathlib.Path.home() / ".kaggle" / "kaggle.json")
    sec = os.environ.get("SVEMIR_SECRETS")
    if sec:
        out.append(pathlib.Path(sec))
    home = os.environ.get("SVEMIR_HOME")
    if home:
        out.append(pathlib.Path(home) / "data" / "secrets.json")
    return out


def credential() -> tuple[str, str]:
    """(username, key) from the environment, from the file Kaggle downloads, or from the secret store
    this machine already keeps. Never logged, never written, never returned anywhere but here."""
    u, k = os.environ.get("KAGGLE_USERNAME"), os.environ.get("KAGGLE_KEY")
    if u and k:
        return u.strip(), k.strip()
    looked: list[str] = []
    for p in stores():
        if not p.exists():
            continue
        looked.append(str(p))
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue                 # a store may hold anything at all; a bad parse is not our business
        if not isinstance(d, dict):
            continue
        got = _pair_from(d)
        if got:
            return got
    names = ", ".join(sorted({n for pair in FLAT for n in pair}
                             | {".".join(p) for up, kp in NESTED for p in (up, kp)}))
    if looked:
        raise NoCredential("a store exists but carries no Kaggle pair. These key names were looked "
                           "for: " + names + ". Add the pair to the store you already use, or set "
                           "KAGGLE_USERNAME and KAGGLE_KEY.")
    raise NoCredential("no Kaggle credential: set KAGGLE_USERNAME and KAGGLE_KEY, put the "
                       "kaggle.json that 'Create New Token' downloads in ~/.kaggle/, or point "
                       "SVEMIR_SECRETS at the store this machine already keeps.")


def _req(path: str, method: str = "GET", body: dict | None = None, timeout: int = 60) -> dict | list:
    u, k = credential()
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Authorization", "Basic " + base64.b64encode(f"{u}:{k}".encode()).decode())
    r.add_header("User-Agent", UA)
    if data is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300] if hasattr(e, "read") else ""
        # The key is in the header, never in the message: an error may be shown to anyone.
        raise RuntimeError(f"Kaggle said {e.code} for {method} {path}: {detail}") from None
    return json.loads(raw) if raw.strip() else {}


def whoami() -> dict:
    """Prove the credential works without revealing it. Returns the username and the key's LENGTH."""
    u, k = credential()
    out = {"username": u, "key_length": len(k), "key": "not shown",
           "stores_searched": [str(p) for p in stores()]}
    try:
        _req("/kernels/list?user=" + urllib.parse.quote(u) + "&pageSize=1")
        out["authenticated"] = True
    except RuntimeError as e:
        out["authenticated"] = False
        out["said"] = str(e)[:200]
    return out


def pack_is_clean(pack: dict) -> tuple[bool, list[str]]:
    """The bench may send digests and nothing else. Enforced here so the claim in the register is a
    property of the code, not a promise. Returns (ok, offending key paths)."""
    bad: list[str] = []
    # These carry DATA in their keys - a source id, a number, a time - so their keys are values and
    # are not checked against the schema. Their contents are strings either way.
    opaque = {"sids", "sid_names", "numbers", "clock"}

    def walk(o, path="", inside_opaque=False):
        if isinstance(o, dict):
            for kk, vv in o.items():
                if inside_opaque:
                    walk(vv, path + "." + str(kk), False)
                elif kk not in PACK_KEYS:
                    bad.append((path + "." + str(kk)).lstrip("."))
                else:
                    walk(vv, path + "." + str(kk), kk in opaque)
        elif isinstance(o, list):
            for i, vv in enumerate(o[:200]):
                walk(vv, f"{path}[{i}]", inside_opaque)
    walk(pack)
    return (not bad), sorted(set(bad))[:20]


def push(folder: str | pathlib.Path, timeout: int = 180) -> dict:
    """Push a kernel folder (kernel-metadata.json + the notebook or script beside it)."""
    folder = pathlib.Path(folder)
    meta_p = folder / "kernel-metadata.json"
    if not meta_p.exists():
        raise FileNotFoundError(f"{meta_p} is missing")
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    src_name = meta.get("code_file") or ""
    src = folder / src_name
    if not src.exists():
        raise FileNotFoundError(f"code_file {src_name!r} is not in {folder}")
    body = dict(meta)
    body["text"] = src.read_text(encoding="utf-8")
    return _req("/kernels/push", "POST", body, timeout=timeout)


def status(slug: str) -> dict:
    owner, _, name = slug.partition("/")
    return _req(f"/kernels/status?userName={urllib.parse.quote(owner)}&kernelSlug={urllib.parse.quote(name)}")


def wait(slug: str, minutes: int = 30, every: int = 30) -> dict:
    """Poll until the kernel stops running. Kaggle's free GPU sessions are long; this is a helper for
    an operator, not something a scheduled task should sit inside."""
    until = time.time() + minutes * 60
    last: dict = {}
    while time.time() < until:
        last = status(slug)
        if str(last.get("status", "")).lower() not in ("running", "queued"):
            return last
        time.sleep(every)
    return {**last, "timed_out_after_minutes": minutes}


def output(slug: str, dest: str | pathlib.Path) -> list[str]:
    """Download a finished kernel's output files into dest. Returns the paths written."""
    owner, _, name = slug.partition("/")
    res = _req(f"/kernels/output?userName={urllib.parse.quote(owner)}&kernelSlug={urllib.parse.quote(name)}")
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    written = []
    for f in (res.get("files") or []) if isinstance(res, dict) else []:
        url, fn = f.get("url"), f.get("fileName") or f.get("name")
        if not url or not fn:
            continue
        if not url.startswith("https://"):
            continue                      # never fetch a bench artefact over plain http
        r = urllib.request.Request(url)
        r.add_header("User-Agent", UA)
        with urllib.request.urlopen(r, timeout=300) as resp:
            (dest / fn).write_bytes(resp.read())
        written.append(str(dest / fn))
    return written


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "whoami"
    try:
        if cmd == "whoami":
            print(json.dumps(whoami(), ensure_ascii=False, indent=2))
        elif cmd == "check-pack":
            pack = json.loads(pathlib.Path(argv[2]).read_text(encoding="utf-8"))
            ok, bad = pack_is_clean(pack)
            print(json.dumps({"clean": ok, "keys_that_do_not_belong": bad}, ensure_ascii=False, indent=2))
            return 0 if ok else 2
        elif cmd == "push":
            print(json.dumps(push(argv[2]), ensure_ascii=False, indent=2))
        elif cmd == "status":
            print(json.dumps(status(argv[2]), ensure_ascii=False, indent=2))
        elif cmd == "wait":
            print(json.dumps(wait(argv[2], int(argv[3]) if len(argv) > 3 else 30), ensure_ascii=False, indent=2))
        elif cmd == "output":
            print(json.dumps(output(argv[2], argv[3]), ensure_ascii=False, indent=2))
        else:
            print(__doc__)
            return 1
    except NoCredential as e:
        print(json.dumps({"error": "no credential", "how": str(e)}, ensure_ascii=False, indent=2))
        return 3
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv))
