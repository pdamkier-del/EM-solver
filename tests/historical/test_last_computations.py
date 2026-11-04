import sympy as s
import pytest
from em1_solver import Problem,solve
from em1_solver.core.validation import EPS0 as eps,MU0 as mu
from .test_fields import equal

r,R,rho,b,h,omega,A,B0,kappa,m,g,res,V0,d=s.symbols('r R rho b h omega A B0 kappa m g R_res V0 d',positive=True)
theta,z,u,t=s.symbols('theta z u t',real=True)

@pytest.mark.historical(ids=['2021-11:6a'],complete=True)
def test_2021_capacitor_field_direction():
    out=solve(Problem('EV','capacitance',variables={'kind':'parallel_plates','epsilon':eps,'area':s.pi*R*R,
        'distance':d,'V':V0*s.cos(omega*t),'normal':[0,0,1]},assumptions=['negligible_edge_effects']))
    equal(out.symbolic_result['E_vector'],s.Matrix([0,0,V0*s.cos(omega*t)/d]))

@pytest.mark.historical(ids=['2021-11:6c'],complete=True)
def test_2021_correction_and_frequency_limit():
    e0=s.Symbol('E0',positive=True)
    out=solve(Problem('DYN','ampere_maxwell',variables={'E':e0*s.cos(omega*t),'time':t,'coordinate':r,'plate_radius':R,
        'at':{r:0,t:0},'solve_for':omega,'target_values':{'E_correction_inside':e0/100}},
        assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects','induced_correction_zero_at_edge']))
    wlimit=out.symbolic_result['solved_omega']
    equal(wlimit,1/(5*R*s.sqrt(mu*eps)))
    frequency=wlimit/(2*s.pi)
    actual=frequency.subs({R:s.Rational(1,100),mu:s.Float('1.25663706212e-6'),eps:s.Float('8.8541878128e-12')})
    assert abs(float(actual)-.95e9)<.01e9

@pytest.mark.historical(ids=['2022-02:4a'],complete=True)
def test_2022_total_current_with_bore():
    J=s.Symbol('J',positive=True)
    # One single polar surface with a piecewise signed density represents the actual conductor area.
    j=s.Piecewise((0,r<R/2),(J,True))
    # Translation of the circular hole does not change its area, so total current is area-based.
    out=solve(Problem('BA','ampere',variables={'kind':'current_surface','surface':[r*s.cos(theta),r*s.sin(theta),0],
        'parameters':[r,theta],'bounds':[[0,R],[0,2*s.pi]],'J_on_surface':[0,0,j]}))
    equal(out.symbolic_result['I_enc'],s.Rational(3,4)*s.pi*R*R*J)

@pytest.mark.historical(ids=['2022-11:4a','2022-11:4b'],complete=True)
def test_2022_rotating_ring_and_disk_moments():
    out=solve(Problem('BA','multipole',variables={'charges':[],'transported_charge':rho*2*s.pi*R*b*h,
        'period':2*s.pi/omega,'area':s.pi*R*R,'normal':[0,0,1]}))
    equal(out.symbolic_result['circulation_current'],rho*omega*b*h*R)
    equal(out.symbolic_result['magnetic_dipole'],s.Matrix([0,0,s.pi*rho*omega*b*h*R**3]))
    # Full disk: m=1/2 integral r cross J dV, J=rho omega (z-hat cross r).
    pos=s.Matrix([r*s.cos(theta),r*s.sin(theta),z]);current=rho*omega*s.Matrix([-r*s.sin(theta),r*s.cos(theta),0])
    disk=solve(Problem('BA','multipole',variables={'charges':[],'position':pos,'current_density':current,'jacobian':r,
        'bounds':[(r,0,R),(theta,0,2*s.pi),(z,-h/2,h/2)]}))
    equal(disk.symbolic_result['magnetic_dipole'],s.Matrix([0,0,s.pi*rho*omega*h*R**4/4]))

@pytest.mark.historical(ids=['2023-11:5a','2023-11:5b','2023-11:5c','2023-11:5d'],complete=True)
def test_2023_falling_ring_both_gradient_signs():
    v=s.Symbol('v',positive=True)
    for sign in [-1,1]:
        out=solve(Problem('DYN','faraday',variables={'time':t,'B_normal':B0*(1+sign*kappa*v*t),'area':A,'R':res},
            assumptions=['uniform_normal_B','negligible_self_inductance']))
        equal(out.symbolic_result['EMF'],-sign*A*B0*kappa*v)
        equal(out.symbolic_result['P'],(A*B0*kappa*v)**2/res)
        motion=solve(Problem('DYN','feedback',variables={'mass':m,'R':res,'coupling':sign*A*B0*kappa,
            'voltage':0,'drive_force':m*g,'time':t,'initial_velocity':0},
            assumptions=['constant_coefficients','negligible_self_inductance','no_friction']))
        equal(motion.symbolic_result['v_infinity'],m*g*res/(A*B0*kappa)**2)
        assert all(check.passed for check in motion.checks)
        # Same mechanical damping and Joule heat; opposite current when the field gradient reverses.
        equal(motion.symbolic_result['I'],-sign*A*B0*kappa*motion.symbolic_result['v']/res)
