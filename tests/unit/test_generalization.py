"""Analytic references derived independently of the production kernels."""
import sympy as s
import pytest
from em1_solver.assisted_backend import respond,MODELS


def request(model,variables,wanted,units,positive=(),numbers=None,operations=None):
    part=dict(id='a',model=model,wanted=wanted,orientation_confirmed=True)
    if operations:part['operations']=operations
    return dict(schema_version='assisted-1.0',text='Kontrol med eksplicitte fysiske data.',confirmed=True,variables=variables,
        units=units,positive=list(positive),numbers=numbers or {},assumptions=list(MODELS[model]['assumptions']),subproblems=[part])


def results(r):
    a=respond(r,solve=True)
    assert a['status'] in ('calculated_under_confirmed_model','partial'),str(a.get('errors'))+str([(p['errors'],p['status']) for p in a['subproblems']])
    return a,a['subproblems'][0]['solution']['results']


def expression(result,sy):return s.sympify(result['expression'],locals=sy)


def test_rl_reference_initial_slope_and_zero():
    r=request('RL_step',dict(time='t',R='R',L='L',voltage='V',I0='I0'),['I','initial_slope','zero_time'],
        dict(t='s',R='ohm',L='H',V='V',I0='A'),['R','L'],dict(R='12 ohm',L='85 mH',V='-6 V',I0='0.32 A'))
    reply,v=results(r)
    sy={k:s.Symbol(k,positive=True) if k in ('R','L') else s.Symbol(k,real=True) for k in ('t','R','L','V','I0')}
    assert s.simplify(expression(v['initial_slope'],sy)-(sy['V']-sy['R']*sy['I0'])/sy['L'])==0
    assert abs(float(reply['subproblems'][0]['solution']['numerical']['zero_time']['value'])-.003504098378)<1e-10


@pytest.mark.parametrize('voltage,initial',[('2 V','0.1 A'),('0 V','0 A')])
def test_no_fabricated_zero_time(voltage,initial):
    r=request('RL_step',dict(time='t',R='R',L='L',voltage='V',I0='I0'),['I','zero_time'],
        dict(t='s',R='ohm',L='H',V='V',I0='A'),['R','L'],dict(R='10 ohm',L='1 H',V=voltage,I0=initial))
    reply,v=results(r)
    assert reply['status']=='partial' and 'zero_time' not in v


def test_plane_images_reference():
    r=request('image_plane',dict(charges=[['q',['0','0','a']]],normal=['0','0','1'],offset='0',point=['0','0','2*a'],surface_point=['0','0','0']),
        ['V','E','F','Q_induced','sigma_induced'],dict(q='C',a='m'),['a'])
    reply,v=results(r);q,a,e=s.symbols('q a epsilon_0',positive=True)
    sy={'q':s.Symbol('q',real=True),'a':a,'epsilon_0':e};q=sy['q']
    assert s.simplify(expression(v['F'],sy)[2]+q**2/(16*s.pi*e*a**2))==0
    assert s.simplify(expression(v['E'],sy)[2]-2*q/(9*s.pi*e*a**2))==0
    assert s.simplify(expression(v['sigma_induced'],sy)+q/(2*s.pi*a**2))==0


@pytest.mark.parametrize('model,total',[('image_sphere_grounded',None),('image_sphere_isolated','0')])
def test_spherical_images_independent_force(model,total):
    data=dict(charges=[['q',['0','0','d']]],center=['0','0','0'],radius='a')
    if total is not None:data['sphere_charge']=total
    r=request(model,data,['F','Q_conductor'],dict(q='C',d='m',a='m'),['a','d'],dict(a='2 cm',d='7 cm',q='3 nC'))
    reply,v=results(r);a,d=s.symbols('a d',positive=True);q=s.Symbol('q',real=True);ep=s.Symbol('epsilon_0',positive=True)
    expected=-q*q*a*d/(4*s.pi*ep*(d*d-a*a)**2)
    if total is not None:expected+=q*q*a/(4*s.pi*ep*d**3)
    assert s.simplify((expression(v['F'],dict(a=a,d=d,q=q,epsilon_0=ep))[2]-expected).subs(d,a+s.Symbol('gap',positive=True)))==0


@pytest.mark.parametrize('variables',[
 dict(charges=[['q',['0','0','-a']]],normal=['0','0','1'],offset='0'),
 dict(charges=[['q',['0','0','a']],['q',['0','0','a']]],normal=['0','0','1'],offset='0'),
 dict(charges=[['q',['0','0','a']]],normal=['0','0','2'],offset='0')])
def test_invalid_plane_geometries_refused(variables):
    r=request('image_plane',variables,['F'],dict(q='C',a='m'),['a'])
    assert respond(r,solve=True)['status']=='not_solved'


def test_bound_currents_cylindrical_reference():
    r=request('magnetization_currents',dict(M=['0','0','k*s**2'],coordinates=['s','phi','z'],system='cylindrical',normal=['1','0','0'],surface_coordinate='s',surface_value='a'),
        ['J_bound','K_bound'],dict(s='m',phi='1',z='m',k='A/m^3',a='m'),['s','a'])
    reply,v=results(r);sy={k:s.Symbol(k,positive=True) if k in ('a','s') else s.Symbol(k,real=True) for k in ('s','phi','z','k','a')}
    assert s.simplify(expression(v['J_bound'],sy)-s.Matrix([0,-2*sy['k']*sy['s'],0]))==s.zeros(3,1)
    assert s.simplify(expression(v['K_bound'],sy)-s.Matrix([0,sy['k']*sy['a']**2,0]))==s.zeros(3,1)


def test_magnetized_sphere_reference():
    r=request('magnetized_sphere',dict(M=['0','0','M0'],radius='a',center=['0','0','0'],point=['0','0','2*a']),
        ['B_inside','B','J_bound'],dict(M0='A/m',a='m'),['a'])
    reply,v=results(r);m=s.Symbol('M0',real=True);mu=s.Symbol('mu_0',positive=True);sy=dict(M0=m,mu_0=mu,a=s.Symbol('a',positive=True))
    assert s.simplify(expression(v['B_inside'],sy)[2]-2*mu*m/3)==0
    assert s.simplify(expression(v['B'],sy)[2]-mu*m/12)==0


@pytest.mark.parametrize('model,variables,wanted,units,positive,reference',[
 ('RL_driven',dict(time='t',R='R',L='L',voltage='v0*exp(-R*t/L)',I0='i0'),['I'],dict(t='s',R='ohm',L='H',v0='V',i0='A'),['R','L'],'(i0+v0*t/L)*exp(-R*t/L)'),
 ('RC_driven',dict(time='t',R='R',C='C',voltage='v0',Q0='q0'),['Q','I_initial'],dict(t='s',R='ohm',C='F',v0='V',q0='C'),['R','C'],'(v0-q0/C)/R')])
def test_driven_circuits(model,variables,wanted,units,positive,reference):
    reply,v=results(request(model,variables,wanted,units,positive));sy={k:s.Symbol(k,positive=True) if k in positive else s.Symbol(k,real=True) for k in units}
    assert s.simplify(expression(v[wanted[-1]],sy)-s.sympify(reference,locals=sy))==0


def test_generic_differentiate_evaluate_limit_operations():
    r=request('RL_step',dict(time='t',R='R',L='L',voltage='V',I0='I0'),['I'],dict(t='s',R='ohm',L='H',V='V',I0='A'),['R','L'],operations=[
        dict(kind='differentiate',id='slope',result='I',variable='t',at='0'),
        dict(kind='evaluate',id='initial',result='I',variable='t',value='0'),
        dict(kind='limit',id='steady',result='I',variable='t',value='oo')])
    reply,v=results(r);assert {'slope','initial','steady'}<=set(v)


def test_rl_driven_stationary_time_and_curvature():
    r=request('RL_driven',dict(time='t',R='R',L='L',voltage='v0*exp(-R*t/L)',I0='0'),['I','extremum_times'],
        dict(t='s',R='ohm',L='H',v0='V'),['R','L','v0'])
    reply,v=results(r);sy={k:s.Symbol(k,positive=True) if k in ('R','L','v0') else s.Symbol(k,real=True) for k in ('t','R','L','v0')}
    assert s.simplify(expression(v['extremum_times'],sy)-sy['L']/sy['R'])==0
    # Positive source gives a maximum, verified independently by its second derivative.
    current=expression(v['I'],sy);assert s.simplify(s.diff(current,sy['t'],2).subs(sy['t'],sy['L']/sy['R'])).is_negative


def test_flux_to_emf_to_inductive_current_to_power_energy():
    r=request('faraday_flux',dict(time='t',flux='-a*t',N='1'),['EMF'],
        dict(t='s',a='V',L='H',R='ohm',T='s'),['L','R','T'],operations=[
        dict(kind='linear_ode',id='coil_current',result='EMF',variable='t',coefficient='L',resistance='R',initial='0',unit='A'),
        dict(kind='transform',id='heat_rate',result='coil_current',variable='t',value='coil_current**2*R',unit='W'),
        dict(kind='integrate',id='heat',result='heat_rate',variable='t',lower='0',upper='T')])
    reply,v=results(r);sy={k:s.Symbol(k,positive=True) if k in ('L','R','T') else s.Symbol(k,real=True) for k in ('t','a','L','R','T')}
    expected=sy['a']/sy['R']*(1-s.exp(-sy['R']*sy['t']/sy['L']))
    assert s.simplify(expression(v['coil_current'],sy)-expected)==0
    expected_heat=s.integrate(sy['R']*expected**2,(sy['t'],0,sy['T']))
    assert s.simplify(expression(v['heat'],sy)-expected_heat)==0


def test_transform_cannot_hide_unit_mismatch():
    r=request('ampere_wire',dict(I='I',distance='d'),['B'],dict(I='A',d='m'),['d'],operations=[
        dict(kind='transform',id='bad',result='B',variable='d',value='B+I',unit='T')])
    assert respond(r,solve=True)['status']=='not_solved'


def test_interpretation_preserves_evidence_and_conflicts():
    from em1_solver.assisted_backend import plan
    p=plan('En RL-kreds har R=12 ohm; L=85 mH; I0=0,32 A. Bestem startafledte og nulpassage.')
    assert {v['name'] for v in p['extraction']['givens']}=={'R','L','I0'}
    assert 'initial_slope' in p['extraction']['wanted'] and 'zero_time' in p['extraction']['wanted']
    assert p['extraction']['assumptions_confirmed']==[]
    p=plan('R=10 ohm; R=20 ohm; antag en ukendt spænding.')
    assert p['extraction']['conflicts']==['R']
    assert all(v['status']=='conflict_do_not_transfer' for v in p['extraction']['givens'])


def test_charge_to_field_potential_to_force_energy_composition():
    r=request('sphere_regions',dict(coordinate='r',regions=[dict(lower='0',upper='a',density='rho0',permittivity='epsilon_0')]),['force','energy'],
        dict(r='m',a='m',rho0='C/m^3',q='C'),['r','a'],operations=[
        dict(kind='transform',id='force',result='E',variable='r',value='q*E',unit='N'),
        dict(kind='transform',id='energy',result='V',variable='r',value='q*V',unit='J')])
    r['assumptions'].append('V_infinity_zero')
    reply,v=results(r);sy={k:s.Symbol(k,positive=True) if k in ('r','a','epsilon_0') else s.Symbol(k,real=True) for k in ('r','a','rho0','q','epsilon_0')}
    energy=expression(v['energy'],sy).subs(sy['r'],sy['a']/2)
    assert s.simplify(energy-11*sy['q']*sy['rho0']*sy['a']**2/(24*sy['epsilon_0']))==0
