"""Deterministic combined app/source ZIP. Does not rebuild frozen releases."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def build(target):
    target=Path(target);files={};prefix='EM1-Desktop-Integrated/'
    def add_tree(base,sub):
        for path in sorted(base.rglob('*')):
            if not path.is_file() or set(path.relative_to(base).parts)&{'__pycache__','.pytest_cache','vendor','wheelhouse','.git'}:continue
            if path.suffix=='.pyc' or path.name.startswith('EM1_ERROR_LOG') or path.name.startswith('EM1_START_LOG'):continue
            files[sub+path.relative_to(base).as_posix()]=path.read_bytes()
    add_tree(ROOT/'desktop_app','')
    backend='vendor/EM-solver-assisted/'
    for name in ['em1_solver','desktop_integration','data','tests']:add_tree(ROOT/name,backend+name+'/')
    for name in ['requirements-backend-lock.txt','tools/certify_solvers.py']:
        files[backend+name]=(ROOT/name).read_bytes()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    manifest=dict(source_base_commit=commit,working_tree_changes=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),native_windows_tested=False,files={name:hashlib.sha256(data).hexdigest() for name,data in sorted(files.items())})
    files['BUILD_MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w') as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(prefix+name,(2026,11,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,data)
    sha=hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(sha+'  '+target.name+'\n')
    print(json.dumps(dict(path=str(target),bytes=target.stat().st_size,sha256=sha)))


if __name__=='__main__':build(sys.argv[1])
