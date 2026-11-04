"""Symbolic SI dimensions, independent of printed unit labels and numerical values."""
import sympy as sp
from .units import UNITS
from .solution import Check

class DimensionError(ValueError): pass
class UnknownDimension(DimensionError): pass

ZERO=(sp.S.Zero,)*4
BASES=('[mass]','[length]','[time]','[current]')

def unit_dimension(unit):
    dimensionality=UNITS.Unit(unit).dimensionality
    if any(k not in BASES for k in dimensionality):raise DimensionError('Unsupported base dimension')
    return tuple(sp.Rational(str(dimensionality.get(k,0))) for k in BASES)

def dimension(expr, symbols):
    if isinstance(expr,sp.MatrixBase):
        values=[dimension(v,symbols) for v in expr if v!=0]
        values=[v for v in values if v is not None]
        if not values:return None
        if any(v!=values[0] for v in values):raise DimensionError('Vektorkomponenter har forskellige dimensioner')
        return values[0]
    expr=sp.sympify(expr)
    if expr.func==sp.log:
        # SymPy sometimes rewrites c*log(x) as log(x**c), even if c carries
        # physical units. Normalize for dimensions only; this does not select
        # a logarithmic branch or validate the physical domain of x.
        argument=expr.args[0]
        if isinstance(argument,sp.Pow) and dimension(argument.base,symbols) in (None,ZERO):
            return dimension(argument.exp,symbols)
    if expr==0:return None # Zero can be added to a dimensional quantity.
    if expr.is_Number or expr in (sp.pi,sp.E,sp.oo,-sp.oo):return ZERO
    if isinstance(expr,sp.Symbol):
        constants={'epsilon_0':'F/m','mu_0':'H/m'}
        unit=symbols.get(expr,symbols.get(expr.name,constants.get(expr.name)))
        if unit is None:raise UnknownDimension('Mangler dimension for '+expr.name)
        return unit_dimension(unit)
    if isinstance(expr,sp.Add):
        # SymPy splits log(V1/V2) into log(V1)-log(V2). A common unit
        # reference cancels only if coefficients cancel for each dimension.
        groups={};terms=[]
        for term in expr.args:
            logs=term.atoms(sp.log)
            if len(logs)==1:
                logarithm=next(iter(logs));coef=sp.cancel(term/logarithm)
                if not coef.has(sp.log):
                    base_dim=dimension(logarithm.args[0],symbols)
                    if base_dim not in (None,ZERO):
                        groups[base_dim]=groups.get(base_dim,0)+coef;terms.append(coef);continue
            terms.append(term)
        if any(sp.simplify(coef)!=0 for coef in groups.values()):raise DimensionError('Dimensionel logaritme uden annulleret enhedsreference')
        dims=[dimension(a,symbols) for a in terms];dims=[d for d in dims if d is not None]
        if any(d!=dims[0] for d in dims):raise DimensionError('Addition af uforenelige dimensioner')
        return dims[0] if dims else None
    if isinstance(expr,sp.Mul):
        dims=[dimension(a,symbols) for a in expr.args]
        return tuple(sum((d or ZERO)[i] for d in dims) for i in range(4))
    if isinstance(expr,sp.Pow):
        base,power=expr.args
        if dimension(power,symbols) not in (None,ZERO):raise DimensionError('Eksponent er ikke dimensionsløs')
        bd=dimension(base,symbols) or ZERO
        if not power.is_number and bd!=ZERO:raise UnknownDimension('Symbolsk eksponent på dimensionsbærende størrelse')
        return tuple(sp.simplify(v*power) for v in bd)
    if isinstance(expr,sp.Piecewise):
        dims=[dimension(value,symbols) for value,_ in expr.args if value!=0]
        if any(d!=dims[0] for d in dims):raise DimensionError('Regioner har uforenelige dimensioner')
        return dims[0] if dims else None
    if isinstance(expr,sp.Integral):
        dim=dimension(expr.function,symbols)
        if dim is None:return None
        for variable,*bounds in expr.limits:
            vd=dimension(variable,symbols) or ZERO
            for bound in bounds:
                if bound not in (0,sp.oo,-sp.oo) and dimension(bound,symbols)!=vd:raise DimensionError('Integrationsgrænse har forkert dimension')
            dim=tuple(a+b for a,b in zip(dim,vd))
        return dim
    if isinstance(expr,sp.Derivative):
        dim=dimension(expr.expr,symbols) or ZERO
        for variable,count in expr.variable_count:dim=tuple(a-count*b for a,b in zip(dim,dimension(variable,symbols) or ZERO))
        return dim
    if expr.func in (sp.Abs,sp.conjugate,sp.re,sp.im):return dimension(expr.args[0],symbols)
    if expr.func in (sp.Min,sp.Max):
        dims=[dimension(a,symbols) for a in expr.args if a!=0]
        dims=[d for d in dims if d is not None]
        if any(d!=dims[0] for d in dims):raise DimensionError('Min/Max sammenligner uforenelige dimensioner')
        return dims[0] if dims else None
    if expr.func==sp.sign:return ZERO
    if expr.func in (sp.sin,sp.cos,sp.tan,sp.exp,sp.log,sp.asin,sp.acos,sp.atan):
        if any(dimension(a,symbols) not in (None,ZERO) for a in expr.args):raise DimensionError('Funktionsargument skal være dimensionsløst')
        return ZERO
    raise UnknownDimension('Dimensionsregel mangler for '+str(expr.func))

def check_solution(answer, symbol_units):
    passed=True;count=0
    for key,value in answer.symbolic_result.items():
        unit=answer.units.get(key)
        if not unit or not isinstance(unit,str) or not isinstance(value,(sp.Basic,sp.MatrixBase)):
            continue
        try:
            actual=dimension(value,symbol_units);expected=unit_dimension(unit)
            ok=actual is None or actual==expected
            answer.checks.append(Check('Dimension: '+key,passed=ok,detail=unit))
            if not ok:answer.warnings.append('WARNING: dimensional inconsistency: '+key)
            passed &= ok;count+=1
        except UnknownDimension as exc:
            answer.checks.append(Check('Dimension: '+key,passed=None,detail=str(exc)));passed=False
        except (DimensionError,ValueError,TypeError) as exc:
            answer.checks.append(Check('Dimension: '+key,passed=False,detail=str(exc)))
            answer.warnings.append('WARNING: dimensional inconsistency: '+key);passed=False
    return passed and count>0

def check_inputs(problem,answer):
    """Validate physical input roles as well as output dimensions.

    This prevents two compensating input-unit mistakes from hiding in a
    dimensionally plausible final result.
    """
    roles={
      'magnetic_dipole_interaction':{'moment':'A*m^2','B':'T','moment_magnitude':'A*m^2','B_magnitude':'T','theta':'1'},
      'lorentz_force':{'q':'C','v':'m/s','E':'V/m','B':'T','mass':'kg','B_magnitude':'T','voltage':'V'},
      'feedback':{'mass':'kg','R':'ohm','coupling':'T*m','voltage':'V','drive_force':'N','time':'s','initial_velocity':'m/s'},
      'capacitance':{'epsilon':'F/m','inner_radius':'m','outer_radius':'m','length':'m','area':'m^2','distance':'m','Q':'C','V':'V','normal':'1'},
      'laplace_legendre':{'r':'m','theta':'1','radius':'m'},
      'rc_transient':{'time':'s','R':'ohm','C':'F','Q0':'C','L':'H','voltage':'V','I0':'A','fraction':'1'},
      'ampere_maxwell':{'E':'V/m','time':'s','coordinate':'m','plate_radius':'m'},
      'point_charges':{'point':'m','test_charge':'C','far_coordinate':'m'},
      'coulomb_integral':{'source':'m','point':'m','test_charge':'C'},
      'gauss_radial':{'coordinate':'m','length':'m'},
      'field_calculus':{'V':'V','E':'V/m','A':'T*m','B':'T'},
      'ampere':{'coordinate':'m','radius':'m','distance':'m','I':'A','turn_density':'1/m','J_phi':'A/m^2','K':'A/m','normal':'1','surface':'m','J_on_surface':'A/m^2'},
      'magnetic_superposition':{'point':'m'},
      'biot_savart':{'source':'m','point':'m','I':'A'},
      'wire_force':{'I':'A','I1':'A','I2':'A','B':'T','source':'m','distance':'m','length':'m','displacement_tangent':'1'},
      'magnetic_material':{'M':'A/m','H':'A/m','normal':'1','N':'1','I':'A'},
      'faraday':{'time':'s','flux':'Wb','B_normal':'T','area':'m^2','N':'1','R':'ohm','surface':'m','B_on_surface':'T'},
      'motional_emf':{'time':'s','source':'m','v':'m/s','B':'T','R':'ohm'},
      'circuit_power':{'time':'s','I':'A','R':'ohm'},
      'resistance':{'coordinate':'m','area':'m^2','conductivity':'S/m','voltage':'V','I':'A'},
      'polarization':{'P':'C/m^2','E':'V/m','epsilon':'F/m','normal':'1'},
      'images':{'point':'m','test_charge':'C'},
      'conductors':{'coordinate':'m','central_charge':'C','normal':'1','E_inside':'V/m','E_outside':'V/m','epsilon_inside':'F/m','epsilon_outside':'F/m','enclosed_charge':'C','metal_charge':'C','outer_radius':'m','charge':'C','radius':'m'},
      'multipole':{'r':'m','theta':'1','phi':'1','magnetic_current':'A','area':'m^2','normal':'1','transported_charge':'C','period':'s','position':'m','current_density':'A/m^2','magnetic_field_point':'m'},
      'inductance_energy':{'flux':'Wb','I':'A','N':'1','B_squared':'T^2','mu':'H/m'},
    }.get(problem.family,{})
    data=problem.variables|problem.functions;ok=True
    def validate(name,value,unit):
        nonlocal ok
        if isinstance(value,list):value=sp.Matrix(value)
        try:
            actual=dimension(value,problem.symbol_units)
            passed=actual is None or actual==unit_dimension(unit)
            answer.checks.append(Check('Inputdimension: '+name,passed=passed,detail=unit))
            if not passed:answer.warnings.append('WARNING: dimensional inconsistency: input '+name)
            ok &= passed
        except UnknownDimension as exc:
            answer.checks.append(Check('Inputdimension: '+name,passed=None,detail=str(exc)));ok=False
        except DimensionError as exc:
            answer.checks.append(Check('Inputdimension: '+name,passed=False,detail=str(exc)))
            answer.warnings.append('WARNING: dimensional inconsistency: input '+name);ok=False
    for name,unit in roles.items():
        if name in data:validate(name,data[name],unit)
    if problem.family in ('field_calculus','polarization','magnetic_material') and 'coordinates' in data:
        units={'cartesian':['m','m','m'],'cylindrical':['m','1','m'],'spherical':['m','1','1']}[data['system']]
        for i,(coordinate,unit) in enumerate(zip(data['coordinates'],units)):validate(f'coordinate_{i}',coordinate,unit)
    if problem.family in ('point_charges','images','multipole'):
        for group in ('charges','initial_charges'):
            for i,(q,pos) in enumerate(data.get(group,[])):
                validate(f'{group}_{i}_q',q,'C');validate(f'{group}_{i}_position',pos,'m')
    if problem.family in ('gauss_radial','ampere'):
        for i,reg in enumerate(problem.regions):
            validate(f'region_{i}_lower',reg.lower,'m')
            if reg.upper not in (sp.oo,-sp.oo):validate(f'region_{i}_upper',reg.upper,'m')
            validate(f'region_{i}_density',reg.density,'C/m^3' if problem.family=='gauss_radial' else 'A/m^2')
            if problem.family=='gauss_radial':validate(f'region_{i}_epsilon',reg.permittivity,'F/m')
        for radius,value in data.get('surface_charges',[]):validate('surface_radius',radius,'m');validate('sigma',value,'C/m^2')
        for radius,value in data.get('surface_currents',[]):validate('surface_radius',radius,'m');validate('K',value,'A/m')
    if problem.family=='coulomb_integral':validate('density',data['density'],{'line':'C/m','surface':'C/m^2','volume':'C/m^3'}[data.get('kind','line')])
    if problem.family=='conductors':
        for i,(inner,outer,q) in enumerate(data.get('shells',[])):
            validate(f'shell_{i}_inner',inner,'m');validate(f'shell_{i}_outer',outer,'m');validate(f'shell_{i}_charge',q,'C')
        for epsilon in data.get('gap_permittivities',[]):validate('gap_epsilon',epsilon,'F/m')
        for angle,epsilon in data.get('sectors',[]):validate('solid_angle',angle,'1');validate('sector_epsilon',epsilon,'F/m')
    if problem.family=='magnetic_material':
        for length,mu in data.get('segments',[]):validate('segment_length',length,'m');validate('segment_mu',mu,'H/m')
    if problem.family=='wire_force':
        for path in data.get('paths',[]):validate('wire_path',path['source'],'m')
    if problem.family=='magnetic_superposition':
        measure=UNITS.Unit('1')
        for coordinate,*_ in data.get('distribution_bounds',[]):
            unit=problem.symbol_units.get(coordinate,problem.symbol_units.get(coordinate.name))
            if unit is None:ok=False;continue
            measure*=UNITS.Unit(unit)
        for source in data['sources']:
            validate('source_center',source['center'],'m')
            if 'radius' in source:validate('source_radius',source['radius'],'m')
            if 'I' in source:validate('source_I',source['I'],str(UNITS.ampere/measure))
            if 'J' in source:validate('source_J',source['J'],str(UNITS.ampere/UNITS.meter**2/measure))
    return ok
