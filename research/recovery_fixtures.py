"""Offline permission evidence fixtures: actual files, hashes, routes and timestamps."""
import hashlib
import json
from urllib.parse import urlsplit


def permission(root, sid, url, at):
    stamp = at.strftime('%Y%m%dT%H%M%SZ')
    d = root / 'research' / 'evidence' / 'legal' / sid / stamp
    d.mkdir(parents=True, exist_ok=True)
    p = urlsplit(url)
    origin = p.scheme + '://' + p.netloc
    bodies = {'robots.txt': b'User-agent: *\nAllow: /\n',
              'robots_verdict.json': json.dumps({origin: {'paths': {url: {'allowed_for_us': True}}}}).encode()}
    files = {}
    for name, body in bodies.items():
        (d / name).write_bytes(body)
        files[name] = {'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body), 'status': 200,
                       'url': origin + '/robots.txt' if name == 'robots.txt' else None}
    raw = json.dumps({'sid': sid, 'captured_at_utc': stamp, 'user_agent': '*', 'urls': [url], 'files': files}).encode()
    (d / 'MANIFEST.json').write_bytes(raw)
    return {'sid': sid, 'captured_at_utc': stamp, 'allowed_for_us': True, 'capture_ok': True,
            'evidence_dir': d.relative_to(root).as_posix(), 'manifest_sha256': hashlib.sha256(raw).hexdigest(),
            'status_by_url': {url: 200}}
