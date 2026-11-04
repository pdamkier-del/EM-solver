import pytest
import sympy as s
from em1_solver import Problem,solve,InputError

@pytest.mark.variation(family='magnetic_dipole_interaction')
@pytest.mark.parametrize('angle,energy,torque,state',[(0,-1,0,'stable_parallel'),(s.pi/2,0,-1,'not_equilibrium_or_symbolically_undetermined'),(s.pi,1,0,'unstable_antiparallel')])
def test_angle_dipole(angle,energy,torque,state):
 m,b=s.symbols('m b',positive=True)
 out=solve(Problem('BA','magnetic_dipole_interaction',variables={'moment_magnitude':m,'B_magnitude':b,'theta':angle},symbol_units={m:'A*m^2',b:'T'}))
 assert s.simplify(out.symbolic_result['U']-energy*m*b)==0
 assert s.simplify(out.symbolic_result['torque_theta']-torque*m*b)==0
 assert out.symbolic_result['alignment']==state
 assert all(c.passed is True for c in out.checks)

@pytest.mark.variation(family='magnetic_dipole_interaction')
@pytest.mark.parametrize('sign',[-1,1])
def test_vector_charge_independent_torque_direction(sign):
 m,b=s.symbols('m b',positive=True)
 out=solve(Problem('BA','magnetic_dipole_interaction',variables={'moment':[sign*m,0,0],'B':[0,0,b]},symbol_units={m:'A*m^2',b:'T'}))
 assert out.symbolic_result['torque']==s.Matrix([0,-sign*m*b,0]) and out.symbolic_result['U']==0

@pytest.mark.variation(family='magnetic_dipole_interaction')
def test_missing_field_rejected():
 with pytest.raises(InputError):solve(Problem('BA','magnetic_dipole_interaction',variables={'moment':[1,0,0]}))
