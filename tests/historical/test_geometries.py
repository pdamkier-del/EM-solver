import sympy as s
import pytest
from em1_solver import Problem,solve
from em1_solver.core.validation import EPS0 as eps,MU0 as mu
from .test_fields import equal

a,b,R,w,I,sigma,q,k,N,L=s.symbols('a b R w I sigma q k N L',positive=True)
u=s.Symbol('u',positive=True);v,t=s.symbols('v t',real=True);z=s.Symbol('z',positive=True)

@pytest.mark.historical(ids=['2024-11:3a','2024-11:3b'],complete=True)
def test_2024_current_ribbon():
    out=solve(Problem('BA','magnetic_superposition',variables={'point':[b+w,0,0],
        'sources':[{'kind':'wire','center':[u,0,0],'I':I/w}],'distribution_bounds':[(u,0,w)],'limits':{'B':[w,0]}},
        assumptions=['parallel_infinite_sources','magnetostatic']))
    equal(out.symbolic_result['B'],s.Matrix([0,mu*I/(2*s.pi*w)*s.log((b+w)/b),0]))
    equal(out.symbolic_result['limit_B'],s.Matrix([0,mu*I/(2*s.pi*b),0]))

@pytest.mark.historical(ids=['2025-01:5c'],complete=True)
def test_2025_half_cylindrical_current_foil():
    out=solve(Problem('BA','magnetic_superposition',variables={'point':[0,0,0],
        'sources':[{'kind':'wire','center':[a*s.cos(v),a*s.sin(v),0],'I':I/s.pi}],
        'distribution_bounds':[(v,s.pi/2,3*s.pi/2)]},assumptions=['parallel_infinite_sources','magnetostatic']))
    equal(out.symbolic_result['B'],s.Matrix([0,mu*I/(s.pi**2*a),0]))

@pytest.mark.historical(ids=['2025-01:3a','2025-01:3b'],complete=True)
def test_2025_annular_disk_potential_and_field():
    out=solve(Problem('EV','coulomb_integral',variables={'kind':'surface','source':[u*s.cos(v),u*s.sin(v),0],
        'parameters':[u,v],'bounds':[[a,a+b],[0,2*s.pi]],'density':sigma,'point':[0,0,z]}))
    equal(out.symbolic_result['V'],sigma/(2*eps)*(s.sqrt((a+b)**2+z*z)-s.sqrt(a*a+z*z)))
    expected=s.Matrix([0,0,sigma*z/(2*eps)*(1/s.sqrt(a*a+z*z)-1/s.sqrt((a+b)**2+z*z))])
    equal(out.symbolic_result['E'],expected)
    derivative=solve(Problem('EV','field_calculus',variables={'coordinates':[z,s.Symbol('theta'),s.Symbol('phi')],'system':'cartesian',
        'V':out.symbolic_result['V']}))
    equal(derivative.symbolic_result['E'][0],expected[2])
    # Disk/plane limit is taken after computing finite-geometry potential.
    reduced=out.symbolic_result['E'].subs(a,0)
    limit=s.Matrix([s.limit(component,b,s.oo) for component in reduced])
    equal(limit,s.Matrix([0,0,sigma/(2*eps)]))

def test_Biot_Savart_loop_general_axial_field():
    out=solve(Problem('BA','biot_savart',variables={'source':[R*s.cos(v),R*s.sin(v),0],'parameter':v,
        'bounds':[0,2*s.pi],'I':I,'point':[0,0,z]}))
    equal(out.symbolic_result['B'],s.Matrix([0,0,mu*I*R*R/(2*(R*R+z*z)**s.Rational(3,2))]))

@pytest.mark.historical(ids=['2024-11:5a','2024-11:5b','2024-11:5c'],complete=True)
def test_2024_dipole_coupled_loops():
    # Leading-order small-loop approximation, a << b. Axis and equatorial projections differ.
    moment=solve(Problem('BA','multipole',variables={'charges':[],'magnetic_current':I,'area':s.pi*a*a,'normal':[0,0,1],
        'magnetic_field_point':[0,0,b]},assumptions=['far_field']))
    dipole=moment.symbolic_result['magnetic_dipole']
    # Generic dipole field is supplied as geometric flux input; explicit orientation matters.
    axis_B=moment.symbolic_result['B_magnetic_far'][2]
    equatorial=solve(Problem('BA','multipole',variables={'charges':[],'magnetic_current':I,'area':s.pi*a*a,'normal':[0,0,1],
        'magnetic_field_point':[b,0,0]},assumptions=['far_field']))
    eq_B=equatorial.symbolic_result['B_magnetic_far'][2]
    mutual=[]
    for field in [axis_B,eq_B]:
        flux=field*s.pi*a*a
        out=solve(Problem('DYN','inductance_energy',variables={'flux':flux,'I':I,'N':1,'mutual':True}))
        mutual.append(out.symbolic_result['M'])
    equal(mutual[0],mu*s.pi*a**4/(2*b**3));equal(mutual[1],-mu*s.pi*a**4/(4*b**3))
    rate=s.Symbol('dI_dt',positive=True)
    for m,expected_sign in zip(mutual,[-1,1]):
        induction=solve(Problem('DYN','faraday',variables={'time':t,'flux':m*rate*t,'R':R},assumptions=['negligible_self_inductance']))
        equal(induction.symbolic_result['I'],-m*rate/R)
        assert s.sign(induction.symbolic_result['I'])==expected_sign
