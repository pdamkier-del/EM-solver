import sympy as s
import pytest
from em1_solver import Problem,solve
from em1_solver.core.validation import EPS0 as eps
from .test_fields import equal

r,a,Q,er=s.symbols('r a Q epsilon_r',positive=True)
q=s.Symbol('q_unknown',real=True)

@pytest.mark.historical(ids=['2025-11:3a','2025-11:3b'],complete=True)
def test_2025_zero_inner_sphere_potential():
    for relative,expected in [(1,-Q/2),(er,-er*Q/(1+er))]:
        out=solve(Problem('EV','conductors',variables={'coordinate':r,'shells':[(0,a,q),(2*a,2*a,Q)],
            'gap_permittivities':[eps,eps*relative]},assumptions=['concentric_spheres','electrostatic']))
        potential_at_inner=out.symbolic_result['V'].subs(r,a)
        # Use the generic inverse-result machinery on the actual evaluated conductor potential.
        inverse=solve(Problem('EV','conductors',variables={'coordinate':a,'shells':[(0,a,q),(2*a,2*a,Q)],
            'gap_permittivities':[eps,eps*relative],'solve_for':q,'target_values':{'V':0}},assumptions=['concentric_spheres','electrostatic']))
        equal(inverse.symbolic_result['solved_q_unknown'],expected)
        equal(potential_at_inner.subs(q,expected),0)

@pytest.mark.historical(ids=['2023-11:4a','2023-11:4b','2023-11:4c'],complete=True)
def test_2023_sphere_half_immersed_in_dielectric():
    e1,e2,R=s.symbols('epsilon_1 epsilon_2 R',positive=True)
    out=solve(Problem('EV','conductors',variables={'kind':'spherical_sectors','charge':Q,'radius':R,'coordinate':r,
        'sectors':[(2*s.pi,e1),(2*s.pi,e2)]},assumptions=['radial_dielectric_interfaces','electrostatic','no_external_sources']))
    equal(out.symbolic_result['D_0']/out.symbolic_result['D_1'],e1/e2)
    equal(out.symbolic_result['sigma_free_0']/out.symbolic_result['sigma_free_1'],e1/e2)
    equal(out.symbolic_result['sigma_free_0'],Q*e1/(2*s.pi*R*R*(e1+e2)))
    equal(out.symbolic_result['E'],Q/(2*s.pi*(e1+e2)*r*r))
    assert all(c.passed for c in out.checks)
    assert 'entydighed' in out.reasoning
