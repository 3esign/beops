"""Complete headline retention and reversible release inputs, tested on real temporary files."""
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import apply_retention as retention
import backup_restore
import build_headlines
import prepare_release
import baseline
from contracts import atomic_json


def git(root,*args):
    env=os.environ.copy()
    for k in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR'):env.pop(k,None)
    return subprocess.check_output(['git','-C',str(root),*args],env=env,stderr=subprocess.PIPE,text=True).strip()


class Archive(unittest.TestCase):
    def test_all_months_and_revisions_are_preserved_without_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);atomic_json(root/'research/COLLECTORS.json',{'sources':[{'sid':'S68','name':'Outlet'}]})
            d=root/'data/live/rows/S68';d.mkdir(parents=True)
            for month,text in [('2025-01','A'*600),('2026-09','Changed headline')]:
                row={'sid':'S68','parameter':'headline','result':text,'link':'javascript:window.__bad=1','resultTime':month+'-01T10:00:00Z','receivedTime':month+'-01T10:01:00Z','dedupe_key':'same-url'}
                (d/(month+'.jsonl')).write_text(json.dumps(row)+'\n'+json.dumps(row)+'\n',encoding='utf-8')
            value=json.loads(build_headlines.build(root).read_text(encoding='utf-8'))
            self.assertEqual(value['count'],2);self.assertEqual(len(value['rows'][1]['title']),600)
            self.assertEqual({r['revision_key'] for r in value['rows']},{'same-url'})

    def test_current_retention_never_erases_headline_or_digest_text(self):
        policy=json.loads((ROOT/'research/RETENTION.json').read_text(encoding='utf-8'))
        self.assertTrue(all(r['keep_days'] is None for r in policy['rules'] if r['id'] in ('R1','R3')))
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);d=root/'data/live/rows/S68';d.mkdir(parents=True)
            p=d/'2020-01.jsonl';raw=json.dumps({'sid':'S68','parameter':'headline','result':'Old headline','receivedTime':'2020-01-01T00:00:00Z'})+'\n';p.write_text(raw)
            plan=retention.due(root,policy,dt.datetime(2035,1,1,tzinfo=dt.timezone.utc))
            self.assertEqual(plan['rows'],[]);self.assertIsNone(plan['first_erasure_due'])
            retention.apply(root,policy,dt.datetime(2035,1,1,tzinfo=dt.timezone.utc),plan)
            self.assertEqual(p.read_text(),raw)

    def test_archive_corruption_is_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);atomic_json(root/'research/COLLECTORS.json',{'sources':[]})
            d=root/'data/live/rows/S68';d.mkdir(parents=True);(d/'2020-01.jsonl').write_text('{broken')
            with self.assertRaisesRegex(ValueError,'invalid JSONL'):build_headlines.build(root)

    def test_deleted_source_cannot_leave_a_stale_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);out=root/'baseline';atomic_json(out/'S68.json',{'buckets':{'old':1}})
            with patch.object(baseline,'ROWS',root/'absent'),patch.object(baseline,'OUT',out):baseline.build()
            self.assertEqual(json.loads((out/'S68.json').read_text())['buckets'],{})


class RecoveryFiles(unittest.TestCase):
    def repo(self,root):
        root.mkdir();git(root,'init','-q');(root/'source.txt').write_text('first\n');git(root,'add','source.txt');git(root,'-c','user.name=Semir Poturak','-c','user.email=scumutator@gmail.com','commit','-qm','first');return git(root,'rev-parse','HEAD')

    def test_fixed_oid_survives_head_moving_and_hashes_runtime_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=pathlib.Path(tmp);root=base/'source';oid=self.repo(root);(root/'source.txt').write_text('second\n');git(root,'add','source.txt');git(root,'-c','user.name=Semir Poturak','-c','user.email=scumutator@gmail.com','commit','-qm','second')
            atomic_json(root/'data/live/rows/S01/value.json',{'real':42})
            result=prepare_release.prepare(root,base/'release',oid)
            self.assertEqual((base/'release/source.txt').read_text(),'first\n');self.assertEqual(result['source_oid'],oid)
            manifest=json.loads((base/'release/runtime/release-inputs.json').read_text());self.assertEqual(manifest['files'][0]['sha256'],hashlib.sha256((base/'release/data/live/rows/S01/value.json').read_bytes()).hexdigest())

    def test_archive_does_not_copy_evidence_twice_or_include_scratch(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=pathlib.Path(tmp);root=base/'source';self.repo(root)
            for name in ('research/evidence/proof.txt','research/_scratch/unused.txt','research/code.txt'):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(name)
            git(root,'add','research');git(root,'-c','user.name=Semir Poturak','-c','user.email=scumutator@gmail.com','commit','-qm','fixture')
            prepare_release.prepare(root,base/'release')
            self.assertEqual((base/'release/research/evidence/proof.txt').read_text(),'research/evidence/proof.txt')
            self.assertTrue((base/'release/research/code.txt').exists())
            self.assertFalse((base/'release/research/_scratch').exists())

    def test_backup_restore_checks_every_byte_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=pathlib.Path(tmp);root=base/'source';self.repo(root);atomic_json(root/'data/live/rows/S01/value.json',{'real':42})
            archive=base/'backup.zip';backup_restore.backup(root,archive);result=backup_restore.restore(archive,base/'restored')
            self.assertGreater(result['verified_files'],1);self.assertEqual((root/'source.txt').read_bytes(),(base/'restored/source.txt').read_bytes())
            with self.assertRaises(ValueError):backup_restore.restore(archive,base/'restored')

    def test_corrupt_and_traversal_backups_create_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=pathlib.Path(tmp)
            for i,name in enumerate(['../escape.txt','ok.txt']):
                a=base/f'bad{i}.zip'
                with zipfile.ZipFile(a,'w') as z:
                    z.writestr(name,'changed');z.writestr('BACKUP_MANIFEST.json',json.dumps({'files':[{'path':name,'bytes':2,'sha256':'0'*64}]}))
                with self.assertRaises(ValueError):backup_restore.restore(a,base/f'out{i}')
                self.assertFalse((base/f'out{i}').exists())
