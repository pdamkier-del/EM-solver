import pytest,sympy as s
from em1_solver.text_parser import analyze,solve_text
from em1_solver.core.new_problem import symbols_for
from em1_solver.core.validation import EPS0
from em1_solver.backend import respond

TEXT='En kugle med radius R består af et lineært isotropt dielektrikum med relativ permittivitet epsilon_r. Den frie ladningstæthed er rho(r)=k*r. Der er vakuum udenfor. Bestem D, E og polarisationen P.'

def test_free_charge_to_D_to_E_to_P_uses_the_given_medium():
 p,a=solve_text(TEXT);sy=symbols_for(p.problem);r,R,k,er=[sy[n] for n in ('r','R','k','epsilon_r')]
 at=R/2;D=k*at**2/4
 assert s.simplify(a.symbolic_result['D'].subs(r,at)-D)==0
 assert s.simplify(a.symbolic_result['E'].subs(r,at)-D/(EPS0*er))==0
 assert s.simplify(a.symbolic_result['P'].subs(r,at)-D*(1-1/er))==0
 assert s.simplify(a.symbolic_result['E'].subs(r,2*R)-k*R**2/(16*EPS0))==0
 assert a.symbolic_result['P'].subs(r,2*R)==0

@pytest.mark.parametrize('missing',['lineært','isotropt','frie','Der er vakuum udenfor.','med relativ permittivitet epsilon_r'])
def test_missing_material_conditions_block_automatic_substitution(missing):assert not analyze(TEXT.replace(missing,'')).ready

def test_contradictory_material_is_not_an_ordinary_dielectric_solution():
 p=analyze(TEXT.replace('epsilon_r.','epsilon_r=-2.'))
 assert not p.ready

def test_frontend_sees_the_constitutive_model_and_actual_polarization_step():
 result=respond(dict(text=TEXT),solve=True)
 assert result['status']=='verified_with_assumptions',result
 model=result['interpretation']['model']['objects'][0]['material']
 assert model['permittivity']=='epsilon_0*epsilon_r'
 assert any(step['law']=='Definition af polarisation' and step['physical_reasoning'] for step in result['solution']['steps'])

def test_material_potential_and_polarization_chain_has_consistent_bounds():
 text=TEXT.replace('Bestem D, E og polarisationen P.','V(infinity)=0. Bestem D, E, P og V.')
 p,a=solve_text(text)
 assert {'D','E','P','V'}<=set(a.symbolic_result)
 assert all(c.passed is not False for c in a.checks)
 assert any(c.name.startswith('Potentialkontinuitet') and c.passed is True for c in a.checks)
