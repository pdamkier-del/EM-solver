"""Exact symbolic references transcribed from supplied answer PDF; exam dates follow originals."""
import sympy as s
import pytest
from em1_solver import Problem, Region, solve
from em1_solver.core.validation import EPS0 as eps, MU0 as mu

x,y,z=s.symbols('x y z', real=True)
r,a,b,R,L,C,k,q=s.symbols('r a b R L C k q', positive=True)
theta,phi=s.symbols('theta phi', real=True)

def equal(a,b):
    residual=s.simplify(s.expand(a-b))
    if isinstance(residual,s.MatrixBase):assert all(v==0 for v in residual),residual
    else:assert residual==0,residual

def calc(**data):
    return solve(Problem('EV','field_calculus',variables={'coordinates':[x,y,z],'system':'cartesian',**data},assumptions=['electrostatic','magnetostatic']))

@pytest.mark.historical(ids=['2021-06:5a','2021-06:5c'],complete=True)
def test_2021_june_polynomial():
    e=s.Matrix([C*y*y,C*(2*x*y+z*z),2*C*y*z])
    out=calc(E=e,volume_bounds=[(x,0,L),(y,0,L),(z,0,L)])
    equal(out.symbolic_result['curl_E'],s.zeros(3,1))
    equal(out.symbolic_result['rho'],2*eps*C*(x+y))
    equal(out.symbolic_result['Q'],2*eps*C*L**4)
    assert out.method=='Gradient, divergens og rotation'
    assert all(c.passed for c in out.checks)

@pytest.mark.historical(ids=['2021-11:3a'],complete=True)
def test_2021_nonstatic_field():
    out=calc(E=[y,-x,1])
    equal(out.symbolic_result['curl_E'],s.Matrix([0,0,-2]))
    assert any(c.passed is False for c in out.checks)
    assert any('ikke være elektrostatisk' in w for w in out.warnings)

@pytest.mark.historical(ids=['2021-11:3b'],complete=True)
def test_2021_harmonic_potential():
    out=solve(Problem('EV','field_calculus',variables={'coordinates':[r,theta,phi],'system':'spherical','V':a*r*r*(2*s.cos(theta)**2-s.sin(theta)**2)}))
    equal(out.symbolic_result['laplacian_V'],0)

@pytest.mark.historical(ids=['2022-02:5a'],complete=True)
def test_2022_electrostatic_density():
    out=calc(E=[-a*2*x*y/R**3,-a*x*x/R**3,0])
    equal(out.symbolic_result['curl_E'],s.zeros(3,1))
    equal(out.symbolic_result['rho'],-2*eps*a*y/R**3)

@pytest.mark.historical(ids=['2022-11:2a','2022-11:2b'],complete=True)
def test_2022_spherical_density_from_field():
    out=solve(Problem('EV','field_calculus',variables={'coordinates':[r,theta,phi],'system':'spherical',
        'E':[a*(2*r*r/R**2-r/R),0,0],'volume_bounds':[(r,0,R),(theta,0,s.pi),(phi,0,2*s.pi)]},assumptions=['electrostatic']))
    equal(out.symbolic_result['rho'],eps*a*(8*r/R**2-3/R))
    equal(out.symbolic_result['Q'],4*s.pi*R*R*eps*a)

@pytest.mark.historical(ids=['2023-11:3a','2023-11:3b'],complete=True)
def test_2023_nonstatic_polynomial():
    out=calc(E=[C*(x*x+z*z)/a**2,C*(y*y+x*x)/a**2,C*(z*z+y*y)/a**2],
             volume_bounds=[(x,0,a),(y,0,a),(z,0,a)])
    equal(out.symbolic_result['rho'],2*eps*C*(x+y+z)/a**2)
    equal(out.symbolic_result['Q'],3*eps*C*a*a)
    equal(out.symbolic_result['dB_dt'],-2*C/a**2*s.Matrix([y,z,x]))
    assert any(c.passed is False for c in out.checks)

@pytest.mark.historical(ids=['2025-01:1a','2025-01:1b'],complete=True)
def test_2025_linear_field():
    out=calc(E=[a+b*x,0,0])
    equal(out.symbolic_result['rho'],eps*b)
    pot=solve(Problem('EV','potential_from_field',variables={'field':a+b*x,'coordinate':x,'start':0,'end':L}))
    equal(pot.symbolic_result['delta_V'],-a*L-b*L*L/2)
    # The x=L face is at lower potential for the supplied positive a,b.
    assert pot.symbolic_result['delta_V'].is_negative
    assert float(pot.symbolic_result['delta_V'].subs({a:500,b:50,L:20}))==-20000

@pytest.mark.historical(ids=['2025-11:2a','2025-11:2b','2025-11:2c'],complete=True)
def test_2025_log_potential():
    out=solve(Problem('EV','field_calculus',variables={'coordinates':[r,theta,phi],'system':'spherical','V':-a*s.log(r/R),
        'volume_bounds':[(r,0,R),(theta,0,s.pi),(phi,0,2*s.pi)]}, numerical_values={a:134,R:5}))
    equal(out.symbolic_result['E'],s.Matrix([a/r,0,0]))
    equal(out.symbolic_result['rho'],eps*a/r**2)
    equal(out.symbolic_result['Q'],4*s.pi*eps*a*R)
    assert abs(float(out.numerical_result['Q'])-74.55e-9)<0.1e-9
    assert abs(float((a/r).subs({a:134,r:s.sqrt(2)}))-94.8)<0.1
    equal(s.limit(out.symbolic_result['Q'].subs(R,r),r,0),0)

@pytest.mark.historical(ids=['2023-02:4a'],complete=True)
def test_2023_vector_potential():
    out=calc(A=[3*k*z*y,-2*k*z*y,k*z*z])
    equal(out.symbolic_result['B'],k*s.Matrix([2*y,3*y,-3*z]))
    equal(out.symbolic_result['J'],s.Matrix([0,0,-2*k/mu]))
    assert next(c for c in out.checks if c.name=='Magnetisk divergens').passed

@pytest.mark.historical(ids=['2026-01:4a'],complete=True)
def test_2026_vector_potentials_both_cases():
    out=calc(A=[-k*y,k*x,0]);equal(out.symbolic_result['B'],s.Matrix([0,0,2*k]))
    out2=solve(Problem('BA','field_calculus',variables={'coordinates':[r,phi,z],'system':'cylindrical','A':[0,k*r,0]},assumptions=['magnetostatic']))
    equal(out2.symbolic_result['B'],s.Matrix([0,0,2*k]))

@pytest.mark.historical(ids=['2026-01:5a','2026-01:5b','2026-01:5c'],complete=True)
def test_2026_legendre():
    v0=s.Symbol('V_0',real=True)
    out=solve(Problem('EV','laplace_legendre',variables={'r':r,'theta':theta,'radius':R,'coefficients':[(2,2*v0)]},
        assumptions=['axial_symmetry','charge_free_inside_outside','V_infinity_zero','finite_at_origin']))
    equal(out.symbolic_result['V_outside'],v0*(3*s.cos(theta)**2-1)*(R/r)**3)
    equal(out.symbolic_result['V_inside'],v0*(3*s.cos(theta)**2-1)*(r/R)**2)
    equal(out.symbolic_result['E_outside'],3*v0*R**3/r**4*s.Matrix([3*s.cos(theta)**2-1,2*s.cos(theta)*s.sin(theta),0]))
    assert all(c.passed for c in out.checks)

@pytest.mark.historical(ids=['2024-11:2a','2024-11:2b'],complete=True)
def test_2024_gauss_cylinder():
    out=solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'cylinder','length':L},regions=[Region(0,a,k*r*r)],assumptions=['infinite_cylindrical_symmetry']))
    equal(out.symbolic_result['Q_enc'].subs(r,a/2),s.pi*k*L*(a/2)**4/2)
    equal(out.symbolic_result['E'].subs(r,a/2),k*(a/2)**3/(4*eps))
    equal(out.symbolic_result['E'].subs(r,2*a),k*a**3/(8*eps))
    # Actual one-sided symbolic branches agree at the interface.
    equal((k*r**3/(4*eps)-k*a**4/(4*eps*r)).subs(r,a),0)
    equal(s.limit(k*r**3/(4*eps),r,0),0)

@pytest.mark.historical(ids=['2022-02:2a'],complete=True)
def test_2022_cylinder_gap():
    out=solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'cylinder'},regions=[Region(0,a,2*q/(s.pi*a*a))],assumptions=['infinite_cylindrical_symmetry']))
    equal(out.symbolic_result['E'].subs(r,2*a),q/(2*s.pi*eps*a))

@pytest.mark.historical(ids=['2024-02:2a','2024-02:2b'],complete=True)
def test_2024_polarized_cube():
    out=solve(Problem('EV','polarization',variables={'coordinates':[x,y,z],'system':'cartesian','P':[a*x,a*y,a*z],
        'normal':[1,0,0],'surface_substitutions':{x:L/2}}))
    equal(out.symbolic_result['sigma_bound'],a*L/2);equal(out.symbolic_result['rho_bound'],-3*a)
    equal(6*L*L*out.symbolic_result['sigma_bound']+L**3*out.symbolic_result['rho_bound'],0)
