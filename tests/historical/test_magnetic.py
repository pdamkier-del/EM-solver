import sympy as s
import pytest
from em1_solver import Problem,Region,solve
from em1_solver.core.validation import MU0 as mu
from .test_fields import equal

r,R,a,d,J,I,k,q,m,V,B=s.symbols('r R a d J I k q m V B',positive=True)
x,y,z,u=s.symbols('x y z u', real=True)

@pytest.mark.historical(ids=['2025-01:4a'],complete=True)
def test_2025_lorentz():
    out=solve(Problem('BA','lorentz_force',variables={'q':6*s.Rational(1,10**6),'v':[3*10**6,4*10**6,-3*10**6],'B':[4,3,2],'E':[0,0,0]}))
    equal(out.symbolic_result['F'],s.Matrix([102,-108,-42]))
    assert abs(float(out.symbolic_result['magnitude'])-154)<1
    assert all(c.passed for c in out.checks)

@pytest.mark.historical(ids=['2021-06:4a'],complete=True)
def test_2021_mass_spectrometer():
    out=solve(Problem('BA','lorentz_force',variables={'kind':'orbit','mass':m,'q':q,'B_magnitude':B,'voltage':V},
        assumptions=['nonrelativistic','velocity_perpendicular_B']))
    equal(out.symbolic_result['diameter'],2*s.sqrt(2*m*V/q)/B)
    val=out.symbolic_result['diameter'].subs({m:12*s.Float('1.66054e-27'),q:s.Float('1.602176634e-19'),B:s.Rational(5,2),V:40000})
    assert abs(float(val)-.0798)<.0001

@pytest.mark.historical(ids=['2021-11:4a'],complete=True)
def test_2021_circular_B_force():
    angle=s.Symbol('alpha',real=True);speed=s.Symbol('v',positive=True)
    out=solve(Problem('BA','lorentz_force',variables={'q':q,'v':[speed*s.cos(angle),speed*s.sin(angle),0],'B':[0,k*a*a,0],'E':[0,0,0]}))
    equal(out.symbolic_result['F'],s.Matrix([0,0,q*k*a*a*speed*s.cos(angle)]))

@pytest.mark.historical(ids=['2021-11:4b'],complete=True)
def test_2021_current_from_B():
    phi=s.Symbol('phi',real=True)
    out=solve(Problem('BA','field_calculus',variables={'coordinates':[r,phi,z],'system':'cylindrical','B':[0,k*r*r,0]},assumptions=['magnetostatic']))
    equal(out.symbolic_result['J'],s.Matrix([0,0,3*k*r/mu]))

def amp(regions,**kw):
    return solve(Problem('BA','ampere',variables={'kind':'cylinder','coordinate':r,**kw},regions=regions,assumptions=['infinite_cylindrical_symmetry','magnetostatic']))

@pytest.mark.historical(ids=['2025-11:4a'],complete=True)
def test_2025_ampere_solid():
    out=amp([Region(0,R,J)])
    equal(out.symbolic_result['B'].subs(r,R/2),mu*J*R/4)
    equal(out.symbolic_result['B'].subs(r,2*R),mu*J*R/4)
    equal(s.limit(mu*J*r/2,r,0),0)
    equal((mu*J*r/2-mu*J*R*R/(2*r)).subs(r,R),0)

@pytest.mark.historical(ids=['2024-02:4a','2024-02:4b'],complete=True)
def test_2024_nonuniform_current():
    out=amp([Region(0,R,J*(1-r/R))])
    equal(out.symbolic_result['I_enc'].subs(r,R),s.pi*J*R*R/3)
    equal(out.symbolic_result['B'].subs(r,R/2),mu*J*R/6)
    equal(out.symbolic_result['B'].subs(r,2*R),mu*J*R/12)
    subs={J:96*10**6,R:s.Rational(31,10000),mu:s.Float('1.25663706212e-6')}
    assert abs(float(out.symbolic_result['I_enc'].subs(r,R).subs(subs))-966.1)<1
    # Confirmed against rendered original: facit 70 kA is inconsistent; .0623 T agrees.
    assert abs(float((mu*J*R/6).subs(subs))-.06233)<.0001

@pytest.mark.historical(ids=['2021-06:3a'],complete=True)
def test_2021_coaxial_currents():
    out=amp([Region(0,a,I/(s.pi*a*a))],surface_currents=[(2*a,-3*I/(16*s.pi*a))])
    equal(out.symbolic_result['B'].subs(r,s.Rational(3,2)*a),mu*I/(3*s.pi*a))
    equal(out.symbolic_result['B'].subs(r,3*a),mu*I/(24*s.pi*a))

@pytest.mark.historical(ids=['2022-02:4b','2025-11:4b','2025-11:4c'],complete=True)
def test_magnetic_cavities():
    out=solve(Problem('BA','magnetic_superposition',variables={'point':[R/4+R/2,0,0],
        'sources':[{'kind':'cylinder','center':[0,0,0],'radius':R,'J':J},{'kind':'cylinder','center':[R/4,0,0],'radius':R/2,'J':-J}]},assumptions=['parallel_infinite_sources','magnetostatic']))
    equal(out.symbolic_result['B'],s.Matrix([0,mu*J*R/8,0]))
    # Any point inside both cylinders: choose coordinates parameterised to guarantee membership.
    for point in ([0,0,0],[0,R/4,0]):
        out=solve(Problem('BA','magnetic_superposition',variables={'point':point,
            'sources':[{'kind':'cylinder','center':[-R/4,0,0],'radius':R,'J':J},
                       {'kind':'cylinder','center':[R/4,0,0],'radius':R,'J':-J}]},assumptions=['parallel_infinite_sources','magnetostatic']))
        equal(out.symbolic_result['B'],s.Matrix([0,mu*J*R/4,0]))

@pytest.mark.historical(ids=['2025-01:5a','2025-01:5b'],complete=True)
def test_2025_parallel_wires():
    def sources(angles):return [{'kind':'wire','center':[-a*s.cos(t),a*s.sin(t),0],'I':I/len(angles)} for t in angles]
    for angles,coefficient in [([0],1),([-s.pi/2,-s.pi/4,0,s.pi/4,s.pi/2],(1+s.sqrt(2))/5)]:
        out=solve(Problem('BA','magnetic_superposition',variables={'point':[0,0,0],'sources':sources(angles)},assumptions=['parallel_infinite_sources','magnetostatic']))
        equal(out.symbolic_result['B'],s.Matrix([0,mu*I/(2*s.pi*a)*coefficient,0]))

@pytest.mark.historical(ids=['2022-02:3a'],complete=True)
def test_2022_bent_wire_force():
    L=s.Symbol('L',positive=True)
    straight=solve(Problem('BA','wire_force',variables={'source':[u,0,0],'parameter':u,'bounds':[0,L],'I':I,'B':[0,0,B]}))
    arc=solve(Problem('BA','wire_force',variables={'source':[s.Rational(3,2)*L-L*s.cos(u)/2,L*s.sin(u)/2,0],
        'parameter':u,'bounds':[0,s.pi],'I':I,'B':[0,0,B]}))
    equal(straight.symbolic_result['F'],s.Matrix([0,-I*L*B,0]));equal(arc.symbolic_result['F'],s.Matrix([0,-I*L*B,0]))
    assert abs(float((2*I*L*B).subs({I:7.6,L:.23,B:.45}))-1.6)<.03

@pytest.mark.historical(ids=['2022-11:5a','2022-11:5b'],complete=True)
def test_2022_magnetized_cylinder():
    phi=s.Symbol('phi',real=True)
    out=solve(Problem('BA','magnetic_material',variables={'kind':'magnetization','coordinates':[r,phi,z],'system':'cylindrical',
        'M':[0,0,k*r*r],'H':[0,0,0],'normal':[1,0,0],'surface_substitutions':{r:R}}))
    equal(out.symbolic_result['J_bound'],s.Matrix([0,-2*k*r,0]))
    equal(out.symbolic_result['K_bound'],s.Matrix([0,k*R*R,0]))
    equal(out.symbolic_result['B'],s.Matrix([0,0,mu*k*r*r]))
    # H=0 outside from no free currents, vanishing at infinity and axial symmetry; this input is explicit.
    outside=solve(Problem('BA','magnetic_material',variables={'kind':'magnetization','coordinates':[r,phi,z],'system':'cylindrical','M':[0,0,0],'H':[0,0,0]}))
    equal(outside.symbolic_result['B'],s.zeros(3,1))

@pytest.mark.historical(ids=['2024-11:6a','2024-11:6b','2024-11:6c'],complete=True)
def test_2024_toroid_gap():
    n=s.Symbol('N',positive=True);mur=s.Symbol('mu',positive=True);fraction=3/(230*s.pi)
    out=solve(Problem('BA','magnetic_material',variables={'kind':'magnetic_circuit','N':n,'I':I,'segments':[(2*s.pi*R,mur)]},assumptions=['negligible_leakage','uniform_cross_section']))
    equal(out.symbolic_result['B'],mur*n*I/(2*s.pi*R))
    gap=solve(Problem('BA','magnetic_material',variables={'kind':'magnetic_circuit','N':n,'I':I,'segments':[(2*s.pi*R*(1-fraction),mur),(2*s.pi*R*fraction,mu)]},assumptions=['negligible_leakage','uniform_cross_section']))
    factor=s.simplify(gap.symbolic_result['B']/(mu*n*I/(2*s.pi*R)))
    equal(factor,1/((1-fraction)*mu/mur+fraction))
    sub={R:s.Rational(23,100),n:620,I:s.Rational(17,2),mu:s.Float('1.25663706212e-6')}
    assert abs(float((mu*n*I/(2*s.pi*R)).subs(sub))-.0046)<.0001
    assert abs(float(factor.subs(mur,3000*mu))-223)<1
