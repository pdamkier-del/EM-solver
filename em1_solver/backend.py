"""Versioned JSON boundary for the separate frontend track. No Streamlit imports.

Only raw text + explicit user corrections enter parsing. Result LaTeX is output,
never reparsed as executable mathematics. Physical and mathematical status differ.
"""
import sympy as sp
from .text_parser import analyze,solve_text
VERSION='1.0'


def physical_model(interpreted):
    f=interpreted.facts
    if f.get('scene'):
        scene=f['scene']
        return dict(objects=scene['objects'],sources=[dict(id=o['id'],kind='q',formula=o['value'],position=o['position'],evidence=o['evidence']) for o in scene['objects'] if o['kind']=='point_charge'],relationships=scene['relations'],coordinates=['x','y','z'],coordinate_system=scene['coordinate_system'],orientation=f['orientation'],boundary_conditions=f.get('boundary_conditions',{}),initial_conditions={},assumptions=interpreted.problem.assumptions if interpreted.problem else [],validity=scene['conditions'],wanted=f['wanted'],units=f['units'],values=f['numbers'],methods=[dict(name='point_charges',status=interpreted.fields['method'].status)],dependencies={})
    sources=[dict(id='source_'+k,kind=k,formula=v['formula'],arguments=v['args'],basis=v['basis'],evidence=v['evidence']) for k,v in f['sources'].items()]
    return dict(objects=[dict(id='body',geometry=f['geometry'],extent=f['extent'],parameters=f['roles'],position=f.get('point'),material=f.get('material_model') or interpreted.fields.get('material').value if 'material' in interpreted.fields else None)],sources=sources,
                relationships=[dict(subject=s['id'],relation='has_support',object='body',regions=interpreted.fields.get('regions').value if 'regions' in interpreted.fields else None) for s in sources],
                coordinates=f.get('coordinates') or [f['coordinate']] if f.get('coordinate') else f.get('coordinates',[]),
                orientation=f['orientation'],boundary_conditions=f.get('boundary_conditions',{}),initial_conditions={},
                assumptions=interpreted.problem.assumptions if interpreted.problem else [],wanted=f['wanted'],units=f['units'],values=f['numbers'],
                methods=[dict(name=f.get('model'),status=interpreted.fields.get('method').status if 'method' in interpreted.fields else 'RED')],
                dependencies=interpreted.problem.data.get('composition',{}) if interpreted.problem else {})


def respond(request,*,solve=False):
    response=dict(schema_version=VERSION,status='not_solved',interpretation=None,solution=None,missing=[],errors=[])
    try:
        if not isinstance(request,dict) or request.get('schema_version',VERSION)!=VERSION:raise ValueError('Unsupported request schema; expected 1.0.')
        if set(request)-{'schema_version','text','corrections','evaluate_integrals'}:raise ValueError('Unknown request field; IDs, presets and gold are not accepted.')
        if not isinstance(request.get('text'),str) or not isinstance(request.get('corrections',{}),dict):raise ValueError('text must be a string and corrections an object.')
        corrections=request.get('corrections',{})
        if any(not isinstance(k,str) or not (isinstance(v,str) or k=='wanted' and isinstance(v,list) and all(isinstance(x,str) for x in v)) for k,v in corrections.items()):raise ValueError('Corrections must be strings; wanted may be a list of strings.')
        if sum(len(str(v)) for v in corrections.values())>8000:raise ValueError('Corrections exceed 8000 characters.')
        if not isinstance(request.get('evaluate_integrals',False),bool):raise ValueError('evaluate_integrals must be boolean.')
        p=analyze(request['text'],request.get('corrections'));response['interpretation']=dict(model=physical_model(p),fields=p.snapshot()['fields'],ready=p.ready)
        response['missing']=[dict(field=k,status=v.status,message=v.message,options=v.options) for k,v in p.questions.items()]
        if not p.ready:return response
        if not solve:response['status']='ready';return response
        _,answer=solve_text(request['text'],request.get('corrections'),evaluate=bool(request.get('evaluate_integrals',False)))
        assumptions=list(dict.fromkeys(p.problem.assumptions+[condition for step in answer.steps for condition in step.assumptions]))
        response['interpretation']['model']['assumptions']=assumptions
        failed=[c.name for c in answer.checks if c.passed is False]
        diagnostic=set(p.facts['wanted'])<=set(['curl_E','div_B'])
        dimensions=[c for c in answer.checks if c.name.startswith('Dimension:')]
        unresolved=any(c.passed is None for c in answer.checks) or not dimensions or any(c.passed is not True for c in dimensions)
        formal=any(v.has(sp.Integral) for v in answer.symbolic_result.values())
        if failed and not diagnostic:response['errors'].append('Physical consistency checks failed: '+', '.join(failed))
        else:response['status']='partial' if unresolved or formal else 'verified_with_assumptions' if assumptions else 'verified'
        from .rendering.structured import serialize
        response['solution']=serialize(answer)
        response['solution']['physical_model_rejected']=bool(failed and diagnostic)
    except (ValueError,TypeError,KeyError) as exc:
        response['status']='not_solved';response['solution']=None;response['errors'].append(str(exc))
    return response
