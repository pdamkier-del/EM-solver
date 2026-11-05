"""Actual MainWindow acceptance for user prose and unmodified historical exam text."""
import os,sys,json,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests/desktop')]
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ.setdefault('APPDATA','/tmp/em1-workflow-acceptance');os.environ.setdefault('MPLCONFIGDIR','/tmp/em1-workflow-mpl')
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from desktop_app import app as host
from test_dyn_panel import wait
from test_task_workflow import CYLINDER,POTENTIAL
from em1_solver.core.task_runtime import block_network


def main():
 out=ROOT/'reports/workflow';out.mkdir(exist_ok=True);block_network();q=QApplication([]);host.init_db();rows=[]
 a=json.loads((ROOT/'data/integration/desktop_historical/2024_02_p4a.request.json').read_text())['text'];b=json.loads((ROOT/'data/integration/desktop_historical/2024_02_p4b.request.json').read_text())['text']
 cases=[('user_cylinder',CYLINDER,None),('user_potential',POTENTIAL,None),('historical_2024_02_p4b',b,'J0*(1-s/S)'),('historical_2024_02_p4ab',a+'\n'+b[b.index('Angiv retningen'):],'J0*(1-s/S)')]
 w=host.MainWindow();w.show();s=w.solver
 for id,text,repair in cases:
  actions=['Indsæt opgavetekst'];s.prompt.setPlainText(text);QTest.mouseClick(s.review_button,Qt.LeftButton);actions.append('Analysér opgave')
  p=s.task_review;wait(q,lambda:not p.busy,15000);assert p.proposal,p.status.text()
  before=json.loads(json.dumps(p.proposal));w.grab().save(str(out/(id+'.review.png')))
  manual=[]
  if repair:
   p.fields['source'].setText(repair);actions.append('Ret den ødelagte PDF-formel');manual.append('J(s) rettet fra det originale opgavebillede på side 27, ikke fra facit.')
  QTest.mouseClick(p.confirm,Qt.LeftButton,pos=QPoint(8,p.confirm.height()//2));assert p.confirm.isChecked();actions.append('Bekræft læste data og viste fysiske betingelser')
  QTest.mouseClick(p.solve,Qt.LeftButton);actions.append('Beregn opgaven');wait(q,lambda:not p.busy,45000)
  assert p.last_reply and p.last_reply['status']=='calculated_under_confirmed_model',p.status.text()
  errors=[x.text() for v in (s.result,s.derivation,s.explanation) for x in v.findChildren(QLabel) if 'Kunne ikke vise matematik' in x.text()];assert not errors,errors
  sol=p.last_reply['subproblems'][0]['solution'];num=sol['numerical']
  # Independent numerical checks; no expected value is sent to the app.
  if id=='user_cylinder':
   assert abs(float(num['density_amplitude']['value'])-3183.098861837907)<1e-8
   assert abs(float(num['B_point_1']['value'])-5e-6)<1e-12
   assert abs(float(num['B_point_2']['value'])-20e-6)<1e-12
  if id.startswith('historical'):
   expected=1.25663706212e-6*96e6*.0031/6
   assert abs(float(num['B_point_1']['value']))<1e-20
   assert abs(float(num['B_point_2']['value'])-expected)<1e-10
   assert abs(float(num['B_point_3']['value'])-expected/2)<1e-10
  w.grab().save(str(out/(id+'.result.png')))
  rows.append(dict(id=id,text=text,actions=actions,semantic_user_actions=len(actions),manual_reentry=manual,proposal_before_confirmation=before,submitted_request=p.last_request,response=p.last_reply,viewer=s.last_payload,math_display_errors=errors))
  q.processEvents();print(id,len(actions),'actions, correct',flush=True)
 w.close();q.processEvents()
 (out/'acceptance.json').write_text(json.dumps(dict(platform='Linux Qt offscreen',native_windows_tested=False,network='Python sockets blocked in GUI and symbolic worker',same_mainwindow_reused=True,actions_definition='Semantic UI actions, not individual keystrokes, reading time or a measured human usability study.',cases=rows),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
