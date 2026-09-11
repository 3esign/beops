"""Operational regressions: failed publication, policy stops and the common GPU mutex."""
import contextlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import timedelta
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import model_capacity as MC
import local_models as LM
import source_policy as SP
import prepare_release as PR
import watchman as W
import test_watchman as WT
NOW, iso = WT.NOW, WT.iso


class Monitoring(unittest.TestCase):
    setUp = WT.WatchmanTests.setUp
    tearDown = WT.WatchmanTests.tearDown
    def test_operator_publication_pause_is_visible(self):
        marker=W.ROOT/'runtime/PUBLISH_PAUSED';marker.parent.mkdir();marker.write_text('fixture')
        self.assertEqual(W.published(NOW)['state'],W.PAUSED)

    def test_blocked_source_is_not_called_stalled(self):
        self.t.receipt('S01', NOW-timedelta(days=2))
        with patch.object(W.source_policy, 'decision', return_value=('blocked', 'manual refusal')):
            checks = W.sources(NOW)
        self.assertEqual(checks[0]['state'], W.BLOCKED)
        self.assertEqual(checks[0]['network_requests'], 0)

    def test_failed_attempt_preserves_age_and_commit_of_success(self):
        self.t.history('2026-09-10T11')
        (W.LIVE/'publish-receipt.json').write_text(json.dumps({'published':False,'at':iso(NOW+timedelta(minutes=1)),'why':'private path must not leak'}))
        got = W.published(NOW+timedelta(minutes=2))
        self.assertEqual(got['state'], W.LATE)
        self.assertEqual(got['commit'], 'commit')
        self.assertEqual(got['age_min'], 2)
        self.assertNotIn('private path', got['said'])

    def test_local_unpushed_commit_cannot_make_publication_healthy(self):
        self.assertEqual(W.published(NOW)['state'], W.UNKNOWN)
        self.t.history('2026-09-10T11')
        p = W.LIVE/'publish-last-success.json'; d=json.loads(p.read_text());d['site_local_hash']='different';p.write_text(json.dumps(d))
        self.assertEqual(W.published(NOW)['state'], W.UNKNOWN)

    def test_active_stale_history_is_not_the_published_history(self):
        self.t.history('2026-09-10T11')
        (W.ROOT/'public/history.json').write_text(json.dumps({'history_ends':'2020-01-01T00'}))
        self.assertEqual(W.history(NOW)['state'], W.OK)


class Policy(unittest.TestCase):
    def test_permission_failure_and_empty_pause_marker_stop_fetches(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td); src={'sid':'S1','url':'https://example.org/feed'}
            self.assertEqual(SP.decision(root,root,src,{},NOW)[0], 'blocked')
            marker=root/'receipts/S1/PAUSED';marker.parent.mkdir(parents=True);marker.touch()
            with patch.object(SP.permission_policy,'authorize',return_value=(True,'verified')):
                self.assertEqual(SP.decision(root,root,src,{},NOW)[0], 'paused')


@unittest.skipUnless(pathlib.Path('C:/Svemir/lib/mind_lock.js').exists(), 'Svemir host integration is not installed')
class SharedGPU(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        env=patch.dict(os.environ,{'SVEMIR_DATA':self.tmp.name,'BEOPS_SVEMIR_ROOT':'C:/Svemir'})
        env.start();self.addCleanup(env.stop)
        self.lock=pathlib.Path(self.tmp.name)/'brain/locks/ollama.lock'

    def test_foreign_svemir_owner_defers_without_sending_http(self):
        subprocess.run(['node','-e',"const m=require('C:/Svemir/lib/mind_lock.js');if(!m.tryLock('ollama','foreign-fixture',30).ok)process.exit(1)"],check=True,timeout=5)
        with patch.object(LM,'LOCK',pathlib.Path(self.tmp.name)/'private.lock'),patch.object(LM.urllib.request,'build_opener') as opener:
            with self.assertRaises(LM.ModelDeferred):
                LM.request('http://127.0.0.1:11434','/api/tags',timeout=.1)
            opener.assert_not_called()
        self.assertEqual(json.loads(self.lock.read_text())['owner'],'foreign-fixture')

    def test_nested_metadata_and_chat_hold_same_global_owner(self):
        owners=[]
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,size):return b'{}'
        def send(*a,**kw):owners.append(json.loads(self.lock.read_text())['owner']);return Response()
        with patch.object(LM,'LOCK',pathlib.Path(self.tmp.name)/'private.lock'),patch.object(LM.urllib.request,'build_opener') as opener:
            opener.return_value.open.side_effect=send
            LM.request('http://127.0.0.1:11434','/api/chat',{'model':'fixture'})
        self.assertEqual(len(owners),2);self.assertEqual(owners[0],owners[1]);self.assertFalse(self.lock.exists())

    def test_parent_death_releases_lease_without_waiting_for_ttl(self):
        code="from model_capacity import shared_slot; import time\nwith shared_slot(1):\n print('ready',flush=True)\n time.sleep(60)\n"
        env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'tools')
        proc=subprocess.Popen([sys.executable,'-B','-c',code],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            import queue, threading
            ready=queue.Queue();threading.Thread(target=lambda:ready.put(proc.stdout.readline()),daemon=True).start()
            self.assertEqual(ready.get(timeout=6).strip(),'ready')
            proc.kill();proc.wait(timeout=5)
            deadline=time.monotonic()+5
            while self.lock.exists() and time.monotonic()<deadline:time.sleep(.05)
            self.assertFalse(self.lock.exists())
        finally:
            if proc.poll() is None:proc.kill();proc.wait(timeout=5)
            proc.stdout.close();proc.stderr.close()


class DiskCapacity(unittest.TestCase):
    def test_insufficient_space_is_refused_before_creating_release(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)/'source';root.mkdir();dest=root.parent/'release'
            with patch.object(PR,'git',return_value='fixed-oid'),patch.object(PR.shutil,'disk_usage',return_value=type('Space',(),{'free':0})()):
                with self.assertRaisesRegex(RuntimeError,'disk space insufficient'):PR.prepare(root,dest)
            self.assertFalse(dest.exists())
