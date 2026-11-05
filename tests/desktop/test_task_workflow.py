"""User tasks and unchanged historical prose through the actual MainWindow."""
import os,json
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ.setdefault('APPDATA','/tmp/em1-task-workflow-tests')
import pytest
import sympy as sp
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from desktop_app import app as host
from test_dyn_panel import wait
ROOT=Path(__file__).resolve().parents[2]
CYLINDER=r'''En uendeligt lang, massiv cylindrisk leder har radius \(a=4,0\,\mathrm{cm}\) og fører en samlet strøm \(I=8,0\,\mathrm A\) i positiv \(z\)-retning.
Strømtætheden er ikke konstant, men givet ved
\[ \mathbf J(s)=J_0\frac{s^2}{a^2}\,\hat{\mathbf z}, \]
hvor \(s\) er den cylindriske afstand fra lederens akse.
a) Bestem konstanten \(J_0\).
b) Bestem magnetfeltet \(\mathbf B(s)\) både inden for og uden for lederen.
c) Beregn feltets størrelse ved \(s=2,0\,\mathrm{cm}\) og \(s=8,0\,\mathrm{cm}\).'''
POTENTIAL='Et elektrisk potentiale er givet ved V(x,y,z) = a*x**2 + b*y**2. Bestem det elektriske felt E og ladningstætheden rho.'

@pytest.fixture(scope='module')
def app():
 q=QApplication.instance() or QApplication([]);host.init_db();return q

def analyze(app,text):
 w=host.MainWindow();w.show();s=w.solver;s.prompt.setPlainText(text);QTest.mouseClick(s.review_button,Qt.LeftButton)
 p=s.task_review;wait(app,lambda:not p.busy,15000);assert p.proposal,p.status.text();return w,p

def solve(app,w,p):
 QTest.mouseClick(p.confirm,Qt.LeftButton,pos=QPoint(8,p.confirm.height()//2));assert p.confirm.isChecked()
 QTest.mouseClick(p.solve,Qt.LeftButton);wait(app,lambda:not p.busy,45000)
 assert p.last_reply,p.status.text();assert p.last_reply['status']=='calculated_under_confirmed_model',p.last_reply
 errors=[l.text() for v in (w.solver.result,w.solver.derivation,w.solver.explanation) for l in v.findChildren(QLabel) if 'Kunne ikke vise matematik' in l.text()];assert not errors,errors
 return p.last_reply['subproblems'][0]['solution']

def test_exact_user_cylinder_complete_all_parts_without_retyping(app):
 w,p=analyze(app,CYLINDER)
 assert p.proposal['model']=='ampere_regions' and not p.proposal['issues']
 assert p.fields['total_current'].text()=='8.0 A' and p.quantities['a'].text()=='4.0 cm'
 assert p.proposal['normalization_symbol']=='J_0' and p.proposal['points']==['2.0 cm','8.0 cm']
 assert 'J_0' not in p.quantities and not p.unit_fields
 sol=solve(app,w,p);v=sol['results'];sy={n:sp.Symbol(n,positive=True) if n in ('s','a') else sp.Symbol(n,real=True) for n in ('s','a','I_given')};sy['mu_0']=sp.Symbol('mu_0',positive=True)
 coefficient=sp.sympify(v['density_amplitude']['expression'],locals=sy)
 assert sp.simplify(coefficient-2*sy['I_given']/(sp.pi*sy['a']**2))==0
 field=sp.sympify(v['normalized_B']['expression'],locals=sy)
 for rad in (sy['a']/2,2*sy['a']):
  expected=sy['mu_0']*sy['I_given']*rad**3/(2*sp.pi*sy['a']**4) if rad==sy['a']/2 else sy['mu_0']*sy['I_given']/(2*sp.pi*rad)
  assert sp.simplify(field.subs(sy['s'],rad)-expected)==0
 assert abs(float(sol['numerical']['density_amplitude']['value'])-3183.09886183791)<1e-7
 assert abs(float(sol['numerical']['B_point_1']['value'])-5e-6)<1e-12
 assert abs(float(sol['numerical']['B_point_2']['value'])-20e-6)<1e-12
 assert len(sol['views']['derivation']['step_ids'])>=8
 p.fields['total_current'].setText('10 A');assert p.last_reply is None and w.solver.last_payload is None
 w.close()

def test_exact_potential_symbolic_coefficients_not_forced_positive(app):
 w,p=analyze(app,POTENTIAL);assert not p.unit_fields and set(p.fields)=={'source'} and not p.quantities
 sol=solve(app,w,p);sy={n:sp.Symbol(n,real=True) for n in ('a','b','x','y','z')};sy['epsilon_0']=sp.Symbol('epsilon_0',positive=True)
 e=sp.sympify(sol['results']['E']['expression'],locals=sy);rho=sp.sympify(sol['results']['rho']['expression'],locals=sy)
 assert sp.simplify(e-sp.Matrix([-2*sy['a']*sy['x'],-2*sy['b']*sy['y'],0]))==sp.zeros(3,1)
 assert sp.simplify(rho+2*sy['epsilon_0']*(sy['a']+sy['b']))==0
 assert p.last_request['positive']==[] and not p.last_request['numbers']
 w.solver.prompt.setPlainText(POTENTIAL+' Ny tekst.');assert p.proposal is None and not p.solve.isEnabled() and w.solver.last_payload is None
 w.close()

def test_historical_2024_02_p4b_original_pdf_text_needs_one_formula_repair(app):
 original=json.loads((ROOT/'data/integration/desktop_historical/2024_02_p4b.request.json').read_text())['text']
 w,p=analyze(app,original)
 assert any(i['field']=='source' for i in p.proposal['issues'])
 p.fields['source'].setText('J0*(1-s/S)')
 sol=solve(app,w,p)
 # Reference derived from the printed question, not supplied solution:
 # Itotal=pi*J0*S²/3; B(S)=mu0*J0*S/6, B(2S)=half.
 assert abs(float(sol['numerical']['B_point_1']['value']))<1e-20
 mu=1.25663706212e-6;expected=mu*96e6*.0031/6
 assert abs(float(sol['numerical']['B_point_2']['value'])-expected)<1e-10
 assert abs(float(sol['numerical']['B_point_3']['value'])-expected/2)<1e-10
 w.close()

@pytest.mark.parametrize('text,fragment',[
 ('En endelig cylindrisk leder med radius a=4 cm har J(s)=J0*s/a. Bestem magnetfeltet.','endelig'),
 ('V(x,y,z)=a*x**2. Bestem E. V(x,y,z)=b*y**2.','Flere potential'),
 ('V(x,y,z)=f(t)*x. Bestem E.',''),
])
def test_unsafe_or_ambiguous_text_does_not_silently_choose_model(app,text,fragment):
 w=host.MainWindow();w.show();s=w.solver;s.prompt.setPlainText(text);QTest.mouseClick(s.review_button,Qt.LeftButton);p=s.task_review
 wait(app,lambda:not p.busy,15000);assert p.proposal is None and p.last_reply is None and not p.solve.isEnabled()
 if fragment:assert fragment in p.status.text()
 w.close()

def test_missing_direction_and_ambiguous_units_remain_explicit(app):
 w,p=analyze(app,'En uendelig massiv cylindrisk leder med radius a=4 cm har J(s)=J0*s/a. J0=3 A/m^2. Bestem magnetfeltet B(s).')
 assert any(i['field']=='direction' for i in p.proposal['issues'])
 QTest.mouseClick(p.confirm,Qt.LeftButton,pos=QPoint(8,p.confirm.height()//2));QTest.mouseClick(p.solve,Qt.LeftButton);wait(app,lambda:not p.busy,45000)
 assert p.last_reply is None and 'Strømretning' in p.status.text();w.close()
 w,p=analyze(app,'V(x,y,z)=a*b*x**2. Bestem E og rho.')
 assert set(p.unit_fields)=={'a','b'}
 assert not p.confirm.isChecked();w.close()


def test_historical_full_main_question_current_and_field_share_givens(app):
    a=json.loads((ROOT/'data/integration/desktop_historical/2024_02_p4a.request.json').read_text())['text']
    b=json.loads((ROOT/'data/integration/desktop_historical/2024_02_p4b.request.json').read_text())['text']
    text=a+'\n'+b[b.index('Angiv retningen'):]
    w,p=analyze(app,text)
    assert p.quantities['J0'].text()=='96.0 A/mm**2'
    p.fields['source'].setText('J0*(1-s/S)')
    sol=solve(app,w,p)
    assert {'I_enc','I','B'}<=set(sol['views']['result']['results'])
    assert abs(float(sol['numerical']['I']['value'])-float(sp.pi*96e6*.0031**2/3))<1e-8
    assert abs(float(sol['numerical']['B_point_2']['value'])-1.25663706212e-6*96e6*.0031/6)<1e-10
    w.close()


def test_conflicting_numbers_are_not_silently_taken_from_last_assignment(app):
    text='V(x,y,z)=a*x**2. a=2 V/m^2; a=4 V/m^2. Bestem E.'
    w,p=analyze(app,text);assert p.quantities['a'].text()==''
    QTest.mouseClick(p.confirm,Qt.LeftButton,pos=QPoint(8,p.confirm.height()//2));QTest.mouseClick(p.solve,Qt.LeftButton);wait(app,lambda:not p.busy,45000)
    assert p.last_reply is None and 'forskellige' in p.status.text()
    p.quantities['a'].setText('2 V/m^2');sol=solve(app,w,p);assert p.last_request['numbers']['a']=='2 V/m^2'
    w.close()


def test_changed_text_during_analysis_never_receives_the_old_proposal(app):
    w=host.MainWindow();w.show();s=w.solver;s.prompt.setPlainText(POTENTIAL);QTest.mouseClick(s.review_button,Qt.LeftButton);p=s.task_review
    s.prompt.setPlainText('En helt anden opgave.');wait(app,lambda:not p.busy,15000)
    assert p.proposal is None and p.last_reply is None and not p.solve.isEnabled()
    assert 'ændret' in p.status.text();w.close()


def test_total_charge_from_potential_does_not_request_a_vacuum_assumption(app):
    w,p=analyze(app,'I et dielektrikum er V(x,y,z)=a*x**2+b*y**2. Bestem E og den samlede ladningstæthed rho.')
    assert p.proposal['assumptions']==['electrostatic']
    sol=solve(app,w,p);assert p.last_request['assumptions']==['electrostatic']
    assert 'rho' in sol['results'];w.close()
