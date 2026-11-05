"""Compare prior raw-text evidence and evaluate a withheld internal generation run.
The evaluator owns IDs, references and seeds; production receives text only.
"""
import sys,json,hashlib,random,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import sympy as sp
from evaluate_text_parser import attempt,verify_bank,verify_historical,manifest
from em1_solver.text_parser import analyze
from em1_solver.core.new_problem import symbols_for
from em1_solver.core.validation import EPS0,MU0
from em1_solver.core.parsing import expression
from em1_solver.core.task_runtime import block_network


def metrics(records):
    outcomes=[r['result'] for r in records];passed=sum(r['status']=='verified' for r in outcomes);wrong=sum(r['status']=='wrong_or_unverified' for r in outcomes)
    emitted=passed+wrong
    return dict(attempted=len(records),correct=passed,refused=sum(r['status']=='abstained' for r in outcomes),errors=sum(r['status']=='error' for r in outcomes),incorrect=wrong,
                emitted=emitted,correctness_among_answers=round(passed/emitted,4) if emitted else None,autonomous_rate=round(passed/len(records),4),silent_wrong=sum(r.get('silent_wrong',False) for r in outcomes))


def verify_history_total(row,p,answer):
    try:return verify_historical(row,p,answer)
    except AssertionError as exc:
        if 'Ingen passende uafhængig facitcheck' not in str(exc) or p.problem.wanted!=['Q']:raise
    # Generic vocabulary reconciliation: total Q equals Q_enc at the outer edge.
    recipe=json.loads((ROOT/'data/historical_problems'/f"{row['exam'].replace('-','_')}_p{row['problem']}{row['subproblem']}.json").read_text())
    sy=symbols_for(p.problem);coord=p.facts['coordinate'];outer=p.facts['active_regions'][-1]['upper']
    candidates=[c for c in recipe['expected'] if c['result']=='Q_enc' and c.get('subs',{}).get(coord)=={'expr':outer} and c.get('unit')=='C']
    assert candidates,'No independent total-charge reference at the stated outer boundary'
    for reference in candidates:
        expected=expression(reference['value']['expr'],sy)
        assert sp.simplify(answer.symbolic_result['Q']-expected).equals(0) is True
    assert all(c.passed is True for c in answer.checks if c.name.startswith('Dimension:'))
    return dict(symbolic=True,numerical='not available',dimensions=True,reference_mapping='Q_enc at source outer boundary -> total Q')


def generated(seed):
    rng=random.Random(seed);cases=[]
    phrases=[
      'En massiv kugle med radius R bærer volumenladningen rho(r)={density}. V(infinity)=0. Bestem den samlede ladning Q, E og V.',
      'En kuglesymmetrisk fordeling har radius R. Dens tæthed er rho(r)={density}. Potentialet sættes til nul i det uendeligt fjerne. Beregn V, E og den totale ladning Q.',
      'I en kugle med radius R findes rho(r)={density}. Udenfor er tætheden nul. V(infinity)=0. Udled E, V og den samlede ladning Q.'
    ]
    for i in range(8):
        n,m=rng.sample(range(5),2);density=f'k*(r/R)**{n}+j*(r/R)**{m}'
        text=rng.choice(phrases).format(density=density)
        if i%2==0:text=text.replace('rho(r)=',r'\rho(r)=').replace('(r/R)',r'\frac{r}{R}')
        cases.append(dict(group='solid_composite',text=text,parameters=dict(n=n,m=m)))
    for i in range(6):
        n=rng.choice([0,1,2]);text=f'En kugleskal a<r<b bærer rho(r)=k*r**{n} og nul ellers. V(infinity)=0. Bestem V og den totale ladning Q.'
        cases.append(dict(group='hollow_composite',text=text,parameters=dict(n=n)))
    for i in range(4):
        n=rng.choice([0,1,2,3]);sign=rng.choice([-1,1]);text=f'En uendelig cylinder med radius R fører J(s)={sign}*k*(s/R)**{n} zhat. Beregn B(s) og den totale strøm I.'
        cases.append(dict(group='current_composite',text=text,parameters=dict(n=n,sign=sign)))
    for i in range(2):
        n=rng.choice([2,3,4]);text=f'En kondensator har cirkulære plader med radius R. E(t)=(K*sin(omega*t)+H*t**{n}) zhat er uniformt mellem pladerne. Randeffekter ignoreres. Bestem B(s,t) og forskydningsstrøm.'
        cases.append(dict(group='displacement_composite',text=text,parameters=dict(n=n)))
    for text in [
      'En cylinder med radius R har rho(s)=k*s. Bestem E.',
      'En massiv kugle med radius R har rho(r)=k*r. Bestem V.',
      'En uendelig cylinder med radius R fører J(s)=k*s. Bestem B.',
      'En kondensator med cirkulære plader har E(t)=E0*t zhat. Bestem B(s,t).'
    ]:cases.append(dict(group='missing_prerequisite',text=text,incomplete=True))
    return cases


def check_generated(case,p,answer):
    sy=symbols_for(p.problem);group=case['group'];params=case.get('parameters',{})
    def assert_equal(actual,expected):
        difference=sp.simplify(actual-expected)
        assert difference.equals(0) is True,(actual,expected,difference)
    if group in ('solid_composite','hollow_composite'):
        r,k=sy['r'],sy['k'];u=sp.Dummy('u',positive=True)
        if group=='solid_composite':
            R,j=sy['R'],sy['j'];lo=sp.S.Zero;hi=R;density=k*(u/R)**params['n']+j*(u/R)**params['m'];points=[R/3,2*R]
        else:lo=sy['a'];hi=sy['a']+sp.Symbol('gap',positive=True);density=k*u**params['n'];points=[lo/2,(lo+hi)/2,2*hi]
        replace={sy['b']:hi} if group=='hollow_composite' else {}
        total=4*sp.pi*sp.integrate(density*u*u,(u,lo,hi));assert_equal(answer.symbolic_result['Q'].subs(replace),total)
        for point in points:
            if group=='solid_composite' and point==points[0] or group=='hollow_composite' and point==points[1]:
                enclosed=4*sp.pi*sp.integrate(density*u*u,(u,lo,point));outside=sp.integrate(density*u,(u,point,hi));potential=enclosed/(4*sp.pi*EPS0*point)+outside/EPS0
            elif group=='hollow_composite' and point==points[0]:enclosed=0;potential=sp.integrate(density*u,(u,lo,hi))/EPS0
            else:enclosed=total;potential=total/(4*sp.pi*EPS0*point)
            assert_equal(answer.symbolic_result['V'].subs(replace).subs(r,point),potential)
            if group=='solid_composite':assert_equal(answer.symbolic_result['E'].subs(r,point),enclosed/(4*sp.pi*EPS0*point**2))
    elif group=='current_composite':
        k,R,s=sy['k'],sy['R'],sy['s'];n=params['n'];sign=params['sign'];total=sign*2*sp.pi*k*R**2/(n+2)
        assert_equal(answer.symbolic_result['I'],total)
        assert_equal(answer.symbolic_result['B'].subs(s,R/3),MU0*sign*k*(R/3)**(n+1)/(R**n*(n+2)))
        assert_equal(answer.symbolic_result['B'].subs(s,2*R),MU0*total/(4*sp.pi*R))
    elif group=='displacement_composite':
        K,H,w,t,s,R=[sy[n] for n in ('K','H','omega','t','s','R')];n=params['n'];rate=K*w*sp.cos(w*t)+n*H*t**(n-1)
        assert_equal(answer.symbolic_result['B'].subs(s,R/2),MU0*EPS0*rate*R/4)
        assert_equal(answer.symbolic_result['I_displacement'].subs(s,2*R),sp.pi*R**2*EPS0*rate)
    else:raise AssertionError('An incomplete task must not be solved.')
    assert not any(c.passed is False for c in answer.checks),'Physical/dimensional check failed'
    assert any(c.name.startswith('Dimension:') and c.passed is True for c in answer.checks),'No dimensions'
    return dict(symbolic=True,numerical='symbolic parameter-space checks',dimensions=True)


def main(output_directory=None):
    output_directory=Path(output_directory) if output_directory else ROOT/'reports/autonomy'
    output_directory.mkdir(parents=True,exist_ok=True)
    block_network();frozen=manifest();baseline=json.loads((ROOT/'reports/parser/evaluation.json').read_text());labels=json.loads((ROOT/'data/parser/evaluation_ground_truth.json').read_text())
    bank=[];historical=[]
    for row in json.loads((ROOT/'data/blind_unseen_bank_v2.json').read_text())['tests']:
        result=attempt(row['problem'],labels.get(row['id'],{}),lambda p,a,id=row['id']:verify_bank(id,p,a))
        bank.append(dict(id=row['id'],result=result))
    for row in json.loads((ROOT/'data/exam_problem_registry.json').read_text()):
        id=f"{row['exam']}:{row['problem']}{row['subproblem']}";raw=row['source_context']+'\n'+row['source_question']
        historical.append(dict(id=id,exam=row['exam'],result=attempt(raw,labels.get(id,{}),lambda p,a,row=row:verify_history_total(row,p,a))))
    # Production source is frozen before new seed-derived cases are instantiated.
    seed_doc=json.loads((ROOT/'data/autonomy/sealed_seed.json').read_text());new_cases=generated(int(seed_doc['seed'],16));fresh=[]
    for i,case in enumerate(new_cases):
        result=attempt(case['text'],{},lambda p,a,case=case:check_generated(case,p,a))
        fresh.append(dict(case=i,group=case['group'],expected_incomplete=case.get('incomplete',False),text=case['text'],result=result))
    assert frozen==manifest(),'Source changed during evaluation'
    holdout=[r for r in historical if r['exam'] in ('2022-02','2023-02')]
    output=dict(protocol='Known-bank, historical and previously seen internal-generated regression. This run is not a new independent blind test. IDs and references enter verification only.',baseline_summary=baseline['summary'],
        summary=dict(bank=metrics(bank),historical=metrics(historical),old_holdout_regression=metrics(holdout),internal_generated=metrics(fresh)),
        complete_generated=metrics([r for r in fresh if not r['expected_incomplete']]),correctly_refused_generated=sum(r['expected_incomplete'] and r['result']['status']=='abstained' for r in fresh),
        bank=bank,historical=historical,internal_generated=fresh,source_manifest=frozen,evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seed_sha256=hashlib.sha256((ROOT/'data/autonomy/sealed_seed.json').read_bytes()).hexdigest())
    (output_directory/'evaluation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2,default=str)+'\n');print(json.dumps(output['summary'],indent=2))
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output-directory',type=Path)
    main(parser.parse_args().output_directory)
