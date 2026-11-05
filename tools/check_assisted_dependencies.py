"""Offline replay with only pinned distributions under Python -S; no downloads."""
import sys, tempfile, shutil, subprocess, json, os
from pathlib import Path
from importlib.metadata import distribution
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='em1-assisted-deps-') as folder:
 target=Path(folder)/'dependencies'; target.mkdir()
 packages={}
 for line in (root/'requirements-backend-lock.txt').read_text().splitlines():
  if not line or line.startswith('#'): continue
  name,version=line.split('==');d=distribution(name);assert d.version==version;packages[name]=version
  for file in d.files:
   if '..' in file.parts or str(file).endswith('.pyc'):continue
   source=d.locate_file(file)
   if source.is_file():
    dest=target/file;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
 script=Path(folder)/'check.py'
 script.write_text('import sys,json\nfrom pathlib import Path\nsys.path[:0]='+repr([str(target),str(root)])+'''\nfrom em1_solver.assisted_backend import respond
from em1_solver.core.task_runtime import block_network
if __name__ == '__main__':
 import multiprocessing
 multiprocessing.freeze_support();block_network()
 states=[]
 for path in sorted(Path('data/integration/assisted_v1').glob('*.request.json')):
  result=respond(json.loads(path.read_text()),solve=True)
  assert result==json.loads(path.with_name(path.name.replace('.request.','.response.')).read_text()),path.name
  states.append(result['status'])
 assert not any(n.split('.')[0] in ('streamlit','PySide6','numpy','pandas') for n in sys.modules)
 print(json.dumps(dict(statuses=states,network='blocked',isolated_no_site=True,frontend_imported=False)))
''')
 env=os.environ.copy();env.pop('PYTHONPATH',None);env['PYTHONNOUSERSITE']='1'
 p=subprocess.run([sys.executable,'-S',str(script)],cwd=root,env=env,capture_output=True,text=True,timeout=90)
 assert p.returncode==0,p.stderr
 report=json.loads(p.stdout);report['dependencies']=packages
 (root/'reports/assisted_evening/dependency_isolation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
