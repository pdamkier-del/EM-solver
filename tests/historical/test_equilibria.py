import sympy as s
import pytest
from em1_solver import Problem,solve
from em1_solver.core.validation import EPS0 as eps
from .test_fields import equal

@pytest.mark.historical(ids=['2023-11:1a','2023-11:1b','2023-11:1c'],complete=True)
def test_2023_line_and_square_equilibria_and_energy():
    a,q=s.symbols('a q',positive=True);Q=s.Symbol('Q_unknown',real=True);ke=1/(4*s.pi*eps)
    configs=[
        ([(q,[-a/2,0,0]),(Q,[0,0,0]),(q,[a/2,0,0])],-q/4,ke*q/a*(4*Q+q)),
        ([(q,[-a/2,-a/2,0]),(q,[a/2,-a/2,0]),(q,[a/2,a/2,0]),(q,[-a/2,a/2,0]),(Q,[0,0,0])],
         -(2*s.sqrt(2)+1)*q/4,ke*q/a*(4*s.sqrt(2)*Q+(4+s.sqrt(2))*q)),
    ]
    for charges,expectedQ,expectedU in configs:
        out=solve(Problem('EV','point_charges',variables={'charges':charges,'force_on_index':0,'solve_for':Q,
            'target_values':{'F':s.zeros(3,1)},'substitute_results':['F','U']},assumptions=['free_point_charges_3D']))
        equal(out.symbolic_result['solved_Q_unknown'],expectedQ)
        equal(out.symbolic_result['U'],expectedU)
        equal(out.symbolic_result['at_solution_U'],0)
        equal(out.symbolic_result['at_solution_F'],s.zeros(3,1))
        assert out.symbolic_result['equilibrium_stability']=='unstable_if_unconstrained_3D'
        assert any('Earnshaw' in w for w in out.warnings)
        # Verify every force, including the central charge, after substitution.
        for idx in range(len(charges)):
            final=[(qval.subs(Q,expectedQ) if hasattr(qval,'subs') else qval,pos) for qval,pos in charges]
            one=solve(Problem('EV','point_charges',variables={'charges':final,'force_on_index':idx}))
            equal(one.symbolic_result['F'],s.zeros(3,1))
