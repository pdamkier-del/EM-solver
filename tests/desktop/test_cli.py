import json,subprocess,sys
from pathlib import Path

def test_cli_raw_text_then_cached_views_without_solver(tmp_path):
 raw=tmp_path/'task.txt';reply=tmp_path/'reply.json'
 raw.write_text('V(x,y,z)=k*x**2. Bestem E.',encoding='utf-8')
 first=subprocess.run([sys.executable,'-m','em1_solver.backend_client','--input',str(raw),'--output',str(reply),'--view','result'],capture_output=True,text=True,timeout=30)
 assert first.returncode==0,first.stderr
 assert json.loads(first.stdout)['status']=='verified'
 # A cached view runs even if the original task is no longer available.
 raw.unlink()
 for view in ('derivation','explanation'):
  result=subprocess.run([sys.executable,'-m','em1_solver.backend_client','--response',str(reply),'--view',view],capture_output=True,text=True,timeout=10)
  assert result.returncode==0,result.stderr
  assert json.loads(result.stdout)['steps']
