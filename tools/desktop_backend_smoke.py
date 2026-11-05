"""Offline UI-independent contract smoke, including cached presentation levels."""
import sys,json,copy,hashlib,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from em1_solver.backend_client import run_text,choose_view
from em1_solver.core.task_runtime import block_network

CASES=[
 ('EV_point','I et kartesisk system er punktladning q1 ved (-a,0,0); punktladning q2 ved (a,0,0). Bestem E i origo.'),
 ('EV_potential','En kugleskal a<r<b har rho(r)=k/r**2. V(infinity)=0. Bestem V og Q.'),
 ('EV_material','En kugle med radius R består af et lineært isotropt dielektrikum med relativ permittivitet epsilon_r. Den frie ladningstæthed er rho(r)=k*r. Der er vakuum udenfor. Bestem D, E og P.'),
 ('BA','En uendelig cylinder med radius R har J(s)=k*s zhat. Bestem B og den totale strøm I.'),
 ('DYN','En kondensator har cirkulære plader med radius R. E(t)=E0*t**2 zhat er uniformt mellem pladerne. Randeffekter ignoreres. Bestem B(s,t) og forskydningsstrøm.'),
 ('missing','En cylinder med radius R har rho(s)=k*s. Bestem E.')]

def main():
 block_network();records=[]
 try:import jsonschema
 except ImportError:jsonschema=None
 schema=json.loads((ROOT/'docs/backend/schema-v1.json').read_text())
 fixtures=ROOT/'data/integration/desktop_v1';fixtures.mkdir(parents=True,exist_ok=True)
 for name,text in CASES:
  request=dict(schema_version='1.0',text=text,corrections={},evaluate_integrals=False)
  response=run_text(text)
  if jsonschema is not None:jsonschema.validate(response,schema)
  for kind,payload in [('request',request),('response',response)]:
   (fixtures/(name+'.'+kind+'.json')).write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
  before=copy.deepcopy(response)
  levels={level:choose_view(response,level) for level in ('result','derivation','explanation')}
  assert response==before
  assert response['status']=='not_solved' if name=='missing' else response['status'] in ('verified','verified_with_assumptions')
  records.append(dict(case=name,status=response['status'],levels=list(levels),steps=len(response['solution']['steps']) if response['solution'] else 0))
 source_hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'em1_solver').rglob('*.py'))}
 fixture_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(fixtures.glob('*.json')) if p.name!='index.json'}
 (fixtures/'index.json').write_text(json.dumps(dict(schema_version='1.0',presentation_version='1.0',python=platform.python_version(),cases=records,files_sha256=fixture_hashes,source_sha256=source_hashes,requirements_sha256=hashlib.sha256((ROOT/'requirements-backend-lock.txt').read_bytes()).hexdigest()),indent=2)+'\n')
 (ROOT/'reports/desktop/backend_smoke.json').write_text(json.dumps(dict(network='outbound socket connections blocked',formal_json_schema_validated=jsonschema is not None,cases=records),indent=2)+'\n')
 print(json.dumps(records),flush=True)
if __name__=='__main__':
 import multiprocessing
 multiprocessing.freeze_support();main()
