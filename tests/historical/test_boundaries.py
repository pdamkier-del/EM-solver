import sympy as s
import pytest
from em1_solver import Problem,solve
from em1_solver.core.validation import EPS0 as eps,MU0 as mu
from .test_fields import equal

a,b,R,q,Q,L,er,V,k=s.symbols('a b R q Q L epsilon_r V k',positive=True)
r=s.Symbol('r',positive=True);x,y,z=s.symbols('x y z',real=True)

@pytest.mark.historical(ids=['2021-06:1a','2021-06:1c'],complete=True)
def test_2021_offcenter_cavity_total_and_potential():
    out=solve(Problem('EV','conductors',variables={'kind':'cavity_totals','enclosed_charge':q,'metal_charge':3*q,'outer_radius':R},
        assumptions=['electrostatic','closed_conductor','spherical_outer_surface','no_external_sources']))
    equal(out.symbolic_result['Q_inner'],-q);equal(out.symbolic_result['Q_outer'],4*q);equal(out.symbolic_result['V'],4*q/(4*s.pi*eps*R))

@pytest.mark.historical(ids=['2022-02:2b'],complete=True)
def test_2022_coaxial_surface_charges():
    # Total free line charge is +2lambda inside, -lambda on the shell.
    lam=s.Symbol('lambda',positive=True)
    inner=solve(Problem('EV','conductors',variables={'kind':'boundary','normal':[-1,0,0],'E_inside':[0,0,0],
        'E_outside':[2*lam/(2*s.pi*eps*b),0,0],'epsilon_inside':eps,'epsilon_outside':eps}))
    outer=solve(Problem('EV','conductors',variables={'kind':'boundary','normal':[1,0,0],'E_inside':[0,0,0],
        'E_outside':[lam/(2*s.pi*eps*b),0,0],'epsilon_inside':eps,'epsilon_outside':eps}))
    equal(inner.symbolic_result['sigma_free'],-2*lam/(2*s.pi*b));equal(outer.symbolic_result['sigma_free'],lam/(2*s.pi*b))

@pytest.mark.historical(ids=['2022-02:2c'],complete=True)
def test_2022_dielectric_cylindrical_potential():
    lam=s.Symbol('lambda',positive=True)
    out=solve(Problem('EV','potential_from_field',variables={'field':lam/(s.pi*eps*er*r),'coordinate':r,
        'start':b,'end':a}))
    equal(out.symbolic_result['delta_V'],lam/(s.pi*eps*er)*s.log(b/a))
    sub={a:.001,b:.004,lam:90e-9,er:4.2,eps:s.Float('8.8541878128e-12')}
    assert abs(float(out.symbolic_result['delta_V'].subs(sub))-1100)<50

@pytest.mark.historical(ids=['2021-11:2c'],complete=True)
def test_2021_dielectric_shell_charge_separation():
    # Every metal/dielectric interface is evaluated with outward normal from the metal.
    for radius,sign in [(a,1),(b,-1)]:
        out=solve(Problem('EV','conductors',variables={'kind':'boundary','normal':[sign,0,0],
            'E_inside':[0,0,0],'E_outside':[Q/(4*s.pi*eps*er*radius**2),0,0],'epsilon_inside':eps,'epsilon_outside':eps*er}))
        equal(out.symbolic_result['sigma_free'],sign*Q/(4*s.pi*radius**2))
        equal(out.symbolic_result['sigma_total'],sign*Q/(4*s.pi*er*radius**2))
        equal(out.symbolic_result['sigma_bound'],-sign*(er-1)*Q/(4*s.pi*er*radius**2))
    # Inner empty-cavity surface has no charge; outer vacuum surface carries Q1+Q2.
    vacuum=solve(Problem('EV','conductors',variables={'kind':'boundary','normal':[1,0,0],
        'E_inside':[0,0,0],'E_outside':[(Q+q)/(4*s.pi*eps*R**2),0,0],'epsilon_inside':eps,'epsilon_outside':eps}))
    equal(vacuum.symbolic_result['sigma_free'],(Q+q)/(4*s.pi*R**2));equal(vacuum.symbolic_result['sigma_bound'],0)

@pytest.mark.historical(ids=['2022-02:5b'],complete=True)
def test_2022_work_along_arc():
    u=s.Symbol('u',real=True);source=s.Matrix([R*s.cos(u),R*s.sin(u),0])
    e=s.Matrix([-2*V*source[0]*source[1]/R**3,-V*source[0]**2/R**3,0])
    out=solve(Problem('EV','potential_from_field',variables={'field':s.simplify(e.dot(source.diff(u))),'coordinate':u,
        'start':0,'end':s.pi/6,'test_charge':Q}))
    equal(out.symbolic_result['W_external'],3*Q*V/8)
