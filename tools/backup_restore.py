"""Local, manifest-verified backup/restore. Never includes secrets or overwrites a restore target."""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import subprocess
import zipfile
from contracts import exclusive


def forbidden(path):
    parts = pathlib.PurePosixPath(path.replace('\\', '/')).parts
    if parts[-1].endswith(('.lock','.tmp')) or parts[-1] == 'BACKUP_MANIFEST.json':
        return True
    return any(p.lower() in {'.git', 'node_modules', '__pycache__', '_to_delete', 'runtime'}
               or p.lower().startswith(('.env', 'secrets.', 'kaggle.')) for p in parts)


def safe_name(name):
    p = pathlib.PurePosixPath(name)
    if p.is_absolute() or not p.parts or any(x in ('', '.', '..') or ':' in x or '\\' in x for x in p.parts):
        raise ValueError('unsafe backup member')
    return p


def backup(root, archive):
    root, archive = pathlib.Path(root).resolve(), pathlib.Path(archive).resolve()
    if archive.is_relative_to(root) or archive.exists():
        raise ValueError('backup must be a new file outside the source')
    oid = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    files = []
    with exclusive(root/'research/08-provenance/LEDGER.lock'), exclusive(root/'data/live/.write.lock'):
        # Runtime logs and caches are deliberately not needed for reconstructing observations.
        for path in sorted(root.rglob('*')):
            rel = path.relative_to(root).as_posix()
            if forbidden(rel) or not path.is_file():
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError('linked input outside backup boundary: '+rel)
            files.append((path,rel))
        manifest = {'schema':'beops-backup/v1', 'source_commit':oid,
                    'scope':'working source, evidence, observations, live rows, receipts and derived state; no secrets, Git history or runtime logs', 'files':[]}
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
            for path,rel in files:
                before=path.stat();payload=path.read_bytes();after=path.stat()
                if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                    raise RuntimeError('input changed during backup: '+rel)
                manifest['files'].append({'path':rel,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()})
                z.writestr(rel,payload)
            current=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
            if current!=oid:raise RuntimeError('source commit moved during backup')
            z.writestr('BACKUP_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=1))
    return {'archive':str(archive),'files':len(files),'bytes':archive.stat().st_size,'source_commit':oid}


def restore(archive, target):
    target=pathlib.Path(target).resolve()
    if target.exists():raise ValueError('restore destination already exists')
    with zipfile.ZipFile(archive) as z:
        m=json.loads(z.read('BACKUP_MANIFEST.json'))
        declared=[r['path'] for r in m['files']]
        if len(declared)!=len(set(declared)) or set(z.namelist())!=set(declared+['BACKUP_MANIFEST.json']):
            raise ValueError('backup membership mismatch')
        # Validate every member before creating the output tree.
        for row in m['files']:
            safe_name(row['path'])
            if forbidden(row['path']):raise ValueError('forbidden backup member')
            payload=z.read(row['path'])
            if len(payload)!=row['bytes'] or hashlib.sha256(payload).hexdigest()!=row['sha256']:
                raise ValueError('backup hash mismatch: '+row['path'])
        target.mkdir(parents=True)
        for row in m['files']:
            path=target/row['path'];path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as out:out.write(z.read(row['path']))
        (target/'BACKUP_MANIFEST.json').write_text(json.dumps(m,indent=1),encoding='utf-8')
    return {'target':str(target),'verified_files':len(m['files']),'source_commit':m['source_commit']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['backup','restore']);ap.add_argument('source');ap.add_argument('destination');a=ap.parse_args()
    print(json.dumps((backup if a.command=='backup' else restore)(a.source,a.destination)))
