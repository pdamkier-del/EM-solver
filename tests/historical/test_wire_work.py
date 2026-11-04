import sympy as s
import pytest
from em1_solver import Problem,solve
from em1_solver.core.validation import MU0 as mu
from .test_fields import equal

@pytest.mark.historical(ids=['2024-02:3a','2024-02:3b'],complete=True)
def test_2024_rectangular_loop_force_and_work():
    u,x,y,z=s.symbols('u x y z',real=True)
    a,b,d,i1,i2=s.symbols('a b d I1 I2',positive=True)
    paths=[{'source':[b-u,d,0],'parameter':u,'bounds':[0,b]},
           {'source':[0,d+u,0],'parameter':u,'bounds':[0,a]},
           {'source':[u,d+a,0],'parameter':u,'bounds':[0,b]},
           {'source':[b,d+a-u,0],'parameter':u,'bounds':[0,a]}]
    out=solve(Problem('BA','wire_force',variables={'paths':paths,'I':i2,'B':[0,0,mu*i1/(2*s.pi*y)],
        'field_coordinates':[x,y,z],'work_coordinate':d,'work_bounds':[d,d/5],'displacement_tangent':[0,1,0]}))
    equal(out.symbolic_result['F'],s.Matrix([0,mu*i1*i2*a*b/(2*s.pi*d*(d+a)),0]))
    equal(out.symbolic_result['W_external'],mu*b*i1*i2/(2*s.pi)*s.log((d/5+a)/(s.Rational(1,5)*(d+a))))
    sub={a:.24,b:.38,d:.14,i1:15,i2:1.8,mu:s.Float('1.25663706212e-6')}
    assert abs(float(out.symbolic_result['magnitude'].subs(sub))-9.3e-6)<.1e-6
    assert abs(float(out.symbolic_result['W_external'].subs(sub))-2.6e-6)<.1e-6
    assert out.symbolic_result['F'][1].is_positive

@pytest.mark.historical(ids=['2024-02:5c'],complete=True)
def test_2024_triangular_rod_reaction_force():
    t,B,v,rl=s.symbols('t B v r_line',positive=True);u=s.Symbol('u',real=True)
    out=solve(Problem('DYN','motional_emf',variables={'source':[v*t,u,0],'parameter':u,
        'bounds':[-v*t/s.sqrt(3),v*t/s.sqrt(3)],'v':[v,0,0],'B':[0,0,-B],'time':t,
        'R':2*s.sqrt(3)*rl*v*t},assumptions=['negligible_self_inductance','stationary_return_path']))
    equal(out.symbolic_result['F_external'],s.Matrix([2*B*B*v*v*t/(3*s.sqrt(3)*rl),0,0]))
    assert all(check.passed for check in out.checks)
