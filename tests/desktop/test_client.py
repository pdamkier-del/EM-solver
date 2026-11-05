import copy,json
from em1_solver.backend_client import run_text,choose_view,validate_response
import pytest

def test_view_switch_does_not_recompute(monkeypatch):
 response=run_text('V(x,y,z)=k*x**2. Bestem E.')
 before=copy.deepcopy(response)
 import em1_solver.backend as backend
 def forbidden(*args,**kwargs):raise AssertionError('View change called solver')
 monkeypatch.setattr(backend,'respond',forbidden)
 for level in ('result','derivation','explanation'):
  view=choose_view(response,level)
  assert view['status']=='verified';json.dumps(view,allow_nan=False)
 assert response==before

def test_incomplete_task_never_appears_as_an_approved_result():
 response=run_text('En cylinder med radius R har rho(s)=k*s. Bestem E.')
 view=choose_view(response,'result')
 assert view['status']=='not_solved' and view['missing'] and 'results' not in view

def test_contract_validation_detects_bad_refs_and_status():
 response=run_text('V(x,y,z)=k*x**2. Bestem E.')
 bad=copy.deepcopy(response);bad['solution']['views']['derivation']['step_ids']=['missing']
 with pytest.raises(ValueError):validate_response(bad,require_views=True)
 bad=copy.deepcopy(response);bad['solution']['checks'][0]['passed']=False
 with pytest.raises(ValueError):validate_response(bad,require_views=True)
 bad=copy.deepcopy(response);bad['solution']['results']['E']['latex']=r'\input{file}'
 with pytest.raises(ValueError):validate_response(bad,require_views=True)

def test_physical_rejection_survives_result_only_view():
 response=run_text('E=alpha*y xhat+beta*z yhat+gamma*x zhat. Kan det være elektrostatisk i et simpelt sammenhængende område?')
 view=choose_view(response,'result')
 assert view['physical_model_rejected'] is True and view['warnings']
 assert response['solution']['physical_model_rejected'] is True

def test_verified_contract_cannot_hide_required_field_uncertainty():
 response=run_text('V(x,y,z)=k*x**2. Bestem E.')
 bad=copy.deepcopy(response);bad['interpretation']['fields']['wanted']['status']='RED'
 with pytest.raises(ValueError):validate_response(bad,require_views=True)
 bad=copy.deepcopy(response);bad['solution']['physical_model_rejected']='false'
 with pytest.raises(ValueError):validate_response(bad,require_views=True)
