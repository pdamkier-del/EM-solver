import os,sys,json,zipfile,hashlib,time,copy
from pathlib import Path
OUT=Path(__file__).resolve().parent
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['APPDATA']=str(OUT/'local_state');os.environ['MPLCONFIGDIR']=str(OUT/'mpl_cache')
archive=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[2]/'distribution/EM1-Solver-Desktop-Workflow-2026-11-05.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='5d3846e05f4a9a15733e1f3ca88a83d18e97bfc92aaffab7f4984f5da13a278d'
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;z.extractall(OUT/'delivered_app')
ROOT=OUT/'delivered_app/EM1-Desktop-Integrated';VENDOR=ROOT/'vendor/EM-solver-assisted';sys.path[:0]=[str(ROOT),str(VENDOR)]
from PySide6.QtWidgets import QApplication,QLabel,QTableWidgetItem
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
import app as host
from em1_solver.assisted_backend import MODELS
from em1_solver.core.task_runtime import block_network


def wait(q,predicate,seconds):
 end=time.monotonic()+seconds
 while not predicate() and time.monotonic()<end:q.processEvents();QTest.qWait(10)
 q.processEvents()
 if not predicate():raise RuntimeError('GUI timeout')


def fill(p,r):
 p.text.setPlainText(r['text']);p.model.setCurrentIndex(p.model.findData(r['subproblems'][0]['model']))
 def form(v):return '['+','.join(form(x) for x in v)+']' if isinstance(v,list) else str(v)
 for key,value in r['variables'].items():
  if key in p.tables:
   t=p.tables[key];t.setRowCount(len(value))
   for row,item in enumerate(value):
    cells=[item[0],*item[1]] if key=='charges' else list(item.values()) if isinstance(item,dict) else item
    for col,cell in enumerate(cells):t.setItem(row,col,QTableWidgetItem(str(cell)))
  else:p.fields[key].setText(form(value))
 ops=r['subproblems'][0].get('operations',[]);p.operations.setRowCount(len(ops));keys=('kind','id','result','variable','value','at','domain','unit','lower','upper','coefficient','resistance','initial')
 for row,op in enumerate(ops):
  for col,key in enumerate(keys):p.operations.setItem(row,col,QTableWidgetItem(op.get(key,'')))
 p._scan_symbols();defaults={'E':'V/m','B':'T','V':'V','I':'A','EMF':'V','Q':'C'}
 for row in range(p.symbols.rowCount()):
  name=p.symbols.item(row,0).text();unit=r['units'].get(name,defaults.get(name,''));p.symbols.setItem(row,1,QTableWidgetItem(unit));p.symbols.setItem(row,2,QTableWidgetItem(r['numbers'].get(name,'')));p.symbols.item(row,3).setCheckState(Qt.Checked if name in r['positive'] else Qt.Unchecked)
 p.wanted.setText(','.join(r['subproblems'][0]['wanted']))
 for condition in r['assumptions']:
  if condition in p.conditions:p.conditions[condition].setChecked(True)
 p.orientation.setChecked(True);p.confirm.setChecked(True)
 return dict(prompt=1,open_model=1,model_selection=1,scalar_field_entries=sum(bool(v.text()) for v in p.fields.values()),table_cells=sum(t.rowCount()*t.columnCount() for t in p.tables.values()),scan_symbols=1,unit_entries=p.symbols.rowCount(),numeric_entries=sum(bool(p.symbols.item(row,2).text()) for row in range(p.symbols.rowCount())),positive_flags=len(r['positive']),wanted=1,conditions=sum(b.isChecked() for b in p.conditions.values()),orientation=1,confirmation=1,solve=1,operation_cells=sum(len(op) for op in ops))


def main():
 p=OUT/'questions_and_inputs.json';seal=json.loads((OUT/'seal.json').read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==seal['sha256'];cases=json.loads(p.read_text())
 block_network();q=QApplication([]);q.setStyle('Fusion');q.setStyleSheet(host.STYLE);host.init_db();w=host.MainWindow();w.show();s=w.solver;records=[];prior={};guided={}
 for case in cases:
  id=case['id'];previous=OUT/(id+'.app.json')
  if previous.exists():
   a=json.loads(previous.read_text());records.append(a);prior[id]=a
   if a.get('route')=='guided_shared' and a.get('guided_response'):guided[case['head']]=a
   print(id,'already recorded',flush=True);continue
  record=dict(id=id,domain=case['domain'],route=case['plan']['route'],text=case['text'])
  s.prompt.setPlainText(case['text']);QTest.mouseClick(s.solve_button,Qt.LeftButton);wait(q,lambda:s.solve_button.isEnabled(),125)
  record['automatic_reply']=copy.deepcopy(s._backend_reply);record['automatic_view']=copy.deepcopy(s.last_payload);record['automatic_semantic_actions']=2
  plan=case['plan']
  try:
   if plan['route']=='guided_shared':
    if case['head'] not in guided:
     s.prompt.setPlainText(case['full_head']);QTest.mouseClick(s.review_button,Qt.LeftButton);p=s.task_review;wait(q,lambda:not p.busy,15)
     record['proposal']=copy.deepcopy(p.proposal);record['guided_status_before_solve']=p.status.text()
     if not p.proposal:raise RuntimeError(p.status.text())
     QTest.mouseClick(p.confirm,Qt.LeftButton,pos=QPoint(8,p.confirm.height()//2));QTest.mouseClick(p.solve,Qt.LeftButton);wait(q,lambda:not p.busy,45)
     record['guided_response']=copy.deepcopy(p.last_reply);record['guided_request']=copy.deepcopy(p.last_request);record['guided_view']=copy.deepcopy(s.last_payload);record['guided_semantic_actions']=4;guided[case['head']]=copy.deepcopy(record)
    else:
     record.update({k:copy.deepcopy(v) for k,v in guided[case['head']].items() if k.startswith('guided_') or k=='proposal'});record['guided_actions_shared_with']=str(case['head'])+'a'
   else:
    r=copy.deepcopy(plan['request']);r['text']=case['text'];extra=r.pop('extra_assumptions',[]);r['assumptions']=list(MODELS[r['subproblems'][0]['model']]['assumptions'])+extra
    if plan.get('dependency'):
     dep=plan['dependency'];earlier=prior[dep['part']]['manual_response'];solution=earlier['subproblems'][0]['solution']
     r['variables'][dep['target']]=solution['results'][dep['result']]['expression'];record['dependency_transferred']=dict(from_part=dep['part'],result=dep['result'],actual_expression=r['variables'][dep['target']])
    s.prompt.setPlainText(case['text']);QTest.mouseClick(s.physical_model_button,Qt.LeftButton);panel=s.assisted;actions=fill(panel,r);record['manual_action_details']=actions;record['manual_semantic_actions']=sum(actions.values())
    record['manual_request']=panel.request();QTest.mouseClick(panel.solve,Qt.LeftButton);wait(q,lambda:not panel.busy,45)
    record['manual_response']=copy.deepcopy(panel.last_reply);record['manual_view']=copy.deepcopy(s.last_payload);record['manual_status_text']=panel.status.text()
   record['math_display_errors']=[x.text() for view in (s.result,s.derivation,s.explanation) for x in view.findChildren(QLabel) if 'Kunne ikke vise matematik' in x.text()]
  except Exception as exc:record['harness_or_form_error']=str(exc)
  w.grab().save(str(OUT/(id+'.png')));previous.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');records.append(record);prior[id]=record
  response=record.get('manual_response') or record.get('guided_response') or {};print(id,'raw', (record['automatic_reply'] or {}).get('status'),'assisted',response.get('status'),record.get('harness_or_form_error',''),flush=True)
 w.close();q.processEvents()
 (OUT/'execution.json').write_text(json.dumps(dict(source_commit=seal['source_commit'],archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),sealed_inputs_sha256=seal['sha256'],native_windows_tested=False,platform='Linux CPython 3.13.5 Qt offscreen, real packaged MainWindow with production stylesheet',network='Python sockets blocked in parent GUI and computation workers',references_used_as_input=False,app_modified_during_test=False,cases=records),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
