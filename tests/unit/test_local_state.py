from em1_solver.core import local_state

def test_autosave_is_local_atomic_and_drops_stale_answers():
    problem=dict(preset='ev_cylinder',values={'rho':'rho0'})
    local_state.save(problem,{'text':'resultat','latex':'latex'})
    assert local_state.load()['answer']['text']=='resultat'
    local_state.save(problem)
    assert local_state.load()['answer']['text']=='resultat'
    local_state.save(problem|{'values':{'rho':'rho1'}})
    assert local_state.load()['answer'] is None
    assert not list(local_state.path().parent.glob('*.tmp'))


def test_specialized_autosave_is_separate_and_restorable():
    local_state.save({'preset':'ev_sphere'})
    local_state.save({'family':'laplace_legendre'},{'text':'answer'},filename='specialized.json')
    assert local_state.load()['problem']['preset']=='ev_sphere'
    assert local_state.load('specialized.json')['answer']['text']=='answer'
