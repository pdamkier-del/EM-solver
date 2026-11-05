"""Actual host application including new law-driven extensions."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ.setdefault('APPDATA','/tmp/em1-generalized-tests')
import pytest
from PySide6.QtWidgets import QApplication,QTableWidgetItem
from PySide6.QtCore import Qt
from test_existing_app import solve_in_host,explicit_request

def request(model,variables,wanted,units,positive=(),numbers=None,operations=None):
    r=explicit_request(model,variables,units,list(positive),wanted)
    r['numbers']=numbers or {}
    if operations:r['subproblems'][0]['operations']=operations
    return r

@pytest.fixture(scope='module')
def app():
    from desktop_app import app as host
    q=QApplication.instance() or QApplication([]);host.init_db();return q

@pytest.mark.parametrize('r',[
 request('image_plane',dict(charges=[['q',['0','0','a']]],normal=['0','0','1'],offset='0',point=['0','0','2*a']),['V','E','F'],dict(q='C',a='m'),['a']),
 request('image_sphere_grounded',dict(charges=[['q',['0','0','a+h']]],center=['0','0','0'],radius='a'),['F','Q_induced'],dict(q='C',a='m',h='m'),['a','h']),
 request('magnetized_sphere',dict(M=['0','0','M0'],radius='a',center=['0','0','0'],point=['0','0','2*a']),['B_inside','B','K_bound'],dict(M0='A/m',a='m'),['a']),
 request('magnetization_currents',dict(M=['0','0','k*s**2'],coordinates=['s','phi','z'],system='cylindrical',normal=['1','0','0']),['J_bound','K_bound'],dict(k='A/m^3',s='m',phi='1',z='m'),['s']),
 request('RL_step',dict(time='t',R='R',L='L',voltage='V',I0='I0'),['I','initial_slope','zero_time'],dict(t='s',R='ohm',L='H',V='V',I0='A'),['R','L'],dict(R='12 ohm',L='85 mH',V='-6 V',I0='0.32 A')),
 request('faraday_flux',dict(time='t',flux='-a*t',N='1'),['EMF'],dict(t='s',a='V',L='H',R='ohm'),['L','R'],operations=[dict(kind='linear_ode',id='coil_current',result='EMF',variable='t',coefficient='L',resistance='R',initial='0',unit='A')])])
def test_new_features_through_main_window(app,r):
    reply=solve_in_host(app,r)
    assert reply['status']=='calculated_under_confirmed_model',reply


def test_explicit_suggestion_transfer_does_not_confirm_assumptions(app):
    from desktop_integration.dyn_panel import DynPanel
    p=DynPanel();p.model.setCurrentIndex(p.model.findData('RL_step'))
    p.text.setPlainText('En RL-kreds har R=12 ohm; L=85 mH; I0=0.32 A; voltage=-6 V. Find strømmen.')
    p._analyze();p._transfer_suggestions()
    assert p.fields['R'].text()=='R' and p.fields['L'].text()=='L'
    assert p.symbols.rowCount()==4
    assert not p.confirm.isChecked() and not p.orientation.isChecked()
    assert all(not c.isChecked() for c in p.conditions.values())
    p.close()
