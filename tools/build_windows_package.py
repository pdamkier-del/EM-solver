"""Reproducible source/application package; Windows wheels are prepared separately."""
from pathlib import Path
import hashlib,zipfile,sys,json,subprocess
ROOT=Path(__file__).resolve().parents[1]

def build(target):
    target=Path(target);excluded={'.git','.venv','__pycache__','.pytest_cache','.local-state','wheelhouse'}
    files=[p for p in ROOT.rglob('*') if p.is_file() and not (set(p.relative_to(ROOT).parts)&excluded) and p.suffix!='.pyc' and p.name not in ('feature_freeze.json','test-results.json','test-results.xml')]
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            info=zipfile.ZipInfo('EM1-Solver/'+str(path.relative_to(ROOT)).replace('\\','/'),date_time=(2026,11,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            archive.writestr(info,path.read_bytes())
        info=zipfile.ZipInfo('EM1-Solver/BUILD_INFO.json',date_time=(2026,11,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        archive.writestr(info,json.dumps({'commit':commit,'checkpoint':'exam-ready-2026-11-05','windows_native_validation':'not executed in Linux environment; follow docs/WINDOWS_INSTALLATION.md'},indent=2)+'\n')
    digest=hashlib.sha256(target.read_bytes()).hexdigest();target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n')
    print(str(target),digest)
if __name__=='__main__':build(sys.argv[1] if len(sys.argv)>1 else str(ROOT.parent/'EM1-Solver-Windows.zip'))
