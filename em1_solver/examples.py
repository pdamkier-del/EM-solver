"""Structured input examples; strings are interpreted only by the arithmetic AST parser."""
import copy
import sympy as sp
from .core.problem import Problem,Region,InputError
from .core.parsing import expression

SYMBOLS={name:sp.Symbol(name,positive=True) for name in
    'a b d R L q Q I J rho sigma alpha epsilon_r epsilon_0 mu_0 m v V B omega tau N A k C Q0'.split()}
SYMBOLS.update({name:sp.Symbol(name,real=True) for name in 'x y z t u w theta phi'.split()})
SYMBOLS['s']=sp.Symbol('s',positive=True)
SYMBOLS['r']=sp.Symbol('r',positive=True)

def spec(domain, variables, assumptions=(),regions=()):
    return {'domain':domain,'variables':variables,'assumptions':list(assumptions),'regions':list(regions)}

EXAMPLES={
 'units':spec('EV',{'field_unit':'V/m','coordinate_power':2}),
 'point_charges':spec('EV',{'charges':[['q',['-a','0','0']],['-q',['a','0','0']]],'point':['0','0','b']}),
 'coulomb_integral':spec('EV',{'kind':'line','source':['a*cos(u)','a*sin(u)','0'],'parameters':['u'],'bounds':[['pi/2','3*pi/2']],'density':'Q/(pi*a)','point':['0','0','0']}),
 'gauss_radial':spec('EV',{'coordinate':'s','symmetry':'cylinder'},['infinite_cylindrical_symmetry'],[{'lower':'0','upper':'R','density':'alpha*s^2','permittivity':'epsilon_0'}]),
 'field_calculus':spec('EV',{'coordinates':['x','y','z'],'system':'cartesian','V':'alpha*x*y'},['electrostatic']),
 'potential_from_field':spec('EV',{'coordinate':'x','field':'a+b*x','start':'0','end':'L'}),
 'conductors':spec('EV',{'coordinate':'r','shells':[['0','a','Q'],['a+b','a+b+d','q']]},['concentric_spheres','electrostatic']),
 'capacitance':spec('EV',{'kind':'sphere','epsilon':'epsilon_0*epsilon_r','inner_radius':'a','outer_radius':'a+b','Q':'Q'}),
 'polarization':spec('EV',{'coordinates':['x','y','z'],'system':'cartesian','P':['alpha*x','alpha*y','alpha*z'],'normal':['1','0','0']}),
 'images':spec('EV',{'charges':[['q',['a','b','0']]],'point':['a','b','0'],'planes':[1],'self_index':0,'test_charge':'q'},['grounded_infinite_planes']),
 'laplace_legendre':spec('EV',{'r':'r','theta':'theta','radius':'R','coefficients':[[2,'2*V']]},['axial_symmetry','charge_free_inside_outside','V_infinity_zero','finite_at_origin']),
 'ampere':spec('BA',{'kind':'cylinder','coordinate':'s'},['infinite_cylindrical_symmetry','magnetostatic'],[{'lower':'0','upper':'R','density':'J*(1-s/R)'}]),
 'magnetic_superposition':spec('BA',{'point':['0','0','0'],'sources':[{'kind':'cylinder','center':['-a','0','0'],'radius':'a+b','J':'J'},{'kind':'cylinder','center':['a','0','0'],'radius':'a+b','J':'-J'}]},['parallel_infinite_sources','magnetostatic']),
 'biot_savart':spec('BA',{'source':['R*cos(u)','R*sin(u)','0'],'parameter':'u','bounds':['0','2*pi'],'I':'I','point':['0','0','a']}),
 'lorentz_force':spec('BA',{'kind':'force','q':'q','v':['v','0','0'],'B':['0','0','B'],'E':['0','0','0']}),
 'wire_force':spec('BA',{'source':['u','0','0'],'parameter':'u','bounds':['0','L'],'I':'I','B':['0','0','B']}),
 'magnetic_material':spec('BA',{'kind':'magnetization','coordinates':['s','phi','z'],'system':'cylindrical','M':['0','0','k*s^2'],'H':['0','0','0'],'normal':['1','0','0']}),
 'multipole':spec('EV',{'charges':[['q',['-a','0','0']],['-q',['a','0','0']]],'r':'r','theta':'theta','phi':'phi'}),
 'faraday':spec('DYN',{'time':'t','B_normal':'B*sin(omega*t)','area':'pi*a^2','R':'R','time_bounds':['0','2*pi/omega']},['uniform_normal_B','negligible_self_inductance']),
 'motional_emf':spec('DYN',{'source':['0','u','0'],'parameter':'u','bounds':['0','L'],'v':['v','0','0'],'B':['0','0','B'],'time':'t','R':'R'},['negligible_self_inductance','stationary_return_path']),
 'circuit_power':spec('DYN',{'I':'I*exp(-t/tau)','R':'R','time':'t','time_bounds':['0','tau']}),
 'feedback':spec('DYN',{'mass':'m','R':'R','coupling':'B*d','voltage':'V','drive_force':'0','time':'t','initial_velocity':'0'},['constant_coefficients','negligible_self_inductance','no_friction']),
 'resistance':spec('DYN',{'coordinate':'x','bounds':['0','d'],'area':'A','conductivity':'1/(b*x)','voltage':'V'},['one_dimensional_steady_current']),
 'inductance_energy':spec('DYN',{'flux':'mu_0*I*pi*R^2*N/L','I':'I','N':'N'}),
 'ampere_maxwell':spec('DYN',{'E':'V*cos(omega*t)/d','time':'t','coordinate':'s','plate_radius':'R'},['uniform_axial_E','circular_symmetry','negligible_edge_effects']),
 'rc_transient':spec('DYN',{'kind':'RC','time':'t','R':'R','C':'C','Q0':'Q0','fraction':'1/100'}),
}

# Fields representing labels rather than arithmetic expressions.
LABELS={'kind','symmetry','system','field_unit'}
INTEGER_FIELDS={'self_index','coordinate_power','series_order','force_on_index'}

def decode(value,key=''):
    if isinstance(value,str):
        return value if key in LABELS else expression(value,SYMBOLS)
    if isinstance(value,bool):return value
    if isinstance(value,(int,float)):
        return value if key in INTEGER_FIELDS else sp.Rational(str(value))
    if isinstance(value,list):return [decode(v,key) for v in value]
    if isinstance(value,dict):return {k:decode(v,k) for k,v in value.items()}
    raise InputError('Input skal bestå af tal, udtryk, lister eller objekter.')

def problem_from_spec(family,data,numerical_values=None,numerical_units=None):
    vars=decode(data['variables'])
    # Integer indices and degree fields must remain Python integers.
    if 'planes' in vars:
        if not all(sp.sympify(v).is_integer for v in vars['planes']):raise InputError('Planindekser skal være heltal.')
        vars['planes']=[int(v) for v in vars['planes']]
    if 'coefficients' in vars:
        if not all(sp.sympify(n).is_integer for n,_ in vars['coefficients']):raise InputError('Legendre-grader skal være heltal.')
        vars['coefficients']=[(int(n),c) for n,c in vars['coefficients']]
    regions=[Region(**decode(row)) for row in data.get('regions',[])]
    unknown=set(numerical_values or {})-set(SYMBOLS)
    if unknown:raise InputError('Ukendte numeriske symboler: '+', '.join(sorted(unknown)))
    substitutions={SYMBOLS[name]:value for name,value in (numerical_values or {}).items()}
    units={SYMBOLS[name]:value for name,value in (numerical_units or {}).items() if name in SYMBOLS}
    return Problem(data['domain'],family,geometry='manuelt specificeret',variables=vars,regions=regions,
                   assumptions=data.get('assumptions',[]),wanted=data.get('wanted',[]),numerical_values=substitutions,numerical_units=units)
