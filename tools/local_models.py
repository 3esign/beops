"""Local-only model calls with one shared GPU lock and a deadline for the whole job."""
import contextlib
import functools
import ipaddress
import json
import os
import pathlib
import threading
import time
import urllib.request
from urllib.parse import urlsplit
from contracts import exclusive

_job = threading.local()
LOCK = pathlib.Path(os.environ.get("BEOPS_MODEL_LOCK", "C:/Svemir/data/locks/beops-model.lock"))


class ModelDeferred(TimeoutError):
    """No inference request was sent: wait for capacity without spending a retry."""


@contextlib.contextmanager
def model_slot(timeout):
    with contextlib.ExitStack() as stack:
        try:
            stack.enter_context(exclusive(LOCK, timeout=timeout))
        except TimeoutError as exc:
            raise ModelDeferred('local model capacity is busy') from exc
        yield


def endpoint(base):
    p = urlsplit(base)
    local = p.hostname == "localhost"
    try:
        local = local or ipaddress.ip_address(p.hostname or "").is_loopback
    except ValueError:
        pass
    if p.scheme != "http" or not local or p.username or p.password or p.path not in ("", "/"):
        raise ValueError("model endpoint must be local loopback HTTP")
    return base.rstrip("/")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("model endpoint redirect refused")


def request(base, path, payload=None, timeout=60, verify_model=True):
    base = endpoint(base)
    remaining = getattr(_job, "deadline", time.monotonic() + timeout) - time.monotonic()
    if remaining <= 0:
        raise ModelDeferred("model job deadline reached before request")
    with model_slot(min(30, max(0, remaining))):
        return _request_locked(base, path, payload, timeout, verify_model)


def _request_locked(base, path, payload, timeout, verify_model):
    remaining = getattr(_job, "deadline", time.monotonic() + timeout) - time.monotonic()
    if remaining <= 0:
        raise ModelDeferred("model job deadline reached before request")
    if payload and payload.get("model") and verify_model:
        model = payload["model"]
        if "cloud" in model.lower():
            raise ValueError("cloud model is not permitted")
        info = request(base, "/api/show", {"model": model}, min(remaining, 10), False)
        if any(info.get(k) for k in ("remote_host", "remote_model", "remote_url")):
            raise ValueError("model metadata identifies a remote model")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    remaining = getattr(_job, "deadline", time.monotonic() + timeout) - time.monotonic()
    if remaining <= 0:
        raise ModelDeferred("model job deadline reached before request")
    with opener.open(req, timeout=min(timeout, remaining)) as response:
        body = response.read(8 * 1024 * 1024 + 1)
        if len(body) > 8 * 1024 * 1024:
            raise ValueError("model response too large")
        return json.loads(body)


def budget(seconds):
    def decorate(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            previous = getattr(_job, "deadline", None)
            _job.deadline = min(previous or float("inf"), time.monotonic() + seconds)
            try:
                return fn(*args, **kwargs)
            finally:
                if previous is None:
                    del _job.deadline
                else:
                    _job.deadline = previous
        return wrapped
    return decorate
