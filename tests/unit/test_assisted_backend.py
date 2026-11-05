import copy
import json
import subprocess
import sys
import pytest
import sympy as sp
from em1_solver.assisted_backend import respond, catalog, plan, VERSION


def request(model='faraday_uniform', variables=None, wanted=None):
    return dict(schema_version=VERSION,confirmed=True,units={'t':'s','B0':'T','w':'1/s','S':'m^2','Z':'ohm'},
        positive=['S','Z'],variables=variables or dict(time='t',B_normal='B0*cos(w*t)',area='S',N='1',R='Z'),
        assumptions=['uniform_normal_B','negligible_self_inductance'],
        subproblems=[dict(id='a',model=model,wanted=wanted or ['EMF','I'],orientation_confirmed=True)])


def test_no_silent_example_values_or_confirmation():
    r=respond(dict(schema_version=VERSION,subproblems=[dict(id='a',model='RL_step')]))
    assert r['status']=='needs_confirmation' and r['subproblems']==[]
    assert {q['field'] for q in r['questions']} >= {'I0','time','R','L','voltage','wanted','confirmed','orientation_confirmed','assumptions'}
    assert all('default' not in card for card in catalog()['models'].values())


def test_faraday_views_and_conditional_status():
    r=respond(request(),solve=True)
    assert r['status']=='calculated_under_confirmed_model',r
    a=r['subproblems'][0];assert a['verification']['interpretation']=='user_confirmed_not_machine_verified'
    assert set(a['solution']['views'])=={'result','derivation','explanation'}
    sy={k:sp.Symbol(k) for k in ['B0','S','w','t']}
    assert sp.simplify(sp.sympify(a['solution']['results']['EMF']['expression'],locals=sy)-sp.sympify('B0*S*w*sin(w*t)',locals=sy))==0
    ids=[s['id'] for s in a['solution']['steps']];assert len(ids)==len(set(ids))


def test_rc_initial_condition_and_shared_subparts():
    r=request('RC_discharge',dict(time='t',R='Z',C='Cap',Q0='Q0'),['Q','I'])
    r['units']={'t':'s','Z':'ohm','Cap':'F','Q0':'C'};r['positive']=['Z','Cap'];r['assumptions']=['constant_coefficients']
    r['subproblems'].append(dict(id='b',model='RC_discharge',wanted=['tau'],orientation_confirmed=True))
    a=respond(r,solve=True);assert a['status']=='calculated_under_confirmed_model',a
    assert len(a['subproblems'])==2
    q=sp.sympify(a['subproblems'][0]['solution']['results']['Q']['expression'])
    assert sp.simplify(q.subs('t',0)-sp.Symbol('Q0'))==0


@pytest.mark.parametrize('change',[{'confirmed':'yes'},{'units':{'t':9}},{'positive':'R'},{'numbers':{'Z':float('nan')}},{'gold':42}])
def test_invalid_inputs_fail_closed(change):
    assert respond(request()|change,solve=True)['status']=='not_solved'


def test_wrong_units_and_numeric_assumptions_rejected():
    r=request();r['units']['B0']='m'
    assert respond(r,solve=True)['status']=='not_solved'
    r=request();r['numbers']={'Z':'-2 ohm'}
    assert respond(r,solve=True)['status']=='not_solved'


def test_missing_resistance_does_not_invent_current():
    r=request();del r['variables']['R']
    a=respond(r,solve=True)
    assert a['status']=='not_solved' and a['subproblems'][0]['solution'] is None


def test_numeric_area_and_interval_cannot_break_confirmed_geometry():
    r=request();r['variables']['area']='-1'
    assert respond(r,solve=True)['status']=='not_solved'
    r=request();r['variables']['time_bounds']=['4','2']
    assert respond(r,solve=True)['status']=='not_solved'
    r=request();r['variables']['time']='t+1'
    assert respond(r,solve=True)['status']=='not_solved'


def test_rl_preserves_nonzero_initial_current():
    r=request('RL_step',dict(time='t',R='Z',L='Ind',voltage='U0',I0='j0'),['I','tau'])
    r['units']={'t':'s','Z':'ohm','Ind':'H','U0':'V','j0':'A'}
    r['positive']=['Z','Ind'];r['assumptions']=['constant_coefficients']
    reply=respond(r,solve=True)
    assert reply['status']=='calculated_under_confirmed_model',reply
    actual=sp.sympify(reply['subproblems'][0]['solution']['results']['I']['expression'])
    assert sp.simplify(actual.subs('t',0)-sp.Symbol('j0'))==0
    r['variables']['R']='Z*(1+t)'
    assert respond(r,solve=True)['status']=='not_solved'


def test_partial_batch_keeps_success_and_failed_part_separate():
    r=request();r['subproblems'].append(dict(id='b',model='faraday_uniform',wanted=['unsupported'],orientation_confirmed=True))
    reply=respond(r,solve=True)
    assert reply['status']=='partial'
    assert reply['subproblems'][0]['solution'] is not None
    assert reply['subproblems'][1]['status']=='not_solved' and reply['subproblems'][1]['solution'] is None


def test_unknown_model_and_local_typo():
    r=request();r['subproblems'][0]['model']='unknown'
    assert respond(r,solve=True)['status']=='needs_confirmation'
    r=request();r['subproblems'][0]['variables']={'Nn':'2'}
    assert respond(r,solve=True)['status']=='not_solved'


def test_cli_roundtrip():
    run=subprocess.run([sys.executable,'-m','em1_solver.assisted_backend'],input=json.dumps(request()),text=True,capture_output=True,timeout=25)
    assert run.returncode==0,run.stderr
    assert json.loads(run.stdout)['status']=='calculated_under_confirmed_model'


def test_plan_suggests_without_filling_or_confirming_physics():
    r=plan('En metalstang med masse m hviler på skinner.\na) Find EMF.\nb) Bestem stangens hastighed.')
    assert {c['model'] for c in r['candidates']} >= {'feedback','motional_curve'}
    assert r['subproblem_markers']==['a','b']
    assert 'variables' not in r and r['interpretation_status']=='unconfirmed'
    assert plan('En lang cylinder med ukendt tæthed.')['idealization_suggestion']


@pytest.mark.parametrize('name',['2025_01_p6a','2021_06_p6a','2026_01_p2c','2023_02_p6a','2023_11_p5c','2026_01_p3a','2023_02_p5b','missing_initial_charge'])
def test_offline_integration_fixtures(name):
    from pathlib import Path
    folder=Path('data/integration/assisted_v1')
    request=json.loads((folder/(name+'.request.json')).read_text())
    expected=json.loads((folder/(name+'.response.json')).read_text())
    assert respond(request,solve=True)==expected
