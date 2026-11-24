import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('check',ROOT/'scripts/check.py')
CHECK=importlib.util.module_from_spec(spec);spec.loader.exec_module(CHECK)

class EvidenceTests(unittest.TestCase):
    def test_git_baseline_and_whitespace_configuration_invalidate_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def git(*args):
                return subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True)
            git('init');git('config','core.autocrlf','false')
            p=root/'facts.txt';p.write_bytes(b'base \n')
            git('add','.');git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','A')
            first=git('rev-parse','HEAD').stdout.decode().strip()
            p.write_bytes(b'base\n');git('add','.')
            git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','B')
            p.write_bytes(b'base \nmore\n')
            before=CHECK.fingerprint(root,[],{})
            result=subprocess.run(['git','-C',str(root),'diff','--check'],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            git('reset','--mixed',first)
            self.assertEqual(subprocess.run(['git','-C',str(root),'diff','--check'],capture_output=True).returncode,0)
            self.assertNotEqual(before,CHECK.fingerprint(root,[],{}))
            before=CHECK.fingerprint(root,[],{})
            git('config','core.whitespace','-trailing-space')
            self.assertNotEqual(before,CHECK.fingerprint(root,[],{}))
    def test_changed_content_environment_or_command_invalidates_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);subprocess.run(['git','init',str(root)],capture_output=True,check=True)
            p=root/'facts.txt';p.write_text('original')
            def key(command='test', env='one'):
                return CHECK.fingerprint(root,[command],{'setting':env})
            old=key();p.write_text('changed')
            self.assertNotEqual(old,key());self.assertNotEqual(key(),key(env='two'))
            self.assertNotEqual(key(),key(command='different'))
            before=key();p.unlink();self.assertNotEqual(before,key())
    def test_log_changes_do_not_invalidate_and_failures_are_not_reusable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);subprocess.run(['git','init',str(root)],capture_output=True,check=True)
            subprocess.run(['git','-C',str(root),'config','core.excludesFile',''],check=True)
            (root/'.gitignore').write_text('.aipm/\n')
            old=CHECK.fingerprint(root,[],{})
            (root/'.aipm').mkdir();(root/'.aipm/log').write_text('new output')
            self.assertEqual(old,CHECK.fingerprint(root,[],{}))
            self.assertFalse(CHECK.reusable({'key':old,'status':'failed'},old))
            self.assertFalse(CHECK.reusable({'key':old,'status':'passed'},'different'))
            self.assertTrue(CHECK.reusable({'key':old,'status':'passed'},old))
