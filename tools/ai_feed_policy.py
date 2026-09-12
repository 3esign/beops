"""Read-only permission projection for the AI packet; uses the collector's exact policy."""
import json
import pathlib
import sys
from datetime import datetime, timezone, timedelta
import permission_policy


def allowed(root, now):
    root = pathlib.Path(root)
    ledger = permission_policy.latest(root / 'research/08-provenance/LEDGER.jsonl')
    collectors = json.loads((root / 'research/COLLECTORS.json').read_text(encoding='utf-8'))
    result = []
    for source in collectors['sources']:
        if not source.get('enabled', True):
            continue
        url = source['url'].replace('{from_iso}', (now - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ'))
        ok, _ = permission_policy.authorize(source['sid'], ledger, root, url, now)
        if ok:
            result.append(source['sid'])
    return result


if __name__ == '__main__':
    print(json.dumps(allowed(sys.argv[1], datetime.fromisoformat(sys.argv[2].replace('Z', '+00:00')))))
