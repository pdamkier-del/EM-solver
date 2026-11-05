"""Small typed extensions over existing solvers, executed inside the bounded worker.

No text, task IDs, historical recipes or gold values are read here.
"""
import copy
import sympy as sp
from .new_problem import execute,build,symbols_for
from .problem import Problem,InputError
from .registry import solve
from .dimensions import check_solution
from .units import numerical
from .validation import EPS0,regional_limit


def _physical_logs(expr):
    def fix(log):
        argument=log.args[0]
        powers=[v for v in sp.Mul.make_args(argument) if v.is_Pow]
        if powers and all(v.base.is_positive is True and v.exp.is_real is True for v in powers):
            combined=sp.powsimp(argument,combine='base',force=True)
            if combined.is_Pow and combined.base.is_positive is True and combined.exp.is_real is True:return combined.exp*sp.log(combined.base)
        return log
    return expr.replace(lambda v:v.func==sp.log,fix)

def _branch(expr,coordinate,midpoint):
    folded=sp.piecewise_fold(expr)
    if not isinstance(folded,sp.Piecewise):return folded
    for value,condition in folded.args:
        at=sp.simplify(condition.subs(coordinate,midpoint))
        if at is sp.true:return value
        if at is not sp.false:raise InputError('Regionordningen er ikke bevist for potentialintegralet.')
    raise InputError('Ingen feltregion ved kontrolpunktet.')


def execute_plan(parsed,evaluate=False):
    plan=parsed.data['composition'];base=copy.deepcopy(parsed)
    targets=list(parsed.wanted);base.wanted=list(plan['seed_wanted'])
    problem=build(base);coordinate=problem.variables.get('coordinate')
    if targets==['Q'] and problem.family=='gauss_radial' and problem.variables['symmetry']=='sphere':
        from .solution import solution
        from .validation import positive,finite_integral
        answer=solution(problem,'Volumenintegral af ladning','Den givne volumenladning integreres over sit område. En materialelov er ikke nødvendig for den givne frie ladnings totale mængde.',[r'Q=\int\rho\,d\tau',r'd\tau=4\pi r^2dr'])
        terms=[];previous=sp.S.Zero
        for region in problem.regions:
            positive(region.upper-region.lower,'Regionsbredde')
            if region.lower.is_nonnegative is not True or sp.simplify(region.lower-previous).is_nonnegative is not True:raise InputError('Kilderegioner er ikke bevist ordnede og adskilte.')
            integrand=4*sp.pi*coordinate**2*region.density
            answer.add('Integrer den givne ladning i regionen',sp.Integral(integrand,(coordinate,region.lower,region.upper)))
            terms.append(finite_integral(integrand,(coordinate,region.lower,region.upper)));previous=region.upper
        answer.symbolic_result={'Q':sp.simplify(sum(terms))};answer.units={'Q':'C'};answer.wanted=targets
        check_solution(answer,problem.symbol_units)
        if problem.numerical_values:numerical(answer,problem.numerical_values,problem.numerical_units)
        return answer
    answer=execute(base,evaluate_integrals=evaluate)
    rules=[]
    if problem.family in ('gauss_radial','ampere'):
        radius=problem.regions[-1].upper
        if problem.family=='gauss_radial':
            symmetry=problem.variables['symmetry'];weight={'sphere':coordinate**2,'cylinder':coordinate,'plane':sp.S.One}[symmetry]
            for region in problem.regions:
                local=_branch(answer.symbolic_result['D'],coordinate,(region.lower+region.upper)/2)
                answer.check('Gauss differentiallov i åben region',sp.diff(weight*local,coordinate)/weight-region.density)
                if region.upper.is_finite is not False:
                    answer.check('Normal D-kontinuitet uden fri fladeladning',regional_limit(answer.symbolic_result['D'],coordinate,region.upper,'+')-regional_limit(answer.symbolic_result['D'],coordinate,region.upper,'-'))
        else:
            from .validation import MU0
            answer.check('Ampère cirkulationsidentitet',answer.symbolic_result['B']*2*sp.pi*coordinate-MU0*answer.symbolic_result['I_enc'])
            for region in problem.regions:
                local=_branch(answer.symbolic_result['B'],coordinate,(region.lower+region.upper)/2)
                answer.check('Ampère differentiallov i åben region',sp.diff(coordinate*local,coordinate)/coordinate-MU0*region.density)
        if problem.family=='gauss_radial':
            if problem.variables['symmetry']!='sphere' and set(targets)&{'Q','V'}:raise InputError('Total Q/V kræver en fuld integrations-/referencemodel for denne symmetri.')
            if 'Q' in targets:
                answer.symbolic_result['Q']=regional_limit(answer.symbolic_result['Q_enc'],coordinate,radius,'-');answer.units['Q']='C'
                answer.add('Total ladning: evaluér den omsluttede ladning ved kildens yderkant',answer.symbolic_result['Q']);rules.append('enclosed_charge_to_total')
            if 'V' in targets:
                if 'V_infinity_zero' not in base.assumptions:raise InputError('Potentialets reference V(infinity)=0 er ikke angivet.')
                total=regional_limit(answer.symbolic_result['Q_enc'],coordinate,radius,'-')
                outer=total/(4*sp.pi*EPS0*coordinate);edge=outer.subs(coordinate,radius);segments=[];lo=sp.S.Zero
                for region in problem.regions:
                    if sp.simplify(region.lower-lo)!=0:segments.append((lo,region.lower))
                    segments.append((region.lower,region.upper));lo=region.upper
                values=[]
                for lo,hi in reversed(segments):
                    field=_branch(answer.symbolic_result['E'],coordinate,(lo+hi)/2)
                    step=solve(Problem('EV','potential_from_field',variables=dict(field=field,coordinate=coordinate,start=hi,end=coordinate),wanted=['delta_V'],symbol_units=problem.symbol_units))
                    value=_physical_logs(sp.simplify(edge+step.symbolic_result['delta_V']));answer.steps.extend(step.steps)
                    answer.check('Potentialets gradient i åben region',sp.diff(value,coordinate)+field)
                    answer.check('Potentialkontinuitet ved '+str(hi),value.subs(coordinate,hi)-edge)
                    values.append((value,sp.And(coordinate>=lo,coordinate<=hi)));edge=sp.limit(value,coordinate,lo,dir='+') if lo==0 else value.subs(coordinate,lo)
                answer.symbolic_result['V']=sp.Piecewise(*reversed(values),(outer,True));answer.units['V']='V'
                answer.equations.append(r'V(r)=V(b)+\int_r^b E_r(u)\,du')
                answer.check('Potentialets fjernreference',sp.limit(outer,coordinate,sp.oo));rules.append('field_to_regional_potential')
        else:
            if 'I' in targets:
                value=answer.symbolic_result['I_enc']
                if plan.get('current_scope')=='total':value=regional_limit(value,coordinate,radius,'-')
                elif plan.get('current_scope')!='enclosed':raise InputError('Strømmens integrationsområde mangler.')
                answer.symbolic_result['I']=value;answer.units['I']='A';answer.add('Strømmen fås ved integration af den aksiale strømtæthed',value);rules.append('current_density_to_current')
    missing=set(targets)-set(answer.symbolic_result)
    if missing:raise InputError('Planen bestemmer ikke: '+', '.join(sorted(missing)))
    answer.stable=False # Component certificates do not certify a new composed plan.
    answer.wanted=targets;labels={'enclosed_charge_to_total':'samlet ladning','field_to_regional_potential':'stykvis potentialintegration','current_density_to_current':'integreret strøm'}
    answer.method+=' → '+', '.join(labels[r] for r in rules)
    check_solution(answer,problem.symbol_units)
    if problem.numerical_values:numerical(answer,problem.numerical_values,problem.numerical_units)
    return answer
