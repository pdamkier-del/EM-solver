import pytest
import sympy as s
from em1_solver import Problem,Region,solve,InputError
from em1_solver.core.validation import EPS0 as eps,MU0 as mu
from em1_solver.core.validation import regional_limit
from em1_solver.core.dimensions import check_solution
x,y,z,t=s.symbols('x y z t',real=True)
a,b,R,L,q,m,v,V,B,C,Q,F=s.symbols('a b R L q m v V B C Q F',positive=True)
BASE={a:'m',b:'m',R:'ohm',L:'m',q:'C',m:'kg',v:'m/s',V:'V',B:'T',C:'F',Q:'C',F:'N',t:'s',x:'m',y:'m',z:'m'}
def eq(a,b):
 r=s.simplify(s.expand(a-b));assert all(v.equals(0) for v in r) if isinstance(r,s.MatrixBase) else r.equals(0)
def dimensions(out):
 checks=[c for c in out.checks if c.name.startswith('Dimension:')]
 assert checks and all(c.passed is True for c in checks),checks

@pytest.mark.variation(family='lorentz_force')
@pytest.mark.parametrize('sign,velocity,field,expected',[(1,[v,0,0],[0,0,B],[0,-q*v*B,0]),(-1,[v,0,0],[0,0,B],[0,q*v*B,0]),(1,[0,v,0],[0,0,B],[q*v*B,0,0]),(1,[0,0,v],[0,0,B],[0,0,0])])
def test_lorentz_directions_and_charge(sign,velocity,field,expected):
 out=solve(Problem('BA','lorentz_force',variables={'q':sign*q,'v':velocity,'B':field,'E':[0,0,0]},symbol_units=BASE))
 eq(out.symbolic_result['F'],s.Matrix(expected));eq(out.symbolic_result['magnetic_power'],0);dimensions(out)

@pytest.mark.variation(family='lorentz_force')
@pytest.mark.parametrize('bad', ['mass','q','B_magnitude'])
def test_orbit_invalid_zero_rejected(bad):
 data={'kind':'orbit','mass':m,'q':q,'B_magnitude':B,'voltage':V};data[bad]=0
 with pytest.raises(InputError):solve(Problem('BA','lorentz_force',variables=data,assumptions=['nonrelativistic','velocity_perpendicular_B']))

@pytest.mark.variation(family='laplace_legendre')
@pytest.mark.parametrize('degree',[0,1,2,3,4])
def test_legendre_modes_and_limits(degree):
 r=s.Symbol('r',positive=True);theta=s.Symbol('theta',real=True)
 out=solve(Problem('EV','laplace_legendre',variables={'r':r,'theta':theta,'radius':a,'coefficients':[(degree,V)]},
 assumptions=['axial_symmetry','charge_free_inside_outside','V_infinity_zero','finite_at_origin'],symbol_units=BASE|{r:'m',theta:'1'}))
 eq(out.symbolic_result['V_inside'].subs(r,a),V*s.legendre(degree,s.cos(theta)))
 eq(s.limit(out.symbolic_result['V_outside'],r,s.oo),0)
 assert all(c.passed for c in out.checks);dimensions(out)

@pytest.mark.variation(family='laplace_legendre')
def test_legendre_missing_boundary_rejected():
 with pytest.raises(InputError):solve(Problem('EV','laplace_legendre',variables={'r':a,'theta':t,'radius':b,'coefficients':[(2,V)]}))

@pytest.mark.variation(family='feedback')
@pytest.mark.parametrize('sign,drive,voltage',[(1,0,V),(-1,0,V),(1,F,0),(-1,F,0),(1,F,V),(1,F,-V)])
def test_feedback_drive_signs_limits_and_energy(sign,drive,voltage):
 out=solve(Problem('DYN','feedback',variables={'mass':m,'R':R,'coupling':sign*B*a,'voltage':voltage,'drive_force':drive,'time':t,'initial_velocity':0},
 assumptions=['constant_coefficients','negligible_self_inductance','no_friction'],symbol_units=BASE))
 assert all(c.passed for c in out.checks);dimensions(out)
 eq(out.symbolic_result['v'].subs(t,0),0)
 eq(s.limit(out.symbolic_result['v'],t,s.oo),out.symbolic_result['v_infinity'])
 eq(out.symbolic_result['v_infinity'],voltage/(sign*B*a)+drive*R/(B*a)**2)

@pytest.mark.variation(family='feedback')
@pytest.mark.parametrize('bad', ['mass','R','coupling'])
def test_feedback_nonphysical_coefficients_rejected(bad):
 data={'mass':m,'R':R,'coupling':B*a,'voltage':V,'drive_force':0,'time':t,'initial_velocity':0};data[bad]=0
 with pytest.raises(InputError):solve(Problem('DYN','feedback',variables=data,assumptions=['constant_coefficients','negligible_self_inductance','no_friction']))

@pytest.mark.variation(family='capacitance')
@pytest.mark.parametrize('kind',['sphere','cylinder','parallel_plates'])
@pytest.mark.parametrize('factor',[1,3,10])
def test_capacitance_geometry_scaling_and_energy(kind,factor):
 data={'kind':kind,'epsilon':factor*eps,'Q':q}
 if kind=='parallel_plates':data|={'area':a*a,'distance':b}
 else:data|={'inner_radius':a,'outer_radius':a+b,'length':L}
 out=solve(Problem('EV','capacitance',variables=data,assumptions=['negligible_edge_effects','infinite_cylindrical_symmetry'],symbol_units=BASE))
 expected={'sphere':4*s.pi*factor*eps*a*(a+b)/b,'cylinder':2*s.pi*factor*eps*L/s.log((a+b)/a),'parallel_plates':factor*eps*a*a/b}[kind]
 eq(out.symbolic_result['C'],expected);eq(out.symbolic_result['U'],q*q/(2*expected));dimensions(out)

@pytest.mark.variation(family='capacitance')
def test_capacitance_invalid_geometry_and_assumptions():
 with pytest.raises(InputError):solve(Problem('EV','capacitance',variables={'kind':'sphere','epsilon':eps,'inner_radius':a,'outer_radius':a/2}))
 with pytest.raises(InputError):solve(Problem('EV','capacitance',variables={'kind':'parallel_plates','epsilon':eps,'area':a*a,'distance':b}))

@pytest.mark.variation(family='rc_transient')
@pytest.mark.parametrize('sign,rf,cf',[(1,1,1),(-1,2,3),(1,4,2)])
def test_RC_variations(sign,rf,cf):
 out=solve(Problem('DYN','rc_transient',variables={'kind':'RC','time':t,'R':rf*R,'C':cf*C,'Q0':sign*Q},symbol_units=BASE))
 eq(out.symbolic_result['I'],sign*Q/(rf*cf*R*C)*s.exp(-t/(rf*cf*R*C)))
 eq(s.limit(out.symbolic_result['Q'],t,s.oo),0);dimensions(out)

@pytest.mark.variation(family='rc_transient')
@pytest.mark.parametrize('sign',[-1,1])
def test_RL_variations_and_limits(sign):
 inductance=s.Symbol('L_ind',positive=True)
 out=solve(Problem('DYN','rc_transient',variables={'kind':'RL','time':t,'R':R,'L':inductance,'voltage':sign*V,'I0':0},symbol_units=BASE|{inductance:'H'}))
 eq(s.limit(out.symbolic_result['I'],t,s.oo),sign*V/R);dimensions(out)

@pytest.mark.variation(family='rc_transient')
def test_RL_unreachable_target_rejected():
 with pytest.raises(InputError):solve(Problem('DYN','rc_transient',variables={'kind':'RL','time':t,'R':2,'L':1,'voltage':4,'I0':0,'target_values':{'I':3},'solve_for':t}))
 with pytest.raises(InputError):solve(Problem('DYN','rc_transient',variables={'kind':'RL','time':t,'R':2,'L':1,'voltage':s.sin(t),'I0':0}))

@pytest.mark.variation(family='gauss_radial')
@pytest.mark.parametrize('power',[0,1,2,3])
def test_gauss_density_variations(power):
 r=s.Symbol('r',positive=True);density=s.Symbol('density_coefficient',positive=True)
 out=solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'cylinder'},regions=[Region(0,a,density*r**power)],assumptions=['infinite_cylindrical_symmetry'],symbol_units={r:'m',a:'m',density:f'C/m^{3+power}'}))
 eq(out.symbolic_result['E'].subs(r,a/2),density*(a/2)**(power+1)/(eps*(power+2)))
 eq(out.symbolic_result['E'].subs(r,2*a),density*a**(power+1)/(2*eps*(power+2)));dimensions(out)

@pytest.mark.variation(family='ampere')
@pytest.mark.parametrize('power',[0,1,2,3])
def test_ampere_current_variations(power):
 r=s.Symbol('r',positive=True);coef=s.Symbol('J_coefficient',positive=True)
 out=solve(Problem('BA','ampere',variables={'kind':'cylinder','coordinate':r},regions=[Region(0,a,coef*r**power)],assumptions=['infinite_cylindrical_symmetry','magnetostatic'],symbol_units={r:'m',a:'m',coef:f'A/m^{2+power}'}))
 eq(out.symbolic_result['B'].subs(r,a/2),mu*coef*(a/2)**(power+1)/(power+2));dimensions(out)

@pytest.mark.variation(family='faraday')
@pytest.mark.parametrize('field,area,expected',[('B*t/tau','a^2','-B*a^2/tau'),('B','a^2*t/tau','-B*a^2/tau'),('B*t/tau','a^2*t/tau','-2*B*a^2*t/tau^2'),('-B*t/tau','a^2','B*a^2/tau')])
def test_Faraday_field_and_area_variations(field,area,expected):
 from em1_solver.core.parsing import expression
 tau=s.Symbol('tau',positive=True);symbols={'B':B,'t':t,'tau':tau,'a':a}
 out=solve(Problem('DYN','faraday',variables={'time':t,'B_normal':expression(field,symbols),'area':expression(area,symbols),'N':3},assumptions=['uniform_normal_B'],symbol_units=BASE|{tau:'s'}))
 eq(out.symbolic_result['EMF'],3*expression(expected,symbols));dimensions(out)

@pytest.mark.variation(family='field_calculus')
@pytest.mark.parametrize('power',[1,2,3])
def test_potential_field_round_trip(power):
 coeff=s.Symbol('coefficient',positive=True)
 out=solve(Problem('EV','field_calculus',variables={'coordinates':[x,y,z],'system':'cartesian','V':coeff*x**power}))
 back=solve(Problem('EV','potential_from_field',variables={'coordinate':x,'field':out.symbolic_result['E'][0],'start':0,'end':a}))
 eq(back.symbolic_result['delta_V'],coeff*a**power)

@pytest.mark.variation(family='gauss_radial')
@pytest.mark.parametrize('power',[0,1,3])
def test_hollow_gauss_variations(power):
 r=s.Symbol('r',positive=True);coef=s.Symbol('coef',positive=True)
 out=solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'cylinder'},regions=[Region(a,2*a,coef*r**power)],
 assumptions=['infinite_cylindrical_symmetry'],symbol_units={a:'m',r:'m',coef:f'C/m^{3+power}'}))
 eq(out.symbolic_result['E'].subs(r,a/2),0)
 eq(out.symbolic_result['E'].subs(r,3*a),coef*((2*a)**(power+2)-a**(power+2))/(3*a*eps*(power+2)))
 dimensions(out)

@pytest.mark.variation(family='ampere')
def test_ampere_hollow_multiple_regions_and_return_current():
 r=s.Symbol('r',positive=True);j=s.Symbol('J',positive=True)
 out=solve(Problem('BA','ampere',variables={'kind':'cylinder','coordinate':r},regions=[Region(a,2*a,j),Region(3*a,4*a,-2*j)],
 assumptions=['infinite_cylindrical_symmetry','magnetostatic'],symbol_units={a:'m',r:'m',j:'A/m^2'}))
 eq(out.symbolic_result['I_enc'].subs(r,a/2),0)
 eq(out.symbolic_result['I_enc'].subs(r,5*a),-11*s.pi*j*a*a)
 eq(out.symbolic_result['B'].subs(r,5*a),-11*mu*j*a/10);dimensions(out)

@pytest.mark.variation(family='faraday')
def test_faraday_rejects_unjustified_circuit_and_negative_turns():
 with pytest.raises(InputError):solve(Problem('DYN','faraday',variables={'time':t,'flux':V*t,'R':R}))
 with pytest.raises(InputError):solve(Problem('DYN','faraday',variables={'time':t,'flux':V*t,'N':-1}))

@pytest.mark.variation(family='laplace_legendre')
def test_legendre_independent_numerical_reference():
 r=s.Symbol('r',positive=True);theta=s.Symbol('theta',real=True)
 out=solve(Problem('EV','laplace_legendre',variables={'r':r,'theta':theta,'radius':a,'coefficients':[(2,V)]},
 assumptions=['axial_symmetry','charge_free_inside_outside','V_infinity_zero','finite_at_origin'],
 numerical_values={r:2,a:1,V:2,theta:s.pi/2},symbol_units=BASE|{r:'m',theta:'1'}))
 assert abs(float(out.numerical_result['E_outside'][0])+3/16)<1e-12
 assert abs(float(out.numerical_result['E_outside'][1]))<1e-12

@pytest.mark.variation(family='ampere_maxwell')
@pytest.mark.parametrize('wave',['V*sin(omega*t)','V*cos(omega*t)','V*exp(-t/tau)','V'])
def test_Maxwell_waves_and_radial_limits(wave):
 from em1_solver.core.parsing import expression
 r,omega,tau=s.symbols('s omega tau',positive=True);symbolmap={'V':V,'t':t,'omega':omega,'tau':tau}
 field=expression(wave,symbolmap)
 out=solve(Problem('DYN','ampere_maxwell',variables={'E':field,'time':t,'coordinate':r,'plate_radius':a},
 assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects'],symbol_units=BASE|{V:'V/m',r:'m',omega:'1/s',tau:'s'}))
 eq(out.symbolic_result['B'].subs(r,a/2),mu*s.Symbol('epsilon_0',positive=True)*a*s.diff(field,t)/4)
 eq(out.symbolic_result['B'].subs(r,2*a),mu*eps*a*s.diff(field,t)/4)
 eq(regional_limit(out.symbolic_result['B'],r,0,direction='+'),0);dimensions(out)

@pytest.mark.variation(family='ampere_maxwell')
def test_Maxwell_does_not_invent_boundary_or_symmetry():
 r=s.Symbol('s',positive=True)
 with pytest.raises(InputError):solve(Problem('DYN','ampere_maxwell',variables={'E':V,'time':t,'coordinate':r,'plate_radius':a}))
 out=solve(Problem('DYN','ampere_maxwell',variables={'E':V,'time':t,'coordinate':r,'plate_radius':a},assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects']))
 assert 'E_correction_inside' not in out.symbolic_result
 with pytest.raises(InputError):solve(Problem('DYN','ampere_maxwell',variables={'E':V,'time':t,'coordinate':r,'plate_radius':0},assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects']))
