"""Original nonhistorical cases: changed functions, topology, sources and workflows.
Expected results are derived independently here, not frozen solver outputs.
"""
import pytest
import sympy as s
from em1_solver.core.new_problem import parse,execute,build,Parsed
from em1_solver.core.problem import InputError
from em1_solver.core.validation import EPS0,MU0
from em1_solver.core.dimensions import check_solution
from em1_solver.rendering.plain import text
from em1_solver.rendering.latex import document


def eq(a,b):
    delta=s.simplify(a-b)
    assert all(v.equals(0) for v in delta) if isinstance(delta,s.MatrixBase) else delta.equals(0)


def prepared(description,known,wanted,units,positive,assumptions,extra=None):
    p=parse(description,known,wanted=wanted)
    p.units.update(units);p.positive=positive;p.assumptions=assumptions
    if extra:p.data.update(extra)
    return p

CASES=[]
def case(id,parsed,expected,family):CASES.append((id,parsed,expected,family))

# Nonmonomial densities and several independently specified radial regions.
for name,sym,geom,extent,power in [('cyl_mixed','cylinder','cylinder','uendelig',2),('sphere_mixed','sphere','kugle','',3),('cyl_quartic','cylinder','cylinder','uendelig',4),('sphere_linear','sphere','kugle','',1)]:
    coord='s' if sym=='cylinder' else 'r';k=power+3
    p=prepared(f'En {extent} {geom} med radius a. Find det elektriske felt.',f'rho({coord}) = rho0*(1+({coord}/a)**{power})', ['E'],{coord:'m','a':'m','rho0':'C/m^3'},[coord,'a'],['infinite_cylindrical_symmetry' if sym=='cylinder' else 'spherical_symmetry'])
    p.data['radius']='a';q=build(p);r=q.variables['coordinate'];a=next(x for x in q.symbol_units if str(x)=='a');rho=next(x for x in q.symbol_units if str(x)=='rho0')
    denom=2 if sym=='cylinder' else 3
    case(name,p,('E',rho*(r/denom+r**(power+1)/((power+denom)*a**power))/EPS0,{r:a/3}), 'gauss_radial')

for name,geometry,density in [('hollow_charge','cylinderskal','rho0*(s/a)**2'),('hollow_current','cylinderskal','J0*(1+s/a)')]:
    current='current' in name;source='J' if current else 'rho';unit='A/m^2' if current else 'C/m^3'
    p=prepared('En uendelig hul cylinder.',f'{source}(s) = {density}', ['B' if current else 'E'],{'s':'m','a':'m','J0' if current else 'rho0':unit},['s','a'],['infinite_cylindrical_symmetry']+(['magnetostatic'] if current else []),{'regions':[{'lower':'a','upper':'3*a','density':density}]})
    q=build(p);r=q.variables['coordinate'];a=next(x for x in q.symbol_units if str(x)=='a')
    case(name,p,('B' if current else 'E',s.S.Zero,{r:a/2}),'ampere' if current else 'gauss_radial')

for n in [1,2,4]:
    p=prepared('En uendelig cylinder med radius a og aksial strøm.',f'J(s) = J0*(s/a)**{n}', ['B'],{'s':'m','a':'m','J0':'A/m^2'},['s','a'],['infinite_cylindrical_symmetry','magnetostatic'],{'radius':'a'})
    q=build(p);r=q.variables['coordinate'];a=next(x for x in q.symbol_units if str(x)=='a');j=next(x for x in q.symbol_units if str(x)=='J0')
    case('current_power_'+str(n),p,('B',MU0*j*r**(n+1)/((n+2)*a**n),{r:a/4}),'ampere')

for n in [2,3,5]:
    p=prepared('Bestem det elektriske felt fra potentialet.',f'V = V0*((x/a)**{n} + y*z/a**2)\ncoordinates = [x,y,z]', ['E'],{'V0':'V','a':'m','x':'m','y':'m','z':'m'},['a'],['electrostatic'])
    q=build(p);x,y,z=q.variables['coordinates'];a=next(x for x in q.symbol_units if str(x)=='a');v=next(x for x in q.symbol_units if str(x)=='V0')
    case('mixed_potential_'+str(n),p,('E',s.Matrix([-n*v*x**(n-1)/a**n,-v*z/a**2,-v*y/a**2]),{}),'field_calculus')

for sign in [1,-1]:
    p=prepared('Tre punktladninger. Find det elektriske felt.',f'charges = [[q,[a,0,0]],[{sign}*2*q,[0,2*a,0]],[-q,[0,0,3*a]]]\npoint = [0,0,0]', ['E'],{'q':'C','a':'m'},['a'],[])
    q=build(p);a=next(x for x in q.symbol_units if str(x)=='a');charge=next(x for x in q.symbol_units if str(x)=='q')
    case('three_noncollinear_'+str(sign),p,('E',charge/(4*s.pi*EPS0*a*a)*s.Matrix([-1,-sign*s.Rational(1,2),s.Rational(1,9)]),{}),'point_charges')

for n in [2,3]:
    p=prepared('Bestem magnetfelt fra vektorpotentiale.',f'A = [0,0,A0*(x/a)**{n}*y/a]\ncoordinates = [x,y,z]', ['B'],{'A0':'T*m','a':'m','x':'m','y':'m','z':'m'},['a'],[])
    q=build(p);x,y,z=q.variables['coordinates'];a=next(x for x in q.symbol_units if str(x)=='a');v=next(x for x in q.symbol_units if str(x)=='A0')
    case('curl_cross_polynomial_'+str(n),p,('B',s.Matrix([v*x**n/a**(n+1),-n*v*x**(n-1)*y/a**(n+1),0]),{}),'field_calculus')

# The general fallback is tested as an exact unevaluated physics relation.
for id,source,bounds in [('ellipse','[a*cos(u),2*a*sin(u),0]','[0,2*pi]'),('helix','[a*cos(u),a*sin(u),a*u]','[0,pi]'),('parabola','[u,u**2/a,0]','[0,a]'),('arc','[a*cos(u),a*sin(u),0]','[0,pi/3]')]:
    p=prepared('En generel parameteriseret linje.',f'source = {source}\nparameter = u\nbounds = {bounds}\npoint = [0,0,4*a]\nI = I0', ['B'],{'a':'m','u':'m' if id=='parabola' else '1','I0':'A'},['a'],['magnetostatic'])
    # Store independent expected Biot-Savart construction from the vector identity.
    q=build(p);u=q.variables['parameter'];r=s.Matrix(q.variables['source']);delta=s.Matrix(q.variables['point'])-r
    integrand=MU0*q.variables['I']*r.diff(u).cross(delta)/(4*s.pi*(delta.dot(delta))**s.Rational(3,2))
    expected=s.Matrix([s.Integral(s.trigsimp(v),(u,*q.variables['bounds'])) for v in integrand])
    case('wire_'+id,p,('B',expected,{}),'biot_savart')

# Different time laws AND evolving area, winding count, current and heat.
for i,law in enumerate(['t/tau','(t/tau)**3','sin(t/tau)','cos(t/tau)','exp(-t/tau)','1/(1+t/tau)']):
    p=prepared('Tidsafhængigt magnetfelt. Beregn EMF og strøm.',f'B(t) = B0*({law})\narea = a**2\nN = 3\nresistance = Z', ['EMF','current','power'],{'B0':'T','t':'s','tau':'s','a':'m','Z':'ohm'},['a','tau','Z'],['uniform_normal_B','negligible_self_inductance'])
    q=build(p);t=q.variables['time'];expected=-3*s.diff(q.variables['B_normal']*q.variables['area'],t)
    case('flux_law_'+str(i),p,('EMF',expected,{}),'dependency')
for i,area in enumerate(['a**2*(1+t/tau)','a**2*(1+t/tau)**2','a**2*exp(t/tau)']):
    p=prepared('Et loop i tidsafhængigt magnetfelt.',f'B(t) = B0*cos(t/tau)\narea = {area}\nN = 2\nresistance = Z', ['EMF','current','power'],{'B0':'T','t':'s','tau':'s','a':'m','Z':'ohm'},['a','tau','Z'],['uniform_normal_B','negligible_self_inductance'])
    q=build(p);t=q.variables['time'];expected=-2*s.diff(q.variables['B_normal']*q.variables['area'],t)
    case('moving_area_'+str(i),p,('EMF',expected,{}),'dependency')
p=prepared('En enkelt kreds med kendt flux.', 'flux = f0*t**2/tau**2\ntime = t\nN = 1\nresistance = Z\ntime_bounds = [0,tau]', ['energy'],{'f0':'Wb','t':'s','tau':'s','Z':'ohm'},['tau','Z'],['negligible_self_inductance'])
q=build(p);f=next(x for x in q.symbol_units if str(x)=='f0');tau=next(x for x in q.symbol_units if str(x)=='tau');Z=next(x for x in q.symbol_units if str(x)=='Z')
case('heat_quadratic_flux',p,('W',4*f*f/(3*Z*tau),{}),'dependency')

@pytest.mark.parametrize('id,parsed,expected,family',CASES,ids=[c[0] for c in CASES])
def test_unseen_problem(id,parsed,expected,family):
    assert build(parsed).family==family
    out=execute(parsed);key,value,subs=expected
    eq(out.symbolic_result[key].subs(subs),value.subs(subs))
    dims=[c for c in out.checks if c.name.startswith('Dimension:')]
    assert dims and all(c.passed is True for c in dims),[(c.name,c.detail) for c in dims]
    assert not any('inconsistency' in w for w in out.warnings)
    assert out.steps and out.equations and out.direction
    assert 'Resultat' in text(out) and 'Resultat' in document(out)
    if family=='dependency' and 'I' in out.symbolic_result:
        eq(out.symbolic_result['I'],out.symbolic_result['EMF']/build(parsed).variables['R'])
        eq(out.symbolic_result['P'],out.symbolic_result['I']**2*build(parsed).variables['R'])

@pytest.mark.parametrize('description,known,wanted',[
 ('En cylinder med radius R.','rho(s) = rho0',['E']),
 ('En endelig cylinder med radius R.','rho(s) = rho0',['E']),
 ('En uendelig cylinder.','rho(s) = rho0',['E']),
 ('En ring.','lambda = q',['E']),
 ('Et felt.','B(t) = B0*cos(t)',['current']),
 ('Ukendt.','',[]),
])
def test_unseen_rejects_insufficient_data(description,known,wanted):
    p=parse(description,known,wanted=wanted);p.positive=['s','R']
    with pytest.raises(InputError):execute(p)


def test_parser_does_not_execute_code():
    p=parse('En kugle med radius R.','rho(r) = __import__(os)',wanted=['E']);p.positive=['r','R'];p.assumptions=['spherical_symmetry']
    with pytest.raises(InputError):execute(p)


def test_numeric_units_are_extracted_without_conflating_radius_and_resistance():
    p=parse('En uendelig cylinder med radius a. Find det elektriske felt.','rho(s) = alpha*s**2\na = 7 cm\nalpha = 2 nC/m^5')
    assert p.geometry=='cylinder' and p.wanted==['E'] and p.data['radius']=='a'
    assert p.quantities['a']=='7 cm' and p.data['coordinate']=='s'


def test_closed_form_current_arc_has_positive_normal_direction():
    from em1_solver.core.curve import line_integrals
    p=prepared('En bue.', 'source = [a*cos(u),a*sin(u),0]\nparameter = u\nbounds = [0,pi/5]\npoint = [0,0,0]\nI = I0',['B'],{'a':'m','u':'1','I0':'A'},['a'],['magnetostatic'])
    out=line_integrals(build(p),evaluate=True,budget=3)
    a=next(x for x in build(p).symbol_units if str(x)=='a');I=next(x for x in build(p).symbol_units if str(x)=='I0')
    eq(out.symbolic_result['B'],s.Matrix([0,0,MU0*I/(20*a)]))


def test_ellipse_numerical_quadrature_and_direction():
    from em1_solver.core.curve import numerical_curve
    p=prepared('En ring.', 'source = [a*cos(u),2*a*sin(u),0]\nparameter = u\nbounds = [0,2*pi]\npoint = [0,0,0]\nI = I0',['B'],{'a':'m','u':'1','I0':'A'},['a'],['magnetostatic','off_source'])
    out=execute(p);subs={x:s.Rational(1) for x in build(p).symbol_units if str(x) in ('a','I0')}
    numeric=numerical_curve(out,subs,timeout=8)
    b=numeric['B'];assert abs(float(b[0]))<1e-18 and abs(float(b[1]))<1e-18 and float(b[2])>0
    # Independent elliptic-integral formula at the centre, semiaxes 1 and 2.
    expected=float(MU0.subs(MU0,1.25663706212e-6))*float(s.elliptic_e(s.Rational(3,4)))/s.pi
    assert abs(float(b[2])-float(expected))<1e-15


def test_timeout_preserves_formal_integral():
    from em1_solver.core.curve import bounded_integral
    u=s.Symbol('u',real=True)
    value=bounded_integral(s.exp(-u**4),( (u,0,1), ),seconds=0.001)
    assert value==s.Integral(s.exp(-u**4),(u,0,1))


def test_curve_endpoint_singularity_is_rejected():
    p=prepared('En linje.', 'source = [u,0,0]\nparameter = u\nbounds = [0,1]\npoint = [0,0,0]\nlambda = q',['E'],{'u':'m','q':'C/m'},[],[])
    with pytest.raises(InputError,match='singularitet'):execute(p)


def test_dimension_zero_integrals_and_minmax():
    from em1_solver.core.dimensions import dimension,unit_dimension,DimensionError
    u,a,L=s.symbols('u a L',real=True)
    vector=s.Matrix([s.Integral(0,(u,-L,L)),s.Integral(a,(u,-L,L)),s.Integral(0,(u,-L,L))])
    assert dimension(vector,{u:'m',a:'T/m',L:'m'})==unit_dimension('T')
    assert dimension(s.Max(a,L),{a:'m',L:'m'})==unit_dimension('m')
    with pytest.raises(DimensionError):dimension(s.Max(a,L),{a:'m',L:'s'})
