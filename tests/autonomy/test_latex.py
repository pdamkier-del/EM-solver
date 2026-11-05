import pytest
from em1_solver.text_parser import analyze,solve_text
from em1_solver.text_parser.normalize import normalize
from em1_solver.core.new_problem import symbols_for
from em1_solver.core.validation import EPS0
import sympy as s

@pytest.mark.parametrize('raw,expected',[(r'\frac{a}{b}','((a)/(b))'),(r'\frac{a}{\frac{b}{c}}','((a)/(((b)/(c))))'),(r'r^{2}','r**(2)'),(r'\hat{z}',' zhat '),(r'\mathbf{E}','E'),(r'\rho_{0}','rho_0')])
def test_explicit_latex_grammar(raw,expected):assert normalize(raw)==expected

def test_latex_reaches_the_existing_engine():
 p,a=solve_text(r'En massiv kugle med radius R har $\rho(r)=\frac{k r^{2}}{R^{2}}$. Bestem E.')
 sy=symbols_for(p.problem)
 assert s.simplify(a.symbolic_result['E'].subs(sy['r'],sy['R']/2)-sy['k']*sy['R']/(40*EPS0))==0

@pytest.mark.parametrize('raw',[r'\frac{k}{',r'\frac k r',r'\hat{q}',r'\input{secret}'])
def test_incomplete_or_executable_tex_is_not_executed(raw):
 try:p=analyze('V(x,y,z)='+raw+'. Bestem E.')
 except ValueError:return
 assert not p.ready
