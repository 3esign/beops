"""Replay stored gauge captures and repair unverifiable model claims without rewriting evidence."""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import pathlib
from contracts import content_id, exclusive, json_rows, utc
import collect_daemon as collector
import organ_mind as mind
import claim_evidence

ROOT=pathlib.Path(__file__).resolve().parents[1]


def headlines(root=ROOT, apply=False):
    root=pathlib.Path(root).resolve();live=root/'data/live';ledger=live/'corrections.jsonl'
    cfg=json.loads((root/'research/COLLECTORS.json').read_text(encoding='utf-8'))
    already={r['original_id'] for r in json_rows(ledger)};entries=[];unresolved=[]
    for src in cfg['sources']:
        if src.get('parser') not in ('rss','city_listing'):continue
        candidates=[r for f in (live/'rows'/src['sid']).glob('*.jsonl') for r in json_rows(f)
                    if isinstance(r.get('result'),str) and len(r['result'])==200 and (r.get('row_id') or content_id(r)) not in already]
        if not candidates:continue
        receipts=[json.loads(p.read_text(encoding='utf-8')) for p in (live/'receipts'/src['sid']).glob('*.json')]
        raw={r.get('raw_sha256'):r.get('raw_file') for r in receipts if r.get('raw_file')}
        for row in candidates:
            oid=row.get('row_id') or content_id(row);ref=raw.get(row.get('raw_sha256'))
            if not ref:unresolved.append({'id':oid,'reason':'raw capture absent'});continue
            path=(root/ref).resolve()
            if not path.is_relative_to(root):raise ValueError('raw path outside project')
            body=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
            if hashlib.sha256(body).hexdigest()!=row['raw_sha256']:raise ValueError('raw payload hash mismatch')
            match=next((r for r in collector.PARSERS[src['parser']](body,utc(row['receivedTime']),src) if r['dedupe_key']==row['dedupe_key']),None)
            if match and len(match.get('result') or '')>200 and match['result'].startswith(row['result']):
                entry={'schema':'beops-row-correction/v1','at':dt.datetime.now(dt.timezone.utc).isoformat(),'sid':src['sid'],'original_id':oid,'raw_sha256':row['raw_sha256'],'fields':{'result':match['result']},'reason':'Restore full original headline from verified raw capture; old parser cut at 200 characters'}
                entry['id']=content_id(entry);entries.append(entry)
    if apply and entries:
        with exclusive(live/'.write.lock'):
            current={r['original_id'] for r in json_rows(ledger)}
            with ledger.open('a',encoding='utf-8') as out:
                for row in entries:
                    if row['original_id'] not in current:out.write(json.dumps(row,ensure_ascii=False)+'\n')
    return {'restored_full_titles':len(entries),'unresolved':unresolved,'applied':bool(apply)}


def gauges(root=ROOT, apply=False):
    root=pathlib.Path(root).resolve();live=root/'data/live';cfg=json.loads((root/'research/COLLECTORS.json').read_text(encoding='utf-8'))
    entries=[];unresolved=[];ledger=live/'corrections.jsonl';already={r['original_id'] for r in json_rows(ledger)}
    for src in cfg['sources']:
        if src.get('parser')!='rhmz_gauges':continue
        raw={}
        for p in (live/'receipts'/src['sid']).glob('*.json'):
            r=json.loads(p.read_text(encoding='utf-8'))
            if r.get('raw_sha256') and r.get('raw_file'):raw[r['raw_sha256']]=r['raw_file']
        parsed={}
        for f in (live/'rows'/src['sid']).glob('*.jsonl'):
            for row in json_rows(f):
                oid=row.get('row_id') or content_id(row)
                if oid in already:continue
                digest=row.get('raw_sha256');ref=raw.get(digest)
                if not ref:unresolved.append({'id':oid,'reason':'raw receipt not found'});continue
                if digest not in parsed:
                    p=(root/ref).resolve()
                    if not p.is_relative_to(root):raise ValueError('raw path outside project')
                    body=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
                    if hashlib.sha256(body).hexdigest()!=digest:raise ValueError('raw payload hash mismatch')
                    parsed[digest]={r['dedupe_key']:r for r in collector.parse_rhmz_gauges(body,utc(row['receivedTime']),src)}
                new=parsed[digest].get(row.get('dedupe_key'))
                if not new:unresolved.append({'id':oid,'reason':'row not present in replay'});continue
                fields={k:new[k] for k in ('result','resultQuality') if new[k]!=row.get(k)}
                if fields:
                    entry={'schema':'beops-row-correction/v1','at':dt.datetime.now(dt.timezone.utc).isoformat(),'sid':src['sid'],'original_id':oid,'raw_sha256':digest,'fields':fields,'reason':'B03: preserve empty gauge measurement cells; replay verified original raw bytes'}
                    entry['id']=content_id(entry);entries.append(entry)
    if apply and entries:
        with exclusive(live/'.write.lock'):
            current={r['original_id'] for r in json_rows(ledger)}
            with ledger.open('a',encoding='utf-8') as out:
                for r in entries:
                    if r['original_id'] not in current:out.write(json.dumps(r,ensure_ascii=False)+'\n')
    return {'planned_corrections':len(entries),'applied':bool(apply),'unresolved':unresolved,'entries':entries}


def model_record(root=ROOT, apply=False):
    root=pathlib.Path(root).resolve();live=root/'data/live';directory=live/'derived/mind';digests={}
    for p in (directory/'digests').glob('*.json'):
        d=json.loads(p.read_text(encoding='utf-8'));digests[hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True).encode()).hexdigest()]=d
    utter=[r for p in directory.glob('????-??.jsonl') for r in json_rows(p)]
    key=lambda r:(r.get('conversation'),r.get('entity'),r.get('round'))
    retracted={key(r) for r in utter if r.get('state')=='retracted'}
    invalid=[]
    for r in utter:
        if r.get('state')!='thought' or key(r) in retracted:continue
        digest=digests.get(r.get('digest_sha256'))
        if digest is None or set(r.get('cites') or [])-{f['id'] for f in digest['facts']}:
            invalid.append(r)
    claims=list(json_rows(directory/'claims.jsonl'));changes=[]
    now=dt.datetime.now(dt.timezone.utc);nowtext=now.isoformat()
    for claim in claims:
        if claim.get('outcome')=='retracted':continue
        matches=[r for r in utter if r.get('state')=='thought' and r.get('conversation')==claim.get('conversation') and r.get('entity')==claim.get('entity') and r.get('claim')==claim.get('claim')]
        if claim.get('round') is None and len(matches)==1:claim['round']=matches[0].get('round')
        claim.setdefault('claim_id',content_id(claim))
        if key(claim) in {key(r) for r in invalid} or key(claim) in retracted:
            new={'outcome':'retracted','evidence':[],'reason':'source utterance was retracted'}
        elif utc(claim.get('due')) and utc(claim['due'])<=now:
            new=claim_evidence.evaluate(claim,live)
        else:continue
        if claim.get('outcome')!=new['outcome'] or claim.get('scoring_version') != 'closed-window/v2':
            old=claim.get('outcome');claim.update(new,settled_at=nowtext,scoring_version='closed-window/v2')
            changes.append({'kind':'rescored','at':nowtext,'claim_id':claim['claim_id'],'prior_outcome':old,**new})
    if apply:
        old_live,old_out=mind.LIVE,mind.OUT_DIR
        try:
            mind.LIVE,mind.OUT_DIR=live,directory
            with exclusive(live/'.write.lock'):
                path=directory/'claims.jsonl';tmp=path.with_suffix('.repair.tmp')
                tmp.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in claims),encoding='utf-8');tmp.replace(path)
                for event in changes:mind._append(directory/'claim-events.jsonl',event)
                for r in invalid:mind.retract(r['conversation'],r['entity'],r['round'],'B08: cited fact absent from saved digest; original utterance preserved',now)
        finally:mind.LIVE,mind.OUT_DIR=old_live,old_out
    return {'invalid_accepted_utterances':len(invalid),'claim_corrections':changes,'applied':bool(apply)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));ap.add_argument('--apply',action='store_true');a=ap.parse_args()
    print(json.dumps({'gauges':gauges(a.root,a.apply),'headlines':headlines(a.root,a.apply),'model_record':model_record(a.root,a.apply)},ensure_ascii=False,indent=1))
