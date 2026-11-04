from .problem import InputError
from .units import numerical


def solvers():
    from ..solvers import electrostatics as ev, magnetostatics as ba, electrodynamics as dyn
    from ..solvers.dimensions import units
    from ..solvers.algebra import algebra
    return {
        'point_charges':ev.point_charges,'coulomb_integral':ev.coulomb_integral,
        'gauss_radial':ev.gauss_radial,'field_calculus':ev.field_calculus,
        'potential_from_field':ev.potential_from_field,'conductors':ev.conductors,
        'capacitance':ev.capacitance,'polarization':ev.polarization,'images':ev.images,
        'laplace_legendre':ev.laplace_legendre,'ampere':ba.ampere,
        'magnetic_superposition':ba.magnetic_superposition,'biot_savart':ba.biot_savart,
        'lorentz_force':ba.lorentz_force,'wire_force':ba.wire_force,
        'magnetic_dipole_interaction':ba.magnetic_dipole_interaction,'magnetic_material':ba.magnetic_material,'multipole':ba.multipole,
        'faraday':dyn.faraday,'motional_emf':dyn.motional_emf,
        'circuit_power':dyn.circuit_power,'feedback':dyn.feedback,'resistance':dyn.resistance,
        'inductance_energy':dyn.inductance_energy,'ampere_maxwell':dyn.ampere_maxwell,
        'rc_transient':dyn.rc_transient,'units':units,'algebra':algebra,
    }


DOMAINS = {
    'EV': {'point_charges','coulomb_integral','gauss_radial','field_calculus','potential_from_field','conductors','capacitance','polarization','images','laplace_legendre','multipole','units'},
    'BA': {'magnetic_dipole_interaction','ampere','magnetic_superposition','biot_savart','lorentz_force','wire_force','magnetic_material','multipole','field_calculus'},
    'DYN': {'faraday','motional_emf','circuit_power','feedback','resistance','inductance_energy','ampere_maxwell','rc_transient','field_calculus'},
}


def solve(problem):
    if problem.domain not in DOMAINS or (problem.family not in DOMAINS[problem.domain] and problem.family!='algebra'):
        raise InputError('Ukendt kombination af område og metodefamilie.')
    result = solvers()[problem.family](problem)
    if 'at' in problem.variables:
        import sympy as sp
        for key,value in list(result.symbolic_result.items()):
            if isinstance(value,(sp.Basic,sp.MatrixBase)):
                result.symbolic_result[key]=sp.simplify(value.subs(problem.variables['at'],simultaneous=True))
        result.add('Indsæt det eksplicit angivne evalueringspunkt',problem.variables['at'])
    if 'limits' in problem.variables:
        import sympy as sp
        for key,spec in problem.variables['limits'].items():
            if key not in result.symbolic_result:raise InputError('Ukendt resultat i grænsekontrol: '+key)
            coordinate,point,*direction=spec
            direction=direction[0] if direction else '+'
            value=result.symbolic_result[key]
            from .validation import regional_limit
            evaluate=lambda v:regional_limit(v,coordinate,point,direction)
            limit=value.applyfunc(evaluate) if isinstance(value,sp.MatrixBase) else evaluate(value)
            result.symbolic_result['limit_'+key]=limit
            if key in result.units:result.units['limit_'+key]=result.units[key]
            result.add(f'Grænse af {key}, når {coordinate} går mod {point}',limit)
    if 'solve_for' in problem.variables:
        import sympy as sp
        unknowns=problem.variables['solve_for']
        if isinstance(unknowns,sp.Symbol):unknowns=[unknowns]
        if not isinstance(unknowns,list) or not all(isinstance(v,sp.Symbol) for v in unknowns):
            raise InputError('solve_for skal være et symbol eller en liste af symboler.')
        targets,=problem.require('target_values')
        residuals=[]
        for key,target in targets.items():
            if key not in result.symbolic_result:raise InputError('Ukendt resultat i ligningsbetingelse: '+key)
            residual=result.symbolic_result[key]-target
            residuals.extend(list(residual) if isinstance(residual,sp.MatrixBase) else [residual])
        result.add('Indsæt de eksplicit krævede resultatbetingelser; løs for de angivne ubekendte',sp.Tuple(*residuals))
        if all(sp.simplify(r)==0 for r in residuals):raise InputError('Ligningsbetingelserne er identiteter og bestemmer ikke de ubekendte.')
        branches=sp.solve(residuals,unknowns,dict=True)
        if len(branches)==1:
            for symbol,value in branches[0].items():
                key='solved_'+symbol.name
                result.symbolic_result[key]=value
                if symbol in problem.symbol_units:result.units[key]=problem.symbol_units[symbol]
            result.add('Den entydige løsning under symbolernes antagelser',branches[0])
            for key in problem.variables.get('substitute_results',[]):
                if key not in result.symbolic_result:raise InputError('Ukendt resultat til efterindsættelse: '+key)
                result.symbolic_result['at_solution_'+key]=sp.simplify(result.symbolic_result[key].subs(branches[0]))
                if key in result.units:result.units['at_solution_'+key]=result.units[key]
                result.add('Indsæt den fundne løsning i '+key,result.symbolic_result['at_solution_'+key])
        else:
            result.symbolic_result['solution_branches']=branches
            result.warnings.append(f'Ligningsbetingelserne gav {len(branches)} løsningsgrene. Ingen gren vælges automatisk.')
    # Stable is intentionally false until every assigned historical question is covered.
    if problem.numerical_values:
        numerical(result, problem.numerical_values, problem.numerical_units)
    dimensions_ok=False
    if problem.symbol_units:
        from .dimensions import check_solution,check_inputs
        dimensions_ok=check_solution(result,problem.symbol_units)
        dimensions_ok=check_inputs(problem,result) and dimensions_ok
    from .certification import certified
    result.stable=bool(dimensions_ok and certified(problem.family) and all(c.passed is True for c in result.checks))
    return result
