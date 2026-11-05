"""Offline raw-text evaluation. IDs and gold enter verification ONLY after solve_text.

No assisted inputs, recipes, IDs or expected values enter the production parser.
The historical recipes are verification data, never a fallback solving path here.
"""
import sys,json,hashlib,copy,re,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import sympy as sp
from em1_solver.text_parser import analyze,solve_text
from em1_solver.core.new_problem import symbols_for
from em1_solver.core.parsing import expression
from em1_solver.core.dimensions import unit_dimension
from em1_solver.core.task_runtime import block_network


def manifest():
    paths=[ROOT/'app.py',*sorted((ROOT/'em1_solver').rglob('*.py'))]
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def semantic(p):
    f=p.facts;ori=p.fields.get('orientation');orientation=ori.value if ori else None
    return dict(geometry=f.get('geometry'),source=f.get('source'),wanted=sorted(f.get('wanted',[])),
                regions=p.fields['regions'].value if 'regions' in p.fields else None,orientation=orientation)


def field_checks(p,label):
    if not label:return {}
    actual=semantic(p);out={}
    for key,expected in label.get('fields',{}).items():
        if expected is None:continue # Explicitly unscorable from damaged text, not a free success.
        if key=='wanted':out[key]=set(actual[key])==set(expected)
        elif key=='regions' and isinstance(expected,list):
            try:
                def density(value):
                    symbols={n:sp.Symbol(n,real=True) for n in re.findall(r'\b[A-Za-z_]\w*\b',str(value))}
                    return sp.Matrix([expression(v,symbols) for v in value]) if isinstance(value,list) else expression(value,symbols)
                def same(a,b):
                    if a==b:return True
                    residual=sp.simplify(density(a)-density(b))
                    return all(v==0 for v in residual) if isinstance(residual,sp.MatrixBase) else residual==0
                rows=actual[key]
                out[key]=isinstance(rows,list) and len(rows)==len(expected) and all(a['lower']==b['lower'] and a['upper']==b['upper'] and same(a['density'],b['density']) for a,b in zip(rows,expected))
            except (ValueError,TypeError,KeyError):out[key]=False
        else:out[key]=actual[key]==expected
    for name,value in label.get('facts',{}).items():out[name]=p.facts.get(name)==value
    if 'source_expression' in label:
        try:
            actual=p.facts['formula'];expected=label['source_expression']
            names=set(re.findall(r'\b[A-Za-z_]\w*\b',str(actual)+' '+str(expected)))
            symbols={name:sp.Symbol(name,real=True) for name in names}
            def math(value):return sp.Matrix([expression(v,symbols) for v in value]) if isinstance(value,list) else expression(value,symbols)
            residual=sp.simplify(math(actual)-math(expected))
            out['source_formula']=all(v==0 for v in residual) if isinstance(residual,sp.MatrixBase) else residual==0
        except (ValueError,TypeError,KeyError):out['source_formula']=False
    return out


def verify_bank(id,p,answer):
    """Normalize dummy variable/interval names for the frozen independent oracles."""
    from blind_oracles import verify
    parsed=copy.deepcopy(p.problem);result=copy.deepcopy(answer)
    if id in ('EV03','EV05','BA02'):
        parsed.units['h']='m';parsed.positive.append('h')
        sy=symbols_for(parsed)
        replacement={sy['b']:sy['a']+sy['h']}
        result.symbolic_result={k:v.subs(replacement) for k,v in result.symbolic_result.items()}
    if id in ('EV09','BA05','EV11'):
        parameter='phi' if id=='EV11' else 'u'
        parsed.units[parameter]='1' if id=='EV11' else 'm';sy=symbols_for(parsed)
        result.symbolic_result={k:v.xreplace({sy['parser_u']:sy[parameter]}) for k,v in result.symbolic_result.items()}
    verify(id,parsed,result)
    return dict(symbolic=True,numerical='not separately checked by this oracle',dimensions=True)


def verify_historical(row,p,answer):
    recipe=json.loads((ROOT/'data/historical_problems'/f"{row['exam'].replace('-','_')}_p{row['problem']}{row['subproblem']}.json").read_text())
    symbols=symbols_for(p.problem)
    def decode(value):
        if isinstance(value,dict) and set(value)=={'expr'}:return expression(value['expr'],symbols)
        if isinstance(value,dict) and set(value)=={'matrix'}:return sp.Matrix(decode(value['matrix']))
        if isinstance(value,list):return [decode(v) for v in value]
        raise ValueError('Denne facitstruktur kræver en særskilt verifier.')
    checked=[];numeric=[]
    for check in recipe.get('expected',[]):
        name=check['result']
        if name not in p.problem.wanted:continue
        if name not in answer.symbolic_result:raise AssertionError('Søgt resultat mangler: '+name)
        expected=decode(check['value']);actual=answer.symbolic_result[name]
        residual=sp.simplify(actual-expected)
        assert all(v.equals(0) is True for v in residual) if isinstance(residual,sp.MatrixBase) else residual.equals(0) is True,(name,actual,expected)
        assert unit_dimension(answer.units[name])==unit_dimension(check['unit'])
        checked.append(name)
        if 'numeric' in check:
            n=check['numeric'];value=actual.subs({symbols[k]:sp.Rational(str(v)) for k,v in n['values'].items()})
            from em1_solver.core.units import CONSTANTS
            value=value.subs({s:sp.Float(CONSTANTS[s.name]) for s in value.free_symbols if s.name in CONSTANTS})
            assert abs(float(value)-n['value'])<=n['tolerance'];numeric.append(name)
    assert set(p.problem.wanted)<=set(checked),'Ingen passende uafhængig facitcheck for alle søgte størrelser.'
    dims=[c for c in answer.checks if c.name.startswith('Dimension:')]
    assert dims and all(c.passed is True for c in dims),'Dimensionskontrol mangler'
    return dict(symbolic=True,numerical=numeric or 'not available',dimensions=True)


def attempt(text,label,verifier,corrections=None):
    start=time.monotonic();r=dict(status='abstained',corrections=corrections or {},silent_wrong=False)
    try:
        p=analyze(text,corrections);r.update(ready=p.ready,fields=field_checks(p,label),interpretation=p.snapshot(),questions={k:v.message for k,v in p.questions.items()})
        if not p.ready:return r
        r['full_parse']=bool(label and r['fields'] and all(r['fields'].values()) and label.get('full_review',False))
        _,a=solve_text(text,corrections,evaluate=False,timeout=18)
        r.update(status='solved_unverified',result={k:str(v) for k,v in a.symbolic_result.items()},warnings=a.warnings,method=a.method,
                 checks=[dict(name=c.name,passed=c.passed) for c in a.checks])
        try:
            r['verification']=verifier(p,a);r['status']='verified'
            r['correct_refusal']=set(p.facts['wanted'])<=set(['curl_E','div_B']) and any(c.passed is False for c in a.checks)
        except (AssertionError,ValueError,KeyError,TypeError) as exc:
            r['status']='wrong_or_unverified';r['reason']=str(exc)
            # Count EVERY incorrect/unverified automatic output conservatively, even if generic warnings exist.
            r['silent_wrong']=True
    except Exception as exc:r.update(status='error',reason=type(exc).__name__+': '+str(exc))
    finally:r['seconds']=round(time.monotonic()-start,3)
    return r


def summary(records):
    fields={};total=len(records)
    for key in ('geometry','source','wanted','regions','orientation'):
        values=[r['autonomous']['fields'][key] for r in records if key in r['autonomous'].get('fields',{})]
        fields[key]=dict(correct=sum(values),scorable=len(values),percent=round(100*sum(values)/len(values),1) if values else None)
    groups=Counter();failures=Counter()
    for r in records:
        a=r['autonomous'];aided=r.get('corrected')
        if a['status']=='verified':groups['0']+=1
        elif aided and aided['status']=='verified':groups['1' if len(aided['corrections'])==1 else '2–3']+=1
        else:groups['manual']+=1
        failures.update(a.get('questions',{}).keys())
    verified=sum(r['autonomous']['status']=='verified' for r in records)
    return dict(total=total,autonomous_full_parse=sum(r['autonomous'].get('full_parse',False) for r in records),autonomous_solved=verified,
                autonomous_percent=round(100*verified/total,1),correction_buckets={k:groups[k] for k in ('0','1','2–3','manual')},
                correct_refusals=sum(r['autonomous'].get('correct_refusal',False) for r in records),
                silent_wrong=sum(r['autonomous']['silent_wrong'] or r.get('corrected',{}).get('silent_wrong',False) for r in records),
                figure_required=sum('figure' in r['autonomous'].get('questions',{}) for r in records),field_accuracy=fields,unresolved_fields=dict(failures.most_common()),
                statuses=dict(Counter(r['autonomous']['status'] for r in records)))


def main():
    block_network()
    start=manifest();frozen=json.loads((ROOT/'reports/parser/evaluation_manifest.json').read_text())
    assert start==frozen['source_manifest'],'Parseren er ændret siden udviklingsfrysningen. Frys ikke på ny efter holdout uden at bevare første resultat.'
    split=json.loads((ROOT/'data/parser/split.json').read_text());labels=json.loads((ROOT/'data/parser/evaluation_ground_truth.json').read_text())
    bank=json.loads((ROOT/'data/blind_unseen_bank_v2.json').read_text())['tests'];bank_records=[]
    historical=json.loads((ROOT/'data/exam_problem_registry.json').read_text());history_records=[]
    for row in bank:
        label=labels.get(row['id'],{});verifier=lambda p,a,id=row['id']:verify_bank(id,p,a)
        record=dict(id=row['id'],autonomous=attempt(row['problem'],label,verifier))
        if record['autonomous']['status']!='verified' and 0<len(label.get('corrections',{}))<=3:
            record['corrected']=attempt(row['problem'],label,verifier,label['corrections'])
        bank_records.append(record);print(row['id'],record['autonomous']['status'],flush=True)
    for row in historical:
        id=f"{row['exam']}:{row['problem']}{row['subproblem']}";label=labels.get(id,{})
        raw=row['source_context']+'\n'+row['source_question'];verifier=lambda p,a,row=row:verify_historical(row,p,a)
        record=dict(id=id,exam=row['exam'],autonomous=attempt(raw,label,verifier))
        if record['autonomous']['status']!='verified' and 0<len(label.get('corrections',{}))<=3:record['corrected']=attempt(raw,label,verifier,label['corrections'])
        history_records.append(record)
    assert start==manifest(),'Koden ændrede sig under målingen.'
    holdout=[r for r in history_records if r['exam'] in split['holdout_exams']]
    output=dict(limitation=split['limitation']+' 55-banken er nu også kendt regression, ikke en ny blindtest. Korrektioner er menneskelige evalueringsinput, aldrig parserdata.',
                baseline_autonomous_bank=dict(solved=3,total=55),summary=dict(bank=summary(bank_records),holdout=summary(holdout),historical=summary(history_records)),
                bank_records=bank_records,historical_records=history_records,source_manifest=start,
                evaluator_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'tools/evaluate_text_parser.py',ROOT/'tools/blind_oracles.py']},
                data_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'data/parser/evaluation_ground_truth.json',ROOT/'data/exam_problem_registry.json',ROOT/'data/blind_unseen_bank_v2.json']})
    (ROOT/'reports/parser/evaluation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2,default=str)+'\n')
    print(json.dumps(output['summary'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
