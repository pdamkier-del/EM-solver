import sympy as s
import pytest
from em1_solver import Problem,solve
from em1_solver.core.validation import EPS0 as eps,MU0 as mu
from em1_solver.core.units import UNITS
from .test_fields import equal

x,y,z,t=s.symbols('x y z t',real=True)
a,b,h,L,R,q,I,N,V,rho,k,omega=s.symbols('a b h L R q I N V rho k omega',positive=True)

@pytest.mark.historical(ids=['2021-06:5b'],complete=True)
def test_2021_coefficient_dimensions():
    out=solve(Problem('EV','units',variables={'field_unit':'V/m','coordinate_power':2}))
    assert UNITS.Unit(out.symbolic_result['coefficient_unit'])==UNITS.volt/UNITS.meter**3

@pytest.mark.historical(ids=['2021-06:3b'],complete=True)
def test_2021_parallel_force():
    out=solve(Problem('BA','wire_force',variables={'kind':'parallel','I1':I/4,'I2':I,'distance':a,'length':L},assumptions=['parallel_infinite_wires']))
    equal(out.symbolic_result['F_signed_attraction']/L,mu*I*I/(8*s.pi*a))
    assert out.symbolic_result['F_signed_attraction'].is_positive

@pytest.mark.historical(ids=['2021-11:5a'],complete=True)
def test_2021_rotating_cylinder():
    radial=s.Symbol('s',positive=True)
    out=solve(Problem('BA','ampere',variables={'kind':'azimuthal_cylinder','coordinate':radial,'radius':R,'J_phi':rho*omega*radial},
        assumptions=['infinite_cylindrical_symmetry','magnetostatic','B_infinity_zero']))
    equal(out.symbolic_result['B'].subs(radial,R/2),mu*rho*omega*(R*R-R*R/4)/2)
    equal(out.symbolic_result['B'].subs(radial,2*R),0)

@pytest.mark.historical(ids=['2022-11:1a','2022-11:1b','2022-11:1c'],complete=True)
def test_2022_zeros_and_work():
    data=[(-6*s.Rational(1,10**6),[0,0,0]),(3*s.Rational(1,10**6),[s.Rational(12,100),0,0])]
    potential=solve(Problem('EV','point_charges',variables={'charges':data,'point':[x,0,0],'solve_for':x,'target_values':{'V':0}}))
    assert potential.symbolic_result['solution_branches']==[{x:s.Rational(2,25)},{x:s.Rational(6,25)}]
    electric=solve(Problem('EV','point_charges',variables={'charges':data,'point':[x,0,0],'solve_for':x,'target_values':{'E':s.zeros(3,1)}}))
    equal(electric.symbolic_result['solved_x'],s.Rational(6,25)+3*s.sqrt(2)/25)
    assert abs(float(electric.symbolic_result['solved_x'])-.410)<.001
    final=[data[0],(data[1][0],[s.Rational(24,100),0,0])]
    out=solve(Problem('EV','point_charges',variables={'charges':final,'initial_charges':data,'point':[0,0,1]}))
    assert abs(float(out.symbolic_result['W_external'].subs(eps,s.Float('8.8541878128e-12')))-.674)<.001

@pytest.mark.historical(ids=['2022-11:3a','2022-11:3b','2022-11:3c','2022-11:3d'],complete=True)
def test_2022_CMS_solenoid():
    n=2180;length=s.Rational(25,2);radius=3;current=18200
    field=solve(Problem('BA','ampere',variables={'kind':'solenoid','turn_density':n/length,'I':current},assumptions=['ideal_long_solenoid','magnetostatic']))
    induction=solve(Problem('DYN','inductance_energy',variables={'flux':field.symbolic_result['B']*s.pi*radius**2,'I':current,'N':n}))
    inductance=induction.symbolic_result['L']
    subs={mu:s.Float('1.25663706212e-6')}
    assert abs(float(field.symbolic_result['B'].subs(subs))-3.99)<.01
    assert abs(float(inductance.subs(subs))-13.5)<.1
    assert abs(float(induction.symbolic_result['U'].subs(subs))-2.24e9)<.01e9
    rc=solve(Problem('DYN','rc_transient',variables={'kind':'RL','time':t,'R':s.Rational(75,10**6),'L':inductance,'voltage':26,'I0':0,
        'solve_for':t,'target_values':{'I':current}}))
    assert abs(float(rc.symbolic_result['solved_t'].subs(subs))/3600-2.70)<.01
    assert abs(float(current*s.Rational(75,10**6))-1.37)<.01
    wire=solve(Problem('DYN','resistance',variables={'coordinate':x,'bounds':[0,2*s.pi*radius*n],
        'area':s.Rational(30,1000)*s.Rational(266,10000),'conductivity':1/s.Rational(265,10**10),'I':current},assumptions=['one_dimensional_steady_current']))
    assert abs(float(wire.symbolic_result['P'])-452e6)<2e6

@pytest.mark.historical(ids=['2023-02:3a'],complete=True)
def test_2023_quadrupole_far_field():
    d=s.Symbol('d',positive=True);coord=s.Symbol('z_positive',positive=True)
    out=solve(Problem('EV','point_charges',variables={'charges':[(q,[0,0,d]),(q,[0,0,-d]),(-2*q,[0,0,0])],
        'point':[0,0,coord],'far_coordinate':coord,'series_order':5}))
    equal(out.symbolic_result['E_far'],s.Matrix([0,0,6*q*d*d/(4*s.pi*eps*coord**4)]))
    assert out.symbolic_result['E_far'][2].is_positive

@pytest.mark.historical(ids=['2023-02:5a','2023-02:5d'],complete=True)
def test_2023_wire_loop_mutual_and_inverse_amplitude():
    flux=solve(Problem('DYN','faraday',variables={'time':t,'flux_integrand':mu*I*b/(2*s.pi*x),'bounds':[(x,a,a+h)]}))
    mutual=solve(Problem('DYN','inductance_energy',variables={'flux':flux.symbolic_result['Phi'],'I':I,'N':1,'mutual':True}))
    c=mutual.symbolic_result['M'];equal(c,mu*b/(2*s.pi)*s.log((a+h)/a))
    c_positive=s.Symbol('C_geometric',positive=True)
    power=s.Symbol('P_avg',positive=True)
    inverse=solve(Problem('DYN','faraday',variables={'time':t,'flux':c_positive*I*s.cos(omega*t),'R':R,'average_bounds':[0,2*s.pi/omega],
        'solve_for':I,'target_values':{'P_average':power}},assumptions=['negligible_self_inductance']))
    equal(inverse.symbolic_result['solved_I'],s.sqrt(2*R*power)/(c_positive*omega))
    sub={b:s.Rational(14,100),h:s.Rational(1,10),a:s.Rational(5,100),R:s.Rational(1,100),omega:100*s.pi,power:s.Rational(19,10**6),mu:s.Float('1.25663706212e-6')}
    assert abs(float(inverse.symbolic_result['solved_I'].subs(c_positive,c).subs(sub))-64)<1

@pytest.mark.historical(ids=['2023-11:2a','2023-11:2b'],complete=True)
def test_2023_parallel_transmission_sheets():
    sheet=solve(Problem('BA','ampere',variables={'kind':'sheet','K':[-I/b,0,0],'normal':[0,1,0]},assumptions=['infinite_current_sheet','magnetostatic']))
    bfield=2*sheet.symbolic_result['B_positive'];equal(bfield,s.Matrix([0,0,-mu*I/b]))
    energy=solve(Problem('DYN','inductance_energy',variables={'B_squared':bfield.dot(bfield),'mu':mu,'jacobian':b*L,'bounds':[(x,0,h)],'I':I}))
    equal(energy.symbolic_result['U'],mu*I*I*h*L/(2*b));equal(energy.symbolic_result['L'],mu*h*L/b)
    sub={I:9500,h:.012,L:4,b:.3,mu:s.Float('1.25663706212e-6')}
    assert abs(float(energy.symbolic_result['U'].subs(sub))-9.07)<.01
    assert abs(float(energy.symbolic_result['L'].subs(sub))-201e-9)<1e-9

@pytest.mark.historical(ids=['2024-11:1b'],complete=True)
def test_2024_corner_images():
    out=solve(Problem('EV','images',variables={'charges':[(q,[a,a,0])],'point':[a,a,0],'planes':[0,1],
        'self_index':0,'test_charge':q},assumptions=['grounded_infinite_planes']))
    equal(out.symbolic_result['F'],-q*q*(4-s.sqrt(2))/(4*s.pi*eps*16*a*a)*s.Matrix([1,1,0]))
    assert 'U' not in out.symbolic_result

@pytest.mark.historical(ids=['2026-01:2d'],complete=True)
def test_2026_RC_wire_force():
    c,q0,d=s.symbols('C Q0 d',positive=True)
    rc=solve(Problem('DYN','rc_transient',variables={'kind':'RC','time':t,'R':R,'C':c,'Q0':q0}))
    current=rc.symbolic_result['I']
    out=solve(Problem('BA','wire_force',variables={'kind':'parallel','I1':current,'I2':-current,'distance':d,'length':L},assumptions=['parallel_infinite_wires']))
    equal(out.symbolic_result['F_signed_attraction'],-mu*L/(2*s.pi*d)*(q0/(R*c))**2*s.exp(-2*t/(R*c)))
    assert out.symbolic_result['F_signed_attraction'].is_negative
