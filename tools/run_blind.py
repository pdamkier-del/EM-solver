"""Evaluate blind problems through the public New Problem confirmation/runtime API."""
import sys,json,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from em1_solver.core.new_problem import parse,build
from em1_solver.core.task_runtime import run_confirmed
from em1_solver.rendering.danish_solution import render
from em1_solver.rendering.latex import document
from blind_inputs import A,assisted
from blind_oracles import verify
from dataclasses import asdict

class RenderCapture:
 def __getattr__(self,name):return lambda *args,**kwargs:None

def attempt(row,p,autonomous=False):
 start=time.monotonic();result={'interpretation':asdict(p),'method':None,'outcome':'FAIL','failure_class':None,'warnings':[],'silent_wrong':False,'correct_refusal':False}
 stage='build'
 try:
  problem=build(p);result['method']=problem.family;stage='solve'
  out=run_confirmed(p,False,timeout=20)
  result.update(solution={k:str(v) for k,v in out.symbolic_result.items()},warnings=out.warnings,checks=[asdict(c)|{'residual':str(c.residual)} for c in out.checks])
  stage='oracle';verify(row['id'],p,out)
  stage='render';render(RenderCapture(),out,mode='Eksamen');assert 'Resultat' in document(out)
  result['outcome']='PASS';result['correct_refusal']=row['id'] in ('GEN02','GEN03')
 except Exception as exc:
  message=str(exc);result['comment']=message
  if row['id'] in ('GEN04','GEN05') and any(x in message.lower() for x in ['uendelig cylinder er ikke','symmetri','ukendt længde','længde og feltpunkt']):result.update(outcome='PASS',correct_refusal=True)
  elif 'Tidsgrænsen' in message:result['failure_class']='TIMEOUT';result['outcome']='TIMEOUT'
  elif stage=='render':result['failure_class']='RENDERING'
  elif stage=='oracle':
   result['failure_class']='UNITS' if 'Units' in message else 'REGION_HANDLING' if row['id']=='EV06' else 'SIGN_DIRECTION' if 'direction' in message else 'SYMBOLIC_ALGEBRA'
   result['silent_wrong']=bool(not result['warnings'] and any(c['passed'] is False for c in result.get('checks',[])) is False)
  elif 'Ukendt kombination' in message:result['failure_class']='MISSING_SOLVER_CAPABILITY'
  else:result['failure_class']='PARSER' if not p.data or not p.wanted else 'METHOD_SELECTION' if 'solver_spec' in p.data else 'INPUT_VALIDATION'
 result['failure_stage']=stage if result['outcome']!='PASS' else None
 if autonomous and result['outcome']=='FAIL' and stage in ('build','oracle') and result['failure_class'] in ('INPUT_VALIDATION','METHOD_SELECTION','UNITS'):
  result['secondary_failure_class']=result['failure_class'];result['failure_class']='PARSER'
 result['elapsed_seconds']=round(time.monotonic()-start,3)
 return result

def main():
 mode=sys.argv[1] if len(sys.argv)>1 else 'baseline';full=mode=='full'
 rows=json.loads((ROOT/'data/blind_unseen_bank_v2.json').read_text())['tests'];rows=[r for r in rows if full or r['id'] in A]
 manifest=json.loads((ROOT/'reports/blind_baseline_source_manifest.json').read_text())
 if mode=='baseline':
  for name,h in manifest['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,'Baseline code changed: '+name
 source_start={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'app.py',*sorted((ROOT/'em1_solver').rglob('*.py'))]}
 records=[]
 for row in rows:
  auto=attempt(row,parse(row['problem']),autonomous=True)
  aided=auto if auto['outcome']=='PASS' else attempt(row,assisted(row))
  records.append(dict(id=row['id'],domain='GEN' if row['id'].startswith('GEN') else row['domain'],autonomous=auto,assisted=aided))
  print(row['id'],auto['outcome'],aided['outcome'],aided.get('failure_class'),flush=True)
 path=ROOT/'reports'/('blind_unseen_full' if full else 'blind_unseen_baseline' if mode=='baseline' else 'blind_unseen_after_fixes')
 def metric(rs,key):
  passed=sum(r[key]['outcome']=='PASS' for r in rs)
  return dict(total=len(rs),passed=passed,percent=round(100*passed/len(rs),1) if rs else 0,correct_refusals=sum(r[key]['correct_refusal'] for r in rs),silent_wrong=sum(r[key]['silent_wrong'] for r in rs),timeouts=sum(r[key]['outcome']=='TIMEOUT' for r in rs))
 from collections import Counter
 summary={k:metric(records,k) for k in ('autonomous','assisted')}
 summary['domains']={d:{k:metric([r for r in records if r['domain']==d],k) for k in ('autonomous','assisted')} for d in ['EV','BA','DYN','GEN']}
 summary['failure_distribution']={k:dict(Counter(r[k]['failure_class'] for r in records if r[k]['outcome']!='PASS')) for k in ('autonomous','assisted')}
 source_end={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'app.py',*sorted((ROOT/'em1_solver').rglob('*.py'))]}
 assert source_start==source_end,'Koden ændrede sig under målingen; genkør benchmark.'
 path.with_suffix('.json').write_text(json.dumps(dict(summary=summary,records=records,source_manifest=source_start,bank_sha256=hashlib.sha256((ROOT/'data/blind_unseen_bank_v2.json').read_bytes()).hexdigest(),evaluator_manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'tools/run_blind.py',ROOT/'tools/blind_inputs.py',ROOT/'tools/blind_oracles.py']}),ensure_ascii=False,indent=2,default=str)+'\n')
 lines=['# Blind unseen '+mode,'','Offentlig kæde: parse → redigerbar Parsed → build → run_confirmed (separat proces) → Solution → Eksamen-rendering og LaTeX → uafhængige orakler. Autonomous bruger kun bankens opgavetekst; assisted-input er manuel transskription, ingen facitindsættelse.','', '| ID | Autonomous | Assisted | Method | Failure class | Kommentar |','|---|---|---|---|---|---|']
 for r in records:
  a=r['assisted'];lines.append(f"| {r['id']} | {r['autonomous']['outcome']} | {a['outcome']} | {a['method']} | {a['failure_class'] or '—'} | {a.get('comment','').replace('|','/').replace(chr(10),' ')[:220]} |")
 lines+=['','## Metrics','', '```json',json.dumps(summary,ensure_ascii=False,indent=2),'```','', 'Baselinekode: reports/blind_baseline_source_manifest.json. Rå fortolkninger, resultater, warnings, checks og tider findes i rapportens JSON-sidefil. Testbanken er nu set; genkørsel efter fixes er regression på denne bank, ikke en ny blindtest.']
 path.with_suffix('.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
