"""Same screen and widgets used by the examinee, with all outbound sockets blocked."""
import sys,json,socket,tempfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
CASES=[('gauss','EV','ev_cylinder'),('biot_savart','BA','ba_arc'),('ampere','BA','ba_wire'),('faraday','DYN','dyn_fixed'),('motional','DYN','dyn_sliding'),('material','BA','ba_toroid'),('rejection','EV','ev_field')]

def choose(app,key,value):
    next(x for x in app.selectbox if x.key==key).set_value(value).run()

def run_case(name,domain,preset):
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=40).run()
    app.radio[0].set_value('Manuel solver').run()
    choose(app,'af_domain',domain)
    choose(app,'af_preset',preset)
    assert not app.exception,(name,app.exception)
    if name=='rejection':
        assert app.error and any('Fysisk afvisning' in e.value for e in app.error),(name,app.error)
        assert next(x for x in app.button if x.label=='Løs opgave').disabled
        return dict(case=name,status='correct_refusal')
    assert not app.error,(name,[e.value for e in app.error])
    next(x for x in app.checkbox if x.key=='af_confirm').check().run()
    next(x for x in app.button if x.label=='Løs opgave').click().run()
    assert not app.exception and not app.error,(name,app.exception,[e.value for e in app.error])
    assert any(s.value=='Resultat' for s in app.subheader),name
    assert not any(w.value.startswith('WARNING: dimensional inconsistency') for w in app.warning),name
    return dict(case=name,status='result_rendered')

def main():
    def blocked(*a,**kw):raise AssertionError('Outbound network forbidden')
    socket.socket.connect=blocked;socket.socket.connect_ex=blocked;socket.create_connection=blocked
    with tempfile.TemporaryDirectory(prefix='em1-ui-smoke-') as folder:
        os.environ['EM1_STATE_DIR']=folder
        results=[run_case(*case) for case in CASES]
    (ROOT/'reports/exam_ui_smoke.json').write_text(json.dumps(dict(network='socket connections blocked',platform=sys.platform,cases=results,windows_batch_execution='not available on Linux'),indent=2)+'\n')
    print(json.dumps(results),flush=True)
if __name__=='__main__':main()
