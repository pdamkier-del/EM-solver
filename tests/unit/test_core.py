import socket
import sympy as s
import pytest
from em1_solver import Problem,Region,InputError,solve
from em1_solver.core.engine import derive
from em1_solver.core.validation import EPS0 as eps, MU0 as mu,calculus
from em1_solver.core.units import si,verify_dimension
from em1_solver.core.parsing import expression
from em1_solver.examples import EXAMPLES,problem_from_spec

@pytest.fixture(autouse=True)
def prohibit_network(monkeypatch):
    def blocked(*args,**kwargs):raise AssertionError('Internet/network prohibited during offline physics test')
    monkeypatch.setattr(socket.socket,'connect',blocked)
    monkeypatch.setattr(socket.socket,'connect_ex',blocked)
    monkeypatch.setattr(socket,'create_connection',blocked)

@pytest.mark.parametrize('family',list(EXAMPLES))
def test_every_structured_example_runs_offline(family):
    out=solve(problem_from_spec(family,EXAMPLES[family]))
    assert out.symbolic_result and out.steps and out.method and out.reasoning
    assert not out.stable

@pytest.mark.parametrize('value,unit,expected',[
    ('3 cm','m',.03),('2 mm','m',.002),('5 µm','m',5e-6),('4 nC','C',4e-9),('3 µC','C',3e-6),
    ('2 mA','A',.002),('2 kA','A',2000),('3 mT','T',.003),('4 µF','F',4e-6),('91 mF','F',.091)])
def test_SI_prefixes(value,unit,expected):
    assert abs(si(value,unit).magnitude-expected)<=max(abs(expected)*1e-12,1e-18)

def test_bad_dimension_rejected():
    with pytest.raises(InputError):verify_dimension('3 cm','C')
    q=s.Symbol('q',positive=True)
    p=Problem('EV','point_charges',variables={'charges':[(q,[0,0,0])],'point':[1,0,0]},numerical_values={q:'3 cm'},numerical_units={q:'C'})
    with pytest.raises(InputError):solve(p)

@pytest.mark.parametrize('text',["__import__('os').system('true')",'x.__class__','open(1)','[x for x in x]','lambda: 1','10**1000'])
def test_parser_rejects_execution(text):
    with pytest.raises(InputError):expression(text,{'x':s.Symbol('x')})

def test_parser_exact_arithmetic():
    x=s.Symbol('x');assert expression('1/3 + sin(x)^2',{'x':x})==s.Rational(1,3)+s.sin(x)**2

def test_missing_data_and_symmetry_rejected():
    with pytest.raises(InputError):solve(Problem('BA','lorentz_force'))
    r,R=s.symbols('r R',positive=True)
    with pytest.raises(InputError):solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'cylinder'},regions=[Region(0,R,1)]))

def test_overlapping_radial_materials_rejected():
    r=s.Symbol('r',positive=True)
    with pytest.raises(InputError):solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'sphere'},regions=[Region(0,2,1),Region(1,3,1)],assumptions=['spherical_symmetry']))

def test_divergent_charge_rejected():
    r=s.Symbol('r',positive=True)
    with pytest.raises(InputError):solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'cylinder'},regions=[Region(0,1,r**-3)],assumptions=['infinite_cylindrical_symmetry']))

def test_hollow_multiregion_Gauss():
    r=s.Symbol('r',positive=True)
    out=solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'cylinder'},
        regions=[Region(1,2,3),Region(3,4,2)],assumptions=['infinite_cylindrical_symmetry']))
    assert out.symbolic_result['E'].subs(r,s.Rational(1,2))==0
    assert s.simplify(out.symbolic_result['Q_enc'].subs(r,5)-23*s.pi)==0
    assert s.simplify(out.symbolic_result['E'].subs(r,5)-s.Rational(23,10)/eps)==0

def test_planar_sheet_factor_of_two():
    r=s.Symbol('s',positive=True);sigma=s.Symbol('sigma',positive=True)
    out=solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'plane','surface_charges':[(0,sigma)]},regions=[Region(0,1,0)],assumptions=['infinite_planar_symmetry']))
    assert s.simplify(out.symbolic_result['E']-sigma/(2*eps))==0

def test_singular_charge_rejected():
    with pytest.raises(InputError):solve(Problem('EV','point_charges',variables={'charges':[(1,[0,0,0])],'point':[0,0,0]}))

def test_engine_full_induction_chain():
    t=s.Symbol('t',real=True);b,a,omega,r,T=s.symbols('b a omega R T',positive=True)
    p=Problem('DYN','faraday',variables={'B_normal':b*s.cos(omega*t),'area':a,'time':t,'N':1,'R':r,'time_bounds':[0,2*s.pi/omega]},
        assumptions=['uniform_normal_B','negligible_self_inductance'],wanted=['W'])
    out=derive(p)
    assert s.simplify(out.symbolic_result['W']-s.pi*a*a*b*b*omega/r)==0
    assert [step.text for step in out.steps]==['Homogen magnetisk flux','Faradays lov','Ohms lov','Joules lov','Integreret varme']
    assert not out.warnings

def test_engine_A_to_B_to_flux_to_EMF():
    x,y,z,u,v,t=s.symbols('x y z u v t',real=True)
    p=Problem('DYN','field_calculus',variables={'A':[-y*t/2,x*t/2,0],'coordinates':[x,y,z],'system':'cartesian',
        'surface':[u,v,0],'parameters':[u,v],'surface_bounds':[(0,1),(0,2)],'time':t,'N':1},wanted=['EMF'])
    out=derive(p)
    assert out.symbolic_result['B']==s.Matrix([0,0,t])
    assert out.symbolic_result['Phi']==2*t
    assert out.symbolic_result['EMF']==-2

def test_engine_does_not_guess_orientation_or_inductance():
    t=s.Symbol('t',real=True)
    out=derive(Problem('DYN','faraday',variables={'B_normal':t,'area':2,'time':t,'N':1,'R':1},wanted=['I']))
    assert 'Phi' not in out.symbolic_result and 'I' not in out.symbolic_result
    assert out.warnings

def test_engine_radial_density_to_external_work():
    r=s.Symbol('r',positive=True);radius,alpha,q=s.symbols('R alpha q',positive=True)
    out=derive(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'cylinder',
        'start':radius,'end':2*radius,'test_charge':q},regions=[Region(0,radius,alpha*r*r)],
        assumptions=['infinite_cylindrical_symmetry'],wanted=['W_external']))
    assert s.simplify(out.symbolic_result['W_external']+q*alpha*radius**4*s.log(2)/(4*eps))==0
    assert not out.warnings

def test_numeric_insertion_preserves_symbolic_result():
    q,a=s.symbols('q a',positive=True)
    out=solve(Problem('EV','point_charges',variables={'charges':[(q,[0,0,0])],'point':[a,0,0]},
        numerical_values={q:'3 nC',a:'2 cm'},numerical_units={q:'C',a:'m'}))
    assert out.symbolic_result['E'].free_symbols=={q,a,eps}
    assert abs(float(out.numerical_result['E'][0])-67406.6384)<.1

def test_induction_missing_circuit_assumption_rejected():
    t=s.Symbol('t')
    with pytest.raises(InputError):solve(Problem('DYN','faraday',variables={'flux':t,'time':t,'R':1}))

def test_no_silent_rounding_of_legendre_degree():
    data={'domain':'EV','variables':{'coefficients':[[2.5,'1']]}}
    with pytest.raises(InputError):problem_from_spec('laplace_legendre',data)

def test_contradictory_fields_are_not_silently_overwritten():
    x,y,z=s.symbols('x y z',real=True)
    for data in [{'V':x,'E':[1,0,0]},{'A':[0,0,0],'B':[0,0,1]}]:
        with pytest.raises(InputError):solve(Problem('EV','field_calculus',variables={'coordinates':[x,y,z],'system':'cartesian',**data}))

def test_identity_does_not_determine_an_unknown():
    x,y,z,a=s.symbols('x y z a',real=True)
    with pytest.raises(InputError):solve(Problem('EV','field_calculus',variables={'coordinates':[x,y,z],'system':'cartesian',
        'E':[0,0,0],'solve_for':a,'target_values':{'rho':0}}))

def test_unit_solver_rejects_unknown_unit():
    with pytest.raises(InputError):solve(Problem('EV','units',variables={'field_unit':'not_a_physical_unit','coordinate_power':2}))

def test_latex_export_contains_sections_and_escaped_text():
    from em1_solver.rendering.latex import document,escape
    answer=solve(problem_from_spec('gauss_radial',EXAMPLES['gauss_radial']))
    source=document(answer)
    assert r'\section*{Mellemregninger}' in source
    assert r'\boxed{' in source and source.endswith(r'\end{document}')
    assert escape('a_b & μ₀')==r'a\_b \& \ensuremath{\mu}\ensuremath{{}_0}'

def test_symbolic_region_limits_use_the_correct_side():
    from em1_solver.core.validation import regional_limit
    r,a=s.symbols('r a',positive=True)
    expr=s.Piecewise((r,r<=a),(2*r,True))
    assert regional_limit(expr,r,a,'-')==a
    assert regional_limit(expr,r,a,'+')==2*a
    assert regional_limit(expr,r,0,'+')==0
    with pytest.raises(InputError):regional_limit(expr,r,a,'+-')
