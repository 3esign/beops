"""Recover a failed pre-commit copy in an already-owned public Git mirror.

The publisher must validate ownership and a clean tree before capture. Existing
bytes are kept under .git; newly copied files are moved aside, never deleted.
Committed releases use normal Git history and are not rolled back by this tool.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import uuid
import zipfile


def git(root, *args):
    p = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, encoding='utf-8', timeout=30)
    if p.returncode: raise RuntimeError(p.stderr.strip())
    return p.stdout.strip()


def files(root):
    for p in root.rglob('*'):
        rel = p.relative_to(root)
        if rel.parts[0] == '.git': continue
        if p.is_symlink() or p.is_junction(): raise ValueError('linked public path')
        p.resolve().relative_to(root)
        if p.is_file(): yield p, rel.as_posix()


def capture(root):
    root = pathlib.Path(root).resolve()
    if not (root/'.git').is_dir(): raise ValueError('physical public .git required')
    if git(root, 'status', '--porcelain'): raise ValueError('public tree must be clean')
    head = git(root, 'rev-parse', 'HEAD')
    archive = root/'.git'/('beops-copy-'+uuid.uuid4().hex+'.zip')
    manifest = {'root':str(root), 'head':head, 'files':{}}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for p, rel in files(root):
            data = p.read_bytes()
            manifest['files'][rel] = hashlib.sha256(data).hexdigest()
            z.writestr(rel, data)
        z.writestr('COPY_MANIFEST.json', json.dumps(manifest))
    return {'archive':str(archive), 'head':head, 'files':len(manifest['files'])}


def restore(root, archive):
    root = pathlib.Path(root).resolve()
    with zipfile.ZipFile(archive) as z:
        m = json.loads(z.read('COPY_MANIFEST.json'))
        if root != pathlib.Path(m['root']).resolve() or git(root,'rev-parse','HEAD') != m['head']:
            raise ValueError('mirror identity or HEAD changed; automatic rollback refused')
        for rel, digest in m['files'].items():
            p = (root/rel).resolve()
            p.relative_to(root)
            if pathlib.PurePosixPath(rel).parts[0] == '.git' or hashlib.sha256(z.read(rel)).hexdigest() != digest:
                raise ValueError('invalid copy backup')
        current = list(files(root))  # Validate every physical target before mutation.
        aside = root.parent/'_to_delete'/('beops-copy-failed-'+uuid.uuid4().hex)
        for p, rel in current:
            if rel not in m['files']:
                target = aside/rel
                target.parent.mkdir(parents=True,exist_ok=True)
                p.rename(target)
        for rel in m['files']:
            p = root/rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(z.read(rel))
        git(root,'restore','--staged','--source='+m['head'],'--','.')
        if git(root,'status','--porcelain'): raise RuntimeError('rollback restored bytes but Git tree remains dirty')
        return {'restored':len(m['files']), 'head':m['head'], 'new_files_kept':str(aside)}


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['capture','restore']);ap.add_argument('root');ap.add_argument('archive',nargs='?');a=ap.parse_args()
    print(json.dumps(capture(a.root) if a.command=='capture' else restore(a.root,a.archive)))
