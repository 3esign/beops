"""Remove private-document links from the exported index; fail on missing executable assets."""
import argparse
import json
import pathlib
import re
from urllib.parse import urlsplit, unquote


def validate(root):
    root=pathlib.Path(root).resolve(); removed=[]; errors=[]
    # Public bytes must equal the Git blobs after text normalization, including generated files.
    for file in root.rglob('*'):
        if file.is_relative_to(root/'public/dataset'):
            continue  # Dataset editions have their own byte manifests and -text Git attributes.
        if file.is_file() and '.git' not in file.parts and file.suffix.lower() in ('.py','.js','.html','.json','.jsonl','.md','.ps1','.bat','.cmd','.csv','.txt','.svg','.xml','.css'):
            raw=file.read_bytes()
            if b'\r\n' in raw:
                file.write_bytes(raw.replace(b'\r\n',b'\n'))
    def destination(file, href):
        parsed=urlsplit(href.strip().strip('<>'))
        if parsed.scheme or parsed.netloc or not parsed.path:
            return True
        path=(root/parsed.path.lstrip('/') if parsed.path.startswith('/') else file.parent/unquote(parsed.path)).resolve()
        try:path.relative_to(root)
        except ValueError:return False
        return path.exists()
    for file in sorted(root.rglob('*')):
        if not file.is_file() or '.git' in file.parts or file.suffix.lower() not in ('.md','.html'):continue
        text=file.read_text(encoding='utf-8-sig')
        if file.suffix.lower()=='.md':
            def link(match):
                if destination(file,match[2]):return match[0]
                removed.append({'file':file.relative_to(root).as_posix(),'target':match[2]})
                return match[1]+' (private working record)'
            updated=re.sub(r'\[([^\]\n]+)\]\(([^)\n]+)\)',link,text)
            if updated!=text:file.write_text(updated,encoding='utf-8',newline='\n')
        elif file.parent==root/'docs':
            for match in re.finditer(r'<(?:script|img|iframe|link)\b[^>]*?\b(?:src|href)=["\']([^"\']+)',text,re.I):
                if not destination(file,match[1]):errors.append(file.name+': '+match[1])
    if errors:raise ValueError('Missing public assets: '+ '; '.join(errors[:12]))
    import hashlib
    for manifest in (root/'public/dataset').rglob('MANIFEST.json'):
        for entry in json.loads(manifest.read_text(encoding='utf-8'))['files']:
            payload=(manifest.parent/entry['name']).read_bytes()
            if len(payload)!=entry['bytes'] or hashlib.sha256(payload).hexdigest()!=entry['sha256']:
                raise ValueError('dataset manifest mismatch: '+str(manifest))
    report={'schema':'beops-public-links/v1','private_links_removed':removed,'errors':errors}
    (root/'docs/public-links.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');args=p.parse_args();r=validate(args.root);print('public links:',len(r['private_links_removed']),'private links rendered as text; no missing executable assets')
