"""Structured parser ground truth, independent of numerical solver outcomes."""
import pytest,sympy as sp
from em1_solver.text_parser.normalize import normalize,math_expression
from em1_solver.text_parser import extract,analyze
from em1_solver.text_parser.units import infer_units

@pytest.mark.parametrize('raw,expected',[('ρ(s)=αs²','rho(s)=alpha*s**(2)'),('R=4,2 cm','R=4.2 cm'),('q=3 µC','q=3 uC'),('I=2.0 A','I=2.0 A'),('ρ₀','rho_0')])
def test_normalization(raw,expected):assert normalize(raw)==expected
@pytest.mark.parametrize('raw,expected',[('ks','k*s'),('2s','2*s'),('alpha s^2','alpha*s**2'),('sin(s)','sin(s)')])
def test_implicit(raw,expected):assert math_expression(raw,'s')==expected

def test_vector_labels_are_not_scalar_symbols():
    values,basis=extract.vector_formula('k*x xhat - k*y yhat + 2*k*z zhat',['x','y','z'],['k'])
    assert basis=='cartesian'
    assert [sp.sympify(v) for v in values]==[sp.sympify(v) for v in ['k*x','-k*y','2*k*z']]
    with pytest.raises(ValueError):extract.vector_formula('a xhat b yhat',[],[])

@pytest.mark.parametrize('value,unit',[('4 cm','centimeter'),('2.0 A','ampere'),('3 uC','microcoulomb'),('7 mT','millitesla'),('2 uF','microfarad'),('5 ohm','ohm'),('3 C/m**3','coulomb / meter ** 3')])
def test_numeric_units(value,unit):
    quantities,units,_,_=extract.numeric_values(extract.assignments(normalize('q='+value+' er givet.')))
    from em1_solver.core.units import si
    assert quantities['q']==value
    assert si('1 '+units['q']).dimensionality==si('1 '+unit).dimensionality
    assert si(quantities['q']).magnitude==si(value).magnitude

def test_dimensions_infer_only_unique_unknowns():
    units,missing=infer_units([('k*s**2','C/m^3')],{'s':'m'})
    assert not missing
    from em1_solver.core.units import si
    assert si('1 '+units['k'],'C/m^5')
    assert infer_units([('k*a','C')],{})[1]==['a','k']
    with pytest.raises(ValueError):infer_units([('k*s','C')],{'s':'m','k':'A'})

def test_hollow_cylinder_structural_ground_truth():
    p=analyze('En uendelig hul cylinder har rho(s)=ks for a<s<b og nul ellers. Bestem E.')
    assert p.ready
    assert p.fields['geometry'].value=='hollow_cylinder'
    assert p.fields['regions'].value==[dict(lower='0',upper='a',density='0'),dict(lower='a',upper='b',density='k*s'),dict(lower='b',upper='oo',density='0')]
    assert p.fields['orientation'].value=='radial'
    assert p.facts['orders']==[('a','b')]

def test_only_unknown_extent_is_asked():
    p=analyze('En massiv cylinder med radius R har rho(s)=k*s. Bestem E.')
    assert list(p.questions)==['extent'] and not p.ready
    assert analyze(p.original,{'extent':'infinite'}).ready
    assert not analyze(p.original,{'extent':'finite'}).ready

@pytest.mark.parametrize('text',[
 'En endelig cylinder med radius R har rho(s)=k*s. Bestem E.',
 'En uendelig cylinder med radius R har J(s)=k*s. Bestem B.',
 'En uendelig cylinder med radius R har rho(s)=k*s*cos(phi). Bestem E.',
 'En uendelig cylinder har rho(s)=k*s for a<s<b og rho(s)=h*s for b<s<c. Bestem E.',
 'En kugle med radius R har rho(r)=k*r i et eksternt felt. Bestem E.',
 'En uendelig cylinder med radius R har rho(s)=k*s og er jordet. Bestem E.',
 'V(r)=k*r**2. Bestem E.',
 'En cirkulær loop i xy-plan med radius R har B(t)=B0*t langs +z. Normalen er i +z. Bestem EMF.',
 'En endelig og en uendelig cylinder har rho(s)=k*s. Bestem E.',
 'V(x,y,z)=k*x. k=2. Bestem E.',
 'En uendelig cylinder med radius R har rho(s)=k*s. a) Bestem E. b) Bestem V.',
])
def test_abstain_instead_of_guess(text):assert not analyze(text).ready

@pytest.mark.parametrize('geometry,phrase',[(g,p) for g,p in [
 ('sphere','massiv kugle'),('spherical_shell','kugleskal'),('cylinder','uendelig cylinder'),('hollow_cylinder','hul cylinder'),('line','linjeladning'),('wire','endelig ledning'),('ring','cirkulær loop'),('arc','cirkelbue'),('disk','cirkulær skive'),('plane','uendeligt plan'),('slab','slab'),('capacitor','kondensator'),('current_sheet','strømplan'),('solenoid','solenoide'),('toroid','toroid'),('sliding_rod','stang på skinner'),('rotating_rod','roterende stang'),('point_charges','flere punktladninger')]])
def test_geometry_vocabulary(geometry,phrase):assert geometry in dict(extract.geometry(phrase))

def test_no_implicit_source_for_user_correction():
    with pytest.raises(ValueError,match='navn og argument'):analyze('Bestem E.',{'source_formula':'k*s'})

def test_proportional_constant_must_be_named():
    yes=analyze('En uendelig cylinder med radius R har ladningstætheden proportional med s² med proportionalitetskonstant k. Bestem E.')
    assert yes.ready and yes.facts['formula']=='k*s**2'
    no=analyze('En uendelig cylinder med radius R har ladningstætheden proportional med s². Bestem E.')
    assert not no.ready

def test_unit_name_is_not_a_prefix_of_symbol():
    numbers,_,_,_=extract.numeric_values(extract.assignments('V(theta)=2V0*P2(cos(theta))'))
    assert numbers=={}

@pytest.mark.parametrize('raw',['(r/R)2','__import__(x)','open(x)','x.__class__','[x for x in y]'])
def test_unsafe_or_broken_notation_is_never_ready(raw):
    p=analyze('V(x,y,z)='+raw+'. Bestem E.')
    assert not p.ready

def test_requested_density_does_not_become_given_source():
    p=analyze('I et sfærisk område med radius R er potentialet V(r)=-a*log(r/R), hvor a er en konstant. Bestem ladningstætheden rho(r).')
    assert p.ready and set(p.facts['sources'])=={'V'}

def test_units_do_not_infer_lost_exponents():
    assert not analyze('En uendelig cylinder med radius R har rho(s)=alpha*(s/R)2. Bestem E.').ready

def test_current_does_not_borrow_another_vectors_direction():
    orientation,_=extract.orientation('Strømmen er I og normalretningen er i +z.')
    assert 'current' not in orientation

def test_production_parser_has_no_dataset_io(monkeypatch):
    from pathlib import Path
    def denied(*args,**kwargs):raise AssertionError('Parseren må ikke slå op i en bank eller facit.')
    monkeypatch.setattr(Path,'read_text',denied);monkeypatch.setattr(Path,'read_bytes',denied)
    assert analyze('En uendelig cylinder med radius R har rho(s)=k*s. Bestem E.').ready

@pytest.mark.parametrize('raw',[
 'En uendelig cylinder med radius R har rho(s)=delta(s-R). Bestem E.',
 'En uendelig cylinder med radius R har J(s,t)=k*s*t zhat. Bestem B.',
 'V(x,y,z,t)=a*x*t. Bestem E.',
 'En kugle med radius R har V(R)=V0. Bestem E overalt.',
 'En uendelig cylinder med radius R(t)=a+v*t har rho(s)=k*s. Bestem E.',
])
def test_static_and_boundary_prerequisites_are_not_guessed(raw):assert not analyze(raw).ready

def test_nonstandard_cartesian_coordinate_requires_mapping():
    p=analyze('V(s)=k*s**2. Bestem E.',{'coordinate_system':'cartesian','units':'k:V/m**2; s:m'})
    assert not p.ready and 'coordinate_mapping' in p.questions

def test_an_unknown_function_is_not_silently_turned_into_a_constant():
    assert not analyze('V(x,y,z)=f(x). Bestem E.').ready

def test_prose_boundary_does_not_hide_code_suffix():
    assert not analyze('V(x,y,z)=k*x.__class__. Bestem E.').ready

@pytest.mark.parametrize('text',[
 'En uendelig cylinder med radius R og permeabilitet mu har J(s)=k*s. Strømmen går i +z. Bestem B.',
 'En ledende kugle med radius R har rho(r)=k*r. Bestem E.',
])
def test_material_laws_are_not_silently_replaced_by_free_space(text):
    p=analyze(text)
    assert not p.ready and 'boundary_model' in p.questions
