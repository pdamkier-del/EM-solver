import pytest,sympy as s
from em1_solver.core.problem import Problem,InputError
from em1_solver.core.registry import solve
from em1_solver.core.validation import MU0

def setup():
 x,y,z,t,k=s.symbols('x y z t k',real=True)
 return (x,y,z,t,k),dict(coordinates=[x,y,z],system='cartesian',B=[0,k*x,0])

def test_stationary_current_has_independent_continuity_check():
 (x,y,z,t,k),data=setup()
 out=solve(Problem('BA','field_calculus',variables=data,wanted=['J'],assumptions=['magnetostatic'],symbol_units={x:'m',y:'m',z:'m',k:'T/m'}))
 assert out.symbolic_result['J']==s.Matrix([0,0,k/MU0])
 check=next(c for c in out.checks if c.name.startswith('Statisk strømbevarelse'))
 assert check.passed is True and check.step_id

@pytest.mark.parametrize('factor',[1,2])
def test_given_current_is_not_silently_overwritten(factor):
 (x,y,z,t,k),data=setup();data['J']=[0,0,factor*k/MU0]
 p=Problem('BA','field_calculus',variables=data,wanted=['J'],assumptions=['magnetostatic'])
 if factor==1:assert solve(p).symbolic_result['J']==s.Matrix([0,0,k/MU0])
 else:
  with pytest.raises(InputError,match='Givet J og B'):solve(p)

def test_explicit_time_dependence_cannot_be_labelled_magnetostatic():
 (x,y,z,t,k),data=setup();data.update(B=[0,k*x*t,0],time=t)
 with pytest.raises(InputError,match='ikke verificeret magnetostatisk'):solve(Problem('BA','field_calculus',variables=data,wanted=['J'],assumptions=['magnetostatic']))

def test_no_static_assumption_is_invented_for_a_given_dynamic_B():
 (x,y,z,t,k),data=setup();data.update(B=[0,k*x*t,0],time=t)
 out=solve(Problem('BA','field_calculus',variables=data,wanted=['B']))
 assert 'J' not in out.symbolic_result
 assert not any(c.name.startswith('Statisk strømbevarelse') for c in out.checks)

def test_cylindrical_continuity_uses_metric_factors():
 r,phi,z,k=s.symbols('s phi z k',positive=True)
 out=solve(Problem('BA','field_calculus',variables=dict(coordinates=[r,phi,z],system='cylindrical',A=[0,k*r**2,0]),wanted=['B','J'],assumptions=['magnetostatic'],symbol_units={r:'m',phi:'1',z:'m',k:'T/m'}))
 assert out.symbolic_result['J']==s.Matrix([0,-3*k/MU0,0])
 assert next(c for c in out.checks if c.name.startswith('Statisk strømbevarelse')).passed is True
