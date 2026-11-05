"""The supplied desktop app, not an isolated integration widget."""
import json,os,time
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('APPDATA','/tmp/em1-integrated-desktop-tests')
import pytest
pytest.importorskip('PySide6')
pytest.importorskip('matplotlib')
pytest.importorskip('fitz')
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from desktop_app import app as host
from test_dyn_panel import fill,wait

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def application():
    q=QApplication.instance() or QApplication([])
    host.init_db()
    return q


def test_01_actual_main_window_rc_flow(application):
    window=host.MainWindow();window.show();solver=window.solver
    request=json.loads((ROOT/'data/integration/assisted_v1/2026_01_p2c.request.json').read_text())
    request['numbers']={'R':'0.25 ohm','C':'91 mF','Q0':'5.7 C'}
    solver.prompt.setPlainText(request['text'])
    QTest.mouseClick(solver.physical_model_button,Qt.LeftButton)
    assert solver.assisted is not None
    assert solver.assisted.text.toPlainText()==request['text']
    fill(solver.assisted,request)
    QTest.mouseClick(solver.assisted.solve,Qt.LeftButton)
    wait(application,lambda:solver.last_payload is not None,40000)
    payload=solver.last_payload
    assert payload['backend_schema']=='assisted-1.0'
    assert payload['status']=='assumptions'
    assert '250.549' in payload['result']['numeric_text'] and '0.104767' in payload['result']['numeric_text']
    assert solver.tabs.currentWidget() is solver.derivation
    assert solver.derivation.findChildren(QLabel)
    failures=[x.text() for x in solver.derivation.findChildren(QLabel) if 'Kunne ikke vise matematik' in x.text()]
    assert not failures,failures
    assert 'ikke maskinverificeret' in solver.warning.text()
    solver.assisted.fields['Q0'].setText('new_Q0')
    assert solver.last_payload is None
    window.close()


def explicit_request(model,variables,units,positive,wanted,extra=()):
    from em1_solver.assisted_backend import MODELS
    return dict(schema_version='assisted-1.0',text='Eksplicit fysisk model til integrationskontrol.',confirmed=True,variables=variables,units=units,positive=positive,
        assumptions=MODELS[model]['assumptions']+list(extra),subproblems=[dict(id='a',model=model,wanted=wanted,orientation_confirmed=True)])


def solve_in_host(application,request):
    window=host.MainWindow();window.show();solver=window.solver
    solver.prompt.setPlainText(request['text']);QTest.mouseClick(solver.physical_model_button,Qt.LeftButton)
    fill(solver.assisted,request);QTest.mouseClick(solver.assisted.solve,Qt.LeftButton)
    wait(application,lambda:solver.last_payload is not None,40000)
    reply=solver.assisted.last_reply
    assert solver.last_payload['backend_schema']=='assisted-1.0'
    failures=[x.text() for view in (solver.result,solver.derivation,solver.explanation) for x in view.findChildren(QLabel) if 'Kunne ikke vise matematik' in x.text()]
    assert not failures,failures
    window.close()
    return reply


def test_gauss_sphere_potential_with_confirmed_reference(application):
    import sympy as sp
    r=explicit_request('sphere_regions',dict(coordinate='r',regions=[dict(lower='0',upper='R',density='k*r',permittivity='epsilon_0')]),
        {'r':'m','R':'m','k':'C/m^4'},['r','R'],['E','V','Q'],extra=['V_infinity_zero'])
    reply=solve_in_host(application,r)
    assert reply['status']=='calculated_under_confirmed_model',reply
    sy={n:sp.Symbol(n,positive=True) for n in ['r','R','epsilon_0']};sy['k']=sp.Symbol('k',real=True)
    potential=sp.sympify(reply['subproblems'][0]['solution']['results']['V']['expression'],locals=sy)
    assert sp.simplify(potential.subs(sy['r'],sy['R']/2)-31*sy['k']*sy['R']**3/(96*sy['epsilon_0']))==0


def test_planar_slab_and_multiregion_ampere(application):
    import sympy as sp
    q=explicit_request('plane_regions',dict(coordinate='s',regions=[dict(lower='0',upper='a',density='rho0',permittivity='epsilon_0')]),
        {'s':'m','a':'m','rho0':'C/m^3'},['s','a'],['E'])
    reply=solve_in_host(application,q);assert reply['status']=='calculated_under_confirmed_model',reply
    q=explicit_request('ampere_regions',dict(coordinate='s',regions=[dict(lower='0',upper='a',density='J'),dict(lower='a',upper='a+h',density='-J')]),
        {'s':'m','a':'m','h':'m','J':'A/m^2'},['s','a','h'],['B','I'])
    reply=solve_in_host(application,q);assert reply['status']=='calculated_under_confirmed_model',reply
    result=reply['subproblems'][0]['solution']['results']['I']['expression']
    sy={n:sp.Symbol(n,positive=True) for n in ['a','h']};sy['J']=sp.Symbol('J',real=True)
    assert sp.simplify(sp.sympify(result,locals=sy)-sp.pi*sy['J']*(2*sy['a']**2-(sy['a']+sy['h'])**2))==0


def test_biot_savart_ring_axis_and_ampere_wire(application):
    import sympy as sp
    q=explicit_request('biot_savart_curve',dict(source=['R*cos(u)','R*sin(u)','0'],parameter='u',bounds=['0','2*pi'],I='I',point=['0','0','0']),
        {'R':'m','u':'1','I':'A'},['R'],['B'])
    reply=solve_in_host(application,q);assert reply['status']=='calculated_under_confirmed_model',reply
    sy={'I':sp.Symbol('I',real=True),'R':sp.Symbol('R',positive=True),'mu_0':sp.Symbol('mu_0',positive=True)}
    b=sp.sympify(reply['subproblems'][0]['solution']['results']['B']['expression'],locals=sy)
    assert sp.simplify(b-sp.Matrix([0,0,sy['mu_0']*sy['I']/(2*sy['R'])]))==sp.zeros(3,1)
    q=explicit_request('ampere_wire',dict(I='I',distance='s'),{'I':'A','s':'m'},['s'],['B'])
    reply=solve_in_host(application,q);assert reply['status']=='calculated_under_confirmed_model'


def test_original_demo_and_notes_navigation_preserved(application):
    window=host.MainWindow();window.show();solver=window.solver
    solver.sample.setCurrentIndex(1);QTest.mouseClick(solver.load_test,Qt.LeftButton)
    assert solver.last_payload['viewer_schema']=='em1.desktop.solution.v1'
    for index in [1,2,3,4,0]:window.show_page(index);application.processEvents()
    assert window.pages.currentIndex()==0
    window.close()
