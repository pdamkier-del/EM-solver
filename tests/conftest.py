import json
from pathlib import Path
import pytest
import socket

@pytest.fixture(autouse=True)
def no_network_in_physics(request,monkeypatch):
    if request.node.path.name=='test_app.py':
        return
    def blocked(*args,**kwargs):
        raise AssertionError('Netværk er forbudt under fysik- og historiske tests.')
    monkeypatch.setattr(socket.socket,'connect',blocked)
    monkeypatch.setattr(socket.socket,'connect_ex',blocked)
    monkeypatch.setattr(socket,'create_connection',blocked)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome=yield
    report=outcome.get_result()
    if report.when=='call':
        recipe=None
        if item.get_closest_marker('recipe'):
            recipe=json.loads(item.callspec.params['path'].read_text())
        item.session.em1_results.append({'test':item.nodeid,'outcome':report.outcome,
            'expected_failure':hasattr(report,'wasxfail'),
            'historical':item.get_closest_marker('historical').kwargs if item.get_closest_marker('historical') else None,
            'recipe':{'id':recipe['id'],'status':recipe['status']} if recipe else None,
            'variation':item.get_closest_marker('variation').kwargs if item.get_closest_marker('variation') else None,
            'dimensions':bool(item.get_closest_marker('dimensions'))})

def pytest_sessionstart(session):
    from em1_solver.core.certification import fingerprint
    session.em1_results=[]
    session.em1_fingerprint=fingerprint()

def pytest_sessionfinish(session, exitstatus):
    from em1_solver.core.certification import fingerprint
    path=Path(__file__).resolve().parents[1]/'reports/test-results.json'
    args=list(session.config.invocation_params.args)
    full=not any(arg.startswith('tests/') or arg in ('-k','-m','--lf','--last-failed','--ff','--failed-first') for arg in args)
    full=full and session.em1_fingerprint==fingerprint()
    path.write_text(json.dumps({'exitstatus':exitstatus,'full_suite':full,'collected':session.testscollected,'arguments':args,'fingerprint':fingerprint(),
        'results':session.em1_results},ensure_ascii=False,indent=2)+'\n')

@pytest.fixture(autouse=True)
def isolate_local_autosave(tmp_path,monkeypatch):
    monkeypatch.setenv('EM1_STATE_DIR',str(tmp_path/'autosave'))
