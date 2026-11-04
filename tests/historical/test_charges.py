import sympy as s
import pytest
from em1_solver import Problem, solve
from em1_solver.core.validation import EPS0 as eps
from .test_fields import equal

a,q,Q,z=s.symbols('a q Q z',positive=True)
ke=1/(4*s.pi*eps)

def charges(data,point,test_charge=None):
    return solve(Problem('EV','point_charges',variables={'charges':data,'point':point,**({'test_charge':test_charge} if test_charge is not None else {})}))

@pytest.mark.historical(ids=['2021-06:2a'],complete=True)
def test_2021_tetrahedron_energy():
    positions=[[0,0,0],[a,0,0],[a/2,s.sqrt(3)*a/2,0],[a/2,a/(2*s.sqrt(3)),s.sqrt(s.Rational(2,3))*a]]
    out=charges([(Q,p) for p in positions],[0,0,2*a])
    equal(out.symbolic_result['U'],6*ke*Q*Q/a)

@pytest.mark.historical(ids=['2022-02:1a','2022-02:1b','2022-02:1c'],complete=True)
def test_2022_four_charges():
    data=[(q,[-a,0,0]),(q,[0,-a,0]),(q,[a,0,0]),(-q,[0,a,0])]
    out=charges(data,[0,0,z]);equal(out.symbolic_result['U'],0)
    equal(out.symbolic_result['E'],2*ke*q*s.Matrix([0,a,z])/(a*a+z*z)**s.Rational(3,2))
    equal(out.symbolic_result['E'].subs(z,0),s.Matrix([0,2*ke*q/a**2,0]))
    theta,phi=s.symbols('theta phi',real=True);r=s.Symbol('r',positive=True)
    far=solve(Problem('EV','multipole',variables={'charges':data,'r':r,'theta':theta,'phi':phi}))
    equal(far.symbolic_result['dipole'],s.Matrix([0,-2*q*a,0]))
    equal(far.symbolic_result['V_far'],2*ke*q*(1/r-a*s.sin(theta)*s.sin(phi)/r**2))

@pytest.mark.historical(ids=['2023-02:1a','2023-02:1b','2023-02:1c'],complete=True)
def test_2023_three_charges():
    q1,q2,q3=-3*s.Rational(1,10**6),2*s.Rational(1,10**6),4*s.Rational(1,10**6)
    first=charges([(q2,[a,0,0])],[0,0,0],q1)
    second=charges([(q2,[a,0,0]),(q3,[a/2,s.sqrt(3)*a/2,0])],[0,0,0],q1)
    equal(first.symbolic_result['F'],s.Matrix([-ke*q1*q2/a**2,0,0]))
    equal(second.symbolic_result['F'],s.Matrix([-ke*q1*(q2+q3/2)/a**2,-ke*q1*q3*s.sqrt(3)/(2*a*a),0]))
    third=charges([(q1,[0,0,0]),(q2,[a,0,0]),(q3,[a/2,s.sqrt(3)*a/2,0])],[0,0,a])
    equal(third.symbolic_result['U'],ke*(q1*q2+q1*q3+q2*q3)/a)
    subs={a:s.Rational(1,5),eps:s.Float('8.8541878128e-12')}
    assert abs(float(first.symbolic_result['F'][0].subs(subs))-1.35)<.01
    assert abs(float(second.symbolic_result['F'][1].subs(subs))-2.34)<.01
    assert abs(float(third.symbolic_result['U'].subs(subs))+.45)<.01

@pytest.mark.historical(ids=['2024-02:1a','2024-02:1b'],complete=True)
def test_2024_arc_point_superposition():
    out=charges([(Q,[-a,0,0])],[0,0,0]);equal(out.symbolic_result['E'],s.Matrix([ke*Q/a**2,0,0]))
    data=[(Q/5,[-a*s.cos(angle),a*s.sin(angle),0]) for angle in [-s.pi/2,-s.pi/4,0,s.pi/4,s.pi/2]]
    out=charges(data,[0,0,0]);equal(out.symbolic_result['E'],s.Matrix([ke*Q*(1+s.sqrt(2))/(5*a*a),0,0]))

@pytest.mark.historical(ids=['2024-11:1a'],complete=True)
def test_2024_corner_force():
    out=charges([(-q,[-a,a,0]),(-q,[a,-a,0]),(q,[-a,-a,0])],[a,a,0],q)
    equal(out.symbolic_result['F'],-ke*q*q*(4-s.sqrt(2))/(16*a*a)*s.Matrix([1,1,0]))

@pytest.mark.historical(ids=['2025-11:1a','2025-11:1b'],complete=True)
def test_2025_charges_and_images():
    out=charges([(q,[-a/2,a/2,0])],[a/2,a/2,0],q)
    equal(out.symbolic_result['F'],s.Matrix([ke*q*q/a**2,0,0]))
    energy=charges([(q,[-a/2,a/2,0]),(q,[a/2,a/2,0])],[0,0,a])
    equal(energy.symbolic_result['U'],ke*q*q/a)
    # For self-force at a real charge, omit its singular real self-field, but retain its image.
    imageforce=solve(Problem('EV','images',variables={'charges':[(q,[a/2,a/2,0]),(q,[-a/2,a/2,0])],
        'point':[a/2,a/2,0],'planes':[1],'self_index':0,'test_charge':q},assumptions=['grounded_infinite_planes']))
    equal(imageforce.symbolic_result['F'],ke*q*q/a**2*s.Matrix([1-1/(2*s.sqrt(2)),-1-1/(2*s.sqrt(2)),0]))

@pytest.mark.historical(ids=['2026-01:1a'],complete=True)
def test_2026_point_dipole():
    data=[(q,[-a/2,s.sqrt(3)*a/2,0]),(-q,[a/2,s.sqrt(3)*a/2,0])]
    out=charges(data,[0,0,0]);equal(out.symbolic_result['E'],s.Matrix([ke*q/a**2,0,0]));equal(out.symbolic_result['U'],-ke*q*q/a)

@pytest.mark.historical(ids=['2023-11:1a','2023-11:1b','2023-11:1c'],complete=False)
def test_2023_equilibrium_algebra():
    # Field and energy primitives verified; automatic equilibrium/stability interpretation is not implemented.
    unknown=s.Symbol('Q_unknown', real=True)
    out=charges([(q,[a,0,0]),(unknown,[a/2,0,0])],[0,0,0],q)
    equal(s.solve(out.symbolic_result['F'][0],unknown)[0],-q/4)
    whole=charges([(q,[0,0,0]),(q,[a,0,0]),(-q/4,[a/2,0,0])],[0,0,a])
    equal(whole.symbolic_result['U'],0)
