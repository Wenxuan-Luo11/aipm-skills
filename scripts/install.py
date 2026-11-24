#!/usr/bin/env python3
"""Preview or install the complete lazy-loaded skill set; never overwrite changed files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def safe_target(project,relative):
    path=project/relative
    if not path.resolve().is_relative_to(project.resolve()) or path.resolve()!=path.absolute():raise ValueError('target escapes project or traverses linked directories')
    for p in [path,*path.parents]:
        if p==project.parent:break
        if p.is_symlink():raise ValueError('symlink destinations are not supported')
        if p!=path and p.exists() and not p.is_dir():raise ValueError('parent path is not a directory')
    return path

def read_manifest(path,project):
    if not path.exists():return {'pack':'aipm-dev-skills','manifest_version':1,'project':str(project),'files':{}}
    old=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(old,dict) or old.get('pack')!='aipm-dev-skills' or old.get('manifest_version')!=1 or old.get('project')!=str(project) or not isinstance(old.get('files'),dict):
        raise ValueError('unrecognized installation manifest; refusing to acquire ownership')
    names=json.loads((ROOT/'pack.json').read_text(encoding='utf-8'))['skills']
    names += ['oil-'+name.removeprefix('aipm-') for name in names if name.startswith('aipm-')]
    for rel,sha in old['files'].items():
        parts=Path(rel.replace('\\','/')).parts
        if len(parts)<4 or parts[:2]!=('.agents','skills') or parts[2] not in names or '..' in parts or not isinstance(sha,str) or len(sha)!=64:
            raise ValueError('invalid owned path or digest')
        safe_target(project,rel)
    return old

def install(project,apply=False):
    project=Path(project).resolve()
    if not project.is_dir():raise ValueError('target project must already exist')
    pack=json.loads((ROOT/'pack.json').read_text(encoding='utf-8'))
    entries=[];conflicts=[]
    for name in pack['skills']:
        folder=ROOT/'skills'/name
        for source in sorted(folder.rglob('*')):
            if not source.is_file() or '__pycache__' in source.parts or source.suffix=='.pyc':continue
            rel=Path('.agents/skills')/name/source.relative_to(folder)
            dest=safe_target(project,rel)
            if dest.exists() and (not dest.is_file() or digest(dest)!=digest(source)):conflicts.append(str(rel));continue
            entries.append((source,dest,rel))
    if conflicts:return {'status':'conflict','files':conflicts}
    new=[str(rel) for _,dest,rel in entries if not dest.exists()]
    manifest=safe_target(project,Path('.aipm/harness-install.json'))
    old=read_manifest(manifest,project)
    if apply:
        # Preserve previous ownership: identical pre-existing files are not acquired by this installer.
        owned=dict(old.get('files',{}))
        copied=[]
        try:
            manifest.parent.mkdir(parents=True,exist_ok=True)
            for source,dest,rel in entries:
                if not dest.exists():
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    with dest.open('xb') as handle:handle.write(source.read_bytes())
                    copied.append(dest);owned[rel.as_posix()]=digest(dest)
            pending=manifest.with_suffix('.pending')
            with pending.open('x',encoding='utf-8') as handle:handle.write(json.dumps({**old,'version':pack['version'],'files':owned},indent=2)+'\n')
            pending.replace(manifest)
        except OSError:
            for dest in copied:dest.unlink(missing_ok=True)
            raise
    return {'status':'installed' if apply else 'preview','new_files':new,'skill_count':len(pack['skills'])}

def remove(project,apply=False):
    project=Path(project).resolve();manifest=safe_target(project,Path('.aipm/harness-install.json'))
    if not manifest.exists():return {'status':'not_installed'}
    old=read_manifest(manifest,project);removable=[];preserved=[]
    for rel,sha in old['files'].items():
        normalized=rel.replace('\\','/')
        if not normalized.startswith('.agents/skills/') or '..' in Path(normalized).parts:raise ValueError('invalid owned path')
        p=safe_target(project,Path(normalized))
        if p.is_file() and digest(p)==sha:removable.append((rel,p))
        elif p.exists():preserved.append(rel)
    if apply:
        for _,p in removable:p.unlink()
        old['files']={rel:sha for rel,sha in old['files'].items() if rel in preserved}
        manifest.write_text(json.dumps(old,indent=2)+'\n',encoding='utf-8')
    return {'status':'removed' if apply else 'preview_remove','files':[r for r,_ in removable],'preserved_modified':preserved}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('--apply',action='store_true');p.add_argument('--remove',action='store_true');a=p.parse_args()
    try:result=remove(a.project,a.apply) if a.remove else install(a.project,a.apply)
    except (OSError,ValueError,KeyError) as e:result={'status':'error','error':str(e)}
    print(json.dumps(result,ensure_ascii=False));return int(result['status'] in ('error','conflict'))
if __name__=='__main__':raise SystemExit(main())
