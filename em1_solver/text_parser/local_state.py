"""Versioned parser draft, separate from the frozen manual form's autosave."""
import json,os,tempfile
from ..core.local_state import path

def location():return path().with_name('text-parser.json')
def load():
    p=location()
    if not p.exists():return None
    if p.stat().st_size>500000:raise ValueError('Autosave er for stor.')
    data=json.loads(p.read_text(encoding='utf-8'))
    if data.get('version')!=1 or not isinstance(data.get('text'),str) or not isinstance(data.get('corrections'),dict):raise ValueError('Ukendt parser-autosaveformat.')
    return data

def save(text,corrections,answer=None):
    p=location();p.parent.mkdir(parents=True,exist_ok=True)
    handle,name=tempfile.mkstemp(prefix='parser-',dir=p.parent)
    try:
        with os.fdopen(handle,'w',encoding='utf-8') as stream:
            json.dump(dict(version=1,text=text,corrections=corrections,answer=answer),stream,ensure_ascii=False)
            stream.flush();os.fsync(stream.fileno())
        os.replace(name,p)
    finally:
        if os.path.exists(name):os.unlink(name)
