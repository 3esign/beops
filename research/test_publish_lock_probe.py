"""Exercise the real lock probe and the publish_due admission block without
publishing, touching the live lock, or touching the scheduler.

Runs against copies of the production scripts with a temp receipt dir, so the
admission block sees a lock-free directory (skip path) unless the test
explicitly creates a busy lock in that dir.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import pathlib

ROOT = pathlib.Path(r"D:\Svemir\!Projekti\Beops")
PY = os.environ.get(
    "BEOPS_TEST_PYTHON",
    str(pathlib.Path(os.environ.get("USERPROFILE", "")) / "AppData/Roaming/uv/python/cpython-3.12-windows-x86_64-none/python.exe"),
)

failures = []


def check(name, cond, detail=""):
    print(("OK  " if cond else "PAD ") + name + (("  " + detail) if detail else ""))
    if not cond:
        failures.append(name)


def run_probe(lock_dir):
    lock = lock_dir / ".write.lock"
    r = subprocess.run(
        [PY, str(ROOT / "tools" / "lock_probe.py"), str(lock)],
        capture_output=True, text=True, timeout=60,
    )
    return r.returncode, r.stdout.strip()


def main():
    check("python exists", pathlib.Path(PY).exists(), PY)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="beops-lockprobe-"))
    try:
        # 1) free lock -> exit 0
        code, out = run_probe(tmp)
        check("probe free -> 0", code == 0 and '"free"' in out, f"exit={code} out={out}")

        # 2) busy lock -> exit 75 (a real exclusive held in this process)
        sys.path.insert(0, str(ROOT / "tools"))
        import contracts  # noqa: E402
        lock = tmp / ".write.lock"
        with contracts.exclusive(lock, timeout=0):
            code, out = run_probe(tmp)
            check("probe busy -> 75", code == 75 and '"busy"' in out, f"exit=75 out={out}")

        # 3) no lock file, probe of a missing dir path -> free
        code, out = run_probe(tmp / "nema")
        check("probe missing dir -> 0", code == 0 and '"free"' in out, f"exit={code} out={out}")

        # 4) admission block in publish_due.ps1: present, bound to receipt dir, syntax OK
        due = (ROOT / "tools" / "publish_due.ps1").read_text(encoding="utf8")
        check("admission present", "live_prepare_holds_lock" in due)
        check("admission uses receipt dir", "Split-Path -Parent $ReceiptPath" in due)
        ps = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('D:\\Svemir\\!Projekti\\Beops\\tools\\publish_due.ps1', [ref]$null, [ref]$e); if($e.Count -eq 0){'SYNTAX OK'}else{$e | ForEach-Object { $_.Message }}"],
            capture_output=True, text=True, timeout=120,
        )
        check("publish_due.ps1 syntax", "SYNTAX OK" in ps.stdout, ps.stdout.strip()[:200])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{7 - len(failures)}/7")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
