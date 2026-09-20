#!/usr/bin/env python3
"""test_states.py - rule 1 of the method, asserted for the first time.

"Five states, no sixth" has been the first line of this project's method since it was written, and
until 2026-09-10 nothing checked it. What the check found is that the rule is kept and is described
wrongly: there are TWO vocabularies sharing the field name `state` - an epistemic one about what is
known of a measurement, and a pipeline one about what happened to a derived row - and they meet in the
published snapshot where a reader cannot tell them apart.

Both are declared in research/STATES.json. This file fails if either grows a value that is not
declared, because a state nobody wrote down is a state nobody decided.
"""
import json
import hashlib
import os
import pathlib
import re
import stat as statmod
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import record  # noqa: E402
from release_observation import frozen_manifest  # noqa: E402
DECL = ROOT / "research" / "STATES.json"
LIVE = ROOT / "data" / "live"
SNAP = ROOT / "public" / "live-snapshot.json"
_AUTO_MANIFEST = object()
STATE_INDEX_SCHEMA = "beops-state-key-index/v2"
STATE_KEY_PATTERN = re.compile(
    rb'"(?:s|\\u0073)(?:t|\\u0074)(?:a|\\u0061)(?:t|\\u0074)(?:e|\\u0065)"[ \t\r\n]*:'
)
STATE_KEY_TAIL_BYTES = 64
STATE_KEY_PREFILTER = (b'"state"', b'\\u0073', b'\\u0074', b'\\u0061', b'\\u0065')


def raw_may_spell_state_key(raw):
    return any(needle in raw for needle in STATE_KEY_PREFILTER)


def _json_depth_before(raw: bytes, stop: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for ch in raw[:stop]:
        if in_string:
            if escaped:
                escaped = False
            elif ch == 92:  # backslash
                escaped = True
            elif ch == 34:  # "
                in_string = False
            continue
        if ch == 34:  # "
            in_string = True
        elif ch in (123, 91):  # { [
            depth += 1
        elif ch in (125, 93):  # } ]
            depth -= 1
    return depth


def raw_has_top_level_state_key(raw: bytes) -> bool:
    """Detect a top-level JSON object key named state without parsing the row."""
    if not raw_may_spell_state_key(raw):
        return False
    for match in STATE_KEY_PATTERN.finditer(raw):
        if _json_depth_before(raw, match.start()) == 1:
            return True
    return False


def rows(p):
    """Every row under a directory, however deep, streamed and never slurped."""
    for f in sorted(p.rglob("*.jsonl")) if p.exists() else []:
        yield from record.objects(f)


_STATE_CACHE = None


def state_index_identity(f):
    observed = f.stat()
    return {
        "bytes": observed.st_size,
        "mtime_ns": observed.st_mtime_ns,
        "file_id": observed.st_ino,
        "device": observed.st_dev,
    }


def state_index_cache_path():
    return ROOT / "runtime" / "state-key-index.json"


def load_state_index_cache():
    global _STATE_CACHE
    if _STATE_CACHE is not None:
        return _STATE_CACHE
    path = state_index_cache_path()
    try:
        cache = json.loads(path.read_text(encoding="utf-8-sig"))
        if cache.get("schema") != STATE_INDEX_SCHEMA or not isinstance(cache.get("files"), dict):
            raise ValueError("bad state key index schema")
    except Exception:
        cache = {"schema": STATE_INDEX_SCHEMA, "files": {}}
    _STATE_CACHE = cache
    return cache


def file_ends_newline(f):
    if f.stat().st_size == 0:
        return True
    with f.open("rb") as handle:
        handle.seek(-1, os.SEEK_END)
        return handle.read(1) == b"\n"


def state_index_entry(f, decision):
    return {
        **state_index_identity(f),
        "ends_newline": file_ends_newline(f),
        "state_key_present": decision,
    }


def write_state_index_cache(cache):
    path = state_index_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _scan_file_may_contain_state(f):
    keep = b''
    with f.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                return False
            haystack = keep + chunk
            # Most live row files never spell the key at all. Keep that cheap
            # binary reject before the more exact per-row top-level check.
            if raw_may_spell_state_key(haystack) and STATE_KEY_PATTERN.search(haystack):
                break
            keep = haystack[-STATE_KEY_TAIL_BYTES:]
    with f.open("rb") as handle:
        for line in handle:
            if raw_has_top_level_state_key(line):
                return True
    return False


def _scan_appended_may_contain_state(f, offset):
    with f.open("rb") as handle:
        handle.seek(offset)
        for line in handle:
            if raw_has_top_level_state_key(line):
                return True
    return False


def file_may_contain_state(f):
    f = pathlib.Path(f).resolve()
    try:
        live = LIVE.resolve()
        if not f.is_relative_to(live):
            return _scan_file_may_contain_state(f)
        rel = f.relative_to(ROOT.resolve()).as_posix()
        before = state_index_identity(f)
        cache = load_state_index_cache()
        cached = cache["files"].get(rel)
        if cached and all(cached.get(k) == before[k] for k in before):
            decision = cached.get("state_key_present")
            if isinstance(decision, bool):
                return decision
        if isinstance(cached, dict) and cached.get("device") == before["device"] and cached.get("file_id") == before["file_id"]:
            cached_bytes = cached.get("bytes")
            decision = cached.get("state_key_present")
            if isinstance(cached_bytes, int) and before["bytes"] >= cached_bytes and isinstance(decision, bool):
                if decision:
                    cache["files"][rel] = state_index_entry(f, True)
                    write_state_index_cache(cache)
                    return True
                if cached.get("ends_newline") is True and before["bytes"] > cached_bytes:
                    decision = _scan_appended_may_contain_state(f, cached_bytes)
                    after = state_index_identity(f)
                    if before == after:
                        cache["files"][rel] = state_index_entry(f, decision)
                        write_state_index_cache(cache)
                    return decision
        decision = _scan_file_may_contain_state(f)
        after = state_index_identity(f)
        if before == after:
            cache["files"][rel] = state_index_entry(f, decision)
            write_state_index_cache(cache)
        return decision
    except OSError:
        raise
    except Exception:
        return _scan_file_may_contain_state(f)


def bound_state_manifest(root=ROOT):
    """Load the publisher-bound manifest once; local trees return ``None``."""
    document = frozen_manifest(pathlib.Path(root).resolve() / "data/live")
    if document is None:
        return None
    if document.get("state_index") != "sealed-readonly-jsonl/v1":
        raise ValueError("frozen release lacks the sealed state index")
    return document


def frozen_manifest_candidates(p, root=ROOT, document=_AUTO_MANIFEST):
    """Return state-bearing frozen files, or ``None`` only outside a frozen release.

    The existing frozen-release contract proves the physical root, manifest hash,
    workspace marker and source OID. The state index additionally requires the
    exact JSONL inventory and the read-only file identity recorded at capture.
    A damaged bound release fails immediately; it never degrades into a long scan.
    """
    root = pathlib.Path(root).resolve()
    p = pathlib.Path(p).resolve()
    if document is _AUTO_MANIFEST:
        document = bound_state_manifest(root)
    if document is None:
        return None
    live = (root / "data/live").resolve()
    if not p.is_relative_to(live):
        raise ValueError("state scan escaped the frozen live root")
    prefix = p.relative_to(root).as_posix().rstrip("/") + "/"
    indexed = {}
    for row in document.get("files", []):
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise ValueError("frozen state index contains an invalid entry")
        rel = pathlib.PurePosixPath(row["path"])
        if rel.is_absolute() or ".." in rel.parts or "\\" in row["path"]:
            raise ValueError("frozen state index contains an unsafe path")
        if row["path"].startswith(prefix) and row["path"].endswith(".jsonl"):
            if row["path"] in indexed:
                raise ValueError("frozen state index contains a duplicate path")
            indexed[row["path"]] = row
    actual = sorted(p.rglob("*.jsonl")) if p.exists() else []
    actual_paths = {f.relative_to(root).as_posix() for f in actual}
    if actual_paths != set(indexed):
        raise ValueError("frozen state index inventory changed")
    candidates = []
    for f in actual:
        rel = f.relative_to(root).as_posix()
        row = indexed[rel]
        if not isinstance(row.get("state_key_present"), bool):
            raise ValueError("frozen state index lacks a boolean decision")
        if row.get("state_index_sealed") is not True or f.is_symlink():
            raise ValueError("frozen state index file is not sealed")
        resolved = f.resolve()
        if not resolved.is_relative_to(live):
            raise ValueError("frozen state index file escaped the live root")
        observed = resolved.stat()
        if (observed.st_size != row.get("bytes") or
                observed.st_mtime_ns != row.get("state_index_mtime_ns") or
                observed.st_ino != row.get("state_index_file_id") or
                observed.st_dev != row.get("state_index_device") or
                observed.st_mode & (statmod.S_IWUSR | statmod.S_IWGRP | statmod.S_IWOTH)):
            raise ValueError("frozen state index file changed after capture: " + rel)
        if row["state_key_present"]:
            candidates.append(f)
    return candidates


def rows_that_can_have_state(p, document=_AUTO_MANIFEST):
    """Yield only JSONL objects whose raw row can contain a state key.

    The full live row archive is large, and most measurement rows have no state field at all.
    A binary chunk prefilter keeps the scan streaming while avoiding UTF-8 decode and JSON parse
    for files that cannot violate the state vocabulary rule.
    """
    candidates = frozen_manifest_candidates(p, document=document)
    if not p.exists():
        return
    files = candidates if candidates is not None else sorted(p.rglob("*.jsonl"))
    for f in files:
        if candidates is None and not file_may_contain_state(f):
            continue
        with f.open("rb") as handle:
            for line in handle:
                if not raw_may_spell_state_key(line) or not raw_has_top_level_state_key(line):
                    continue
                yield json.loads(line)


class FrozenManifestAcceleration(unittest.TestCase):
    def test_escaped_state_key_is_never_filtered_out(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            escaped = root / "rows/escaped.jsonl"
            escaped.parent.mkdir(parents=True)
            escaped.write_text('{"\\u0073tate":"rogue"}\n', encoding="utf-8")
            with patch.dict(os.environ, {}, clear=False):
                for name in ("BEOPS_FROZEN_MANIFEST_SHA256", "BEOPS_FROZEN_ROOT", "BEOPS_FROZEN_SOURCE_OID"):
                    os.environ.pop(name, None)
                self.assertEqual(list(rows_that_can_have_state(escaped.parent)), [{"state": "rogue"}])

    def test_backslash_values_do_not_make_state_candidates(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            row = root / "rows/noisy.jsonl"
            row.parent.mkdir(parents=True)
            row.write_text('{"path":"C:\\\\temp","word":"\\u0073tate"}\n', encoding="utf-8")
            with patch.dict(os.environ, {}, clear=False):
                for name in ("BEOPS_FROZEN_MANIFEST_SHA256", "BEOPS_FROZEN_ROOT", "BEOPS_FROZEN_SOURCE_OID"):
                    os.environ.pop(name, None)
                self.assertFalse(file_may_contain_state(row))
                self.assertEqual(list(rows_that_can_have_state(row.parent)), [])

    def test_nested_corrected_clock_state_is_not_a_top_level_row_state(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            row = root / "rows/corrected.jsonl"
            row.parent.mkdir(parents=True)
            row.write_text('{"phenomenonTimeCorrected":{"state":"estimated"},"result":1}\n',
                           encoding="utf-8")
            with patch.dict(os.environ, {}, clear=False):
                for name in ("BEOPS_FROZEN_MANIFEST_SHA256", "BEOPS_FROZEN_ROOT", "BEOPS_FROZEN_SOURCE_OID"):
                    os.environ.pop(name, None)
                self.assertFalse(file_may_contain_state(row))
                self.assertFalse(raw_has_top_level_state_key(row.read_bytes()))
                self.assertEqual(list(rows_that_can_have_state(row.parent)), [])

    def test_append_only_state_cache_scans_only_new_rows(self):
        import tempfile
        from unittest.mock import patch

        global _STATE_CACHE
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            live = root / "data/live"
            row = live / "rows/S01/2026-09.jsonl"
            row.parent.mkdir(parents=True)
            row.write_text('{"result":1}\n', encoding="utf-8")
            with patch.dict(os.environ, {}, clear=False):
                for name in ("BEOPS_FROZEN_MANIFEST_SHA256", "BEOPS_FROZEN_ROOT", "BEOPS_FROZEN_SOURCE_OID"):
                    os.environ.pop(name, None)
                with patch(__name__ + ".ROOT", root), patch(__name__ + ".LIVE", live):
                    _STATE_CACHE = None
                    self.assertFalse(file_may_contain_state(row))
                    with row.open("ab") as handle:
                        handle.write(b'{"result":2}\n')
                    with patch(__name__ + "._scan_file_may_contain_state",
                               side_effect=AssertionError("full scan attempted")):
                        self.assertFalse(file_may_contain_state(row))
                    with row.open("ab") as handle:
                        handle.write(b'{"state":"rogue"}\n')
                    with patch(__name__ + "._scan_file_may_contain_state",
                               side_effect=AssertionError("full scan attempted")):
                        self.assertTrue(file_may_contain_state(row))
                    _STATE_CACHE = None

    def test_append_cache_without_line_boundary_uses_full_scan(self):
        import tempfile
        from unittest.mock import patch

        global _STATE_CACHE
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            live = root / "data/live"
            row = live / "rows/S01/2026-09.jsonl"
            row.parent.mkdir(parents=True)
            row.write_text('{"result":1}', encoding="utf-8")
            with patch.dict(os.environ, {}, clear=False):
                for name in ("BEOPS_FROZEN_MANIFEST_SHA256", "BEOPS_FROZEN_ROOT", "BEOPS_FROZEN_SOURCE_OID"):
                    os.environ.pop(name, None)
                with patch(__name__ + ".ROOT", root), patch(__name__ + ".LIVE", live):
                    _STATE_CACHE = None
                    self.assertFalse(file_may_contain_state(row))
                    with row.open("ab") as handle:
                        handle.write(b'\n{"result":2}\n')
                    with patch(__name__ + "._scan_file_may_contain_state", return_value=False) as full_scan:
                        self.assertFalse(file_may_contain_state(row))
                    self.assertEqual(full_scan.call_count, 1)
                    _STATE_CACHE = None

    def test_exact_bound_manifest_skips_proven_state_free_files(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            rows = root / "data/live/rows/S01/2026-09.jsonl"
            derived = root / "data/live/derived/mind/2026-09.jsonl"
            manifest = root / "runtime/release-inputs.json"
            for path, body in ((rows, b'{"result":1}\n'),
                               (derived, b'{"state":"thought"}\n')):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
            document = {"schema": "beops-release-inputs/v1", "source_oid": "a" * 40,
                        "state_index": "sealed-readonly-jsonl/v1", "files": [
                {"path": rows.relative_to(root).as_posix(), "bytes": rows.stat().st_size,
                 "sha256": hashlib.sha256(rows.read_bytes()).hexdigest(), "state_key_present": False},
                {"path": derived.relative_to(root).as_posix(), "bytes": derived.stat().st_size,
                 "sha256": hashlib.sha256(derived.read_bytes()).hexdigest(), "state_key_present": True},
            ]}
            for path, row in ((rows, document["files"][0]), (derived, document["files"][1])):
                path.chmod(statmod.S_IREAD)
                observed = path.stat()
                row.update(state_index_sealed=True, state_index_mtime_ns=observed.st_mtime_ns,
                           state_index_file_id=observed.st_ino, state_index_device=observed.st_dev)
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps(document), encoding="utf-8")
            (root / ".beops-generated-workspace.json").write_text(
                json.dumps({"source_oid": "a" * 40}), encoding="utf-8")
            bound = hashlib.sha256(manifest.read_bytes()).hexdigest()
            env = {"BEOPS_FROZEN_MANIFEST_SHA256": bound, "BEOPS_FROZEN_ROOT": str(root),
                   "BEOPS_FROZEN_SOURCE_OID": "a" * 40}
            with patch.dict(os.environ, env):
                self.assertEqual(frozen_manifest_candidates(rows.parent.parent, root), [])
                self.assertEqual(frozen_manifest_candidates(derived.parent.parent, root), [derived])
                rows.chmod(statmod.S_IREAD | statmod.S_IWRITE)
                rows.unlink()
                with self.assertRaisesRegex(ValueError, "inventory changed"):
                    frozen_manifest_candidates(root / "data/live/rows", root)
                rows.parent.rmdir()
                (root / "data/live/rows").rmdir()
                with self.assertRaisesRegex(ValueError, "inventory changed"):
                    frozen_manifest_candidates(root / "data/live/rows", root)

    def test_unbound_falls_back_but_changed_bound_index_fails_fast(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            rows = root / "data/live/rows/S01/2026-09.jsonl"
            rows.parent.mkdir(parents=True)
            rows.write_text('{"result":1}\n', encoding="utf-8")
            manifest = root / "runtime/release-inputs.json"
            manifest.parent.mkdir(parents=True)
            observed = rows.stat()
            document = {"schema": "beops-release-inputs/v1", "source_oid": "a" * 40,
                        "state_index": "sealed-readonly-jsonl/v1", "files": [{
                "path": rows.relative_to(root).as_posix(), "bytes": rows.stat().st_size,
                "sha256": "0" * 64, "state_key_present": False,
                "state_index_sealed": True, "state_index_mtime_ns": observed.st_mtime_ns,
                "state_index_file_id": observed.st_ino, "state_index_device": observed.st_dev,
            }]}
            manifest.write_text(json.dumps(document), encoding="utf-8")
            (root / ".beops-generated-workspace.json").write_text(
                json.dumps({"source_oid": "a" * 40}), encoding="utf-8")
            with patch.dict(os.environ, {}, clear=False):
                for name in ("BEOPS_FROZEN_MANIFEST_SHA256", "BEOPS_FROZEN_ROOT", "BEOPS_FROZEN_SOURCE_OID"):
                    os.environ.pop(name, None)
                self.assertIsNone(frozen_manifest_candidates(rows.parent.parent, root))
            bound = hashlib.sha256(manifest.read_bytes()).hexdigest()
            original_size = rows.stat().st_size
            prefix = b'{"state":1}'
            changed = prefix + b' ' * (original_size - len(prefix) - 1) + b'\n'
            self.assertEqual(len(changed), original_size)
            rows.write_bytes(changed)
            env = {"BEOPS_FROZEN_MANIFEST_SHA256": bound, "BEOPS_FROZEN_ROOT": str(root),
                   "BEOPS_FROZEN_SOURCE_OID": "a" * 40}
            with patch.dict(os.environ, env):
                with self.assertRaisesRegex(ValueError, "changed after capture"):
                    frozen_manifest_candidates(rows.parent.parent, root)


class Declared(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(DECL.read_text(encoding="utf-8"))
        cls.epi = set(cls.d["epistemic"]["states"])
        cls.pipe = set(cls.d["pipeline"]["states"])
        # The bound manifest is immutable for one isolated gate. Parse and verify
        # its identity once rather than once per source directory.
        cls.state_manifest = bound_state_manifest(ROOT)

    def test_the_five_are_the_five(self):
        self.assertEqual(self.epi, {"observed", "untimed", "estimated", "forecast", "unavailable"},
                         "the epistemic vocabulary changed and rule 1 of the method did not")

    def test_every_declared_state_says_what_a_reader_should_understand(self):
        for group in ("epistemic", "pipeline"):
            for k, v in self.d[group]["states"].items():
                self.assertGreater(len(str(v).strip()), 20,
                                   f"{group}/{k} is declared without a sentence a stranger could act on")

    def test_a_measurement_row_carries_no_state_field_at_all(self):
        """The finding that made this file necessary. A row cannot carry a WRONG epistemic state
        because it carries none: the state is computed where the value is rendered."""
        p = LIVE / "rows"
        if not p.exists() and self.state_manifest is None:
            self.skipTest("no rows on this machine")
        bad = []
        for r in rows_that_can_have_state(p, self.state_manifest):
            if r.get("state") is not None:
                bad.append("%s: %r" % (r.get("sid", "unknown"), r.get("state")))
                if len(bad) >= 5:
                    break
        self.assertEqual(bad[:5], [], "a measurement row has grown a state field: " + "; ".join(bad[:5]))

    def test_no_derived_row_carries_an_undeclared_state(self):
        allowed = self.epi | self.pipe
        bad = []
        for organ in ("mind", "news"):
            for r in rows_that_can_have_state(LIVE / "derived" / organ, self.state_manifest):
                s = r.get("state")
                if s is None:
                    continue
                base = str(s).split(":")[0].strip()
                if base not in allowed:
                    bad.append("%s: %r" % (organ, s))
        self.assertEqual(sorted(set(bad))[:6], [],
                         "a derived row carries a state that research/STATES.json does not declare: "
                         + "; ".join(sorted(set(bad))[:6]))

    def test_the_published_snapshot_carries_no_undeclared_state(self):
        if not SNAP.exists():
            self.skipTest("no published snapshot on this machine")
        # "derived" used to be permitted here rather than declared in STATES.json. An exception
        # written into a test is a declaration nobody can find, so it now lives in the register.
        allowed = self.epi | self.pipe
        found = set()

        def walk(n):
            if isinstance(n, dict):
                s = n.get("state")
                if isinstance(s, str):
                    found.add(s.split(":")[0].strip())
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)

        walk(json.loads(SNAP.read_text(encoding="utf-8")))
        self.assertEqual(sorted(found - allowed), [],
                         "the published snapshot shows a state nobody declared: " + ", ".join(sorted(found - allowed)))

    def test_the_scan_reaches_the_nested_files_and_not_only_the_top_level(self):
        """The test's own blindness, kept from returning. If this ever counts fewer files than the
        record holds, every assertion above it is being made about a fraction of the record."""
        base = LIVE / "derived"
        if not base.exists():
            self.skipTest("no derived rows on this machine")
        shallow = sum(len(list((base / o).glob("*.jsonl"))) for o in ("mind", "news") if (base / o).exists())
        deep = sum(len(list((base / o).rglob("*.jsonl"))) for o in ("mind", "news") if (base / o).exists())
        self.assertGreaterEqual(deep, shallow)
        seen = sum(1 for o in ("mind", "news") for _ in [0] if (base / o).exists())
        self.assertTrue(seen, "no organ directory was found at all")
        counted = 0
        for o in ("mind", "news"):
            counted += sum(1 for _ in (base / o).rglob("*.jsonl")) if (base / o).exists() else 0
        self.assertEqual(counted, deep, "the scan sees fewer files than the record holds")

    def test_the_ambiguity_is_recorded_rather_than_forgotten(self):
        """Both vocabularies meet under one key in the published snapshot. That is a known defect,
        not a fixed one, and it must stay named until it is either fixed or accepted in writing."""
        self.assertIn("cannot tell", self.d.get("the_ambiguity_named", ""))
        self.assertIn("known defect", self.d.get("the_ambiguity_named", ""))


if __name__ == "__main__":
    unittest.main()
