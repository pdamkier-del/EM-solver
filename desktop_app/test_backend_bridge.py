"""Dependency-free smoke tests for the real backend response mapping."""
from backend_bridge import translate_backend

def make_reply(status='verified_with_assumptions'):
    return {
      'schema_version':'1.0', 'status':status, 'missing':[], 'errors':[],
      'interpretation':{'model':{'geometry':'infinite_cylinder'},'fields':{}},
      'solution':{
        'method':'Gauss', 'reasoning':'Cylindersymmetri',
        'equations_latex':[r'\oint\mathbf{E}\cdot d\mathbf{a}=Q/\varepsilon_0'],
        'method_contexts':{'m1':{'method':'Gauss', 'reasoning':'Feltet er radialt og konstant paa en koaksial cylinder'}},
        'steps':[{'id':'s1','title':'Indesluttet ladning','latex':r'\rho\pi s^2L', 'physical_reasoning':None,
                  'reasoning_scope':'method','method_context_id':'m1','law':'Gauss',
                  'intermediate_latex':[r'Q_{enc}=\rho V'],'check_ids':['check1']}],
        'checks':[{'id':'check1','name':'Dimension','passed':True}],
        'views':{
          'result':{'wanted':['E'], 'results':{'E':{'latex':r'\frac{\rho s}{2\varepsilon_0}', 'unit':'N/C'}},'numerical':{}},
          'derivation':{'step_ids':['s1'], 'equations_latex':[r'\oint E\,dA=Q/\varepsilon_0']},
          'explanation':{'step_ids':['s1'],'method_context_ids':['m1'],'global_check_ids':[]}
         }, 'warnings':[], 'physical_model_rejected':False,
      }
    }

def test_verified():
    r=translate_backend(make_reply(),'Test opgave')
    assert r['status']=='assumptions'
    assert r['result']['symbolic_latex'].startswith('E = ')
    assert r['steps'][1]['id']=='s1'
    assert 'Feltet er radialt' in r['steps'][1]['reason']
    assert '1 beståede' in r['audit']
    assert 'Dimension' in r['audit']
    assert 'Dimension: bestået' in r['steps'][1]['check']
    assert r['prompt']=='Test opgave'

def test_unsolved_does_not_leak_result():
    raw=make_reply('not_solved')
    raw['missing']=[{'field':'extent','message':'Er den endelig eller uendelig?'}]
    assert translate_backend(raw)['status']=='unsolved'
    assert translate_backend(raw)['result']=={}
    assert translate_backend(raw)['steps']==[]
    assert 'endelig' in translate_backend(raw)['warnings'][0]

def test_missing_solution():
    raw=make_reply('not_solved')
    raw['solution']=None
    assert translate_backend(raw)['result']=={}

def test_unknown_status_rejected():
    raw=make_reply('invented')
    try:translate_backend(raw)
    except ValueError:pass
    else:raise AssertionError('Unknown status accepted')

def test_partial():
    raw=make_reply('partial')
    assert translate_backend(raw)['status']=='partial'


def test_failed_check_blocks_green():
    raw=make_reply('verified')
    raw['solution']['checks'][0]['passed']=False
    out=translate_backend(raw)
    assert out['status']=='unsolved'
    assert out['result']=={}
    assert out['steps']==[]
    assert 'ikke-beståede' in out['audit']
    assert any('FYSISK KONTROL FEJLEDE' in x for x in out['warnings'])

def test_conditions_and_manual_choices_are_visible():
    raw=make_reply()
    raw['interpretation']['model']['assumptions']=['infinite_cylindrical_symmetry']
    raw['interpretation']['model']['validity']=['Feltet er radialt']
    raw['desktop_user_corrections']={'coordinate':'s'}
    out=translate_backend(raw)
    assert 'infinite_cylindrical_symmetry' in out['audit']
    assert 'Feltet er radialt' in out['audit']
    assert 'coordinate=s' in out['audit']
    assert 'BRUGERVALGT MODEL' in str(out['warnings'])

def test_unverified_check_is_not_reported_as_passed():
    raw=make_reply()
    raw['solution']['checks'][0]['passed']=None
    out=translate_backend(raw)
    assert '1 uafklarede' in out['audit']
    assert '0 beståede' in out['audit']

def test_all():
    test_verified();test_unsolved_does_not_leak_result();test_missing_solution();test_unknown_status_rejected();test_partial();test_failed_check_blocks_green();test_conditions_and_manual_choices_are_visible();test_unverified_check_is_not_reported_as_passed()
    print('8 backend-adapter tests OK')

if __name__=='__main__':test_all()
