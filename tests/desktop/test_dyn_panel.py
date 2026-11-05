"""Real Qt widgets -> QProcess -> spawned physics worker -> rendered result.

Runs offscreen on Linux; not a native Windows test. Qt is an optional host
dependency. CI/integration must install requirements-desktop-integration.txt.
"""
import json
import os
import time
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication,QTableWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from desktop_integration.dyn_panel import DynPanel

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def app():return QApplication.instance() or QApplication([])


def wait(app,predicate,timeout=25000):
    end=time.monotonic()+timeout/1000
    while not predicate() and time.monotonic()<end:
        app.processEvents();QTest.qWait(10)
    assert predicate(),'Qt/backend flow did not complete before timeout'


def fill(panel,request):
    panel.text.setPlainText(request['text'])
    panel.model.setCurrentIndex(panel.model.findData(request['subproblems'][0]['model']))
    for key,value in request['variables'].items():
        if isinstance(value,list):
            def form(x):return '['+','.join(form(v) for v in x)+']' if isinstance(x,list) else str(x)
            value=form(value)
        panel.fields[key].setText(str(value))
    panel._scan_symbols()
    for row in range(panel.symbols.rowCount()):
        symbol=panel.symbols.item(row,0).text()
        panel.symbols.setItem(row,1,QTableWidgetItem(request['units'][symbol]))
        panel.symbols.setItem(row,2,QTableWidgetItem(request.get('numbers',{}).get(symbol,'')))
        panel.symbols.item(row,3).setCheckState(Qt.Checked if symbol in request['positive'] else Qt.Unchecked)
    panel.wanted.setText(', '.join(request['subproblems'][0]['wanted']))
    for condition in request['assumptions']:
        if condition in panel.conditions:panel.conditions[condition].setChecked(True)
    panel.orientation.setChecked(True);panel.confirm.setChecked(True)


def test_01_complete_historical_rc_from_input_to_numeric_output(app):
    """First complete task before exposing/testing other model cards."""
    request=json.loads((ROOT/'data/integration/assisted_v1/2026_01_p2c.request.json').read_text())
    request['numbers']={'R':'0.25 ohm','C':'91 mF','Q0':'5.7 C'}
    panel=DynPanel(allowed_models=['RC_discharge']);panel.show()
    fill(panel,request)
    QTest.mouseClick(panel.analyze,Qt.LeftButton)
    assert 'RC' in panel.suggestions.text()
    QTest.mouseClick(panel.solve,Qt.LeftButton)
    wait(app,lambda:panel.last_reply is not None)
    assert panel.last_reply['status']=='calculated_under_confirmed_model',panel.last_reply
    solution=panel.last_reply['subproblems'][0]['solution']
    assert abs(float(solution['numerical']['I_initial']['value'])-250.55)<0.1
    assert abs(float(solution['numerical']['decay_time']['value'])-0.105)<0.001
    assert 'Faktisk udførte beregningskontroller' in panel.output.toPlainText()
    assert 'ikke maskinverificeret' in panel.status.text()
    # Editing givens invalidates the old answer and user confirmation.
    panel.fields['Q0'].setText('another_charge')
    assert panel.last_reply is None and not panel.confirm.isChecked() and not panel.output.toPlainText()
    panel.close()


@pytest.mark.parametrize('name',['2025_01_p6a','2021_06_p6a','2023_02_p6a','2023_11_p5c','2026_01_p3a','2023_02_p5b'])
def test_02_other_historical_model_cards_through_qt(app,name):
    request=json.loads((ROOT/'data/integration/assisted_v1'/f'{name}.request.json').read_text())
    expected=json.loads((ROOT/'data/integration/assisted_v1'/f'{name}.response.json').read_text())
    panel=DynPanel();panel.show();fill(panel,request)
    QTest.mouseClick(panel.solve,Qt.LeftButton)
    wait(app,lambda:panel.last_reply is not None)
    reply=panel.last_reply
    assert reply['status']=='calculated_under_confirmed_model',reply
    actual=reply['subproblems'][0]['solution']
    assert actual['results']==expected['subproblems'][0]['solution']['results']
    assert 'Beregnet under din bekræftede model' in panel.status.text()
    assert panel.output.toPlainText()
    panel.close()


def test_03_missing_charge_abstains_and_never_shows_a_result(app):
    request=json.loads((ROOT/'data/integration/assisted_v1/2026_01_p2c.request.json').read_text())
    del request['variables']['Q0']
    panel=DynPanel();panel.show();fill(panel,request)
    QTest.mouseClick(panel.solve,Qt.LeftButton)
    wait(app,lambda:panel.last_reply is not None)
    assert panel.last_reply['status']=='needs_confirmation'
    assert panel.last_reply['subproblems']==[]
    assert 'Q0' in panel.output.toPlainText() and 'Resultat' not in panel.output.toPlainText()
    panel.close()


def test_04_eighth_card_rl_has_explicit_nonzero_initial_current(app):
    request=dict(text='RL-seriekreds med konstant spænding og I(0)=j0.',variables=dict(time='t',R='Z',L='Ind',voltage='U0',I0='j0'),
        units={'t':'s','Z':'ohm','Ind':'H','U0':'V','j0':'A'},positive=['Z','Ind'],assumptions=['constant_coefficients'],
        subproblems=[dict(model='RL_step',wanted=['I_initial','I_infinity','tau'])])
    panel=DynPanel();panel.show();fill(panel,request)
    QTest.mouseClick(panel.solve,Qt.LeftButton)
    wait(app,lambda:panel.last_reply is not None)
    assert panel.last_reply['status']=='calculated_under_confirmed_model',panel.last_reply
    assert panel.last_reply['subproblems'][0]['solution']['results']['I_initial']['expression']=='j0'
    panel.close()


def test_05_failed_backend_start_is_visible(app):
    panel=DynPanel(python_exe='/no/such/python');panel.show()
    QTest.mouseClick(panel.solve,Qt.LeftButton)
    wait(app,lambda:'kunne ikke startes' in panel.status.text())
    assert panel.editor.isEnabled() and panel.last_reply is None
    panel.close()


def test_06_revoking_user_confirmation_clears_displayed_answer(app):
    request=json.loads((ROOT/'data/integration/assisted_v1/2026_01_p2c.request.json').read_text())
    panel=DynPanel();panel.show();fill(panel,request)
    QTest.mouseClick(panel.solve,Qt.LeftButton)
    wait(app,lambda:panel.last_reply is not None)
    assert panel.output.toPlainText()
    panel.confirm.setChecked(False)
    assert panel.last_reply is None and not panel.output.toPlainText()
    panel.close()
