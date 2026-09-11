"""Bounded HTTP through the shared incognito header boundary. Redirects fail closed."""
import base64
import json
import os
import pathlib
import subprocess
from functools import lru_cache


@lru_cache(maxsize=128)
def user_agent(url):
    """Read the actual workspace header choice without sending a request."""
    p = subprocess.run(['node', str(pathlib.Path(__file__).with_name('net_fetch.js'))],
        input=json.dumps({'url': url, 'headers_only': True}), capture_output=True,
        text=True, encoding='utf-8', timeout=10, check=True,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return json.loads(p.stdout)['user_agent']


def fetch(url, timeout_s=60, max_bytes=2 * 1024 * 1024):
    root = pathlib.Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    bundle = root / "data" / "ca-bundle-windows.pem"
    if bundle.exists():
        env["NODE_EXTRA_CA_CERTS"] = str(bundle)
    try:
        p = subprocess.run(["node", str(root / "tools" / "net_fetch.js")],
            input=json.dumps({"url": url, "timeout_ms": min(timeout_s, 120) * 1000, "max_bytes": max_bytes}),
            capture_output=True, text=True, encoding="utf-8", timeout=min(timeout_s, 120) + 10, env=env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        res = json.loads(p.stdout)
        if res.get("body") is not None:
            res["body"] = base64.b64decode(res["body"], validate=True)
        return res
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {"status": None, "headers": {}, "body": None, "error": str(exc)[:240], "transport": "incognito/failed"}
