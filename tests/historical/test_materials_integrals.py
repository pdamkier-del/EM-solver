import sympy as s
import pytest
from em1_solver import Problem, Region, solve
from em1_solver.core.validation import EPS0 as eps,MU0 as mu
from .test_fields import equal

r,a,b,d,R,L,Q,q,k,J,V,N,I,rho=s.symbols('r a b d R L Q q k J V N I rho',positive=True)
u,v,x,z=s.symbols('u v x z',real=True)

@pytest.mark.historical(ids=['2025-01:2a','2025-01:2b','2025-01:2c'],complete=True)
def test_2025_concentric_conductors():
    out=solve(Problem('EV','conductors',variables={'coordinate':r,'shells':[(0,a,Q),(2*a,3*a,q)]},assumptions=['concentric_spheres','electrostatic']))
    expected=[(a,Q,Q/(4*s.pi*a*a)),(2*a,-Q,-Q/(16*s.pi*a*a)),(3*a,Q+q,(Q+q)/(36*s.pi*a*a))]
    assert out.symbolic_result['surfaces']==expected
    for position,field in [(a/2,0),(s.Rational(3,2)*a,Q/(9*s.pi*eps*a*a)),(s.Rational(5,2)*a,0),(4*a,(Q+q)/(64*s.pi*eps*a*a))]:
        equal(out.symbolic_result['E'].subs(r,position),field)
    equal(out.symbolic_result['U'],(Q*Q*(1/a-1/(2*a))+(Q+q)**2/(3*a))/(8*s.pi*eps))
    assert all(c.passed for c in out.checks)

@pytest.mark.historical(ids=['2021-11:2a'],complete=True)
def test_2021_two_hollow_shells():
    out=solve(Problem('EV','conductors',variables={'coordinate':r,'shells':[(a,2*a,Q),(3*a,4*a,q)]},assumptions=['concentric_spheres','electrostatic']))
    charges=[value for _,value,_ in out.symbolic_result['surfaces']]
    assert charges==[0,Q,-Q,Q+q]
    equal(out.symbolic_result['E'].subs(r,a/2),0)

@pytest.mark.historical(ids=['2021-11:2b','2021-11:2d'],complete=True)
def test_2021_spherical_capacitance():
    er=s.Symbol('epsilon_r',positive=True)
    for epsilon in [eps,eps*er]:
        out=solve(Problem('EV','capacitance',variables={'kind':'sphere','epsilon':epsilon,'inner_radius':a,'outer_radius':a+b}))
        equal(out.symbolic_result['C'],4*s.pi*epsilon*a*(a+b)/b)
    numeric=out.symbolic_result['C'].subs({a:s.Rational(1,10),b:s.Rational(4,10),er:s.Rational(38,10),eps:s.Float('8.8541878128e-12')})
    assert abs(float(numeric)-53e-12)<1e-12

@pytest.mark.historical(ids=['2026-01:2a','2026-01:2b'],complete=True)
def test_2026_large_capacitor():
    capacitance=s.Rational(91,1000);gap=s.Rational(1,10**7);epsilon=s.Rational(96,10)*eps
    area_symbol=s.Symbol('A',positive=True)
    inverted=solve(Problem('EV','capacitance',variables={'kind':'parallel_plates','epsilon':epsilon,'area':area_symbol,'distance':gap,
        'solve_for':area_symbol,'target_values':{'C':capacitance}},assumptions=['negligible_edge_effects']))
    area=inverted.symbolic_result['solved_A']
    out=solve(Problem('EV','capacitance',variables={'kind':'parallel_plates','epsilon':epsilon,'area':area,'distance':gap,'Q':s.Rational(57,10)},assumptions=['negligible_edge_effects']))
    equal(out.symbolic_result['C'],capacitance)
    assert abs(float(area.subs(eps,s.Float('8.8541878128e-12')))-107)<1
    assert abs(float(out.symbolic_result['V'])-62.6)<.1
    assert abs(float(out.symbolic_result['U'])-179)<1

@pytest.mark.historical(ids=['2023-02:2a','2023-02:2b','2023-02:2c'],complete=True)
def test_2023_dielectric_sphere():
    er=s.Symbol('epsilon_r',positive=True);theta,phi=s.symbols('theta phi',real=True)
    out=solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'sphere'},regions=[Region(0,R,k*r,eps*er)],assumptions=['spherical_symmetry']))
    equal(out.symbolic_result['Q_enc'].subs(r,R),s.pi*k*R**4)
    equal(out.symbolic_result['E'].subs(r,R/2),k*R*R/(16*eps*er))
    equal(out.symbolic_result['E'].subs(r,2*R),k*R*R/(16*eps))
    pol=solve(Problem('EV','polarization',variables={'coordinates':[r,theta,phi],'system':'spherical','E':[k*r*r/(4*eps*er),0,0],'epsilon':eps*er}))
    equal(pol.symbolic_result['P'],s.Matrix([(er-1)*k*r*r/(4*er),0,0]))

@pytest.mark.historical(ids=['2024-11:4a','2024-11:4b'],complete=True)
def test_2024_graded_resistor():
    area=s.Symbol('A',positive=True)
    out=solve(Problem('DYN','resistance',variables={'coordinate':x,'bounds':[0,d],'area':area,'conductivity':1/(b*x),'voltage':V},assumptions=['one_dimensional_steady_current']))
    equal(out.symbolic_result['J'],2*V/(b*d*d));equal(out.symbolic_result['R'],b*d*d/(2*area))
    equal(out.symbolic_result['E'],2*V*x/(d*d));equal(out.symbolic_result['rho'],2*eps*V/(d*d))
    # End-surface signs follow the normals pointing from metal into resistor.
    equal(-eps*out.symbolic_result['E'].subs(x,d),-2*V*eps/d)
    assert all(c.passed for c in out.checks)

@pytest.mark.historical(ids=['2025-01:6c'],complete=True)
def test_2025_coil_resistance():
    area=s.Symbol('A',positive=True)
    out=solve(Problem('DYN','resistance',variables={'coordinate':x,'bounds':[0,2*s.pi*R*N],'area':area,'conductivity':1/rho,
        'solve_for':area,'target_values':{'R':L}},assumptions=['one_dimensional_steady_current']))
    equal(out.symbolic_result['R'],2*s.pi*R*N*rho/area)
    solved_area=out.symbolic_result['solved_A']
    numeric=solved_area.subs({R:s.Rational(1,5),N:12,rho:s.Rational(28,10**9),L:s.Rational(6,5)})
    assert abs(float(numeric)-.35e-6)<.01e-6

@pytest.mark.historical(ids=['2024-02:1c','2024-02:1d'],complete=True)
def test_2024_semicircle_charge():
    out=solve(Problem('EV','coulomb_integral',variables={'source':[a*s.cos(u),a*s.sin(u),0],'parameters':[u],
        'bounds':[[s.pi/2,3*s.pi/2]],'density':Q/(s.pi*a),'point':[0,0,0],'kind':'line'}))
    equal(out.symbolic_result['E'],s.Matrix([Q/(2*s.pi**2*eps*a*a),0,0]));equal(out.symbolic_result['V'],Q/(4*s.pi*eps*a))
    # Cases a/b are at the same source distance: use the actual point solver for their potentials.
    for data in [[(Q,[-a,0,0])],[(Q/5,[-a*s.cos(t),a*s.sin(t),0]) for t in [-s.pi/2,-s.pi/4,0,s.pi/4,s.pi/2]]]:
        pts=solve(Problem('EV','point_charges',variables={'charges':data,'point':[0,0,0]}));equal(pts.symbolic_result['V'],Q/(4*s.pi*eps*a))

@pytest.mark.historical(ids=['2026-01:1b','2026-01:1c'],complete=True)
def test_2026_charged_semicircle():
    # Two separate uniform arcs, with different signs and explicitly oriented bounds.
    contributions=[];dipoles=[]
    for lo,hi,density in [(0,s.pi/2,-2*q/(s.pi*a)),(s.pi/2,s.pi,2*q/(s.pi*a))]:
        out=solve(Problem('EV','coulomb_integral',variables={'source':[a*s.cos(u),a*s.sin(u),0],'parameters':[u],
            'bounds':[[lo,hi]],'density':density,'point':[0,0,0],'kind':'line'}))
        contributions.append(out.symbolic_result['E'])
        dipoles.append(out.symbolic_result['dipole'])
    equal(sum(contributions,s.zeros(3,1)),s.Matrix([q/(s.pi**2*eps*a*a),0,0]))
    pol=solve(Problem('EV','multipole',variables={'charges':[(q,[-a/2,s.sqrt(3)*a/2,0]),(-q,[a/2,s.sqrt(3)*a/2,0])]}))
    equal(pol.symbolic_result['dipole'],s.Matrix([-q*a,0,0]))
    # Continuous dipole integral evaluated by the same geometric measure, with charge*position.
    continuous=s.Matrix([-4*q*a/s.pi,0,0])
    computed=sum(dipoles,s.zeros(3,1))
    equal(computed,continuous)

@pytest.mark.historical(ids=['2021-11:1a','2021-11:1b'],complete=True)
def test_2021_hemisphere():
    sigma=s.Symbol('sigma',positive=True)
    out=solve(Problem('EV','coulomb_integral',variables={'source':[R*s.sin(u)*s.cos(v),R*s.sin(u)*s.sin(v),R*s.cos(u)],
        'parameters':[u,v],'bounds':[[s.pi/2,s.pi],[0,2*s.pi]],'density':sigma,'point':[0,0,0],'kind':'surface','test_charge':Q}))
    equal(out.symbolic_result['V'],R*sigma/(2*eps));equal(out.symbolic_result['E'],s.Matrix([0,0,sigma/(4*eps)]))
    # Source PDF visually checked: Q=0.75 microC, not milliC (pdftotext loses the glyph).
    sub={R:s.Rational(22,100),sigma:46*s.Rational(1,10**5),Q:s.Rational(75,10**8),eps:s.Float('8.8541878128e-12')}
    assert abs(float(out.symbolic_result['U_external'].subs(sub))-4.3)<.1
    assert abs(float(out.symbolic_result['F'][2].subs(sub))-9.75)<.01
