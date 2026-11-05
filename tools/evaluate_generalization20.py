"""Prospective self-authored GUI evaluation; references are a later separate step."""
import os,sys,json,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/generalization/evaluation20'
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ.setdefault('APPDATA','/tmp/em1-evaluation20');os.environ.setdefault('MPLCONFIGDIR','/tmp/em1-eval20-mpl')
sys.path[:0]=[str(ROOT),str(ROOT/'tests/desktop')]
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtCore import Qt,QProcess
from PySide6.QtTest import QTest
from desktop_app import app as host
from test_dyn_panel import fill
from em1_solver.core.task_runtime import block_network
from em1_solver.core.certification import fingerprint
import psutil

def main():
    source=OUT/'questions_and_inputs.json';seal=json.loads((OUT/'seal.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==seal['sha256']
    cases=json.loads(source.read_text());block_network();q=QApplication([]);host.init_db();answers=[]
    maximum_rss=0
    def wait(predicate,seconds):
        nonlocal maximum_rss
        end=time.monotonic()+seconds
        while not predicate() and time.monotonic()<end:
            q.processEvents();QTest.qWait(15)
            try:maximum_rss=max(maximum_rss,sum(p.memory_info().rss for p in [psutil.Process(),*psutil.Process().children(recursive=True)]))
            except psutil.Error:pass
        q.processEvents();return predicate()
    for case in cases:
        previous=OUT/(case['id']+'.app.json')
        if previous.exists():
            answers.append(json.loads(previous.read_text()));print(case['id'],'already recorded; not rerun',flush=True);continue
        w=host.MainWindow();w.show();solver=w.solver;solver.prompt.setPlainText(case['text'])
        start=time.monotonic();QTest.mouseClick(solver.solve_button,Qt.LeftButton)
        assert wait(lambda:solver.solve_button.isEnabled(),125),case['id']+' raw GUI timeout'
        raw=solver._backend_reply
        record=dict(id=case['id'],domain=case['domain'],model=case['model'],automatic_response=raw,automatic_view=solver.last_payload,automatic_seconds=round(time.monotonic()-start,3))
        if case['request']:
            solver.prompt.setPlainText(case['text']);QTest.mouseClick(solver.physical_model_button,Qt.LeftButton)
            p=solver.assisted
            # The form currently scans result references as symbols too. Supplying
            # their known physical units is recorded assistance, not an answer.
            import copy
            entered=copy.deepcopy(case['request'])
            for name,unit in {'E':'V/m','V':'V','B':'T','I':'A','EMF':'V','Q':'C'}.items():entered['units'].setdefault(name,unit)
            fill(p,entered);record['submitted_request']=p.request()
            record['extra_result_unit_rows']=[p.symbols.item(row,0).text() for row in range(p.symbols.rowCount()) if p.symbols.item(row,0).text() not in case['request']['units']]
            # Semantic edits, not timed human mouse movements. Every value remains explicit.
            controls=dict(prompt=1,open_model=1,model_selection=1,scalar_fields=len(p.fields),table_cells=sum(t.rowCount()*t.columnCount() for t in p.tables.values()),
                scan_symbols=1,unit_entries=p.symbols.rowCount(),numeric_entries=len(case['request']['numbers']),positive_flags=len(case['request']['positive']),
                wanted=1,assumption_checks=len(case['request']['assumptions']),orientation=1,confirmation=1,solve=1,
                operation_cells=sum(len(op) for op in case['request']['subproblems'][0].get('operations',[])))
            record['assistance_actions']=controls;record['assistance_action_count']=sum(controls.values())
            start=time.monotonic();QTest.mouseClick(p.solve,Qt.LeftButton)
            assert wait(lambda:not p.busy,45),case['id']+' assisted GUI timeout'
            record['assisted_response']=p.last_reply;record['assisted_view']=solver.last_payload;record['assisted_seconds']=round(time.monotonic()-start,3)
            record['math_display_errors']=[x.text() for view in (solver.result,solver.derivation,solver.explanation) for x in view.findChildren(QLabel) if 'Kunne ikke vise matematik' in x.text()]
            w.grab().save(str(OUT/(case['id']+'.png')))
        else:
            record['assisted_response']=None;record['assistance_action_count']=0
            record['no_matching_card_reason']={'EV7':'Intet kort løser en generel kubisk leders randværdiproblem.','BA6':'Ingen entydig B uden materialets hysteresegren og materialedata.','DYN7':'Intet kort for seriel RLC med to begyndelsesbetingelser.'}[case['id']]
        (OUT/(case['id']+'.app.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        answers.append(record);w.close();q.processEvents();print(case['id'],raw.get('status') if raw else None,record.get('assisted_response',{}).get('status') if record.get('assisted_response') else 'no card',flush=True)
    (OUT/'execution.json').write_text(json.dumps(dict(native_windows_tested=False,platform='Linux Qt offscreen',outbound_sockets='blocked',fingerprint=fingerprint(),sealed_questions_sha256=seal['sha256'],reference_answers_used_during_execution=False,maximum_sampled_parent_and_children_rss_bytes=maximum_rss,cases=answers),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
