from ..core.solution import solution
from ..core.units import UNITS
from ..core.problem import InputError
import pint

def units(p):
    field,coordinate_power=p.require('field_unit','coordinate_power')
    if not isinstance(coordinate_power,int):raise InputError('Koordinatpotensen skal være et heltal.')
    result=solution(p,'Dimensionsanalyse','Koefficientens dimension findes ved at dividere feltets dimension med længdepotensen i feltudtrykket.',
        [r'[C]=[\mathrm{felt}]/[\mathrm{længde}]^n'])
    try:coefficient=UNITS.Unit(field)/UNITS.meter**coordinate_power
    except (pint.PintError,TypeError,ValueError) as exc:raise InputError('Ukendt eller ugyldig feltenhed.') from exc
    result.symbolic_result={'coefficient_unit':str(coefficient)}
    result.add('Divider feltets enhed med den angivne koordinatpotens',str(coefficient))
    return result
