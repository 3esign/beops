"""Shared, read-only collector decisions. A blocked request is never a fetch failure."""
import pathlib
from datetime import timedelta
import permission_policy


def render_url(src, now):
    url = src['url']
    if '{from_iso}' in url:
        start = now - timedelta(seconds=int(src.get('window_seconds', 3 * 3600)))
        return url.replace('{from_iso}', start.strftime('%Y-%m-%dT%H:%M:%SZ'))
    return url


def pause_reason(live, sid):
    marker = pathlib.Path(live)/'receipts'/sid/'PAUSED'
    return (marker.read_text(encoding='utf-8').strip() or 'PAUSED marker present') if marker.exists() else None


def decision(root, live, src, entries, now):
    ok, reason = permission_policy.authorize(src['sid'], entries, root, render_url(src, now), now)
    if not ok:
        return 'blocked', reason
    paused = pause_reason(live, src['sid'])
    return ('paused', paused) if paused else ('allowed', reason)
