"""Known historical model replay through the uploaded application's MainWindow.
Expert-supplied models/givens, never raw-text autonomy. Read references afterwards.
"""
import os,sys,json,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('APPDATA','/tmp/em1-desktop-evaluation')
sys.path[:0]=[str(ROOT),str(ROOT/'tests/desktop')]
from em1_solver.core.task_runtime import block_network
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt,QTimer
from desktop_app import app as host
from test_dyn_panel import fill,wait
import sympy as sp


def compare(reply,reference):
    sy={k:sp.Symbol(k,**v) for k,v in reference['symbols'].items()}
    def decode(value):
        if isinstance(value,list):return [decode(v) for v in value]
        if isinstance(value,dict):
            if 'expr' in value:return sp.sympify(value['expr'].replace('^','**'),locals=sy)
            if 'matrix' in value:return sp.Matrix(decode(value['matrix']))
        return value
    s=reply['subproblems'][0]['solution'];checks=[]
    for ref in reference['expected']:
        try:
            item=s['results'][ref['result']];actual=sp.sympify(item['expression'],locals=sy)
            if 'component' in ref:actual=actual[ref['component']]
            for index in ref.get('indices',[]):actual=actual[index]
            actual=actual.subs({sy[k]:decode(v) for k,v in ref.get('subs',{}).items()},simultaneous=True)
            residual=sp.simplify(actual-decode(ref['value']))
            assert all(v.equals(0) is True for v in residual) if isinstance(residual,sp.MatrixBase) else residual.equals(0) is True
            if not ref.get('indices') and 'component' not in ref:assert item['unit']==ref.get('unit',item['unit'])
            if 'sign' in ref:assert sp.sign(sp.simplify(sp.expand_log(actual)))==ref['sign']
            if 'numeric' in ref:
                n=ref['numeric'];value=actual.subs({sy[k]:v for k,v in n['values'].items()}).evalf()
                assert abs(float(value)-n['value'])<=n['tolerance']
            checks.append(dict(result=ref['result'],passed=True,numerical_emitted=ref['result'] in s['numerical'] if 'numeric' in ref else None))
        except (AssertionError,KeyError,ValueError,TypeError) as exc:checks.append(dict(result=ref['result'],passed=False,error=str(exc)))
    return checks


def main():
    block_network();q=QApplication.instance() or QApplication([]);host.init_db()
    import psutil
    proc=psutil.Process();begin=time.monotonic();w=host.MainWindow();w.show();q.processEvents()
    startup=time.monotonic()-begin;rss_start=proc.memory_info().rss;peak=rss_start
    aggregate_peak=[rss_start]
    def sample():
        try:total=proc.memory_info().rss+sum(p.memory_info().rss for p in proc.children(recursive=True) if p.is_running())
        except psutil.Error:return
        aggregate_peak[0]=max(aggregate_peak[0],total)
    timer=QTimer();timer.timeout.connect(sample);timer.start(30)
    output=ROOT/'reports/desktop_integrated';output.mkdir(parents=True,exist_ok=True)
    records=[];folder=ROOT/'data/integration/desktop_historical'
    for path in sorted(folder.glob('*.request.json')):
        request=json.loads(path.read_text());name=path.name.replace('.request.json','');start=time.monotonic()
        solver=w.solver;solver.prompt.setPlainText(request['text'])
        QTest.mouseClick(solver.physical_model_button,Qt.LeftButton);fill(solver.assisted,request)
        solver.last_payload=None;QTest.mouseClick(solver.assisted.solve,Qt.LeftButton)
        wait(q,lambda:solver.last_payload is not None,40000)
        reply=solver.assisted.last_reply
        (output/(name+'.response.json')).write_text(json.dumps(reply,ensure_ascii=False,indent=2)+'\n')
        record=dict(case=name,model=request['subproblems'][0]['model'],seconds=round(time.monotonic()-start,3),
            user_assistance=dict(model_chosen=True,givens_entered=list(request['variables']),numerical_values_entered=request.get('numbers',{}),
                units_entered=True,orientation_confirmed=True,assumptions_confirmed=request['assumptions']),
            outcome='reasoned_refusal',first_failure=None,backend_status=reply['status'])
        if reply['status'] in ('calculated_under_confirmed_model','partial'):
            # The official reference is opened only AFTER runtime and saved output.
            reference=json.loads((ROOT/'data/historical_problems'/f'{name}.json').read_text())
            record['reference_checks']=compare(reply,reference)
            failures=[label.text() for view in (solver.result,solver.derivation,solver.explanation) for label in view.findChildren(QLabel) if 'Kunne ikke vise matematik' in label.text()]
            record['math_display_errors']=list(dict.fromkeys(failures))
            wrong=any(not c['passed'] for c in record['reference_checks'])
            missing_numerical=any(c.get('numerical_emitted') is False for c in record['reference_checks'])
            record['outcome']='incorrect' if wrong else 'partial' if failures or missing_numerical or reply['status']=='partial' else 'correct_assisted'
            if wrong:record['first_failure']='reference_comparison'
            elif failures:record['first_failure']='math_display'
            elif missing_numerical:record['first_failure']='numerical_inputs_missing'
        else:record['first_failure']=reply.get('questions') or reply.get('errors') or reply.get('subproblems')
        records.append(record);peak=max(peak,proc.memory_info().rss)
        print(name,record['outcome'],flush=True)
    # The original raw-text button still invokes the original bridge/runner.
    w.solver.prompt.setPlainText('V(x,y,z)=k*x**2. Bestem E.');w.solver._backend_reply=None
    QTest.mouseClick(w.solver.solve_button,Qt.LeftButton)
    wait(q,lambda:w.solver._backend_reply is not None,40000)
    legacy_status=w.solver._backend_reply['status']
    assert legacy_status in ('verified','verified_with_assumptions'),w.solver._backend_reply
    timer.stop();w.close()
    summary={key:sum(r['outcome']==key for r in records) for key in ['correct_assisted','partial','reasoned_refusal','incorrect']}
    report=dict(scope='Existing uploaded desktop MainWindow, explicit expert-supplied models; known historical regression, not blind/autonomous.',
        platform='Linux Qt offscreen; native Windows not tested',python_outbound_sockets='blocked',summary=summary,
        metrics=dict(main_window_seconds=round(startup,3),rss_after_main_window_mb=round(rss_start/1024**2,1),peak_parent_rss_mb=round(peak/1024**2,1),peak_parent_and_children_rss_mb=round(aggregate_peak[0]/1024**2,1),
            limitation='RSS sum sampled every 30 ms while Qt event loop runs; can double-count shared pages or miss brief spikes; Linux not Windows'),
        original_raw_text_flow=legacy_status,records=records)
    (output/'evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(summary=summary,metrics=report['metrics'])))


if __name__=='__main__':main()
