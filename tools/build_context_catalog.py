"""Normalize captured RZS context without adding collectors or changing raw evidence."""
import gzip
import hashlib
import io
import json
import pathlib
import sys
import zipfile
from datetime import datetime, timezone
from contracts import atomic_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
CAPTURE = '20260906T020314Z'
MAX_BYTES = 80 * 1024 * 1024
# These IDs and labels occur in the captured RZS tables. No inferred municipal geometry.
TERRITORIES = {'79014': 'City of Belgrade', 'RS110': 'Belgrade district',
               '70181': 'Novi Beograd', '70203': 'Palilula (Belgrade)'}
SPECS = {
 '220205IND02': ('Tourist overnight stays', 'monthly'),
 '24021308IND01': ('Registered employment by residence', 'quarterly'),
 '24021105IND01': ('Registered employment by residence', 'annual'),
 '05010107IND02': ('New dwelling prices', 'annual / half-year'),
 '2403040111IND02': ('Gross wages — Serbia', 'monthly'),
 '2403040110IND02': ('Public-sector gross wages — Serbia', 'monthly'),
}


def unpack(path, entry):
    raw = path.read_bytes()
    if entry.get('stored_compression') == 'gzip':
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
            raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != entry['sha256']:
        raise ValueError('captured payload size/hash mismatch')
    if raw[:4] == b'PK\x03\x04':
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names = z.namelist()
            if len(names) != 1 or not names[0].endswith('.json') or z.getinfo(names[0]).file_size > MAX_BYTES:
                raise ValueError('unexpected archive shape')
            raw = z.read(names[0])
    records = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(records, list):
        raise ValueError('expected row array')
    return records


def rights(root):
    p = root / 'research/CONTEXT_DATASETS.json'
    doc = json.loads(p.read_text(encoding='utf-8'))
    permission = doc['rzs_rights']
    evidence = root / permission['evidence']
    raw = evidence.read_bytes()
    if hashlib.sha256(raw).hexdigest() != permission['sha256']:
        raise ValueError('RZS terms hash mismatch')
    return permission, doc


def build(root=ROOT):
    permission, register = rights(root)
    capture = root / 'research/evidence/S148' / CAPTURE
    manifest = json.loads((capture/'MANIFEST.json').read_text(encoding='utf-8'))
    datasets = []
    for entry in manifest['files']:
        code = entry['file'].split('_')[0]
        if code not in SPECS:
            continue
        raw = unpack(capture / entry.get('stored_as', entry['file']), entry)
        national = code.startswith('240304')
        rows, seen = [], set()
        for r in raw:
            territory = str(r['IDTer'])
            if territory not in ({'RS'} if national else TERRITORIES):
                continue
            dims = {k: v for k,v in r.items() if k.startswith('ID') and k not in ('IDTer','IDStatusPodatka')}
            # Preserve subgroup dimensions; only total rows become short AI context.
            key = (territory,str(r['god']),str(r['mes']),json.dumps(dims,sort_keys=True))
            if key in seen:
                raise ValueError('duplicate RZS dimensional key')
            seen.add(key)
            rows.append({'territory_id':territory,'place':r['nTer'],'geography':'national' if national else 'administrative',
                         'period':str(r['god'])+'-'+str(r['mes']), 'value':r['vrednost'],
                         'unit':r['nJedinicaMere'],'dimensions':dims,'status':r.get('IDStatusPodatka'),
                         'metric':r['Indikator']})
        # Quarter/month/half-year codes remain explicit; never sum across levels or modalities.
        latest = []
        for territory in sorted({r['territory_id'] for r in rows}):
            eligible = [r for r in rows if r['territory_id']==territory and r['value'] is not None
                        and all(str(v)=='0' for v in r['dimensions'].values())]
            if eligible:
                latest.append(max(eligible,key=lambda r:r['period']))
        out = {'schema':'beops-context-table/v1','id':'rzs-'+code,'rows':rows,
               'source_sha256':entry['sha256'],'source_url':entry['url']}
        outpath=root/'public/context-tables'/('rzs-'+code+'.json')
        atomic_json(outpath,out)
        datasets.append({'id':'rzs-'+code,'sid':'S148','title':SPECS[code][0],'cadence':SPECS[code][1],
                         'edition':CAPTURE,'url':entry['url'],'source_sha256':entry['sha256'],
                         'attribution':'Statistical Office of the Republic of Serbia (RZS); retrieved 2026-09-06; filtered and normalized by BEOPS.',
                         'reference_years':sorted({str(r['god']) for r in raw}), 'captured_rows':len(raw),
                         'selected_rows':len(rows),'null_rows':sum(r['value'] is None for r in rows),
                         'latest':latest,'table':'context-tables/rzs-'+code+'.json',
                         'table_sha256':hashlib.sha256(outpath.read_bytes()).hexdigest(),
                         'table_eligible':True,'map_eligible':False,
                         'ai_eligible':bool(latest) and code!='05010107IND02',
                         'limitation':'National only.' if national else 'Only explicitly selected administrative IDs. No municipal polygons are supplied.',
                         'rights_evidence':permission['sha256']})
    for item in register.get('held_candidates',[]):
        datasets.append({**item,'table_eligible':False,'map_eligible':False,'ai_eligible':False,'latest':[]})
    catalog={'source':{'sid':'S148','capture':CAPTURE,'publisher':'Statistical Office of the Republic of Serbia'},'schema':'beops-context-catalog/v1','built_at':datetime.now(timezone.utc).isoformat(),
             'datasets':datasets,'rights':permission,'population_release':'2022-06-30',
             'note':'Data edition, publication and observation times are distinct. Blank values are not zero.'}
    atomic_json(root/'public/context-catalog.json',catalog)
    return {'datasets':len(datasets),'tables':6,'selected_rows':sum(d.get('selected_rows',0) for d in datasets)}


if __name__ == '__main__':
    print(json.dumps(build(),ensure_ascii=False))
