"""Check manifest hashes against Git's actual staged bytes before a public commit."""
import hashlib
import json
import pathlib
import subprocess
import sys


def verify(root):
    root=pathlib.Path(root).resolve()
    manifest=subprocess.run(['git','-C',str(root),'show',':docs/export-manifest.json'],check=True,capture_output=True,timeout=30).stdout
    rows=json.loads(manifest)['files']
    specs=''.join(':'+r['path']+'\n' for r in rows).encode('utf-8')
    raw=subprocess.run(['git','-C',str(root),'cat-file','--batch'],input=specs,check=True,capture_output=True,timeout=60).stdout
    at=0
    for row in rows:
        end=raw.find(b'\n',at)
        header=raw[at:end].split()
        if end<0 or len(header)!=3 or header[1]!=b'blob':raise ValueError('missing staged export file: '+row['path'])
        size=int(header[2]);at=end+1;data=raw[at:at+size];at+=size+1
        if size!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('staged bytes differ from manifest: '+row['path'])
    if at!=len(raw):raise ValueError('unexpected trailing Git batch output')
    return {'staged_files_verified':len(rows)}


if __name__=='__main__':print(json.dumps(verify(sys.argv[1])))
