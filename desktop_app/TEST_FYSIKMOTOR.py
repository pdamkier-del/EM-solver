"""Live offline acceptance tests for EM1 Solver. Do not mistake this for full validation.

On Windows, run TEST_FYSIKMOTOR_WINDOWS.bat after backend setup. Each exact-value
check below is independently derived from the relevant Maxwell law and geometry.
Only a small, stated set of examples is covered.
"""
from __future__ import annotations
import ast
import json
from pathlib import Path
from datetime import datetime, timezone

# Only symbols, numbers and basic arithmetic. Never eval solver-produced strings.
def safe_arithmetic(expression: str):
    import sympy as sp
    allowed={'pi':sp.pi,'R':sp.Symbol('R',positive=True), 'k':sp.Symbol('k'),
             'a':sp.Symbol('a',positive=True),'b':sp.Symbol('b',positive=True),
             'epsilon_0':sp.Symbol('epsilon_0',positive=True),
             'mu_0':sp.Symbol('mu_0',positive=True),
             'E0':sp.Symbol('E0'),'t':sp.Symbol('t')}
    def walk(node):
        if isinstance(node,ast.Expression):return walk(node.body)
        if isinstance(node,ast.Name):
            if node.id not in allowed:raise ValueError('Unknown symbol '+node.id)
            return allowed[node.id]
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):
            return sp.Rational(str(node.value))
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):
            return -walk(node.operand) if isinstance(node.op,ast.USub) else walk(node.operand)
        if isinstance(node,ast.BinOp):
            left,right=walk(node.left),walk(node.right)
            if isinstance(node.op,ast.Add):return left+right
            if isinstance(node.op,ast.Sub):return left-right
            if isinstance(node.op,ast.Mult):return left*right
            if isinstance(node.op,ast.Div):return left/right
            if isinstance(node.op,ast.Pow):
                # Reject excessive user-controlled powers rather than expand uncontrolled expressions.
                if not right.is_number or abs(float(right))>12:raise ValueError('Exponent outside test profile')
                return left**right
        raise ValueError('Expression outside safe arithmetic profile: '+type(node).__name__)
    if len(expression)>600:raise ValueError('Expression too large')
    return walk(ast.parse(expression,mode='eval'))


def exact_match(actual: str, expected: str) -> bool:
    import sympy as sp
    return sp.simplify(safe_arithmetic(actual)-safe_arithmetic(expected))==0


CASES=[
  {'id':'EV_sphere', 'title':'Gauss: kugle med rho(r)=kr',
   'text':'En massiv kugle med radius R har rho(r)=k*r. Bestem den totale ladning Q.',
   'corrections':{},'expected':{'Q':'pi*k*R**4'}},
  {'id':'EV_shell', 'title':'Gauss: kugleskal rho=k/r²',
   'text':'En kugleskal a<r<b har rho(r)=k/r**2. V(infinity)=0. Bestem V og Q.',
   'corrections':{},'expected':{'Q':'4*pi*k*(b-a)'}},
  {'id':'BA_cylinder', 'title':'Ampere: varierende strøm i cylinder',
   'text':'En uendelig cylinder med radius R har J(s)=k*s zhat. Bestem B og den totale strøm I.',
   'corrections':{},'expected':{'I':'2*pi*k*R**3/3'}},
  {'id':'DYN_capacitor', 'title':'Ampere–Maxwell: tidsafhængigt E',
   'text':'En kondensator har cirkulære plader med radius R. E(t)=E0*t**2 zhat er uniformt mellem pladerne. Randeffekter ignoreres. Bestem B(s,t) og forskydningsstrøm.',
   'corrections':{},'expected':{'J_displacement':'2*E0*epsilon_0*t'}},
  {'id':'EV_cylinder_manual', 'title':'Gauss: massiv cylinder, assisteret',
   'text':'En uendeligt lang massiv cylinder med radius R har uniform volumenladningstæthed rho0. Bestem det elektriske felt E(s) indenfor og udenfor cylinderen.',
   'corrections':{'coordinate':'s','geometry':'cylinder','extent':'infinite','radius':'R'},
   'required_results':['E']},
]


def run():
    import sys
    from backend_paths import location
    sys.path.insert(0,str(location()[0]))
    from em1_solver.backend_client import run_text
    report={'date_utc':datetime.now(timezone.utc).isoformat(),'scope':'Five selected cases, not general EM1 accuracy.', 'cases':[]}
    good=0
    for case in CASES:
        row={'id':case['id'],'title':case['title'],'corrections':case['corrections']}
        print('\n'+case['title'])
        try:
            reply=run_text(case['text'],corrections=case['corrections'])
            row['status']=reply.get('status')
            sol=reply.get('solution') or {}
            row['step_count']=len(sol.get('steps') or [])
            checks=sol.get('checks') or []
            row['passed_checks']=sum(c.get('passed') is True for c in checks if isinstance(c,dict))
            row['failed_checks']=[c.get('name','?') for c in checks if isinstance(c,dict) and c.get('passed') is False]
            results=sol.get('results') or {}
            row['result_keys']=list(results)
            row['expected_comparisons']={}
            for key,expected in case.get('expected',{}).items():
                actual=(results.get(key) or {}).get('expression')
                if not actual:
                    row['expected_comparisons'][key]={'pass':False,'reason':'Missing expression'}
                else:
                    try:
                        match=exact_match(actual,expected)
                        row['expected_comparisons'][key]={'pass':match,'actual':actual,'expected':expected}
                    except (ValueError,TypeError,SyntaxError,OverflowError) as err:
                        row['expected_comparisons'][key]={'pass':False,'reason':str(err)}
            required=case.get('required_results',[])
            row['pass']=(row['status'] in ('verified','verified_with_assumptions')
                and row['step_count']>0 and not row['failed_checks']
                and all(r['pass'] for r in row['expected_comparisons'].values())
                and all(k in results for k in required))
            if row['pass']:good+=1
            if not row['pass']:
                row['missing']=reply.get('missing')
                row['errors']=reply.get('errors')
            print('  status:',row['status'],'steps:',row['step_count'],
                  'check pass/failed:',row['passed_checks'],len(row['failed_checks']))
            print('  independent comparisons:',row['expected_comparisons'])
            print('  RESULTAT:', 'BESTÅET' if row['pass'] else 'IKKE BESTÅET')
        except Exception as err:
            row['pass']=False;row['error']=repr(err)
            print('  FEJL:',repr(err))
        report['cases'].append(row)
    report['passed']=good
    report['total']=len(CASES)
    path=Path(__file__).resolve().parent/'EM1_FYSIK_TESTRAPPORT.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf8')
    print(f'\nRESULTAT: {good}/{len(CASES)} beståede. Rapport: {path}')
    print('Bemærk: Formelkontrollen dækker kun de eksplicit angivne delresultater.')
    return 0 if good==len(CASES) else 1

if __name__=='__main__':raise SystemExit(run())
