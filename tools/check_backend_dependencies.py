"""Exercise the backend with ONLY the seven pinned installed runtime distributions.

No download, pip install, frontend library or network. An isolated -S interpreter
uses a temporary copy of the declared distributions and the project source/data.
"""
import sys,json,tempfile,shutil,subprocess,os
from pathlib import Path
from importlib.metadata import distribution
ROOT=Path(__file__).resolve().parents[1]

def main():
 packages={}
 for line in (ROOT/'requirements-backend-lock.txt').read_text().splitlines():
  if line and not line.startswith('#'):
   name,version=line.split('==');packages[name]=version
 with tempfile.TemporaryDirectory(prefix='em1-backend-only-') as folder:
  target=Path(folder)/'dependencies';target.mkdir()
  for name,version in packages.items():
   dist=distribution(name);assert dist.version==version,(name,dist.version,version)
   for file in dist.files or []:
    if '..' in file.parts or str(file).endswith('.pyc'):continue
    source=dist.locate_file(file)
    if source.is_file():
     dest=target/file;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
  script=Path(folder)/'isolated.py'
  bootstrap='import sys,json\nsys.path[:0]='+repr([str(target),str(ROOT)])+'\n'
  program='''
from em1_solver.backend_client import run_text,choose_view
from em1_solver.core.task_runtime import block_network
if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support();block_network()
    cases=[
      'V(x,y,z)=k*x**2. Bestem E.',
      'I et kartesisk system er punktladning q1=3 nC i origo. d=2 cm. Bestem E i punktet (d,0,0).',
      'En kugle med radius R består af et lineært isotropt dielektrikum med relativ permittivitet epsilon_r. Den frie ladningstæthed er rho(r)=k*r. Der er vakuum udenfor. Bestem D, E og P.'
    ]
    statuses=[]
    for text in cases:
        reply=run_text(text)
        assert reply['status'] in ('verified','verified_with_assumptions'),reply
        for level in ('result','derivation','explanation'):choose_view(reply,level)
        statuses.append(reply['status'])
    import sympy,pint
    assert not any(name.split('.')[0] in ('streamlit','PySide6','numpy','pandas') for name in sys.modules)
    assert 'dependencies' in sympy.__file__ and 'dependencies' in pint.__file__
    print(json.dumps(dict(statuses=statuses,frontend_imported=False,network='blocked',isolated_python_no_site=True)))
'''
  script.write_text(bootstrap+program,encoding='utf-8')
  env=os.environ.copy();env.pop('PYTHONPATH',None);env['PYTHONNOUSERSITE']='1'
  result=subprocess.run([sys.executable,'-S',str(script)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=90)
  if result.returncode:raise RuntimeError(result.stderr+'\n'+result.stdout)
  report=json.loads(result.stdout);report['pinned_distributions']=packages
  (ROOT/'reports/desktop/dependency_isolation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
