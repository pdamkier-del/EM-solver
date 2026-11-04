"""Small dependency-path arithmetic helper; no exam-specific physics."""
import sympy as sp
from ..core.problem import InputError
from ..core.solution import solution

def algebra(p):
    outputs,units=p.require('outputs','output_units')
    if not outputs or set(outputs)!=set(units):raise InputError('Hvert algebraisk resultat skal have en eksplicit enhed.')
    answer=solution(p,'Sammenkædning af beregnede delresultater',
        'De angivne relationer kombinerer givne størrelser eller tidligere beregnede delresultater. Der tilføjes ingen fysisk antagelse.',[])
    for name,value in outputs.items():
        if not isinstance(value,(sp.Basic,sp.MatrixBase)):raise InputError('Algebraiske resultater skal være symbolske udtryk eller vektorer.')
        answer.add('Indsæt de allerede bestemte størrelser i '+name,value)
        answer.symbolic_result[name]=sp.simplify(value);answer.units[name]=units[name]
    return answer
