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
        if any(part.lower().startswith(('.env','secrets.','kaggle.')) for part in rel.parts):
            raise ValueError('private configuration is not a public mirror input')
        if p.is_symlink() or p.is_junction(): raise ValueError('linked public path')
        p.resolve().relative_to(root)
        if p.is_file(): yield p, rel.as_posix()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def manifest_files(root):
    manifest = pathlib.Path(root) / 'docs' / 'export-manifest.json'
    if not manifest.is_file():
        return {}
    try:
        data = json.loads(manifest.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return {}
    result = {}
    for row in data.get('files', []):
        name = row.get('path')
        sha = row.get('sha256')
        size = row.get('bytes')
        if isinstance(name, str) and isinstance(sha, str) and isinstance(size, int):
            result[name] = {'sha256': sha, 'bytes': size}
    return result


def differs(root_file, stage_file, rel, old_manifest, new_manifest):
    if rel != 'docs/export-manifest.json':
        old = old_manifest.get(rel)
        new = new_manifest.get(rel)
        if old and new and old == new and root_file.stat().st_size == new['bytes']:
            return False
    if root_file.stat().st_size != stage_file.stat().st_size:
        return True
    return sha256_file(root_file) != sha256_file(stage_file)


def write_archive(root, original, backup, partial):
    head = git(root, 'rev-parse', 'HEAD')
    archive = root/'.git'/('beops-copy-'+uuid.uuid4().hex+'.zip')
    manifest = {'root': str(root), 'head': head, 'partial': bool(partial),
                'original_files': [rel for _, rel in original], 'files': {}}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for p, rel in backup:
            data = p.read_bytes()
            manifest['files'][rel] = hashlib.sha256(data).hexdigest()
            z.writestr(rel, data)
        z.writestr('COPY_MANIFEST.json', json.dumps(manifest))
    return {'archive': str(archive), 'head': head, 'files': len(manifest['files']),
            'original_files': len(manifest['original_files']), 'partial': bool(partial)}


def capture(root):
    root = pathlib.Path(root).resolve()
    if not (root/'.git').is_dir(): raise ValueError('physical public .git required')
    if git(root, 'status', '--porcelain'): raise ValueError('public tree must be clean')
    original = list(files(root))
    return write_archive(root, original, original, partial=False)


def capture_changes(root, stage):
    root = pathlib.Path(root).resolve()
    stage = pathlib.Path(stage).resolve()
    if not (root/'.git').is_dir(): raise ValueError('physical public .git required')
    if git(root, 'status', '--porcelain'): raise ValueError('public tree must be clean')
    original = list(files(root))
    staged = {rel: p for p, rel in files(stage)}
    old_manifest = manifest_files(root)
    new_manifest = manifest_files(stage)
    backup = []
    for p, rel in original:
        target = staged.get(rel)
        if target is None or differs(p, target, rel, old_manifest, new_manifest):
            backup.append((p, rel))
    return write_archive(root, original, backup, partial=True)


def restore(root, archive):
    root = pathlib.Path(root).resolve()
    with zipfile.ZipFile(archive) as z:
        m = json.loads(z.read('COPY_MANIFEST.json'))
        if root != pathlib.Path(m['root']).resolve() or git(root,'rev-parse','HEAD') != m['head']:
            raise ValueError('mirror identity or HEAD changed; automatic rollback refused')
        original = set(m.get('original_files') or m['files'].keys())
        for rel, digest in m['files'].items():
            p = (root/rel).resolve()
            p.relative_to(root)
            if pathlib.PurePosixPath(rel).parts[0] == '.git' or hashlib.sha256(z.read(rel)).hexdigest() != digest:
                raise ValueError('invalid copy backup')
        current = list(files(root))  # Validate every physical target before mutation.
        aside = root.parent/'_to_delete'/('beops-copy-failed-'+uuid.uuid4().hex)
        for p, rel in current:
            if rel not in original:
                target = aside/rel
                target.parent.mkdir(parents=True,exist_ok=True)
                p.rename(target)
        for rel in m['files']:
            p = root/rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(z.read(rel))
        # Recreate tracked files using their declared Git text/binary rules.
        # Exact pre-copy working bytes also remain in the recovery archive.
        git(root,'restore','--staged','--worktree','--source='+m['head'],'--','.')
        # Refresh Git's normalized-content view after restoring attributes and
        # working bytes together (a CRLF working file may equal its LF blob).
        git(root,'-c','core.fsmonitor=false','diff','--quiet','--no-ext-diff','--')
        if git(root,'status','--porcelain'): raise RuntimeError('rollback restored bytes but Git tree remains dirty')
        return {'restored':len(m['files']), 'head':m['head'], 'new_files_kept':str(aside), 'original_working_bytes':str(archive)}


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['capture','capture-changes','restore']);ap.add_argument('root');ap.add_argument('path',nargs='?');a=ap.parse_args()
    if a.command == 'capture':
        result = capture(a.root)
    elif a.command == 'capture-changes':
        if not a.path: raise SystemExit('stage path required')
        result = capture_changes(a.root, a.path)
    else:
        result = restore(a.root, a.path)
    print(json.dumps(result))
