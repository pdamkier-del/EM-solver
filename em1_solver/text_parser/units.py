"""Dimensional constraints infer units, not values, signs or physical roles."""
import sympy as sp
from ..core.dimensions import unit_dimension
from ..core.parsing import expression


def infer_units(expressions,known):
    """Each expression is (math, target SI unit). Returns uniquely determined units."""
    names=set()
    import re
    from ..core.parsing import FUNCTIONS
    for expr,_ in expressions:names.update(re.findall(r'\b[A-Za-z_]\w*\b',expr))
    names-=set(FUNCTIONS)|{'pi','oo'}
    symbols={n:sp.Symbol(n,real=True) for n in names}
    unknown=sorted(names-set(known)-{'epsilon_0','mu_0'})
    dims={n:sp.Matrix(unit_dimension(u)) for n,u in known.items() if n in names}
    dims.update({n:sp.Matrix(unit_dimension(u)) for n,u in {'epsilon_0':'F/m','mu_0':'H/m'}.items() if n in names})
    parameters=[]
    for n in unknown:
        variables=sp.symbols('_dim_'+n+'_0:4');parameters.extend(variables);dims[n]=sp.Matrix(variables)
    constraints=[];zero=sp.zeros(4,1)
    def equal(a,b):constraints.extend(list(a-b))
    def dim(value):
        if value==0:return None
        if value.is_Number or value in (sp.pi,sp.E,sp.oo,-sp.oo):return zero
        if value.is_Symbol:return dims[str(value)]
        if value.is_Add:
            ds=[dim(v) for v in value.args];ds=[d for d in ds if d is not None]
            for other in ds[1:]:equal(ds[0],other)
            return ds[0] if ds else None
        if value.is_Mul:
            result=zero
            for v in value.args:result=result+(dim(v) if v!=0 else zero)
            return result
        if value.is_Pow:
            base,power=value.args
            if not power.is_number:raise ValueError('Symbolsk eksponent kræver eksplicitte enheder og domæne.')
            return (dim(base) if base!=0 else zero)*power
        if value.func in (sp.Abs,sp.sign):return dim(value.args[0]) if value.func==sp.Abs else zero
        if value.func in (sp.sin,sp.cos,sp.tan,sp.exp,sp.log,sp.asin,sp.acos,sp.atan):
            equal(dim(value.args[0]),zero);return zero
        raise ValueError('Dimensionsregel mangler for '+str(value.func))
    for expr,unit in expressions:
        value=expression(expr,symbols)
        values=value if isinstance(value,list) else [value]
        for v in values:
            d=dim(v)
            if d is not None:equal(d,sp.Matrix(unit_dimension(unit)))
    if not parameters:
        if any(sp.simplify(c)!=0 for c in constraints):raise ValueError('De angivne enheder er indbyrdes inkonsistente.')
        return dict(known),[]
    solution=sp.linsolve(constraints,parameters)
    if solution is sp.EmptySet or not solution:raise ValueError('Enhederne kan ikke opfylde de fysiske dimensionskrav.')
    values=list(next(iter(solution)));result=dict(known);unresolved=[]
    for i,n in enumerate(unknown):
        ds=values[4*i:4*i+4]
        if any(v.free_symbols for v in ds):unresolved.append(n);continue
        result[n]='*'.join(f'{u}**({v})' for u,v in zip(['kg','m','s','A'],ds))
    return result,unresolved
