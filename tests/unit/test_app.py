"""Retain historical/manual checks after the four-item navigation redesign."""
from streamlit.testing.v1 import AppTest
import pytest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from ui_exam_smoke import run_case,CASES

@pytest.mark.parametrize('case',CASES,ids=[c[0] for c in CASES])
def test_actual_assisted_exam_ui(case):run_case(*case)

def test_historical_presets_run_without_internet(monkeypatch):
    import socket
    def blocked(*args,**kwargs):raise AssertionError('External network forbidden')
    monkeypatch.setattr(socket.socket,'connect',blocked)
    for id in ['2025-11:2a','2025-01:4a','2025-11:5c']:
        app=AppTest.from_file('app.py',default_timeout=30).run()
        app.radio[0].set_value('Historiske opgaver').run()
        app.selectbox[0].set_value(id).run()
        assert not app.exception and not app.error and app.success
