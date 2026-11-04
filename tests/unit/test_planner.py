from em1_solver.core.planner import propose

def test_cylinder_name_does_not_authorize_Gauss():
    assert not any(p.family=='gauss_radial' for p in propose(['rho'],['E'],'Uendelig cylinder',False))
    assert propose(['rho'],['E'],'Uendelig cylinder',True)[0].family=='gauss_radial'

def test_unknown_area_and_known_A_have_deterministic_paths():
    assert propose(['A'],['B'])[0].family=='field_calculus'
    assert propose(['flux'],['current'])[0].family=='faraday'
    assert not propose([],['energy'])
