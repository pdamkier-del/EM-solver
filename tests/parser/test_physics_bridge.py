"""New parser inputs, independent analytical physics assertions. Frozen oracles unchanged."""
import sympy as sp
from em1_solver.text_parser import analyze,solve_text
from em1_solver.core.new_problem import execute,symbols_for
from em1_solver.core.validation import EPS0,MU0

def answer(text,corrections=None):
    p=analyze(text,corrections);assert p.ready,{k:v.message for k,v in p.questions.items()}
    return p,execute(p.problem),symbols_for(p.problem)

def test_unicode_gauss_physics():
    p,a,s=answer('En uendelig massiv cylinder med radius R=4 cm har ρ(s)=αs². Bestem E.')
    assert sp.simplify(a.symbolic_result['E'].subs(s['s'],s['R']/2)-s['alpha']*(s['R']/2)**3/(4*EPS0))==0

def test_ampere_physics():
    _,a,s=answer('En uendelig cylinder med radius R har J(s)=k*s. Strømmen går i -z. Bestem B.')
    assert sp.simplify(a.symbolic_result['B'].subs(s['s'],s['R']/2)+MU0*s['k']*(s['R']/2)**2/3)==0

def test_gradient_physics():
    _,a,s=answer('V(x,y,z)=k*(x**2+y**2+z**2). Bestem E.')
    assert a.symbolic_result['E']==-2*s['k']*sp.Matrix([s['x'],s['y'],s['z']])

def test_faraday_normal_and_chain_rule():
    _,a,s=answer('En cirkulær loop i xy-plan med radius R har en vinding. Et homogent magnetfelt B(t)=B0*cos(omega*t) langs +z. Normalen er i -z. Bestem EMF.')
    assert sp.simplify(a.symbolic_result['EMF']+sp.pi*s['R']**2*s['B0']*s['omega']*sp.sin(s['omega']*s['t']))==0

def test_nonuniform_flux_never_reduced_to_BA():
    p=analyze('En cirkulær loop i xy-plan med radius R har en vinding. B(s,t)=beta*s*t langs +z. Normalen er i +z. Bestem EMF.')
    assert not p.ready

def test_worker_and_original_region_symbols():
    p,a=solve_text('En uendelig hul cylinder har rho(s)=ks for a<s<b og nul ellers. Bestem E.')
    assert not any('parser_gap' in str(v) for v in a.symbolic_result.values())
    assert not any(c.passed is False for c in a.checks)

def test_signed_slab_uses_both_sides_of_the_source():
    _,a,s=answer('En uendelig slab |z|<a har rho(z)=rho0*z**2. Bestem E(z) overalt.')
    assert sp.simplify(a.symbolic_result['E'].subs(s['z'],-2*s['a'])+s['rho0']*s['a']**3/(3*EPS0))==0

def test_cylindrical_vector_potential_needs_no_source_extent():
    _,a,s=answer('I cylindriske koordinater er A=A0*s**2 phihat. Bestem B.')
    assert a.symbolic_result['B']==sp.Matrix([0,0,3*s['A0']*s['s']])

def test_shell_sets_spherical_symmetry_and_restores_interval():
    p,a=solve_text('En kugleskal a<r<b har rho(r)=k/r**2. Bestem E i alle regioner.')
    assert 'spherical_symmetry' in p.problem.assumptions
    sy=symbols_for(p.problem)
    assert sp.simplify(a.symbolic_result['E'].subs(sy['r'],sy['a']/2))==0

def test_explicit_cartesian_arguments_override_body_shape():
    _,a,s=answer('I en kugle med radius R er V(x,y,z)=k*x**2. Bestem E.')
    assert a.symbolic_result['E']==sp.Matrix([-2*s['k']*s['x'],0,0])
