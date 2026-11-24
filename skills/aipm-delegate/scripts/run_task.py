#!/usr/bin/env python3
"""Validate a small task contract, route once, and call the adapted Oil delegate."""
from __future__ import annotations
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys

HERE = Path(__file__).resolve().parent

def relative_paths(values, field):
    if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
        raise ValueError(f"{field} must be a list of nonempty relative paths")
    for value in values:
        normalized = value.replace('\\', '/')
        p = PurePosixPath(normalized)
        if p.is_absolute() or '..' in p.parts or re.match(r'^[A-Za-z]:', normalized):
            raise ValueError(f"{field} must stay within the workspace")
    return values

def prepare(contract_path, routing_path=None):
    contract_path = Path(contract_path).resolve()
    c = json.loads(contract_path.read_text(encoding='utf-8'))
    if not isinstance(c, dict):
        raise ValueError('contract must be an object')
    required = {'id','goal','workspace','role','complexity','entry_files','allowed_paths','checks','outputs'}
    if set(c) != required:
        raise ValueError(f"contract fields must be exactly: {', '.join(sorted(required))}")
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', str(c['id'])):
        raise ValueError('id must be a short lowercase task identifier')
    if not isinstance(c['goal'], str) or not 1 <= len(c['goal']) <= 4000:
        raise ValueError('goal must contain 1–4000 characters')
    if not isinstance(c['workspace'], str) or not c['workspace']:
        raise ValueError('workspace is required')
    workspace = (contract_path.parent / c['workspace']).resolve()
    if not workspace.is_dir():
        raise ValueError('workspace must exist')
    routing = json.loads(Path(routing_path or HERE.parent/'references/routing.json').read_text(encoding='utf-8'))
    if c['role'] in routing['read_roles']:
        mode = 'read'
    elif c['role'] in routing['write_roles']:
        mode = 'write'
    else:
        raise ValueError('unsupported role')
    if c['complexity'] not in routing['profiles']:
        raise ValueError('unsupported complexity; no automatic fallback')
    profile = routing['profiles'][c['complexity']]
    for field in ('entry_files','allowed_paths','outputs'):
        relative_paths(c[field], field)
        for value in c[field]:
            if not (workspace/value).resolve().is_relative_to(workspace):
                raise ValueError(f'{field} resolves outside workspace')
    if len(c['entry_files']) > 4:
        raise ValueError('use at most four entry files; do not attach the entire repository')
    for entry in c['entry_files']:
        p = (workspace/entry).resolve()
        if not p.is_relative_to(workspace) or not p.is_file():
            raise ValueError('entry file is missing or escapes the workspace')
    if mode == 'write' and not c['allowed_paths']:
        raise ValueError('write tasks require allowed_paths')
    if not isinstance(c['checks'], list) or not all(isinstance(v,str) and v.strip() for v in c['checks']):
        raise ValueError('checks must list real verification commands')
    prompt = '\n'.join([
        c['goal'], 'Task contract: '+c['id'], 'Role: '+c['role'],
        'Allowed changes: '+json.dumps(c['allowed_paths'], ensure_ascii=False),
        'Verification commands (report what actually ran): '+json.dumps(c['checks'],ensure_ascii=False),
        'Expected outputs: '+json.dumps(c['outputs'],ensure_ascii=False),
        'Use only necessary context. Do not install, push, publish, change permissions or alter unrelated files.',
        'If scope is insufficient or verification fails, report the evidence; do not weaken tests or silently change model.',
        'Report outcome, changed files, checks and unverified items concisely. Do not claim commands ran unless they did.',
    ])
    state=workspace/'.aipm/delegate'
    if state.resolve()!=state or (workspace/'.aipm').is_symlink():
        raise ValueError('runtime state must not use linked directories')
    args = ['--home',str(state),'run','--runner','codex',
            '--workspace',str(workspace),'--mode',mode,'--model',profile['model'],
            '--effort',profile['effort'],'--prompt',prompt,'--json']
    for entry in c['entry_files']:
        args += ['--file',entry]
    return c, args

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract',required=True)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--session',help='Resume the same Codex task; not a different role')
    parser.add_argument('--timeout',type=int,default=180)
    options=parser.parse_args(argv)
    try:
        c,args=prepare(options.contract)
        if options.timeout <= 0:
            raise ValueError('timeout must be positive')
        args += ['--timeout',str(options.timeout)]
        state=Path(args[1])
        bindings_path=state/'contract-bindings.json'
        if state.exists() and any(item.resolve()!=item for item in state.rglob('*')):
            raise ValueError('runtime state must not contain linked files or directories')
        bindings=json.loads(bindings_path.read_text(encoding='utf-8')) if bindings_path.exists() else {}
        binding={'contract_id':c['id'],'workspace':args[args.index('--workspace')+1],
                 'role':c['role'],'mode':args[args.index('--mode')+1],'profile':c['complexity'],'allowed_paths':sorted(v.replace('\\','/') for v in c['allowed_paths'])}
        if options.session:
            if bindings.get(options.session)!=binding:
                raise ValueError('resume must match the original contract, workspace, role, mode and profile')
            args += ['--session',options.session]
        if options.dry_run:
            args += ['--dry-run']
        spec=importlib.util.spec_from_file_location('aipm_oil_delegate',HERE/'delegate.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            code=module.main(args)
        result=json.loads(output.getvalue())
        if not options.dry_run and code==0 and result.get('session_id'):
            bindings[result['session_id']]=binding
            state.mkdir(parents=True,exist_ok=True)
            bindings_path.write_text(json.dumps(bindings,indent=2)+'\n',encoding='utf-8')
        result.update(contract_id=c['id'], profile=c['complexity'], actual_model=None,
                      actual_model_evidence='CLI event metadata not verified',
                      checks_verified_by_coordinator=False)
        print(json.dumps(result,ensure_ascii=False))
        return code
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'status':'ERROR','error':str(exc)},ensure_ascii=False))
        return 1

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
