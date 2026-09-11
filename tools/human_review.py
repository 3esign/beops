"""Prepare a private blinded review; score only explicitly supplied human annotations.

No model is called. No human label is inferred. The review measures agreement
with a person about the available evidence, not objective truth about the world.
"""
import argparse
import hashlib
import json
import pathlib
from collections import defaultdict
from datetime import datetime, timezone
from contracts import atomic_json, json_rows, exclusive


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def stratified(rows, n, seed):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['kind'], row['stratum'])].append(row)
    for group in groups.values():
        group.sort(key=lambda r: digest([seed, r['id']]))
    chosen = []
    while len(chosen) < n and any(groups.values()):
        for key in sorted(groups):
            if groups[key] and len(chosen) < n:
                chosen.append(groups[key].pop())
    return chosen


def prepare(source, output, per_kind=30, seed='beops-review-20260911'):
    source, output = pathlib.Path(source).resolve(), pathlib.Path(output).resolve()
    if output.exists():
        raise FileExistsError('review output already exists; preserve earlier packet')
    if per_kind < 1 or per_kind > 200:
        raise ValueError('per_kind must be between 1 and 200')
    from organ_news import CATEGORIES
    candidates, excluded = [], defaultdict(int)
    live = source/'data/live'
    with exclusive(live/'.write.lock'):
        digests = {}
        for p in sorted((live/'derived/mind/digests').glob('*.json')):
            value = json.loads(p.read_text(encoding='utf-8'))
            digests[digest(value)] = value
        for kind in ('news', 'mind'):
            for path in sorted((live/'derived'/kind).glob('????-??.jsonl')):
                for line, row in enumerate(json_rows(path), 1):
                    pointer = f'{path.relative_to(source).as_posix()}:{line}'
                    base = {'id':digest([pointer,row])[:24], 'kind':kind, 'private_origin':pointer,
                            'private_row_sha256':digest(row), 'at':row.get('derivedTime')}
                    if kind == 'news':
                        if not row.get('input_headline'):
                            excluded['news_missing_headline'] += 1; continue
                        base.update(stratum=str(row.get('input_sid'))+':'+str(row.get('category')),
                                    title=row['input_headline'], source=row.get('input_sid'),
                                    prediction={k:row.get(k) for k in ('category','belgrade','zones')})
                    else:
                        if row.get('state') not in ('thought','rejected'):
                            excluded['mind_non_utterance'] += 1; continue
                        evidence = digests.get(row.get('digest_sha256'))
                        if not evidence:
                            excluded['mind_missing_digest'] += 1; continue
                        if not (row.get('en') or row.get('sr') or row.get('text')):
                            excluded['mind_empty_text'] += 1; continue
                        base.update(stratum=str(row.get('state'))+':'+str(row.get('entity')),
                                    text=row.get('text') or row.get('en'), sr=row.get('sr'),
                                    facts=evidence.get('facts',[]), cites=row.get('cites',[]),
                                    prediction={'accepted':row.get('state')=='thought'})
                    candidates.append(base)
    selected = []
    for kind in ('news','mind'):
        selected += stratified([r for r in candidates if r['kind']==kind],per_kind,seed)
    selected.sort(key=lambda r:digest([seed,r['id'],'display']))
    packet = {'schema':'beops-human-review/v1','at':datetime.now(timezone.utc).isoformat(),
              'seed':seed,'state':'awaiting_human','categories':CATEGORIES,'rows':selected,
              'available':{k:sum(r['kind']==k for r in candidates) for k in ('news','mind')},
              'excluded':dict(excluded),'scope':'Stratified diagnostic sample; not a population accuracy estimate.'}
    packet['packet_id'] = digest(packet)
    output.mkdir(parents=True)
    atomic_json(output/'packet-private.json',packet)
    blinded = {k:packet[k] for k in ('packet_id','categories')}
    blinded['rows'] = [{k:v for k,v in r.items() if k not in ('prediction','stratum') and not k.startswith('private_')} for r in selected]
    template = pathlib.Path(__file__).with_name('human_review.html').read_text(encoding='utf-8')
    (output/'review.html').write_text(template.replace('__PACKET__',json.dumps(blinded,ensure_ascii=False).replace('</','<\\/')),encoding='utf-8')
    atomic_json(output/'status.json',{'state':'awaiting_human','packet_id':packet['packet_id'],'items':len(selected),'human_annotations':0,'measured_accuracy':None})
    return {'output':str(output),'items':len(selected),'available':packet['available'],'excluded':packet['excluded']}


def score(packet, annotations):
    if annotations.get('packet_id') != packet['packet_id']:
        raise ValueError('annotations belong to a different packet')
    if not str(annotations.get('reviewer','')).strip() or annotations.get('reviewer_type') != 'human':
        raise ValueError('an identified human reviewer is required')
    if annotations.get('independent_before_reveal') is not True:
        raise ValueError('independent annotation before revealing predictions is required')
    known={r['id']:r for r in packet['rows']}; seen=set(); decisions=[]
    for label in annotations.get('rows',[]):
        key=label.get('id')
        if key not in known or key in seen:raise ValueError('unknown or duplicate annotation id')
        seen.add(key); row=known[key]
        if row['kind']=='news':
            if label.get('category') not in packet['categories']+['uncertain']:raise ValueError('invalid human category')
            if label.get('belgrade') not in ('yes','no','uncertain'):raise ValueError('invalid human location')
            for field,value in [('category',label['category']),('belgrade',label['belgrade'])]:
                if value=='uncertain':continue
                expected = value=='yes' if field=='belgrade' else value
                decisions.append({'kind':'news_'+field,'agrees':row['prediction'].get(field)==expected})
        else:
            verdict=label.get('supported')
            if verdict not in ('yes','no','uncertain'):raise ValueError('invalid human evidence judgment')
            if verdict!='uncertain':
                accepted=row['prediction']['accepted'];supported=verdict=='yes'
                decisions.append({'kind':'mind_gate','agrees':accepted==supported,
                                  'false_accept':accepted and not supported,'false_reject':not accepted and supported})
    metrics={}
    for kind in ('news_category','news_belgrade','mind_gate'):
        rows=[r for r in decisions if r['kind']==kind]
        metrics[kind]={'decidable':len(rows),'agreement':sum(r['agrees'] for r in rows)/len(rows) if rows else None,
                       'false_accept':sum(r.get('false_accept',False) for r in rows),'false_reject':sum(r.get('false_reject',False) for r in rows)}
    return {'schema':'beops-human-review-result/v1','packet_id':packet['packet_id'],'reviewer':annotations['reviewer'],
            'state':'complete' if len(seen)==len(known) and known else 'partial',
            'annotated':len(seen),'expected':len(known),'metrics':metrics,
            'scope':'Agreement on this stratified sample only; uncertain judgments excluded from each denominator. Human identity and independence are declared, not technically authenticated.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--source',required=True);prep.add_argument('--output',required=True);prep.add_argument('--per-kind',type=int,default=30)
    calc=sub.add_parser('score');calc.add_argument('--packet',required=True);calc.add_argument('--annotations',required=True);calc.add_argument('--output',required=True)
    args=parser.parse_args()
    if args.command=='prepare':result=prepare(args.source,args.output,args.per_kind)
    else:
        if pathlib.Path(args.output).exists():raise FileExistsError('result already exists')
        result=score(json.loads(pathlib.Path(args.packet).read_text(encoding='utf-8')),json.loads(pathlib.Path(args.annotations).read_text(encoding='utf-8')))
        atomic_json(args.output,result)
    print(json.dumps(result,ensure_ascii=False))
