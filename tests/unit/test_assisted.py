import pytest
from em1_solver.core.assisted import P,defaults,default_regions,compile_problem,validate
from em1_solver.core.new_problem import execute
from em1_solver.core.problem import InputError

@pytest.mark.parametrize('key',list(P))
def test_every_geometry_preset_has_valid_default_structure(key):
    family=P[key].family
    wanted={'gauss_radial':['E'],'coulomb_integral':['E'],'point_charges':['E'],'conductors':['E'],'capacitance':['C'],'field_calculus':['B' if key=='ba_vector_potential' else 'E'],'polarization':['P'],'ampere':['B_positive' if key=='ba_sheet' else 'B'],'biot_savart':['B'],'magnetic_material':['B'],'lorentz_force':['F'],'magnetic_dipole_interaction':['U'],'faraday':['EMF'],'motional_emf':['EMF'],'ampere_maxwell':['B'],'inductance_energy':['L'],'rc_transient':['I']}[family]
    p=compile_problem(key,defaults(key),default_regions(key) if P[key].regions else [],wanted,charges=[['q',[0,0,0]]])
    if key=='ev_field':
        with pytest.raises(InputError,match='Fysisk afvisning'):validate(p)
        return
    _,unknown=validate(p)
    assert not unknown,unknown


def test_region_overlap_rejected_and_empty_regions_rejected():
    key='ev_cylinder'
    with pytest.raises(InputError,match='region'):compile_problem(key,defaults(key),[],['E'])
    rows=[dict(lower='0',upper='R',density='@source',permittivity='epsilon_0'),dict(lower='0',upper='R+h',density='@source',permittivity='epsilon_0')]
    with pytest.raises(InputError):validate(compile_problem(key,defaults(key),rows,['E']))


def test_typed_numeric_radius_keeps_units_and_numeric_solution():
    key='ba_wire';values=defaults(key);values.update(function='3 A',distance='5 cm')
    parsed=compile_problem(key,values,[],['B']);validate(parsed);answer=execute(parsed)
    assert float(answer.numerical_result['B'])>0
    assert answer.givens['numerical_values']
    from em1_solver.rendering.plain import text
    assert 'Givet:' in text(answer) and 'Søges:' in text(answer)


def test_conflicting_plane_normal_is_red():
    with pytest.raises(InputError,match='Normalen'):
        compile_problem('dyn_fixed',defaults('dyn_fixed'),[],['EMF'],orientation={'plane':'xy','normal':'+x','B':'+x'})


def test_finite_cylinder_cannot_be_converted_to_infinite_silently():
    with pytest.raises(InputError,match='Endelig kilde'):
        compile_problem('ev_cylinder',defaults('ev_cylinder'),default_regions('ev_cylinder'),['E'],original='En endelig cylinder med radius R.')


def test_numeric_hollow_region_with_units_has_positive_width_and_si_result():
    row=dict(lower='1 cm',upper='3 cm',density='2 nC/m^3',permittivity='epsilon_0')
    p=compile_problem('ev_hollow',defaults('ev_hollow'),[row],['E'])
    _,unknown=validate(p)
    assert not unknown
    out=execute(p)
    assert out.symbolic_result['E'] is not None


def test_capacitor_energy_and_faraday_heat_have_their_required_inputs():
    p=compile_problem('ev_capacitor',defaults('ev_capacitor')|{'charge':'Q'},[],['C','U'])
    validate(p);assert 'U' in execute(p).symbolic_result
    p=compile_problem('dyn_fixed',defaults('dyn_fixed')|{'time_start':'0','time_end':'T'},[],['W'])
    validate(p);assert 'W' in execute(p).symbolic_result


@pytest.mark.parametrize('value',['-5 ohm','0 ohm'])
def test_negative_or_zero_numeric_resistance_cannot_enter_positive_model(value):
    with pytest.raises(InputError):compile_problem('dyn_fixed',defaults('dyn_fixed')|{'R':value},[],['I'])
    with pytest.raises(InputError):validate(compile_problem('dyn_fixed',defaults('dyn_fixed'),[],['I'],numbers={'Z':value}))


def test_zero_with_units_is_a_valid_region_origin():
    p=compile_problem('ev_cylinder',defaults('ev_cylinder'),[dict(lower='0 cm',upper='3 cm',density='rho0',permittivity='epsilon_0')],['E'])
    validate(p)


@pytest.mark.parametrize('preset,key',[('ev_cylinder','coordinate'),('ev_ring','parameter'),('dyn_fixed','time')])
def test_independent_variable_cannot_be_replaced_by_a_numeric_value(preset,key):
    values=defaults(preset)|{key:'3'}
    with pytest.raises(InputError,match='variabelnavn'):
        compile_problem(preset,values,default_regions(preset) if P[preset].regions else [],['E' if preset.startswith('ev') else 'EMF'])


def test_density_coordinate_mismatch_cannot_be_integrated_as_a_constant_parameter():
    with pytest.raises(InputError,match='koordinat'):
        compile_problem('ev_cylinder',defaults('ev_cylinder')|{'function':'rho0*r**2','coordinate':'s'},default_regions('ev_cylinder'),['E'])
