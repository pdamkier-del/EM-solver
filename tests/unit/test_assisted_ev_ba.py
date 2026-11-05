from em1_solver.assisted_backend import respond,MODELS


def request(model,variables,wanted):
    return dict(schema_version='assisted-1.0',confirmed=True,text='Eksplicit bekræftet model.',variables=variables,
        units={'r':'m','R':'m','s':'m','k':'C/m^4'},positive=['r','R','s'],assumptions=list(MODELS[model]['assumptions']),
        subproblems=[dict(id='a',model=model,wanted=wanted,orientation_confirmed=True)])


def test_potential_reference_is_not_guessed():
    r=request('sphere_regions',dict(coordinate='r',regions=[dict(lower='0',upper='R',density='k*r',permittivity='epsilon_0')]),['V'])
    reply=respond(r,solve=True)
    assert reply['status']=='needs_confirmation'
    assert any(q.get('value')=='V_infinity_zero' for q in reply['questions'])


def test_missing_permittivity_is_not_silently_vacuum():
    r=request('sphere_regions',dict(coordinate='r',regions=[dict(lower='0',upper='R',density='k*r')]),['E'])
    assert respond(r,solve=True)['status']=='not_solved'


def test_endelig_cylinder_cannot_be_confirmed_as_infinite_without_correction():
    r=request('cylinder_regions',dict(coordinate='s',regions=[dict(lower='0',upper='R',density='k*s',permittivity='epsilon_0')]),['E'])
    r['text']='En endelig cylinder har radius R.'
    reply=respond(r,solve=True)
    assert reply['status']=='not_solved' and 'endelig' in reply['errors'][0]


def test_nonzero_curl_cannot_be_confirmed_electrostatic():
    r=request('electric_field_charge',dict(E=['k*y','0','0'],coordinates=['x','y','z'],system='cartesian'),['rho'])
    r['units']={'x':'m','y':'m','z':'m','k':'V/m^2'}
    reply=respond(r,solve=True)
    assert reply['status']=='not_solved'
    assert 'curl' in str(reply)
