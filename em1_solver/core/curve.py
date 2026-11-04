"""Bounded line-source integrals; closed forms are optional, never invented."""
import multiprocessing as mp
import queue
import sympy as sp
from .problem import InputError
from .solution import solution
from .validation import EPS0,MU0
from .dimensions import check_solution
from .units import numerical


def _integrate_worker(output,expr,limits):
    from .task_runtime import block_network
    block_network()
    try:output.put(('ok',sp.integrate(expr,*limits)))
    except Exception as exc:output.put(('error',str(exc)))


def bounded_integral(expr,limits,seconds=2,return_status=False):
    integral=sp.Integral(expr,*limits)
    def finish(value,timed=False):return (value,timed) if return_status else value
    if expr==0:return finish(sp.S.Zero)
    context=mp.get_context('spawn');output=context.Queue()
    process=context.Process(target=_integrate_worker,args=(output,expr,limits));process.start()
    try:
        try:kind,value=output.get(timeout=seconds)
        except queue.Empty:return finish(integral,True)
        return finish(value if kind=='ok' and not value.has(sp.nan,sp.zoo,sp.oo,-sp.oo) else integral)
    finally:
        if process.is_alive():process.terminate()
        process.join(timeout=1);output.close()


def line_integrals(p,evaluate=False,budget=2):
    """Set up arbitrary regular oriented Cartesian curves, then bounded integration."""
    source,u,bounds,point=p.require('source','parameter','bounds','point')
    source,point=sp.Matrix(source),sp.Matrix(point)
    if source.shape!=(3,1) or point.shape!=(3,1) or not isinstance(u,sp.Symbol) or len(bounds)!=2:
        raise InputError('Kurven kræver tre kartesiske komponenter, én parameter og to grænser.')
    if u in point.free_symbols:raise InputError('Feltpunktet må ikke afhænge af kildeparameteren.')
    if any(u in sp.sympify(b).free_symbols for b in bounds):raise InputError('Grænser må ikke afhænge af integrationsparameteren.')
    if sp.simplify(bounds[1]-bounds[0]).is_nonpositive:raise InputError('Kurvegrænserne skal være voksende; vend kilden eller strømmen for modsat orientering.')
    tangent=source.diff(u);jac=sp.sqrt(tangent.dot(tangent));delta=point-source;distance=sp.sqrt(delta.dot(delta))
    if any(sp.simplify(delta.subs(u,b))==sp.zeros(3,1) for b in bounds):raise InputError('Feltpunktet ligger på et endepunkt af kilden (singularitet).')
    if jac==0 or distance==0:raise InputError('Degenereret kurve eller feltpunkt på kilden.')
    if p.family=='coulomb_integral':
        density,=p.require('density');weight=density*jac
        integrands={'Q':weight,'V':weight/(4*sp.pi*EPS0*distance),'E':weight*delta/(4*sp.pi*EPS0*distance**3)}
        units={'Q':'C','V':'V','E':'V/m'}
        method='Coulomb-integral langs parameteriseret linje';equations=[r'dq=\lambda(u)|d\mathbf r^\prime/du|du',r'V=\frac{1}{4\pi\epsilon_0}\int\frac{dq}{|\mathbf r-\mathbf r^\prime|}',r'\mathbf E=\frac{1}{4\pi\epsilon_0}\int\frac{(\mathbf r-\mathbf r^\prime)dq}{|\mathbf r-\mathbf r^\prime|^3}']
    else:
        current,=p.require('I');p.assume('magnetostatic')
        if u in current.free_symbols:raise InputError('Stationær tynd ledning kræver samme strøm langs kurven.')
        integrands={'B':MU0*current*tangent.cross(delta)/(4*sp.pi*distance**3)};units={'B':'T'}
        method='Biot–Savart langs parameteriseret linje';equations=[r'd\mathbf l^\prime=\frac{d\mathbf r^\prime}{du}du',r'\mathbf B=\frac{\mu_0 I}{4\pi}\int\frac{d\mathbf l^\prime\times(\mathbf r-\mathbf r^\prime)}{|\mathbf r-\mathbf r^\prime|^3}']
    result=solution(p,method,'Kildens tangent bestemmer linjeelementet. Ingen Gauss- eller Ampère-symmetri er forudsat.',equations,'Kartesisk basis. Strømretningen følger voksende parameter; ladningsfortegn følger tætheden.')
    result.add('Differentier kildekurven',tangent);result.add('Linjeelementets længdefaktor',jac)
    for key,integrand in integrands.items():
        def integrate(v):
            v=sp.trigsimp(v);formal=sp.Integral(v,(u,*bounds));result.add('Opsæt '+key,formal)
            if not evaluate:return formal
            value,timed=bounded_integral(v,[(u,*bounds)],budget,return_status=True)
            if timed:result.warnings.append('TIMEOUT: analytisk integration af '+key+' nåede tidsbudgettet; det korrekte integral bevares.')
            return value
        result.symbolic_result[key]=integrand.applyfunc(integrate) if isinstance(integrand,sp.MatrixBase) else integrate(integrand)
    result.units=units
    check_solution(result,p.symbol_units)
    if any(v.has(sp.Integral) for v in result.symbolic_result.values()):result.warnings.append('Integraler bevares. Lukket form er ikke fundet eller ikke forsøgt inden tidsbudgettet. Numerisk evaluering kræver alle værdier og et feltpunkt uden for kilden.')
    return result


def _numeric_worker(output,values,substitutions):
    from .task_runtime import block_network
    block_network()
    try:
        results={}
        for key,value in values.items():
            v=value.subs(substitutions)
            if v.free_symbols:continue
            low=v.evalf(20);high=v.evalf(35)
            entries=list(high) if isinstance(high,sp.MatrixBase) else [high]
            if any(x.has(sp.Integral,sp.nan,sp.zoo,sp.oo,-sp.oo) or x.is_real is not True for x in entries):continue
            residual=high-low
            residuals=list(residual) if isinstance(residual,sp.MatrixBase) else [residual]
            if all(abs(float(x))<=1e-12*max(1.,abs(float(y))) for x,y in zip(residuals,entries)):results[key]=high
        output.put(('ok',results))
    except Exception as exc:output.put(('error',str(exc)))


def numerical_curve(answer,substitutions,timeout=5):
    """Bounded quadrature, only after explicit nonsingularity confirmation."""
    from .units import CONSTANTS
    repl=dict(substitutions)
    for value in answer.symbolic_result.values():
        repl.update({x:sp.Float(CONSTANTS[x.name]) for x in value.free_symbols if x.name in CONSTANTS})
    context=mp.get_context('spawn');output=context.Queue();process=context.Process(target=_numeric_worker,args=(output,answer.symbolic_result,repl));process.start()
    try:
        try:kind,value=output.get(timeout=timeout)
        except queue.Empty:raise InputError('Numerisk integration nåede tidsgrænsen. Integralopsætningen bevares.')
        if kind!='ok':raise InputError('Numerisk integration fejlede: '+value)
        if not value:raise InputError('Numerisk resultat kan ikke bestemmes: manglende værdier, singularitet eller utilstrækkelig konvergens.')
        return value
    finally:
        if process.is_alive():process.terminate()
        process.join(timeout=1);output.close()
