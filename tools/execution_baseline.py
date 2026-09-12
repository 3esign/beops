"""Capture one immutable, machine-readable Beops operational baseline.

The five health axes are reported independently. A late AI observation cannot
turn a healthy collector or verified publication red. Command transcripts are
stored inside the baseline directory with local user/cache paths redacted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone

from contracts import atomic_json, exclusive, json_object, json_rows, utc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def redact(value: str, root: pathlib.Path) -> str:
    replacements = [os.environ.get("USERPROFILE"), os.environ.get("TEMP"), os.environ.get("TMP")]
    clean = value
    for item in sorted({str(x) for x in replacements if x}, key=len, reverse=True):
        clean = clean.replace(item, "[local-user-path]").replace(item.replace("\\", "/"), "[local-user-path]")
    return clean.replace(str(root.resolve()), "[beops-root]").replace(str(root.resolve()).replace("\\", "/"), "[beops-root]")


def run_command(name: str, argv: list[str], root: pathlib.Path, timeout: int) -> dict:
    started = time.monotonic()
    try:
        process = subprocess.run(argv, cwd=root, capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", timeout=timeout, check=False,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return {"name": name, "argv": argv, "exit_code": process.returncode,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": process.stdout, "stderr": process.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"name": name, "argv": argv, "exit_code": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}


def parse_json_output(result: dict) -> dict | None:
    raw = result.get("stdout") or ""
    decoder = json.JSONDecoder()
    found, longest = None, -1
    for index, character in enumerate(raw):
        if character != "{":
            continue
        try:
            value, end = decoder.raw_decode(raw[index:])
        except ValueError:
            continue
        if isinstance(value, dict) and end > longest:
            found, longest = value, end
    return found


def row_inventory(root: pathlib.Path) -> dict:
    base = root / "data" / "live" / "rows"
    sources, total = {}, 0
    for directory in sorted(base.iterdir()) if base.exists() else []:
        if not directory.is_dir():
            continue
        rows = files = size = 0
        for path in sorted(directory.glob("*.jsonl")):
            stats = {}
            rows += sum(1 for _ in json_rows(path, stats))
            files += 1
            size += path.stat().st_size
        sources[directory.name] = {"rows": rows, "files": files, "bytes": size}
        total += rows
    return {"rows": total, "sources": sources}


def ai_inventory(root: pathlib.Path) -> dict:
    base = root / "runtime" / "ai-feed"
    states, reasons = Counter(), Counter()
    finishes = {}
    for path in sorted((base / "receipts").glob("*-finish.json")):
        row = json_object(path)
        finishes[row.get("id")] = row
        states[str(row.get("state") or "unknown")] += 1
        if row.get("reason"):
            reasons[str(row["reason"])] += 1
    responses = {path.stem for path in (base / "responses").glob("*.json")}
    entries = {path.stem for path in (base / "entries").glob("*.json")}
    evaluable = responses & set(finishes)
    accepted = {key for key in evaluable if finishes[key].get("state") == "accepted" and key in entries}
    rejected = {key for key in evaluable if finishes[key].get("state") == "failed" and key not in entries}
    return {
        "terminal_attempts": len(finishes),
        "states": dict(sorted(states.items())),
        "reasons": dict(sorted(reasons.items())),
        "responses": len(responses),
        "entries": len(entries),
        "evaluable_responses": len(accepted | rejected),
        "accepted_responses": len(accepted),
        "rejected_responses": len(rejected),
        "operational_without_response": len(finishes) - len(evaluable),
        "orphan_responses": len(responses - set(finishes)),
    }


def snapshot_inventory(root: pathlib.Path, now: datetime) -> dict:
    path = root / "public" / "live-snapshot.json"
    if not path.exists():
        return {"present": False}
    doc = json_object(path)
    as_of = utc(doc.get("as_of"))
    return {
        "present": True,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "as_of": doc.get("as_of"),
        "age_minutes": round((now - as_of).total_seconds() / 60, 2) if as_of else None,
        "sources": len(doc.get("sources") or []),
    }


def check_state(checks: list[dict], name: str) -> str:
    item = next((row for row in checks if row.get("check") == name), None)
    return str((item or {}).get("state") or "unknown")


def summarize_axes(commands: dict[str, dict], watch: dict | None, task_audit: dict | None) -> dict:
    watch = watch or {}
    checks = watch.get("checks") or []
    source_checks = [row for row in checks if str(row.get("check", "")).startswith("source ")]
    hard_source_states = sorted({row.get("state") for row in source_checks
                                 if row.get("state") not in {"ok", "blocked", "paused"}})
    policy_blocks = sum(row.get("state") == "blocked" for row in source_checks)
    processing_ok = all(commands.get(name, {}).get("exit_code") == 0 for name in ("tests", "doctor"))
    guard_text = commands.get("guard", {}).get("stdout") or ""
    guard_match = re.search(r"verdict:\s*(\w+)", guard_text, re.I)
    guard_verdict = guard_match.group(1).lower() if guard_match else "unknown"
    site = parse_json_output(commands.get("site", {}))
    site_ok = commands.get("site", {}).get("exit_code") == 0 and bool((site or {}).get("ok"))
    audit_ok = bool(task_audit and task_audit.get("expected") == 9
                    and task_audit.get("ok", 0) + task_audit.get("alias", 0) == 9
                    and task_audit.get("drift") == 0 and commands.get("tasks", {}).get("exit_code") == 0)
    return {
        "collection": {
            "state": "ok" if check_state(checks, "rows") == "ok" and not hard_source_states else "failed",
            "policy_blocked_sources": policy_blocks,
            "hard_source_states": hard_source_states,
        },
        "evidence_permission": {"state": "ok" if guard_verdict in {"ok", "warn"} else "failed",
                                "guard_verdict": guard_verdict},
        "processing": {"state": "ok" if processing_ok else "failed"},
        "publishing": {"state": "ok" if site_ok and check_state(checks, "published") == "ok" else "failed",
                       "site_verdict": (site or {}).get("operational_verdict")},
        "ai": {"state": check_state(checks, "AI observations")},
        "scheduler": {"state": "ok" if audit_ok else "failed",
                      "matching": (task_audit or {}).get("ok", 0) + (task_audit or {}).get("alias", 0),
                      "aliases": (task_audit or {}).get("alias"), "expected": (task_audit or {}).get("expected")},
    }


def git(root: pathlib.Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", check=True,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return result.stdout.strip()


def capture(root: pathlib.Path, output: pathlib.Path | None = None) -> dict:
    root = pathlib.Path(os.path.abspath(root))
    started_at = datetime.now(timezone.utc)
    stamp = started_at.strftime("%Y%m%dT%H%M%SZ")
    output = pathlib.Path(os.path.abspath(output or root / "research" / "_trail" / f"execution-baseline-{stamp}"))
    if output.exists():
        raise FileExistsError("baseline output already exists; preserve it")
    head_before = git(root, "rev-parse", "HEAD")
    status_before = git(root, "status", "--porcelain", "--untracked-files=all")
    npm = "npm.cmd" if os.name == "nt" else "npm"
    powershell = "powershell.exe" if os.name == "nt" else "pwsh"
    specs = [
        ("tests", [npm, "test"], 125),
        ("doctor", [npm, "run", "doctor"], 25),
        ("tasks", [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "tools/audit_tasks.ps1", "-Json"], 30),
        ("guard", [sys.executable, "-X", "utf8", "-B", "tools/guard.py", "--dry"], 45),
        ("watch", [sys.executable, "-X", "utf8", "-B", "tools/watchman.py", "--dry", "--json"], 45),
        ("site", [npm, "run", "test:site"], 120),
    ]
    commands = {name: run_command(name, argv, root, timeout) for name, argv, timeout in specs}
    captured_at = datetime.now(timezone.utc)
    watch = parse_json_output(commands["watch"])
    task_audit = parse_json_output(commands["tasks"])
    axes = summarize_axes(commands, watch, task_audit)
    head_after = git(root, "rev-parse", "HEAD")
    status_after = git(root, "status", "--porcelain", "--untracked-files=all")
    required = ("collection", "evidence_permission", "processing", "publishing", "scheduler")
    core_pass = all(axes[name]["state"] == "ok" for name in required)
    source_clean = not status_before.strip()
    same_head = head_before == head_after
    gate = "pass" if core_pass and source_clean and same_head else "blocked"
    ai_state = axes["ai"]["state"]
    if gate == "pass" and ai_state != "ok":
        gate = "pass_with_ai_warning"
    data = {
        "schema": "beops-execution-baseline/v1",
        "started_at": started_at.isoformat(),
        "at": captured_at.isoformat(),
        "head": head_before,
        "head_after": head_after,
        "same_head": same_head,
        "source_clean_before_capture": source_clean,
        "worktree_before": status_before.splitlines(),
        "worktree_after_commands": status_after.splitlines(),
        "gate": gate,
        "axes": axes,
        "snapshot": snapshot_inventory(root, captured_at),
        "rows": row_inventory(root),
        "ai": ai_inventory(root),
        "disk": {key: value for key, value in zip(("total", "used", "free"), shutil.disk_usage(root))},
        "commands": {},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = pathlib.Path(tempfile.mkdtemp(prefix=".execution-baseline-", dir=output.parent))
    try:
        for name, result in commands.items():
            transcript = redact((result.get("stdout") or "") + ("\n[stderr]\n" + result["stderr"] if result.get("stderr") else ""), root)
            filename = f"{name}.txt"
            (temporary / filename).write_text(transcript, encoding="utf-8", newline="\n")
            data["commands"][name] = {
                "exit_code": result["exit_code"], "timed_out": result["timed_out"],
                "duration_seconds": result["duration_seconds"], "transcript": filename,
                "transcript_sha256": sha256_bytes(transcript.encode("utf-8")),
            }
        atomic_json(temporary / "baseline.json", data)
        baseline_hash = sha256_file(temporary / "baseline.json")
        os.replace(temporary, output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    status_path = root / "research" / "_trail" / "execution-status.jsonl"
    status_row = {"schema": "beops-execution-status/v1", "at": data["at"], "head": head_before,
                  "gate": gate, "axes": axes, "baseline": output.relative_to(root).as_posix(),
                  "baseline_sha256": baseline_hash}
    with exclusive(root / "runtime" / "execution-status.lock"):
        with status_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(status_row, ensure_ascii=False, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    return {"output": str(output), "baseline_sha256": baseline_hash, "gate": gate,
            "head": head_before, "axes": axes, "ai": data["ai"], "rows": data["rows"]["rows"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", nargs="?")
    parser.add_argument("--root", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = capture(pathlib.Path(args.root), pathlib.Path(args.output) if args.output else None)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
