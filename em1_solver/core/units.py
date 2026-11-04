"""SI conversion and explicit dimensional verification. No implicit units."""
import pint
import sympy as sp
from .problem import InputError

UNITS = pint.UnitRegistry()
CONSTANTS = {'epsilon_0': sp.Float('8.8541878128e-12'), 'mu_0': sp.Float('1.25663706212e-6')}


def si(value, expected_unit=None):
    try:
        quantity = UNITS.Quantity(value)
        if expected_unit is not None:
            quantity = quantity.to(expected_unit)
        return quantity.to_base_units()
    except (pint.PintError, ValueError, TypeError) as exc:
        raise InputError(f'Ugyldig størrelse eller enhed: {value}') from exc


def verify_dimension(value, expected_unit):
    si(value, expected_unit)
    return True


def numerical(solution, substitutions, expected_units=None):
    # A supplied number is in SI; a string with unit is converted before substitution.
    expected_units=expected_units or {}
    repl={}
    for key,value in substitutions.items():
        if isinstance(value,str):
            if key not in expected_units:raise InputError(f'Angiv forventet enhed for {key}, så dimensionskontrollen kan udføres.')
            repl[key]=sp.Float(str(si(value,expected_units[key]).magnitude))
        else:repl[key]=sp.sympify(value)
    if any(not isinstance(v,str) for v in substitutions.values()):
        solution.warnings.append('Enhedsløse numeriske input behandles som SI; deres fysiske dimension er ikke automatisk verificeret.')
    for key, value in solution.symbolic_result.items():
        if isinstance(value, (sp.Basic, sp.MatrixBase)):
            local = {sym: CONSTANTS[sym.name] for sym in value.free_symbols if sym.name in CONSTANTS}
            result = value.subs(local | repl).evalf()
            if not result.free_symbols and not result.has(sp.Integral, sp.Derivative):
                solution.numerical_result[key] = result
    return solution
