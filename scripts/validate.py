#!/usr/bin/env python3
"""Dependency-free package/resource and pinned-source integrity checks (not behavioral evals)."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
def validate(root=ROOT):
    errors=[]
    pack=json.loads((root/'pack.json').read_text(encoding='utf-8'))
    names=pack['skills']
    if len(names)!=len(set(names)):errors.append('duplicate skill in manifest')
    actual={p.name for p in (root/'skills').iterdir() if p.is_dir() and (p/'SKILL.md').exists()}
    if set(names)!=actual:errors.append('manifest differs from skills directories')
    for name in names:
        folder=root/'skills'/name
        if name.startswith('aipm-'):
            notice=folder/'SOURCE-NOTICE.md'
            license_text=(root/'notices/OIL-MIT.txt').read_text(encoding='utf-8').strip()
            if not notice.is_file() or license_text not in notice.read_text(encoding='utf-8'):
                errors.append(f'{name}: missing upstream copyright/permission notice')
        text=(folder/'SKILL.md').read_text(encoding='utf-8')
        match=re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)',text,re.S)
        if not match:errors.append(f'{name}: missing frontmatter');continue
        fields=dict(re.findall(r'^([a-z_-]+):\s*(.+)$',match[1],re.M))
        if fields.get('name')!=name:errors.append(f'{name}: name mismatch')
        if not fields.get('description','').strip('"\' '):errors.append(f'{name}: missing description')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name) or len(name)>64:errors.append(f'{name}: invalid name')
        for md in folder.rglob('*.md'):
            content=re.sub(r'```.*?```','',(md.read_text(encoding='utf-8')),flags=re.S)
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',content):
                if target.startswith(('https:','http:','mailto:','#')):continue
                target=unquote(target.split('#',1)[0].split(' "',1)[0])
                resolved=(md.parent/target).resolve()
                if not resolved.is_relative_to(root.resolve()):errors.append(f'{md.relative_to(root)}: resource escapes package')
                elif not resolved.exists():errors.append(f'{md.relative_to(root)}: missing {target}')
    lock=json.loads((root/'upstream.lock.json').read_text(encoding='utf-8'))
    for rel,digest in lock['oil']['upstream_manifest'].items():
        p=root/'upstream/oil-dev-skills'/rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:errors.append(f'upstream changed: {rel}')
    for notice in ('OIL-MIT.txt','ADDY-MIT.txt'):
        if not (root/'notices'/notice).is_file():errors.append('missing license '+notice)
    return errors

if __name__=='__main__':
    failures=validate()
    print(json.dumps({'status':'failed' if failures else 'passed','errors':failures},ensure_ascii=False))
    raise SystemExit(bool(failures))
