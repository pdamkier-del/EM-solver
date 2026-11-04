import sympy as s
import pytest
from em1_solver import Problem,solve
from em1_solver.core.validation import EPS0 as eps, MU0 as mu
from .test_fields import equal

t,x,y,u=s.symbols('t x y u',real=True)
B,a,R,L,v,T,tau,w,N,k,m,V,d=s.symbols('B a R L v T tau omega N k m V d',positive=True)

def faraday(data,assumptions=()):
    return solve(Problem('DYN','faraday',variables={'time':t,**data},assumptions=['negligible_self_inductance',*assumptions]))

@pytest.mark.historical(ids=['2022-02:6a'],complete=True)
def test_2022_ring_sinusoid():
    out=faraday({'B_normal':B*s.sin(w*t),'area':s.pi*a*a,'R':R},['uniform_normal_B'])
    equal(out.symbolic_result['I'].subs(t,s.pi/(3*w)),-s.pi*a*a*B*w/(2*R))
    assert out.symbolic_result['I'].subs(t,s.pi/(3*w)).is_negative
    assert all(c.passed for c in out.checks)

@pytest.mark.historical(ids=['2022-11:6a'],complete=True)
def test_2022_nonuniform_square_flux():
    out=faraday({'flux_integrand':B*(x*x+y*y)/L**2*s.exp(-t/tau),'bounds':[(x,0,L),(y,0,L)],'R':R})
    equal(out.symbolic_result['I'],2*B*L*L*s.exp(-t/tau)/(3*tau*R))
    assert out.symbolic_result['I'].is_positive

@pytest.mark.historical(ids=['2023-02:5b','2023-02:5c'],complete=True)
def test_2023_mutual_sinusoid():
    c,i0=s.symbols('C I_0',positive=True)
    out=faraday({'flux':c*i0*s.cos(w*t),'R':R})
    equal(out.symbolic_result['EMF'],c*i0*w*s.sin(w*t))
    equal(out.symbolic_result['P'],c*c*i0*i0*w*w/R*s.sin(w*t)**2)
    assert out.symbolic_result['EMF'].subs(t,s.pi/(2*w)).is_positive

@pytest.mark.historical(ids=['2025-01:6a','2025-01:6b'],complete=True)
def test_2025_coil_exponential():
    b=s.Symbol('b',real=True)
    out=faraday({'B_normal':a*(1-s.exp(-t/tau))+b,'area':s.pi*R*R,'N':N,'R':L,'time_bounds':[0,T]},['uniform_normal_B'])
    equal(out.symbolic_result['EMF'],-N*s.pi*R*R*a*s.exp(-t/tau)/tau)
    equal(out.symbolic_result['W'],(N*s.pi*R*R*a)**2/(2*tau*L)*(1-s.exp(-2*T/tau)))
    assert out.symbolic_result['EMF'].is_negative
    numerical=out.symbolic_result['W'].subs({N:12,R:s.Rational(1,5),a:5,tau:60,L:s.Rational(6,5),T:55})
    assert abs(float(numerical)-.33)<.01

@pytest.mark.historical(ids=['2026-01:3a','2026-01:3b','2026-01:3c'],complete=True)
def test_2026_nonuniform_circle():
    rad=s.Symbol('s',nonnegative=True);phi=s.Symbol('phi',real=True)
    out=faraday({'flux_integrand':k*rad**2*s.sin(phi)**2*s.cos(t/T),
        'bounds':[(rad,0,L),(phi,0,2*s.pi)],'R':R,'time_bounds':[0,2*s.pi*T]})
    equal(out.symbolic_result['Phi'].subs(t,0),k*s.pi*L**3/3)
    equal(out.symbolic_result['I'],k*s.pi*L**3/(3*R*T)*s.sin(t/T))
    equal(out.symbolic_result['W'],s.pi**3*k*k*L**6/(9*R*T))
    assert out.symbolic_result['I'].subs(t,5*T).is_negative # clockwise relative to +z

@pytest.mark.historical(ids=['2024-02:5a','2024-02:5b','2024-02:5d'],complete=True)
def test_2024_expanding_triangle():
    resistivity_per_length=s.Symbol('r_line',positive=True)
    side=2*v*t/s.sqrt(3);area=s.sqrt(3)*side**2/4
    out=faraday({'area':area,'B_normal':-B,'R':2*s.sqrt(3)*resistivity_per_length*v*s.Symbol('t_positive',positive=True)},['uniform_normal_B'])
    # Time-dependent R is allowed algebraically; use positive t to enforce a physically positive resistance.
    tp=s.Symbol('tp',positive=True)
    out=solve(Problem('DYN','faraday',variables={'time':tp,'area':v*v*tp*tp/s.sqrt(3),'B_normal':-B,
        'R':2*s.sqrt(3)*resistivity_per_length*v*tp,'time_bounds':[0,T]},assumptions=['uniform_normal_B','negligible_self_inductance']))
    equal(out.symbolic_result['EMF'],2*B*v*v*tp/s.sqrt(3))
    equal(out.symbolic_result['I'],B*v/(3*resistivity_per_length))
    equal(out.symbolic_result['W'],B*B*v**3*T*T/(3*s.sqrt(3)*resistivity_per_length))

@pytest.mark.historical(ids=['2021-06:6a','2021-06:6b','2021-06:6c','2021-06:6d'],complete=True)
def test_2021_sliding_rod():
    distance=s.Symbol('distance',positive=True)
    out=solve(Problem('DYN','motional_emf',variables={'source':[0,u,0],'parameter':u,'bounds':[0,L],'v':[v,0,0],'B':[0,0,B],
        'time':t,'R':R,'time_bounds':[0,distance/v]},assumptions=['negligible_self_inductance','stationary_return_path']))
    equal(out.symbolic_result['I'],-B*L*v/R)
    equal(out.symbolic_result['F_external'],s.Matrix([B*B*L*L*v/R,0,0]))
    equal(out.symbolic_result['P_mechanical'],B*B*L*L*v*v/R)
    equal(out.symbolic_result['W'],B*B*L*L*v*distance/R)
    sub={B:1.2,L:.2,v:3.4,R:.3,distance:1.2}
    assert abs(float(out.symbolic_result['I'].subs(sub))+2.7)<.1
    assert abs(float(out.symbolic_result['F_external'][0].subs(sub))-.65)<.01
    assert abs(float(out.symbolic_result['W'].subs(sub))-.78)<.01
    assert all(c.passed for c in out.checks)

@pytest.mark.historical(ids=['2025-11:5a','2025-11:5b','2025-11:5c','2025-11:5d'],complete=True)
def test_2025_driven_rod():
    out=solve(Problem('DYN','feedback',variables={'mass':m,'R':R,'coupling':B*d,'voltage':V,'drive_force':0,
        'time':t,'initial_velocity':0,'time_bounds':[0,s.oo]},assumptions=['constant_coefficients','negligible_self_inductance','no_friction']))
    equal(out.symbolic_result['acceleration_initial'],B*d*V/(R*m))
    equal(out.symbolic_result['v_infinity'],V/(B*d))
    equal(out.symbolic_result['v'],V/(B*d)*(1-s.exp(-B*B*d*d*t/(m*R))))
    equal(out.symbolic_result['battery_energy'],m*V*V/(B*B*d*d))
    equal(out.symbolic_result['W'],m*V*V/(2*B*B*d*d))
    assert all(c.passed for c in out.checks)
    # Original PDF visually checked: the voltage is squared; text extraction loses the superscript.

@pytest.mark.historical(ids=['2023-11:5c'],complete=False)
def test_2023_falling_ring_terminal_velocity():
    area,b0,kappa,g=s.symbols('A B_0 kappa g',positive=True)
    out=solve(Problem('DYN','feedback',variables={'mass':m,'R':R,'coupling':area*b0*kappa,'voltage':0,'drive_force':m*g,
        'time':t,'initial_velocity':0},assumptions=['constant_coefficients','negligible_self_inductance','no_friction']))
    equal(out.symbolic_result['v_infinity'],m*g*R/(area*b0*kappa)**2)
    # Positive direction here is downwards; mapping to the ring's oriented flux is still manual.

@pytest.mark.historical(ids=['2026-01:2c'],complete=True)
def test_2026_RC_discharge():
    c,q0=s.symbols('C Q0',positive=True)
    out=solve(Problem('DYN','rc_transient',variables={'kind':'RC','time':t,'R':R,'C':c,'Q0':q0,'fraction':s.Rational(1,100)}))
    equal(out.symbolic_result['I'],q0/(R*c)*s.exp(-t/(R*c)))
    equal(out.symbolic_result['decay_time'],R*c*s.log(100))
    sub={R:s.Rational(1,4),c:s.Rational(91,1000),q0:s.Rational(57,10)}
    assert abs(float(out.symbolic_result['I_initial'].subs(sub))-250)<1
    assert abs(float(out.symbolic_result['decay_time'].subs(sub))-.105)<.001
    assert all(check.passed for check in out.checks)

@pytest.mark.historical(ids=['2021-11:6b','2023-02:6a'],complete=True)
def test_displacement_current():
    e0=s.Symbol('E0',positive=True)
    for field in [e0*s.sin(w*t),e0*s.cos(w*t)]:
        out=solve(Problem('DYN','ampere_maxwell',variables={'E':field,'time':t,'coordinate':a,'plate_radius':R},
            assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects']))
        equal(out.symbolic_result['I_displacement'].subs(a,R/2),s.pi*(R/2)**2*eps*s.diff(field,t))
        equal(out.symbolic_result['B'].subs(a,R/2),mu*eps*R/4*s.diff(field,t))

@pytest.mark.historical(ids=['2021-11:6c'],complete=False)
def test_induced_axial_E_correction():
    e0=s.Symbol('E0',positive=True)
    out=solve(Problem('DYN','ampere_maxwell',variables={'E':e0*s.cos(w*t),'time':t,'coordinate':a,'plate_radius':R},
        assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects','induced_correction_zero_at_edge']))
    equal(out.symbolic_result['E_correction_inside'],mu*eps*w*w*(R*R-a*a)*e0*s.cos(w*t)/4)
    assert all(c.passed for c in out.checks)
