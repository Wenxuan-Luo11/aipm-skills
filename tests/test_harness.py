import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
INSTALL=load('installer','scripts/install.py')
VALIDATE=load('validator','scripts/validate.py')
TASK=load('task','skills/aipm-delegate/scripts/run_task.py')
DELEGATE=load('delegate','skills/aipm-delegate/scripts/delegate.py')

class InstallTests(unittest.TestCase):
    def test_legacy_oil_manifest_can_remove_owned_unchanged_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();p=root/'.agents/skills/oil-plan/SKILL.md'
            p.parent.mkdir(parents=True);p.write_text('old version')
            manifest=root/'.aipm/harness-install.json';manifest.parent.mkdir()
            manifest.write_text(json.dumps({'pack':'aipm-dev-skills','manifest_version':1,'project':str(root),
                'files':{'.agents/skills/oil-plan/SKILL.md':INSTALL.digest(p)}}))
            result=INSTALL.remove(root,True)
            self.assertEqual(result['status'],'removed');self.assertFalse(p.exists())
    def test_preview_does_not_write_and_install_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);sentinel=root/'AGENTS.md';sentinel.write_text('existing rules')
            self.assertEqual(INSTALL.install(root)['status'],'preview');self.assertFalse((root/'.agents').exists())
            first=INSTALL.install(root,True);self.assertEqual(first['skill_count'],9)
            self.assertEqual(INSTALL.install(root,True)['new_files'],[])
            self.assertEqual(sentinel.read_text(),'existing rules')
            self.assertTrue((root/'.agents/skills/product-discovery/references/research-record.md').is_file())
    def test_conflict_is_reported_before_any_copy(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'.agents/skills/aipm-plan/SKILL.md';p.parent.mkdir(parents=True);p.write_text('my custom plan')
            self.assertEqual(INSTALL.install(root,True)['status'],'conflict')
            self.assertEqual(p.read_text(),'my custom plan');self.assertFalse((root/'.agents/skills/product-discovery').exists())
    def test_remove_preserves_changed_and_preexisting_identical_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);pre=root/'.agents/skills/delivery-check/SKILL.md';pre.parent.mkdir(parents=True);pre.write_bytes((ROOT/'skills/delivery-check/SKILL.md').read_bytes())
            INSTALL.install(root,True);changed=root/'.agents/skills/aipm-plan/SKILL.md';changed.write_text('user edits')
            result=INSTALL.remove(root,True);self.assertIn('.agents/skills/aipm-plan/SKILL.md',result['preserved_modified'])
            self.assertEqual(changed.read_text(),'user edits');self.assertTrue(pre.exists());self.assertFalse((root/'.agents/skills/aipm-explore/SKILL.md').exists())
    def test_runtime_parent_file_fails_before_copy(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'.aipm').write_text('keep')
            with self.assertRaises(ValueError):INSTALL.install(root,True)
            self.assertFalse((root/'.agents').exists())
    def test_foreign_manifest_is_preserved_before_copy(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'.aipm/harness-install.json';p.parent.mkdir();p.write_text('{"note":"keep"}')
            with self.assertRaises(ValueError):INSTALL.install(root,True)
            self.assertEqual(p.read_text(),'{"note":"keep"}');self.assertFalse((root/'.agents').exists())
    def test_tampered_manifest_cannot_remove_outside_project(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'.aipm/harness-install.json';p.parent.mkdir();p.write_text(json.dumps({'files':{'../outside.txt':'bad'}}))
            with self.assertRaises(ValueError):INSTALL.remove(root,True)

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);(self.root/'README.md').write_text('facts')
        self.c={'id':'sample','goal':'Read facts','workspace':'.','role':'review','complexity':'routine','entry_files':['README.md'],'allowed_paths':[],'checks':[],'outputs':[]}
        self.path=self.root/'task.json'
    def tearDown(self):self.temp.cleanup()
    def prepare(self):self.path.write_text(json.dumps(self.c));return TASK.prepare(self.path)
    def test_review_is_read_only_and_routes_explicit_model(self):
        _,args=self.prepare();self.assertEqual(args[args.index('--mode')+1],'read');self.assertEqual(args[args.index('--model')+1],'gpt-6.1-sol')
    def test_implementation_requires_scope(self):
        self.c['role']='implement'
        with self.assertRaises(ValueError):self.prepare()
        self.c['allowed_paths']=['src/**'];_,args=self.prepare();self.assertEqual(args[args.index('--mode')+1],'write')
    def test_missing_entry_and_parent_traversal_are_rejected(self):
        for paths in [['../outside'],['C:\\outside'],['missing.md']]:
            self.c['entry_files']=paths
            with self.assertRaises(ValueError):self.prepare()
    def test_unknown_model_profile_or_override_does_not_silently_fallback(self):
        self.c['complexity']='cheapest-magic'
        with self.assertRaises(ValueError):self.prepare()
        self.c['complexity']='routine';self.c['mode']='write'
        with self.assertRaises(ValueError):self.prepare()

class DelegateTests(unittest.TestCase):
    def test_new_and_resumed_codex_modes_keep_sandbox(self):
        for session in [None,'session-id']:
            for mode in ['read','write']:
                args,stdin,_=DELEGATE.build_invocation('codex','codex',ROOT,'brief',session,mode,None,model='gpt-6.1-sol',effort='low')
                self.assertNotIn('--dangerously-bypass-approvals-and-sandbox',args)
                self.assertTrue(any(('read-only' if mode=='read' else 'workspace-write') in a for a in args));self.assertEqual(stdin,'brief')
    def test_checkout_config_cannot_select_executable(self):
        info=DELEGATE.detect_binary('codex',{'runner_paths':{'codex':'checkout-controlled.exe'}})
        self.assertNotEqual(info.get('source'),'config')
    def test_linked_scope_is_rejected(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            root=Path(d);target=root/'link'
            try:target.symlink_to(Path(other),target_is_directory=True)
            except OSError:self.skipTest('symlink creation unavailable on host')
            with self.assertRaises(DELEGATE.DelegateError):DELEGATE.resolve_state_dir(str(target))
    def test_unvalidated_runners_are_not_executed(self):
        with self.assertRaises(DELEGATE.DelegateError):DELEGATE.build_invocation('claude','claude',ROOT,'brief',None,'write',None)
    def test_protocol_requires_response_and_surfaces_turn_failure(self):
        started=json.dumps({'type':'thread.started','thread_id':'s'})
        message=json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Evidence report'}})
        self.assertEqual(DELEGATE.parse_runner_output('codex',started+'\n'+message+'\n'+json.dumps({'type':'turn.completed'}),'',0,None)['status'],'completed')
        self.assertEqual(DELEGATE.parse_runner_output('codex',started,'',0,None)['status'],'failed')
        self.assertEqual(DELEGATE.parse_runner_output('codex',started+'\n'+message,'',0,None)['status'],'failed')
        failed=json.dumps({'type':'turn.failed','error':{'message':'Unavailable model'}})
        result=DELEGATE.parse_runner_output('codex',started+'\n'+message+'\n'+failed,'',0,None);self.assertEqual(result['status'],'failed');self.assertIn('Unavailable model',result['error'])

class PackageTests(unittest.TestCase):
    def test_pack_resources_and_pinned_sources_are_intact(self):self.assertEqual(VALIDATE.validate(),[])

if __name__=='__main__':unittest.main()
