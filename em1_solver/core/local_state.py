"""Atomic local-only autosave. No pickle, remote storage or credential data."""
import json,os,tempfile
from pathlib import Path

def path(filename='latest.json'):
    if filename not in ('latest.json','specialized.json'):raise ValueError('Ukendt lokal autosave-fil.')
    override=os.environ.get('EM1_STATE_DIR')
    root=Path(override) if override else Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'EM1Solver'
    return root/filename

def load(filename='latest.json'):
    target=path(filename)
    if not target.exists():return None
    value=json.loads(target.read_text(encoding='utf-8'))
    if value.get('version')!=1 or not isinstance(value.get('problem'),dict):raise ValueError('Ukendt autosave-format.')
    return value

def save(problem,answer=None,filename='latest.json'):
    target=path(filename);target.parent.mkdir(parents=True,exist_ok=True)
    previous=load(filename) if target.exists() else None
    payload={'version':1,'problem':problem,'answer':answer if answer is not None else previous.get('answer') if previous and previous['problem']==problem else None}
    fd,name=tempfile.mkstemp(prefix='em1-',suffix='.tmp',dir=target.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(name,target)
    finally:
        if os.path.exists(name):os.unlink(name)
    return target
