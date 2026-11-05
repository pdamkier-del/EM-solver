import json
from em1_solver.backend import respond
from em1_solver.rendering.math_profile import validate,LatexProfileError
from em1_solver.core.solution import Solution
import pytest

def test_three_levels_reuse_the_same_ordered_derivation():
 text='En kugleskal a<r<b har rho(r)=k/r**2. V(infinity)=0. Bestem V og Q.'
 first=respond({'text':text},solve=True);second=respond({'text':text},solve=True)
 assert first['status']=='verified_with_assumptions',first
 a=first['solution'];b=second['solution']
 assert [s['id'] for s in a['steps']]==[s['id'] for s in b['steps']]
 assert len({s['id'] for s in a['steps']})==len(a['steps'])
 assert list(a['views'])==['result','derivation','explanation']
 assert a['views']['derivation']['step_ids']==[s['id'] for s in a['steps']]
 families={c['method_id'] for c in a['method_contexts'].values()}
 assert {'gauss_radial','potential_from_field'}<=families
 assert any(s['physical_reasoning'] and s['check_ids'] and s['intermediate_latex'] for s in a['steps'])
 assert all(s['method_context_id'] in a['method_contexts'] for s in a['steps'])
 json.dumps(first,allow_nan=False)

def test_field_steps_explain_the_laws_actually_applied():
 r=respond({'text':'V(x,y,z)=k*x**2. Bestem E.'},solve=True)
 assert r['status']=='verified',r
 step=r['solution']['steps'][0]
 assert step['physical_reasoning'] and step['reasoning_scope']=='step'
 context=r['solution']['method_contexts'][step['method_context_id']]
 assert context['method_id']=='field_calculus'
 assert not any(r'\mathbf B=\nabla\times\mathbf A' in eq for eq in context['equations'])
 assert any(c['name']=='Rotation af gradientfelt' and c['passed'] is True for c in r['solution']['checks'])

@pytest.mark.parametrize('bad',[r'\input{secret}',r'\href{https://example.org}{x}',r'\def\x{1}',r'\frac{x}{y',r'\begin{cases}x\end{matrix}',r'x % hidden',r'\right)'])
def test_math_profile_rejects_unsafe_or_unbalanced_tex(bad):
 with pytest.raises(LatexProfileError):validate(bad)

@pytest.mark.parametrize('good',[r'\frac{q}{4\pi\epsilon_0r^2}',r'\mathbf E=E_r\hat r',r'\int_0^R\rho(r)4\pi r^2\,dr',r'\begin{cases}x & x\geq0\\-x&x<0\end{cases}',r'\left[\begin{matrix}x\\y\\z\end{matrix}\right]'])
def test_math_profile_accepts_em1_fragments(good):assert validate(good)==good

def test_unannotated_solution_does_not_claim_a_method_context():
 from em1_solver.rendering.structured import serialize
 out=Solution('x','m','why',{},['E']);out.add('legacy algebra',1)
 rendered=serialize(out)
 assert rendered['steps'][0]['reasoning_scope']=='method' # captured from actual Solution state
 assert not rendered['steps'][0]['physical_reasoning']

def test_point_contribution_has_local_differential_checks():
 response=respond({'text':'I et kartesisk system er punktladning q1 ved (a,0,0). Bestem E i origo.'},solve=True)
 assert response['status']=='verified_with_assumptions',response
 answer=response['solution'];checks={c['id']:c for c in answer['checks']}
 steps=[step for step in answer['steps'] if step['text'].startswith('Coulomb-bidrag')]
 assert steps and all(len(step['check_ids'])==2 for step in steps)
 assert all(checks[id]['passed'] is True for step in steps for id in step['check_ids'])
