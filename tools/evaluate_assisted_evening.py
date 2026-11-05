"""Known-exam structured replay, not a fresh blind or autonomous benchmark.

Runtime receives only explicit givens/model cards. Official-reference checks are
read and applied after answers have been saved. No exam-ID route in production.
"""
import json
import sys
from pathlib import Path
import sympy as sp
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from em1_solver.assisted_backend import respond
from em1_solver.core.task_runtime import block_network


def main():
    block_network()
    folder=ROOT/'data/integration/assisted_v1'
    records=[]
    for path in sorted(folder.glob('*.request.json')):
        request=json.loads(path.read_text())
        reply=respond(request,solve=True)
        path.with_name(path.name.replace('.request.','.response.')).write_text(json.dumps(reply,ensure_ascii=False,indent=2)+'\n')
        record=dict(case=path.stem.replace('.request',''),status=reply['status'],outcome='reasoned_refusal',first_failure=None,checks=[])
        if reply['status']=='needs_confirmation':
            record['first_failure']='missing_confirmed_model_data';records.append(record);continue
        if reply['status']=='not_solved':
            record['first_failure']=reply['errors'] or reply['subproblems'][0]['errors'];records.append(record);continue
        # The reference is opened only after the result is computed and stored.
        reference=json.loads((ROOT/'data/historical_problems'/f"{record['case']}.json").read_text())
        sy={k:sp.Symbol(k,**v) for k,v in reference['symbols'].items()}
        def decode(value):
            if isinstance(value,list):return [decode(v) for v in value]
            if isinstance(value,dict):
                if 'expr' in value:return sp.sympify(value['expr'].replace('^','**'),locals=sy)
                if 'matrix' in value:return sp.Matrix(decode(value['matrix']))
            return value
        solution=reply['subproblems'][0]['solution']
        for check in reference['expected']:
            item=solution['results'].get(check['result'])
            try:
                assert item is not None,'missing result'
                actual=sp.sympify(item['expression'],locals=sy)
                actual=actual.subs({sy[k]:decode(v) for k,v in check.get('subs',{}).items()},simultaneous=True)
                residual=sp.simplify(actual-decode(check['value']))
                assert all(v.equals(0) is True for v in residual) if isinstance(residual,sp.MatrixBase) else residual.equals(0) is True
                assert item['unit']==check.get('unit',item['unit'])
                if 'sign' in check:assert sp.sign(sp.simplify(sp.expand_log(actual)))==check['sign']
                if 'numeric' in check:
                    n=check['numeric'];value=actual.subs({sy[k]:v for k,v in n['values'].items()}).evalf()
                    assert abs(float(value)-n['value'])<=n['tolerance']
                record['checks'].append(dict(result=check['result'],passed=True))
            except (AssertionError,TypeError,ValueError) as exc:
                record['checks'].append(dict(result=check['result'],passed=False,error=str(exc)))
        correct=bool(record['checks']) and all(c['passed'] for c in record['checks'])
        record['outcome']='incorrect' if not correct else 'partial' if reply['status']=='partial' else 'correct_assisted'
        if not correct:record['first_failure']='official_reference_comparison'
        records.append(record)
    summary={key:sum(r['outcome']==key for r in records) for key in ['correct_autonomous','correct_assisted','partial','reasoned_refusal','incorrect']}
    report=dict(benchmark='Known historical typed-model replay; human/model assistance supplied in request fixtures, not raw-text autonomy.',
        outbound_network='blocked in evaluator and spawned solvers',summary=summary,records=records)
    out=ROOT/'reports/assisted_evening';out.mkdir(parents=True,exist_ok=True)
    (out/'dyn_evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':main()
