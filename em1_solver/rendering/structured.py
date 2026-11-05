"""Serialize captured execution provenance; never invent a physical explanation."""
import hashlib,json
import sympy as sp
from .math_profile import validate,PROFILE


def math(value):return validate(sp.latex(value))
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:20]

def serialize(answer):
    contexts={};steps=[];counts={};aliases={}
    for step in answer.steps:
        context=dict(step.context)
        if context:
            for equation in context['equations']:validate(equation)
            context_id='method-'+digest(context);contexts[context_id]=context
        else:context_id=None
        base=step.id or 'step-'+digest([step.text,sp.srepr(step.expression)])
        ordinal=counts.get(base,0);counts[base]=ordinal+1
        id=base if ordinal==0 else base+'-repeat-'+str(ordinal)
        aliases.setdefault(base,[]).append(id)
        steps.append(dict(id=id,text=step.text,title=step.title or step.text,latex=math(step.expression) if step.expression is not None else None,
            physical_reasoning=step.reasoning or None,reasoning_scope='step' if step.reasoning else 'method' if context.get('reasoning') else 'unspecified',
            law=step.law or context.get('method'),method_context_id=context_id,intermediate_latex=[math(v) for v in step.intermediates],
            assumptions=step.assumptions,validity=step.validity,check_ids=[]))
    checks=[]
    for i,check in enumerate(answer.checks):
        id='check-'+digest([check.name,str(check.residual),i])
        checks.append(dict(id=id,name=check.name,passed=check.passed,residual_latex=math(check.residual) if check.residual is not None else None,detail=check.detail,step_ids=aliases.get(check.step_id,[])))
        for step in steps:
            if step['id'] in checks[-1]['step_ids']:step['check_ids'].append(id)
    equations=[validate(eq) for eq in answer.equations]
    results={k:dict(expression=str(v),latex=math(v),unit=answer.units.get(k)) for k,v in answer.symbolic_result.items()}
    numerical={k:dict(value=str(v),latex=math(v),unit=answer.units.get(k)) for k,v in answer.numerical_result.items()}
    ordered=[step['id'] for step in steps]
    return dict(method=answer.method,reasoning=answer.reasoning,equations_latex=equations,steps=steps,results=results,numerical=numerical,checks=checks,direction=answer.direction,warnings=answer.warnings,
        presentation_version='1.0',latex_profile=PROFILE,method_contexts=contexts,
        views=dict(result=dict(wanted=answer.wanted,results={k:v for k,v in results.items() if not answer.wanted or k in answer.wanted},numerical={k:v for k,v in numerical.items() if not answer.wanted or k in answer.wanted},direction=answer.direction),
            derivation=dict(equations_latex=equations,step_ids=ordered),
            explanation=dict(step_ids=ordered,method_context_ids=list(contexts),global_check_ids=[c['id'] for c in checks if not c['step_ids']],warnings=answer.warnings)))
