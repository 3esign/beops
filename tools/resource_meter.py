"""Append-only, process-scoped resource receipts. No inference of watts or tokens."""
from __future__ import annotations

import contextvars
import json
import os
import pathlib
import sys
import time
import uuid
from datetime import datetime, timezone

_active = contextvars.ContextVar("beops_resource_meter", default=None)


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _memory():
    """Process lifetime high-water mark, not a sum and not cycle-only memory."""
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            class Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                    (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
                    "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
            if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
                return None
            return counters.PeakWorkingSetSize
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return value if sys.platform == "darwin" else value * 1024
    except (ImportError, OSError, AttributeError):
        return None


def _immutable(file, value):
    file.parent.mkdir(parents=True, exist_ok=True)
    temporary = file.with_name(file.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, file)
    finally:
        temporary.unlink(missing_ok=True)


def observe_http(body_bytes):
    meter = _active.get()
    if meter:
        meter.request_attempts += 1
        if isinstance(body_bytes, int) and not isinstance(body_bytes, bool) and body_bytes >= 0:
            meter.response_body_bytes += body_bytes
            meter.body_reports += 1


class Meter:
    """One invocation; interrupted processes retain a start with no fabricated finish."""
    def __init__(self, root, activity):
        self.root, self.activity = pathlib.Path(root), activity
        self.id, self.started_at = uuid.uuid4().hex, _now()
        self.directory = self.root / "runtime" / "resources" / "receipts"
        self.wall, self.cpu = time.perf_counter(), time.process_time()
        self.request_attempts = self.response_body_bytes = self.body_reports = 0
        self.outcome = "completed"
        self.record = {"schema": "beops-resource-cycle/v1", "id": self.id,
                       "activity": activity, "started_at": self.started_at,
                       "pid": os.getpid(), "runtime": "python", "phase": "start"}
        self._token = None

    def __enter__(self):
        _immutable(self.directory / (self.id + "-start.json"), self.record)
        self._token = _active.set(self)
        return self

    def __exit__(self, exc_type, exc, traceback):
        _active.reset(self._token)
        record = dict(self.record, phase="finish", finished_at=_now(),
            outcome="failed" if exc_type else self.outcome,
            wall_seconds=max(0, time.perf_counter() - self.wall),
            cpu_seconds=max(0, time.process_time() - self.cpu),
            peak_rss_bytes=_memory(),
            http={"request_attempts": self.request_attempts, "response_body_bytes": self.response_body_bytes,
                  "body_reports": self.body_reports, "unreported_bodies": self.request_attempts - self.body_reports},
            tokens={"input_tokens": None, "output_tokens": None, "cached_input_tokens": None,
                    "reported_calls": 0, "unreported_calls": None if self.activity in ("news", "mind") else 0,
                    "state": "not_instrumented" if self.activity in ("news", "mind") else "not_applicable"},
            electricity_wh=None, money=None,
            scope={"cpu": "current Python process only; excludes Node HTTP children and remote services",
                   "memory": "current process lifetime peak RSS; not cycle-only or additive",
                   "http": "transport.fetch attempts; decoded response body bytes only; excludes headers/TLS/wire overhead",
                   "electricity": "unavailable; no physical energy meter connected to this recorder",
                   "meter_overhead": "start receipt included; final receipt write excluded"})
        if exc_type:
            record["failure_type"] = exc_type.__name__
        try:
            _immutable(self.directory / (self.id + "-finish.json"), record)
        except OSError as error:
            print("resource_meter_finish_unavailable:" + type(error).__name__, file=sys.stderr)
        return False


def run_main(root, activity, main):
    meter = Meter(root, activity)
    try:
        meter.__enter__()
    except OSError as error:
        print("resource_meter_unavailable:" + type(error).__name__, file=sys.stderr)
        return main()
    try:
        result = main()
        meter.outcome = "completed" if result in (None, 0) else "failed"
    except BaseException:
        meter.__exit__(*sys.exc_info())
        raise
    meter.__exit__(None, None, None)
    return result
