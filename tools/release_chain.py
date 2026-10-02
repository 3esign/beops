"""Chain of confirmations: an append-only hash chain over publish outcomes.

Every publish cycle ends in a receipt; until now each receipt replaced the last,
so "what happened before this" required trusting logs scattered over the disk.
The chain gives the guard one cheap artefact instead of a disk scan: each link
commits to the previous link by hash, carries the release inventory Merkle root
(P1) and the cycle outcome, and can be verified end-to-end by reading one small
JSONL file. A broken hash is a STOP; a chain that lags the receipt is a WARN,
never silently trusted.

The chain is a confirmation layer, not a gate: appending must never decide
whether a publication happens, and an append failure must never invalidate a
receipt that is already true. Standard library only. ASCII output only.
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

LINK_SCHEMA = 'beops-chain-link/v1'
GENESIS = '0' * 64
CHAIN_REL = pathlib.Path('data') / 'live' / 'beops-chain.jsonl'
MANIFEST_LAST_REL = pathlib.Path('runtime') / 'release-inputs-last.json'

# The receipt fields a link commits to. published/tests_ok/site_verified/pushed
# distinguish "the world saw it" from "it only built"; why carries the failure
# cause so the chain alone can answer "what went wrong when".
OUTCOME_FIELDS = ('published', 'tests_ok', 'site_verified', 'pushed')


def link_hash(link):
    body = {k: v for k, v in link.items() if k != 'this'}
    canonical = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(canonical.encode('ascii')).hexdigest()


def read_chain(chain_path):
    if not chain_path.is_file():
        return []
    links = []
    with open(chain_path, encoding='utf-8-sig') as stream:
        for number, raw in enumerate(stream, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                links.append(json.loads(raw))
            except ValueError as exc:
                raise ValueError('line %d is not JSON: %s' % (number, exc))
    return links


def verify_links(links):
    """Return None when the chain is internally consistent, else the fault."""
    prev = GENESIS
    for index, link in enumerate(links):
        where = 'link %d (seq %s)' % (index + 1, link.get('seq'))
        if link.get('schema') != LINK_SCHEMA:
            return where + ': unknown schema %r' % link.get('schema')
        if link.get('seq') != index + 1:
            return where + ': expected seq %d' % (index + 1)
        if link.get('prev') != prev:
            return where + ': prev does not match the previous link hash'
        if link.get('this') != link_hash(link):
            return where + ': stored hash does not match the recomputed hash'
        prev = link['this']
    return None


def load_receipt(receipt_path):
    return json.loads(pathlib.Path(receipt_path).read_text(encoding='utf-8-sig'))


def outcome_of(receipt):
    outcome = {field: bool(receipt.get(field)) for field in OUTCOME_FIELDS}
    outcome['why'] = str(receipt.get('why') or '')[:300]
    return outcome


def inventory_root_for(root, receipt):
    """The Merkle root belongs in the link only when the last prepared manifest
    provably describes the same source commit as this receipt; anything else is
    an honest null, never a guess."""
    manifest_path = root / MANIFEST_LAST_REL
    if not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return None
    if manifest.get('source_oid') != receipt.get('source_head'):
        return None
    inventory = manifest.get('inventory') or {}
    return inventory.get('root')


def append_link(root, receipt_path):
    root = pathlib.Path(root)
    chain_path = root / CHAIN_REL
    receipt = load_receipt(receipt_path)
    if not receipt.get('at') or not receipt.get('source_head'):
        raise ValueError('receipt lacks at/source_head; refusing an unanchored link')
    links = read_chain(chain_path)
    fault = verify_links(links)
    if fault:
        # Never extend a broken chain: that would bury the tamper point under
        # fresh valid links. The guard reports the fault; a human decides.
        raise ValueError('chain is broken, not appending: ' + fault)
    head = links[-1] if links else None
    link = {
        'schema': LINK_SCHEMA,
        'seq': (head['seq'] + 1) if head else 1,
        'at': str(receipt['at']),
        'linked_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'prev': head['this'] if head else GENESIS,
        'source_head': str(receipt['source_head']),
        'inventory_root': inventory_root_for(root, receipt),
        'inputs_manifest_sha256': str(receipt.get('inputs_manifest_sha256') or '') or None,
        'outcome': outcome_of(receipt),
    }
    if head and head.get('at') == link['at'] and head.get('source_head') == link['source_head'] \
            and head.get('outcome') == link['outcome']:
        return {'appended': False, 'seq': head['seq'], 'this': head['this'],
                'why': 'head already covers this receipt'}
    link['this'] = link_hash(link)
    chain_path.parent.mkdir(parents=True, exist_ok=True)
    with open(chain_path, 'a', encoding='ascii', newline='\n') as stream:
        stream.write(json.dumps(link, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    return {'appended': True, 'seq': link['seq'], 'this': link['this']}


def verify(root, receipt_path=None):
    """Exit-style verdict: (0, ok) verified; (2, warn) behind or empty; (1, stop) broken."""
    root = pathlib.Path(root)
    chain_path = root / CHAIN_REL
    try:
        links = read_chain(chain_path)
    except ValueError as exc:
        return 1, 'chain unreadable: %s' % exc
    fault = verify_links(links)
    if fault:
        return 1, 'chain broken: ' + fault
    if not links:
        return 2, 'chain is empty: no cycle has been linked yet'
    head = links[-1]
    if receipt_path:
        try:
            receipt = load_receipt(receipt_path)
        except (OSError, ValueError) as exc:
            return 2, 'chain intact (%d links) but the receipt is unreadable: %s' % (len(links), type(exc).__name__)
        if head.get('at') != receipt.get('at') or head.get('source_head') != receipt.get('source_head') \
                or head.get('outcome') != outcome_of(receipt):
            return 2, 'chain intact (%d links) but behind the receipt: head at %s, receipt at %s' \
                % (len(links), head.get('at'), receipt.get('at'))
    return 0, 'chain verified: %d links, head seq %d at %s, published=%s' \
        % (len(links), head['seq'], head.get('at'), head.get('outcome', {}).get('published'))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('command', choices=('append', 'verify', 'head'))
    parser.add_argument('--root', default=str(pathlib.Path(__file__).resolve().parents[1]))
    parser.add_argument('--receipt', help='receipt path; append requires it, verify compares against it')
    args = parser.parse_args()
    root = pathlib.Path(args.root)
    if args.command == 'append':
        receipt = args.receipt or str(root / 'data' / 'live' / 'publish-receipt.json')
        try:
            result = append_link(root, receipt)
        except (OSError, ValueError) as exc:
            print('chain append failed: %s' % exc)
            return 1
        print(json.dumps(result))
        return 0
    if args.command == 'head':
        try:
            links = read_chain(root / CHAIN_REL)
        except ValueError as exc:
            print('chain unreadable: %s' % exc)
            return 1
        print(json.dumps(links[-1] if links else None))
        return 0
    code, message = verify(root, args.receipt)
    print(message)
    return code


if __name__ == '__main__':
    sys.exit(main())
