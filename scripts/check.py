#!/usr/bin/env python3
"""Reuse exact local evidence; keep full logs out of model context. CI always runs fresh."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '.aipm', '__pycache__', '.venv'}

def fingerprint(root, commands, environment=None):
    h = hashlib.sha256()
    runtime = [sys.executable, sys.version, platform.platform(), commands,
               environment if environment is not None else sorted(os.environ.items())]
    h.update(json.dumps(runtime, sort_keys=True).encode())
    for p in sorted(root.rglob('*')):
        if any(part in SKIP for part in p.relative_to(root).parts) or not p.is_file() or p.suffix=='.pyc':
            continue
        h.update(p.relative_to(root).as_posix().encode()+b'\0'+p.read_bytes()+b'\0')
    for args in [['status', '--porcelain=v1'], ['diff', '--binary'], ['diff', '--cached', '--binary']]:
        result = subprocess.run(['git', *args], cwd=root, capture_output=True)
        if result.returncode:
            raise RuntimeError('Git state could not be read; refusing evidence reuse')
        h.update(result.stdout)
    revision=subprocess.run(['git','rev-parse','--verify','HEAD'],cwd=root,capture_output=True)
    h.update(revision.stdout if revision.returncode==0 else b'unborn-head')
    whitespace=subprocess.run(['git','config','--get','core.whitespace'],cwd=root,capture_output=True)
    if whitespace.returncode not in (0,1):
        raise RuntimeError('Git whitespace configuration could not be read')
    h.update(whitespace.stdout)
    return h.hexdigest()

def reusable(record, key):
    return record.get('key')==key and record.get('status')=='passed'

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Ignore local successful evidence')
    options=parser.parse_args(argv)
    state=ROOT/'.aipm';state.mkdir(exist_ok=True)
    log=state/'check.log'; evidence=state/'check-evidence.json'
    commands=[('resources',[sys.executable,'-X','utf8','scripts/validate.py']),
              ('unit_tests',[sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-v']),
              ('whitespace',['git','diff','--check']),
              ('staged_whitespace',['git','diff','--cached','--check'])]
    key=fingerprint(ROOT,commands)
    try: previous=json.loads(evidence.read_text(encoding='utf-8'))
    except (OSError,ValueError): previous={}
    if not options.force and not os.environ.get('CI') and reusable(previous,key):
        print(json.dumps({**previous,'reused':True,'log':'.aipm/check.log'}));return 0
    rows=[]
    with log.open('w',encoding='utf-8') as out:
        for name,command in commands:
            started=time.monotonic()
            result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
            rows.append({'check':name,'exit_code':result.returncode,'seconds':round(time.monotonic()-started,3)})
            if result.returncode:break  # diagnose from the log; never auto-retry failed checks
    stable=fingerprint(ROOT,commands)==key
    passed=all(r['exit_code']==0 for r in rows) and stable
    report={'status':'passed' if passed else 'failed','key':key,'checks':rows,
            'inputs_stable':stable,'reused':False,'log':'.aipm/check.log'}
    if passed:evidence.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    else:evidence.unlink(missing_ok=True)
    print(json.dumps(report));return int(not passed)

if __name__=='__main__':
    raise SystemExit(main())
