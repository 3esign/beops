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
        with patch.object(LM,'LOCK',pathlib.Path(self.tmp.name)/'private.lock'), \
                patch.object(LM.urllib.request,'build_opener') as opener, \
                patch.object(LM,'_request_bridge') as bridge:
            with self.assertRaises(LM.ModelDeferred):
                LM.request('http://127.0.0.1:11434','/api/tags',timeout=.1)
            opener.assert_not_called()
            bridge.assert_not_called()
        self.assertEqual(json.loads(self.lock.read_text())['owner'],'foreign-fixture')

    def test_nested_metadata_and_chat_hold_same_global_owner(self):
        owners=[]
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,size):return b'{}'
        def send(*a,**kw):owners.append(json.loads(self.lock.read_text())['owner']);return Response()
        with patch.object(LM,'LOCK',pathlib.Path(self.tmp.name)/'private.lock'), \
                patch.object(LM,'is_cli_backend',return_value=False), \
                patch.object(LM.urllib.request,'build_opener') as opener:
            opener.return_value.open.side_effect=send
            LM.request('http://127.0.0.1:11434','/api/chat',{'model':'fixture'})
        self.assertEqual(len(owners),2);self.assertEqual(owners[0],owners[1]);self.assertFalse(self.lock.exists())

    def test_cli_backend_uses_shared_capacity_and_remaining_budget(self):
        with patch.dict(os.environ,{'BEOPS_MODEL_BACKEND':'cli'}), \
                patch.object(LM,'exclusive',return_value=contextlib.nullcontext()), \
                patch.object(LM,'shared_slot',return_value=contextlib.nullcontext()) as shared, \
                patch.object(LM,'_request_bridge',return_value={}) as bridge:
            LM._job.deadline=time.monotonic()+1
            try:
                LM.request('http://127.0.0.1:11434','/api/chat',{'model':'qwen2.5-1.5b-hf'},timeout=210)
            finally:
                del LM._job.deadline
        self.assertTrue(shared.called)
        self.assertLessEqual(bridge.call_args.args[2],1)

    def test_cli_cloud_route_is_refused_before_dispatch(self):
        with patch.dict(os.environ,{'BEOPS_MODEL_BACKEND':'cli'}), \
                patch.object(LM,'model_slot',return_value=contextlib.nullcontext()), \
                patch.object(LM,'_request_bridge',return_value={}) as bridge:
            with self.assertRaisesRegex(ValueError,'cloud model is not permitted'):
                LM.request('http://127.0.0.1:11434','/api/chat',{'model':'claude:sonnet'},timeout=10)
        bridge.assert_not_called()

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


class SvemirBridge(unittest.TestCase):
    def run_bridge(self, cmd, args=None, stdin='', models=None):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);lib=root/'lib';lib.mkdir()
            (lib/'cli_bridge.js').write_text("""
exports.chatModels = () => JSON.parse(process.env.STUB_MODELS || '[]');
exports.runLocal = async args => {
  process.env.STUB_LAST_CALL = JSON.stringify(args);
  return {ok:true,out:JSON.stringify({status:'COMPLETED',response:'{"items":[]}'})};
};
""", encoding='utf-8')
            env=os.environ.copy();env['BEOPS_SVEMIR_ROOT']=td
            env['STUB_MODELS']=json.dumps(models if models is not None else [])
            result=subprocess.run(['node',str(ROOT/'tools/svemir_model_bridge.js'),cmd]+(args or []),
                                  input=stdin,capture_output=True,text=True,encoding='utf-8',
                                  timeout=10,env=env)
            return result

    def test_bridge_does_not_invent_available_models(self):
        result=self.run_bridge('tags',models=[])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['models'],[])

    def test_show_embed_and_cloud_chat_fail_closed(self):
        self.assertNotEqual(self.run_bridge('show',['not-installed-model'],models=[]).returncode,0)
        self.assertNotEqual(self.run_bridge('embed',models=[]).returncode,0)
        cloud=self.run_bridge('chat',stdin=json.dumps({'model':'claude:sonnet','messages':[{'role':'user','content':'x'}]}),
                              models=[{'bridge':'claude','model':'sonnet','runnable':True}])
        self.assertNotEqual(cloud.returncode,0)

    def test_local_chat_reports_completed_execution_contract(self):
        models=[{'bridge':'llama','model':'qwen3.5-4b','id':'pc-llama-qwen3-5-4b','runnable':True}]
        result=self.run_bridge('chat',stdin=json.dumps({'model':'qwen3.5:4b','messages':[{'role':'user','content':'x'}]}),
                               models=models)
        self.assertEqual(result.returncode,0,result.stderr)
        doc=json.loads(result.stdout)
        self.assertEqual(doc['requested_model'],'qwen3.5:4b')
        self.assertEqual(doc['model'],'qwen3.5-4b')
        self.assertEqual(doc['backend'],'svemir-cli')
        self.assertTrue(doc['done'])
        self.assertEqual(doc['done_reason'],'stop')
        self.assertEqual(doc['message']['content'],'{"items":[]}')


class SvemirRunner(unittest.TestCase):
    @unittest.skipUnless(pathlib.Path('C:/Svemir/tools/llama_run.js').exists(), 'Svemir llama runner is not installed')
    def test_nonzero_llama_process_exit_is_not_completed(self):
        code=r"""
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('C:/Svemir/tools/llama_run.js','utf8');let printed=[],exits=[];
const fakeFs={writeFileSync:()=>{},existsSync:()=>true,unlinkSync:()=>{}};
vm.runInNewContext(source,{require:n=>n==='child_process'?{spawnSync:()=>({status:1,signal:null,stdout:'',stderr:'model load failed'})}:n==='fs'?fakeFs:require(n),process:{argv:['node','runner','fixture.gguf','fixture'],env:{},exit:c=>{exits.push(c);}},console:{log:s=>printed.push(JSON.parse(s))}});
setImmediate(()=>console.log(JSON.stringify({printed,exits})));
"""
        result=subprocess.run(['node','-e',code],capture_output=True,text=True,encoding='utf-8',timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        doc=json.loads(result.stdout.strip().splitlines()[-1])
        self.assertTrue(any(x.get('status')=='FAILED' for x in doc['printed']))
        self.assertFalse(any(x.get('status')=='COMPLETED' for x in doc['printed']))
        self.assertIn(1,doc['exits'])


class DiskCapacity(unittest.TestCase):
    def test_insufficient_space_is_refused_before_creating_release(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)/'source';root.mkdir();dest=root.parent/'release'
            with patch.object(PR,'git',return_value='fixed-oid'),patch.object(PR.shutil,'disk_usage',return_value=type('Space',(),{'free':0})()):
                with self.assertRaisesRegex(RuntimeError,'disk space insufficient'):PR.prepare(root,dest)
            self.assertFalse(dest.exists())
