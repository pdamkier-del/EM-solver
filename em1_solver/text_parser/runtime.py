"""The only text-to-solution entry point; uncertain interpretations cannot execute."""
import sympy as sp
from .parser import analyze
from ..core.task_runtime import run_confirmed
from ..core.problem import InputError


def solve_text(text,corrections=None,*,evaluate=True,timeout=18):
    interpreted=analyze(text,corrections)
    if not interpreted.ready:raise InputError('Oplysninger skal afklares: '+', '.join(interpreted.questions))
    answer=run_confirmed(interpreted.problem,evaluate=evaluate,timeout=timeout)
    if interpreted.facts['aliases']:
        from ..core.new_problem import symbols_for
        symbols=symbols_for(interpreted.problem)
        replacements={symbols[gap]:symbols[hi]-symbols[lo] for gap,(lo,hi) in interpreted.facts['aliases'].items()}
        from dataclasses import is_dataclass,fields,replace
        import re
        def restore(value):
            if isinstance(value,(sp.Basic,sp.MatrixBase)):return value.subs(replacements)
            if is_dataclass(value):return replace(value,**{field.name:restore(getattr(value,field.name)) for field in fields(value)})
            if isinstance(value,dict):return {restore(k):restore(v) for k,v in value.items()}
            if isinstance(value,list):return [restore(v) for v in value]
            if isinstance(value,tuple):return tuple(restore(v) for v in value)
            if isinstance(value,str):
                for gap,(lo,hi) in interpreted.facts['aliases'].items():value=re.sub(r'\b'+re.escape(gap)+r'\b','('+hi+'-'+lo+')',value)
            return value
        answer=restore(answer)
        answer.warnings.append('Regionrækkefølgen gælder som angivet i opgaven: '+', '.join(lo+' < '+hi for lo,hi in interpreted.facts['orders']))
    if 'div_B' in interpreted.facts['wanted'] and any(c.passed is False and c.name=='Magnetisk divergens' for c in answer.checks):answer.warnings.append('Det foreslåede B-felt opfylder ikke div(B)=0 og kan derfor ikke være et almindeligt fysisk magnetfelt i området.')
    scope=interpreted.facts.get('scope')
    if scope:answer.warnings.append('Gyldighedsområde fra opgaven: '+scope+'. Udtrykket er ikke en løsning uden for dette område.')
    return interpreted,answer
