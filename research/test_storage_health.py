import collections
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import storage_health as s
import guard

Usage = collections.namedtuple('Usage', 'total used free')


class Storage(unittest.TestCase):
    def test_reserve_survives_complete_allocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            required = 4*1234 + 3*5678 + s.RESERVE_BYTES
            with self.assertRaisesRegex(RuntimeError, '2 GiB reserve'):
                s.require_release_capacity(tmp, 1234, 5678, lambda _: Usage(0,0,required-1))
            self.assertEqual(s.require_release_capacity(tmp,1234,5678,lambda _: Usage(0,0,required))['required_bytes'],required)

    def test_inspection_preserves_pause_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);(root/'runtime').mkdir();(root/'runtime/MAINTENANCE').write_text('operator pause')
            result=s.inspect(root, lambda _: Usage(9*s.GIB,8*s.GIB,s.GIB))
            self.assertEqual(result['state'],'WARN')
            self.assertEqual((root/'runtime/MAINTENANCE').read_text(),'operator pause')
            self.assertEqual(len(list(root.rglob('*'))),2)

    def test_unknown_capacity_cannot_be_ok(self):
        def unavailable(_): raise OSError('unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(s.inspect(tmp,unavailable)['state'],'UNKNOWN')

    def test_unknown_storage_reaches_guard_verdict(self):
        record={'verdict':guard.OK}
        with patch.object(guard,'run',return_value=record), patch.object(s,'inspect',return_value={'state':'UNKNOWN'}), patch.object(guard,'report',return_value='unknown'), patch.object(sys,'argv',['guard.py','--dry']):
            self.assertEqual(guard.main(),1)
            self.assertEqual(record['verdict'],guard.UNKNOWN)

    @unittest.skipUnless(sys.platform=='win32','Windows scheduler')
    def test_abandoned_cleanup_preserves_live_retained_and_unowned_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=pathlib.Path(tmp);source=base/'source';source.mkdir();releases=base/'releases';releases.mkdir()
            created=(datetime.now(timezone.utc)-timedelta(hours=3)).isoformat()
            folders=[]
            for n,pid,retained,schema in [('1',2147483647,False,'beops-generated-workspace/v2'),
                                          ('2',os.getpid(),False,'beops-generated-workspace/v2'),
                                          ('3',2147483647,True,'beops-generated-workspace/v2'),
                                          ('4',2147483647,False,'legacy')]:
                folder=releases/('beops-release-'+n*32);folder.mkdir();(folder/'runtime').mkdir()
                (folder/'sentinel').write_text('preserve unless provably abandoned')
                (folder/'.beops-generated-workspace.json').write_text(json.dumps({'schema':schema,'source':str(source),'destination':str(folder),'source_oid':'abc','owner_pid':pid,'created_at':created,'retained':retained}))
                folders.append(folder)
            command=f". '{ROOT/'tools/publish_safety.ps1'}'; Clear-BeopsAbandonedReleases -SourceRoot '{source}' -BaseRoot '{releases}'"
            result=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(folders[0].exists(),result.stdout)
            self.assertTrue(all((f/'sentinel').exists() for f in folders[1:]))

    @unittest.skipUnless(sys.platform=='win32','Windows scheduler')
    def test_half_hour_tick_stays_quiet_after_a_slow_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt=pathlib.Path(tmp)/'receipt.json'
            status=pathlib.Path(tmp)/'publish-scheduler-status.json'
            receipt.write_text(json.dumps({'published':True,'cycle_started_at':'2026-09-14T00:00:00Z','at':'2026-09-14T00:07:00Z'}))
            def call(at):
                return subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'tools/publish_due.ps1'),'-ReceiptPath',str(receipt),'-StatusPath',str(status),'-NowUtc',at],capture_output=True,timeout=20).returncode
            self.assertEqual(call('2026-09-14T00:10:00Z'),75)
            self.assertEqual(call('2026-09-14T00:30:00Z'),75)
            self.assertEqual(call('2026-09-14T00:36:00Z'),0)
