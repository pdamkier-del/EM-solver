import sympy as s
from em1_solver.text_parser import analyze,solve_text
from em1_solver.core.new_problem import symbols_for
from em1_solver.core.validation import EPS0
from em1_solver.backend import respond

def test_two_objects_field_superposition():
 text='I et kartesisk system sidder punktladning q1 ved (-a,0,0); punktladning q2 ved (a,0,0). Bestem E og V i origo.'
 p,a=solve_text(text);sy=symbols_for(p.problem);distance=sy['a']
 assert len([o for o in p.facts['scene']['objects'] if o['kind']=='point_charge'])==2
 assert any(o['kind']=='observation_point' for o in p.facts['scene']['objects'])
 assert s.simplify(a.symbolic_result['E'][0]-(sy['q1']-sy['q2'])*distance/(4*s.pi*EPS0*s.Abs(distance)**3))==0
 assert s.simplify(a.symbolic_result['V']-(sy['q1']+sy['q2'])/(4*s.pi*EPS0*s.Abs(distance)))==0

def test_pair_energy_needs_no_invented_field_point():
 p,a=solve_text('I et kartesisk system er punktladning q1 ved (0,0,0); punktladning q2 ved (d,0,0). Beregn systemets energi U.')
 sy=symbols_for(p.problem)
 assert 'point' not in p.problem.data['solver_spec']['variables']
 assert set(a.symbolic_result).isdisjoint({'E','V'})
 assert s.simplify(a.symbolic_result['U']-sy['q1']*sy['q2']/(4*s.pi*EPS0*s.Abs(sy['d'])))==0

def test_force_on_source_excludes_self_field():
 p,a=solve_text('I et kartesisk system er punktladning q1 ved (0,0,0); punktladning q2 ved (d,0,0). Bestem kraften på q1.')
 sy=symbols_for(p.problem)
 assert s.simplify(a.symbolic_result['F'][0]+sy['q1']*sy['q2']*sy['d']/(4*s.pi*EPS0*s.Abs(sy['d'])**3))==0

def test_scene_abstains_if_any_source_or_frame_is_missing():
 for text in [
  'I et kartesisk system er punktladning q1 ved (a,0,0); punktladning q2 et ukendt sted. Find E i origo.',
  'En punktladning q1 er ved (a,0,0). Find E i origo.',
  'I et kartesisk system er to punktladninger placeret som på figuren. Find E i origo.',
  'I et kartesisk system er punktladning q1 ved (a,0,0). Find E først i origo og derefter i punktet (0,0,z).'
 ]:assert not analyze(text).ready

def test_sdk_scene_is_serializable_and_keeps_all_objects():
 import json
 r=respond(dict(text='I et kartesisk system er punktladning q1 ved (a,0,0); punktladning q2 ved (0,b,0). Bestem E i origo.'),solve=True)
 assert r['status']=='verified_with_assumptions',r
 assert len(r['interpretation']['model']['objects'])==3
 assert len(r['interpretation']['model']['sources'])==2
 json.dumps(r)

def test_numeric_source_at_explicit_origin_uses_si_values():
 import math
 r=respond(dict(text='I et kartesisk system er punktladning q1=3 nC i origo. d=2 cm. Bestem E i punktet (d,0,0).'),solve=True)
 assert r['status']=='verified_with_assumptions',r
 value=r['solution']['numerical']['E']['value']
 # Directly verify a numeric field through the actual engine, not text rendering.
 from em1_solver.text_parser import solve_text
 _,answer=solve_text('I et kartesisk system er punktladning q1=3 nC i origo. d=2 cm. Bestem E i punktet (d,0,0).')
 actual=float(answer.numerical_result['E'][0])
 from em1_solver.core.units import CONSTANTS
 expected=3e-9/(4*math.pi*CONSTANTS['epsilon_0']*.02**2)
 assert math.isclose(actual,expected,rel_tol=1e-10)


def test_source_modifiers_and_symbolic_bindings_are_not_ignored():
 for clause in ['q1+q2 ved (a,0,0)','q1=2*q2 ved (a,0,0)','q1 bevæger sig i (a,0,0)','q1 ved (v*t,0,0)']:
  assert not analyze('I et kartesisk system er punktladning '+clause+'. Find E i origo.').ready

def test_source_budget_does_not_truncate_the_scene():
 text='I et kartesisk system er '+ '; '.join(f'punktladning q{i} ved ({i},0,0)' for i in range(17))+'. Bestem E i origo.'
 p=analyze(text)
 assert not p.ready and 'source_budget' in p.questions

def test_concrete_values_cannot_violate_symbolic_geometry_conditions():
 for text in [
  'I et kartesisk system er punktladning q1 ved (0,0,0); punktladning q2 ved (d,0,0). d=0 cm. Bestem kraften på q1.',
  'I et kartesisk system er punktladning q1 i origo. d=0 cm. Bestem E i punktet (d,0,0).',
  'I et kartesisk system er punktladning q1 ved (sqrt(a),0,0). a=-1 m**2. Bestem E i origo.'
 ]:
  result=respond(dict(text=text),solve=True)
  assert result['status']=='not_solved' and result['errors'],result
