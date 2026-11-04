import sympy as s
import pytest
from em1_solver import Problem,solve
from em1_solver.core.validation import MU0 as mu
from .test_fields import equal

radial,R,I,J=s.symbols('s R I J',positive=True)
phi,z=s.symbols('phi z',real=True);c=s.Symbol('C',real=True)

@pytest.mark.historical(ids=['2022-02:7a','2022-02:7b'],complete=True)
def test_2022_vector_potential_poisson_and_matching():
    inside=solve(Problem('BA','field_calculus',variables={'coordinates':[radial,phi,z],'system':'cylindrical',
        'A':[0,0,-mu*I*radial**2/(4*s.pi*R*R)]},assumptions=['magnetostatic']))
    outside=solve(Problem('BA','field_calculus',variables={'coordinates':[radial,phi,z],'system':'cylindrical',
        'A':[0,0,c*s.log(radial/R)-mu*I/(4*s.pi)]},assumptions=['magnetostatic']))
    equal(inside.symbolic_result['div_A'],0);equal(outside.symbolic_result['div_A'],0)
    equal(inside.symbolic_result['laplacian_A'],s.Matrix([0,0,-mu*I/(s.pi*R*R)]))
    equal(outside.symbolic_result['laplacian_A'],s.zeros(3,1))
    equal(inside.symbolic_result['B'],s.Matrix([0,mu*I*radial/(2*s.pi*R*R),0]))
    equal(outside.symbolic_result['B'],s.Matrix([0,-c/radial,0]))
    match=solve(Problem('BA','field_calculus',variables={'coordinates':[radial,phi,z],'system':'cylindrical',
        'A':[0,0,c*s.log(radial/R)-mu*I/(4*s.pi)],'at':{radial:R},'solve_for':c,
        'target_values':{'B':s.Matrix([0,mu*I/(2*s.pi*R),0])}},assumptions=['magnetostatic']))
    equal(match.symbolic_result['solved_C'],-mu*I/(2*s.pi))
    equal(match.symbolic_result['solved_C'].subs(I,s.pi*R*R*J),-mu*R*R*J/2)

@pytest.mark.historical(ids=['2023-02:4b'],complete=True)
def test_2023_current_through_tilted_disk():
    x,y=s.symbols('x y',real=True);k=s.Symbol('k',positive=True)
    field=solve(Problem('BA','field_calculus',variables={'coordinates':[x,y,z],'system':'cartesian','A':[3*k*z*y,-2*k*z*y,k*z*z]},assumptions=['magnetostatic']))
    # The same oriented surface integral used for magnetic flux applies to current density.
    r,u=s.symbols('r u',real=True)
    normal=s.Matrix([1,1,-1])/s.sqrt(3)
    e1=s.Matrix([1,-1,0])/s.sqrt(2);e2=normal.cross(e1)
    surface=r*s.cos(u)*e1+r*s.sin(u)*e2
    out=solve(Problem('BA','ampere',variables={'kind':'current_surface','surface':surface,'parameters':[r,u],
        'bounds':[[0,R],[0,2*s.pi]],'J_on_surface':field.symbolic_result['J']}))
    equal(out.symbolic_result['I_enc'],2*k*s.pi*R*R/(s.sqrt(3)*mu))
