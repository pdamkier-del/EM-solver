"""Portable historical recipes: typed data, explicit solver paths, independent oracles."""
from dataclasses import dataclass,field
from pathlib import Path
import json
import sympy as sp
from .problem import Problem,Region,InputError
from .parsing import expression
from .dimensions import dimension,unit_dimension,DimensionError

ROOT=Path(__file__).resolve().parents[2]/'data/historical_problems'

@dataclass
class RecipeRun:
    solutions: dict=field(default_factory=dict)
    checks: list=field(default_factory=list)
    passed: bool=False

def paths():return sorted(ROOT.glob('*.json'))

def load(path):return json.loads(Path(path).read_text())

def run(recipe):
    from .registry import solve
    if recipe['status'] not in ('executable','partial'):raise InputError('Opskriften er '+recipe['status'])
    symbols={name:sp.Symbol(name,**assumptions) for name,assumptions in recipe['symbols'].items()}
    context=dict(symbols);answers={};out=RecipeRun()
    def decode(value):
        if isinstance(value,list):return [decode(v) for v in value]
        if isinstance(value,dict):
            if set(value)=={'expr'}:return expression(value['expr'],context)
            if set(value)=={'matrix'}:return sp.Matrix(decode(value['matrix']))
            if set(value)=={'map'}:return {decode(k):decode(v) for k,v in value['map']}
            if 'piecewise' in value:
                return sp.Piecewise(*[(decode(v),decode(c)) for v,c in value['piecewise']])
            if set(value)=={'relation','left','right'}:
                relation={'lt':sp.Lt,'le':sp.Le,'gt':sp.Gt,'ge':sp.Ge,'eq':sp.Eq}[value['relation']]
                return relation(decode(value['left']),decode(value['right']))
            if 'ref' in value and set(value)<= {'ref','indices','substitute'}:
                step,key=value['ref'].split('.',1)
                result=answers[step].symbolic_result[key]
                for index in value.get('indices',[]):result=result[index]
                if 'substitute' in value:result=result.subs({symbols[name]:decode(v) for name,v in value['substitute'].items()},simultaneous=True)
                return result
            return {k:decode(v) for k,v in value.items()}
        return value
    for step in recipe['path']:
        for name,value in step.get('bindings',{}).items():context[name]=decode(value)
        spec=step['problem']
        numerical_values=recipe.get('given_values',{})|spec.get('numerical_values',{})
        p=Problem(domain=spec['domain'],family=spec['family'],geometry=spec.get('geometry',recipe['geometry']),
            variables=decode(spec.get('variables',{})),functions=decode(spec.get('functions',{})),
            regions=[Region(**decode(r)) for r in spec.get('regions',[])],assumptions=spec.get('assumptions',[]),wanted=spec.get('wanted',[]),
            numerical_values={symbols[k]:v for k,v in numerical_values.items()},
            numerical_units={symbols[k]:v for k,v in spec.get('numerical_units',{}).items()},
            symbol_units={symbols[k]:unit for k,unit in recipe['symbol_units'].items() if k in symbols})
        answers[step['id']]=solve(p)
    out.solutions=answers
    for check in recipe['expected']:
        actual=answers[check['step']].symbolic_result[check['result']]
        if 'component' in check:actual=actual[check['component']]
        for index in check.get('indices',[]):actual=actual[index]
        substitutions={symbols[k]:decode(v) for k,v in check.get('subs',{}).items()}
        if substitutions:actual=actual.subs(substitutions,simultaneous=True)
        expected=decode(check['value'])
        if isinstance(actual,(str,list,tuple,dict)):
            symbolic_ok=actual==expected;residual=0 if symbolic_ok else 'structured mismatch'
        else:
            residual=sp.simplify(sp.expand(actual-expected))
            symbolic_ok=all(v.equals(0) is True for v in residual) if isinstance(residual,sp.MatrixBase) else residual.equals(0) is True
        ok=symbolic_ok
        if check.get('unit'):
            try:ok &= dimension(actual,{symbols[k]:v for k,v in recipe['symbol_units'].items()}) in (None,unit_dimension(check['unit']))
            except DimensionError:ok=False
        if 'sign' in check:ok &= sp.sign(sp.simplify(sp.expand_log(actual)))==check['sign']
        if 'numeric' in check:
            numeric=check['numeric'];values={symbols[k]:expression(v,context) if isinstance(v,str) else sp.Rational(str(v)) for k,v in numeric['values'].items()}
            values.update({sym:sp.Float('8.8541878128e-12') if sym.name=='epsilon_0' else sp.Float('1.25663706212e-6') for sym in actual.free_symbols if sym.name in ('epsilon_0','mu_0')})
            evaluated=actual.subs(values).evalf()
            ok &= not evaluated.free_symbols and abs(float(evaluated)-numeric['value'])<=numeric['tolerance']
        out.checks.append({'name':check['step']+'.'+check['result'],'passed':bool(ok),'residual':str(residual)})
    out.passed=bool(out.checks) and all(c['passed'] for c in out.checks)
    return out
