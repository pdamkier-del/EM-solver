import sympy as s
import pytest,json
from em1_solver.text_parser import analyze,solve_text
from em1_solver.core.new_problem import symbols_for
from em1_solver.core.validation import EPS0
from em1_solver.backend import respond

def test_gauss_to_total_charge_and_potential():
 text='En massiv kugle med radius R har rho(r)=k*r**2. Potentialet sættes til nul i det uendeligt fjerne. Bestem E, V og den totale ladning Q.'
 p,a=solve_text(text);sy=symbols_for(p.problem);r,R,k=[sy[n] for n in ('r','R','k')]
 assert s.simplify(a.symbolic_result['Q']-4*s.pi*k*R**5/5)==0
 assert s.simplify(a.symbolic_result['V'].subs(r,R/2)-k*(R**4/4-(R/2)**4/20)/EPS0)==0
 assert s.simplify(a.symbolic_result['V'].subs(r,2*R)-k*R**4/(10*EPS0))==0
 assert not any(c.passed is False for c in a.checks)

def test_missing_reference_blocks_potential_chain():
 p=analyze('En massiv kugle med radius R har rho(r)=k*r. Bestem V.')
 assert not p.ready and 'potential_reference' in p.questions

def test_hollow_spherical_potential_is_continuous():
 p,a=solve_text('En kugleskal a<r<b har rho(r)=k/r**2. V(infinity)=0. Bestem V og Q.')
 assert not any(c.passed is False for c in a.checks)
 assert all('parser_gap' not in str(v) for v in a.symbolic_result.values())

def test_total_current_comes_from_integral():
 p,a=solve_text('En uendelig cylinder med radius R har J(s)=k*s zhat. Bestem den totale strøm I og B.')
 sy=symbols_for(p.problem)
 assert s.simplify(a.symbolic_result['I']-2*s.pi*sy['k']*sy['R']**3/3)==0

def test_frontend_json_contract_has_no_sympy_objects():
 r=respond(dict(schema_version='1.0',text='V(x,y,z)=k*x**2. Bestem E.'),solve=True)
 assert r['status']=='verified'
 assert r['solution']['results']['E']['latex']
 json.dumps(r,allow_nan=False)

def test_unresolved_contract_is_not_verified():
 r=respond(dict(text='En cylinder med radius R har rho(s)=k*s. Bestem E.'),solve=True)
 assert r['status']=='not_solved' and r['solution'] is None and r['missing']

def test_ampere_maxwell_prerequisites_and_displacement_chain():
 text='En kondensator har cirkulære plader med radius R. E(t)=E0*t**2 zhat er uniformt mellem pladerne. Randeffekter ignoreres. Bestem forskydningsstrøm og B(s,t).'
 p,a=solve_text(text);sy=symbols_for(p.problem)
 assert s.simplify(a.symbolic_result['I_displacement'].subs(sy['s'],sy['R']/2)-EPS0*2*sy['E0']*sy['t']*s.pi*sy['R']**2/4)==0
 assert not analyze(text.replace('Randeffekter ignoreres.','')).ready
 assert not analyze(text.replace('uniformt','ikke-homogent')).ready

def test_free_charge_integral_needs_no_dielectric_constitutive_law():
 text='En kugle med radius R består af et lineært dielektrikum med relativ permittivitet epsilon_r. Den frie ladningstæthed er rho(r)=k*r. Bestem den totale frie ladning Q.'
 p,a=solve_text(text);sy=symbols_for(p.problem)
 assert set(a.symbolic_result)=={'Q'}
 assert s.simplify(a.symbolic_result['Q']-s.pi*sy['k']*sy['R']**4)==0
 # The same evidence does not determine E via a vacuum substitution.
 assert not analyze(text.replace('den totale frie ladning Q','E')).ready

def test_compound_radius_is_not_truncated_to_first_symbol():
 assert not analyze('En kugle med radius R/2 har rho(r)=k*r. Bestem E.').ready

def test_relative_permittivity_has_dimensionless_role():
 p=analyze('En kugle med radius R har relativ permittivitet epsilon_r=4.2. rho(r)=k*r. Bestem den totale frie ladning Q.')
 assert p.facts['units']['epsilon_r']=='1'
 assert p.facts['numbers']['epsilon_r']=='4.2 dimensionless'

@pytest.mark.parametrize('payload',[{'schema_version':'2.0','text':'x'},{'text':[]},{'text':'Bestem E.','corrections':{'units':{}}},{'text':'Bestem E.','evaluate_integrals':'false'}])
def test_contract_rejects_invalid_types(payload):
 result=respond(payload,solve=True)
 assert result['status']=='not_solved' and result['errors']
 json.dumps(result,allow_nan=False)

def test_dataset_ids_and_gold_cannot_enter_the_contract():
 assert respond({'text':'Bestem E.','id':'arbitrary'})['errors']
 assert respond({'text':'Bestem E.','gold':'0'})['errors']
