"""Translate the pinned EM1 backend API 1.0 response to the existing viewer schema.

No physics inference or verification takes place here. Unknown status stays unapproved.
"""
from __future__ import annotations
from typing import Any

STATUSES = {"verified":"verified", "verified_with_assumptions":"assumptions",
            "partial":"partial", "ready":"unsolved", "not_solved":"unsolved"}


def translate_assisted(reply:dict,task_text:str='')->dict:
    """Reuse the existing viewer; never upgrade conditional output to verified."""
    if not isinstance(reply,dict) or reply.get('schema_version')!='assisted-1.0':
        raise ValueError('Forventede assisted-1.0')
    parts=reply.get('subproblems',[])
    if len(parts)>1:raise ValueError('Desktopformularen viser ét delspørgsmål ad gangen.')
    part=parts[0] if parts else {}
    model=reply.get('confirmed_model',{})
    conditions=model.get('assumptions',[])
    solution=part.get('solution')
    failed=bool(solution and any(c.get('passed') is False for c in solution.get('checks',[])))
    if failed:solution=None
    messages=list(reply.get('errors',[]))+list(part.get('errors',[]))
    messages += [q.get('message','Manglende oplysning') for q in reply.get('questions',[])]
    if failed:messages.append('En kontrol fejlede; intet godkendt resultat vises.')
    envelope={'schema_version':'1.0','status':'partial' if solution else 'not_solved','solution':solution,
        'missing':[],'errors':messages,'interpretation':{'model':{'geometry':part.get('model','Ikke bekræftet'),'assumptions':conditions}}}
    result=translate_backend(envelope,task_text)
    conditional=bool(solution and reply.get('status')=='calculated_under_confirmed_model')
    result.update(status='assumptions' if conditional else 'partial' if solution else 'unsolved',
        backend_status=reply.get('status','not_solved'),backend_schema='assisted-1.0',
        title='Beregnet under brugerbekræftet model' if solution else 'Oplysninger mangler – ingen løsning')
    readback=['# Brugerbekræftede oplysninger']
    for key,value in model.get('variables',{}).items():readback.append(str(key)+' = '+str(value))
    for key,value in model.get('numbers',{}).items():readback.append(str(key)+' = '+str(value))
    for key,value in model.get('units',{}).items():readback.append('Enhed for '+str(key)+': '+str(value))
    readback += ['# Fortolkningens status','Modellen er bekræftet af brugeren. Programmet har ikke bevist, at modellen svarer til opgaveteksten.',result['audit']]
    result['audit']='\n\n'.join(readback)
    result['warnings'].append('Fysisk fortolkning er brugerbekræftet; kontroller gælder kun den valgte model.')
    return result


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict,list)):
        return str(value)
    return str(value)


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []



def audit_backend_reply(reply: dict) -> dict:
    """Inventory what was actually checked, not a proof of overall correctness.

    Reported checks are statements from the backend. This adapter does not
    recompute Maxwell equations, dimensional analysis, or the task interpretation.
    """
    sol=reply.get('solution') if isinstance(reply.get('solution'),dict) else {}
    interpretation=reply.get('interpretation') if isinstance(reply.get('interpretation'),dict) else {}
    model=interpretation.get('model') if isinstance(interpretation.get('model'),dict) else {}
    raw_checks=sol.get('checks') if isinstance(sol.get('checks'),list) else []
    checks=[c for c in raw_checks if isinstance(c,dict)]
    passed=[c for c in checks if c.get('passed') is True]
    failed=[c for c in checks if c.get('passed') is False]
    inconclusive=[c for c in checks if c.get('passed') not in (True,False)]
    conditions=[]
    for source in (model, sol):
        for key in ('assumptions','validity'):
            values=source.get(key) or []
            if isinstance(values,list):
                for v in values:
                    msg=_string(v).strip()
                    if msg and msg not in conditions:conditions.append(msg)
    corrections=reply.get('desktop_user_corrections') or {}
    text_corrections=reply.get('desktop_text_corrections') or {}
    return {'passed':passed,'failed':failed,'inconclusive':inconclusive,
            'conditions':conditions,'corrections':corrections if isinstance(corrections,dict) else {},
            'text_corrections':text_corrections if isinstance(text_corrections,dict) else {},
            'scope':'En bestået kontrol viser kun den undersøgte egenskab. Hverken opgavefortolkning eller hele fysikken er hermed bevist.'}


def audit_text(audit:dict) -> str:
    out=['# Kontrol og gyldighed',
         f"Backend rapporterede {len(audit['passed'])} beståede, {len(audit['failed'])} ikke-beståede og {len(audit['inconclusive'])} uafklarede kontroller."]
    for key,title in (('failed','Ikke-beståede'),('inconclusive','Uafklarede'),('passed','Beståede')):
        if audit[key]:
            out.append('## '+title+' kontroller')
            for c in audit[key][:30]:
                detail=_string(c.get('detail'))
                out.append('- '+_string(c.get('name') or 'Unavngivet kontrol')+((' — '+detail) if detail else ''))
            if len(audit[key])>30:out.append(f"({len(audit[key])-30} flere kontroller er ikke vist)")
    if not any(audit[k] for k in ('passed','failed','inconclusive')):
        out.append('Ingen individuelle kontroller er rapporteret i svaret.')
    if audit['corrections']:
        out.append('## Brugerens modelrettelser')
        out.append(', '.join(f'{k}={v}' for k,v in audit['corrections'].items()))
    if audit['text_corrections']:
        out.append('## Automatisk genkendte tekstangivelser')
        out.append(_string(audit['text_corrections']))
    if audit['conditions']:
        out.append('## Forudsætninger og gyldighed')
        out.extend('- '+c for c in audit['conditions'][:25])
    out.append('**Vigtigt:** '+audit['scope'])
    return '\n\n'.join(out)

def translate_backend(reply: dict, task_text: str = "") -> dict:
    if not isinstance(reply,dict) or reply.get('schema_version') != '1.0':
        raise ValueError('Backend svarede ikke med API 1.0-JSON')
    status = reply.get('status')
    if status not in STATUSES:
        raise ValueError(f'Ukendt status fra backend: {status}')
    audit=audit_backend_reply(reply)
    if audit['failed'] and status in ('verified','verified_with_assumptions'):
        # A contradictory response cannot be displayed as an approved answer.
        status='not_solved'
    solution = reply.get('solution')
    if solution is not None and not isinstance(solution,dict):
        raise ValueError('solution skal være et objekt eller null')
    interpretation = reply.get('interpretation') or {}
    if not isinstance(interpretation,dict): interpretation = {}
    model = interpretation.get('model') or {}
    if not isinstance(model,dict): model={}
    missing = _as_list(reply.get('missing'))
    errors = _as_list(reply.get('errors'))
    warnings = []
    for item in missing:
        if isinstance(item,dict):
            warnings.append(item.get('message') or ('Manglende oplysning: '+_string(item.get('field'))))
        else: warnings.append(_string(item))
    warnings += [_string(e.get('message',e)) if isinstance(e,dict) else _string(e) for e in errors]
    corrections=reply.get('desktop_user_corrections') or {}
    if isinstance(corrections,dict) and corrections:
        warnings.append('BRUGERVALGT MODEL (ikke selvstændigt verificeret fra opgaveteksten): '+', '.join(str(k)+'='+str(v) for k,v in corrections.items()))
    if audit['failed']:
        warnings.append('FYSISK KONTROL FEJLEDE: backendens grønne status er ikke godkendt af desktopadapteren.')
    method, reason, steps, result = '', '', [], {}
    if solution:
        method=_string(solution.get('method'))
        reason=_string(solution.get('reasoning'))
        contexts_raw=solution.get('method_contexts') or {}
        contexts=contexts_raw if isinstance(contexts_raw,dict) else {ctx.get('id'):ctx for ctx in _as_list(contexts_raw) if isinstance(ctx,dict)}
        checks={check.get('id'):check for check in _as_list(solution.get('checks')) if isinstance(check,dict)}
        views=solution.get('views') or {}
        if not isinstance(views,dict):views={}
        derivation=views.get('derivation') or {}
        result_view=views.get('result') or {}
        if not isinstance(derivation,dict):derivation={}
        if not isinstance(result_view,dict):result_view={}
        ordered_ids=derivation.get('step_ids') or []
        all_steps=[s for s in _as_list(solution.get('steps')) if isinstance(s,dict)]
        by_id={s.get('id'):s for s in all_steps if s.get('id')}
        ordered=[by_id[x] for x in ordered_ids if x in by_id] if ordered_ids else all_steps
        for ix,eq in enumerate(_as_list(derivation.get('equations_latex') or solution.get('equations_latex'))):
            if eq:steps.append({'title':f'Grundligning {ix+1}','latex':eq,'reason':reason if ix == 0 else ''})
        for ix,s in enumerate(ordered):
            ctx=contexts.get(s.get('method_context_id')) or {}
            local=_string(s.get('physical_reasoning'))
            if not local and s.get('reasoning_scope') == 'method':
                local=_string(ctx.get('reason') or ctx.get('reasoning') or ctx.get('physical_reasoning'))
            name=_string(s.get('title') or s.get('text') or ('Trin '+str(ix+1)))
            law=_string(s.get('law'))
            reason_line=local
            if law and law.casefold() not in reason_line.casefold():
                reason_line=('Anvendt lov: '+law+'. '+reason_line).strip()
            check_texts=[]
            for cid in _as_list(s.get('check_ids')):
                c=checks.get(cid)
                if c:
                    check_texts.append(_string(c.get('name'))+': '+('bestået' if c.get('passed') is True else ('ikke bestået' if c.get('passed') is False else 'uafklaret')))
            latex_blocks=[_string(x) for x in _as_list(s.get('intermediate_latex')) if x]
            if s.get('latex'):latex_blocks.append(_string(s['latex']))
            steps.append({'id':s.get('id'),'title':name,'reason':reason_line,'latex':'\n'.join('\\['+x+'\\]' for x in latex_blocks),
                          'check':'; '.join(check_texts)})
        results=result_view.get('results') or solution.get('results') or {}
        if not isinstance(results,dict):results={}
        selected=result_view.get('wanted') or list(results)
        math_parts=[];unit_parts=[]
        for key in selected:
            value=results.get(key)
            if isinstance(value,dict):
                latex=value.get('latex')
                if latex:math_parts.append(_string(key)+' = '+_string(latex))
                if value.get('unit'):unit_parts.append(_string(key)+': '+_string(value['unit']))
        numeric=[]
        numbers=result_view.get('numerical') or solution.get('numerical') or {}
        if isinstance(numbers,dict):
            for key,value in numbers.items():
                numeric.append(_string(key)+': '+(_string(value.get('value')) if isinstance(value,dict) else _string(value)))
        result={'symbolic_latex':math_parts[0] if math_parts else '', 'extra_latex':math_parts[1:],
                'numeric_text':'; '.join(numeric),'units':'; '.join(unit_parts)}
        warnings += [_string(w) for w in _as_list(solution.get('warnings'))]
        if solution.get('physical_model_rejected'):
            warnings.append('Backend har afvist den foreslåede fysiske model. Dette er ikke en godkendt feltløsning.')
        if solution.get('direction'):warnings.append('Retning: '+_string(solution['direction']))
        if solution.get('reasoning') and not any(s.get('reason') for s in steps):
            steps.insert(0,{'title':'Metode og fysisk begrundelse','reason':reason})
        if not steps and method:steps.append({'title':'Metode','reason':reason or method})
    if status in ('not_solved','ready') or not solution:
        # No approved answer must be displayed.
        result={}
        steps=[]
    if not method:
        method=_string(interpretation.get('method') or 'Ikke afgjort')
    geom=_string(model.get('geometry') or model.get('object') or 'Se opgavefortolkningen')
    title='Løsning fra EM1-backend' if solution else 'Kan ikke løses med de givne oplysninger'
    payload={'viewer_schema':'em1.desktop.solution.v1','title':title,'prompt':task_text,
             'status':STATUSES[status],'result':result,'steps':steps,
             'interpretation':{'method':method,'geometry':geom},
             'warnings':warnings,'backend_status':status,'backend_schema':'1.0',
             'audit':audit_text(audit)}
    return payload
