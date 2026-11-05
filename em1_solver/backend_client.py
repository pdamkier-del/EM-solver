"""Offline contract client and pure view selection; no Qt or web framework."""
import argparse,copy,json,multiprocessing,sys
from pathlib import Path
from .rendering.math_profile import validate,PROFILE

STATUSES={'not_solved','ready','partial','verified_with_assumptions','verified'}


def validate_response(response,*,require_views=False):
    required={'schema_version','status','interpretation','solution','missing','errors'}
    if not isinstance(response,dict) or not required<=set(response):raise ValueError('Backend response is missing required fields.')
    if response['schema_version']!='1.0' or not isinstance(response['status'],str) or response['status'] not in STATUSES:raise ValueError('Unsupported backend schema/status.')
    json.dumps(response,ensure_ascii=False,allow_nan=False)
    if not isinstance(response['missing'],list) or not isinstance(response['errors'],list):raise ValueError('Missing data and errors must be arrays.')
    if not all(isinstance(e,str) for e in response['errors']):raise ValueError('Errors must be text.')
    for item in response['missing']:
        if not isinstance(item,dict) or not {'field','status','message','options'}<=set(item):raise ValueError('Incomplete uncertainty.')
        if item['status'] not in ('YELLOW','RED') or not isinstance(item['message'],str) or not isinstance(item['options'],list):raise ValueError('Invalid uncertainty status or options.')
    interpreted=response['interpretation']
    if interpreted is not None:
        if not isinstance(interpreted,dict) or not {'model','fields','ready'}<=set(interpreted) or not isinstance(interpreted['ready'],bool):raise ValueError('Incomplete interpretation.')
    answer=response['solution'];status=response['status']
    if interpreted is not None:
        for field in interpreted['fields'].values():
            if field.get('status') not in ('GREEN','YELLOW','RED'):raise ValueError('Unknown field confidence status.')
            if interpreted['ready'] and field.get('required',True) and field['status']!='GREEN':raise ValueError('Ready interpretation contains unresolved required fields.')
    if status in ('verified','verified_with_assumptions','partial'):
        if answer is None or interpreted is None or not interpreted['ready'] or response['missing'] or response['errors']:raise ValueError('A solved status has unresolved input/errors.')
    if answer is None:return response
    keys={'method','reasoning','equations_latex','steps','results','numerical','checks','warnings','direction','physical_model_rejected'}
    if not isinstance(answer,dict) or not keys<=set(answer):raise ValueError('Incomplete solution.')
    if type(answer['physical_model_rejected']) is not bool:raise ValueError('Physical rejection flag must be boolean.')
    if not all(isinstance(answer[k],str) for k in ('method','reasoning','direction')):raise ValueError('Method/reasoning/direction must be text.')
    if not all(isinstance(answer[k],list) for k in ('equations_latex','steps','checks','warnings')) or not all(isinstance(answer[k],dict) for k in ('results','numerical')):raise ValueError('Invalid solution containers.')
    if not all(isinstance(v,str) for v in answer['warnings']):raise ValueError('Warnings must be text.')
    for equation in answer['equations_latex']:validate(equation)
    for value in answer['results'].values():
        if not isinstance(value,dict) or not {'expression','latex','unit'}<=set(value):raise ValueError('Result lacks expression, LaTeX or unit.')
        if not isinstance(value['expression'],str) or value['unit'] is not None and not isinstance(value['unit'],str):raise ValueError('Result expression/unit has an invalid type.')
        validate(value['latex'])
    for value in answer['numerical'].values():
        if not {'value','unit'}<=set(value):raise ValueError('Incomplete numerical result.')
        if 'latex' in value:validate(value['latex'])
    for step in answer['steps']:
        if not {'text','latex'}<=set(step):raise ValueError('Incomplete derivation step.')
        if step['latex'] is not None:validate(step['latex'])
        for fragment in step.get('intermediate_latex',[]):validate(fragment)
    for check in answer['checks']:
        if not {'name','passed','residual_latex','detail'}<=set(check) or (check['passed'] is not None and type(check['passed']) is not bool):raise ValueError('Incomplete verification check.')
        if check['residual_latex'] is not None:validate(check['residual_latex'])
    if status.startswith('verified') and not any(c['name'].startswith('Dimension:') and c['passed'] is True for c in answer['checks']):raise ValueError('Verified response lacks dimensional checks.')
    if status=='verified_with_assumptions' and not interpreted['model'].get('assumptions'):raise ValueError('Conditional verification has no explicit assumptions.')
    if status.startswith('verified') and any(c['passed'] is None for c in answer['checks']):raise ValueError('Verified response contains unresolved checks.')
    if status.startswith('verified') and any(c['passed'] is False for c in answer['checks']) and not answer['physical_model_rejected']:raise ValueError('Failed physical checks cannot be approved.')
    if require_views:
        if answer.get('latex_profile')!=PROFILE or answer.get('presentation_version')!='1.0' or set(answer.get('views',{}))!={'result','derivation','explanation'}:raise ValueError('Structured views are missing; calculate once using the current backend.')
        ids=[s.get('id') for s in answer['steps']]
        if None in ids or len(set(ids))!=len(ids):raise ValueError('Step identifiers are absent or duplicated.')
        checks={c['id'] for c in answer['checks']}
        if len(checks)!=len(answer['checks']):raise ValueError('Duplicated check identifiers.')
        if any(not set(c['step_ids'])<=set(ids) for c in answer['checks']):raise ValueError('Check references unknown steps.')
        contexts=answer.get('method_contexts',{})
        for step in answer['steps']:
            required_step={'id','title','physical_reasoning','reasoning_scope','law','method_context_id','intermediate_latex','assumptions','validity','check_ids'}
            if not required_step<=set(step):raise ValueError('Missing structured step fields.')
            if step['method_context_id'] is not None and step['method_context_id'] not in contexts:raise ValueError('Unknown executed-method context.')
            if not set(step['check_ids'])<=checks:raise ValueError('Step references unknown checks.')
        for view in ('derivation','explanation'):
            if not set(answer['views'][view]['step_ids'])<=set(ids):raise ValueError('View references unknown steps.')
        for context in contexts.values():
            for fragment in context['equations']:validate(fragment)
    json.dumps(response,ensure_ascii=False,allow_nan=False)
    return response


def choose_view(response,level):
    """No parsing, SymPy operations or solving: cached response -> selected content."""
    if level not in ('result','derivation','explanation'):raise ValueError('Unknown solution view.')
    validate_response(response,require_views=True)
    if response['solution'] is None or response['status'] in ('ready','not_solved'):
        return copy.deepcopy(dict(status=response['status'],missing=response['missing'],errors=response['errors']))
    answer=response['solution'];view=copy.deepcopy(answer['views'][level]);view['status']=response['status'];view['physical_model_rejected']=answer['physical_model_rejected'];view['warnings']=list(answer['warnings']);view['assumptions']=list(response['interpretation']['model'].get('assumptions',[]))
    model=response['interpretation']['model'];view['validity']=list(model.get('validity',[]))
    for obj in model.get('objects',[]):
        if isinstance(obj.get('material'),dict):view['validity'].extend(obj['material'].get('validity',[]))
    if 'step_ids' in view:
        mapping={s['id']:s for s in answer['steps']};view['steps']=[copy.deepcopy(mapping[id]) for id in view['step_ids']]
    if level=='explanation':
        view['method_contexts']=copy.deepcopy(answer['method_contexts']);view['checks']=copy.deepcopy(answer['checks'])
    return view


def run_text(text,*,solve=True,corrections=None,evaluate_integrals=False):
    from .backend import respond
    response=respond(dict(schema_version='1.0',text=text,corrections=corrections or {},evaluate_integrals=evaluate_integrals),solve=solve)
    return validate_response(response,require_views=True)


def main():
    parser=argparse.ArgumentParser(description='Offline EM1 backend; UTF-8 raw text or cached JSON.')
    group=parser.add_mutually_exclusive_group();group.add_argument('--input',type=Path);group.add_argument('--response',type=Path)
    parser.add_argument('--analyse-only',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--view',choices=['result','derivation','explanation'])
    args=parser.parse_args()
    for stream in (sys.stdin,sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    try:
        if args.response:reply=validate_response(json.loads(args.response.read_text(encoding='utf-8')),require_views=True)
        else:reply=run_text(args.input.read_text(encoding='utf-8') if args.input else sys.stdin.read(),solve=not args.analyse_only)
        if args.output:args.output.write_text(json.dumps(reply,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        selected=choose_view(reply,args.view) if args.view else reply
        print(json.dumps(selected,ensure_ascii=False,indent=2,allow_nan=False))
        return 0 if reply['status'] in ('ready','verified','verified_with_assumptions','partial') else 2
    except (ValueError,OSError) as exc:print(str(exc),file=sys.stderr);return 2

if __name__=='__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())
