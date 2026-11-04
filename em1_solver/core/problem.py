from dataclasses import dataclass, field
from typing import Any
import sympy as sp


class InputError(ValueError):
    """Missing, inconsistent or unsupported physical input."""


@dataclass(frozen=True)
class Region:
    lower: Any
    upper: Any
    density: Any = sp.S.Zero
    permittivity: Any = sp.Symbol('epsilon_0', positive=True)


@dataclass
class Problem:
    domain: str
    family: str
    geometry: str = ''
    variables: dict = field(default_factory=dict)
    functions: dict = field(default_factory=dict)
    regions: list[Region] = field(default_factory=list)
    wanted: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    numerical_values: dict = field(default_factory=dict)
    numerical_units: dict = field(default_factory=dict)
    symbol_units: dict = field(default_factory=dict)

    def require(self, *names):
        data = self.variables | self.functions
        missing = [n for n in names if n not in data]
        if missing:
            raise InputError('Mangler oplysninger: ' + ', '.join(missing))
        return [data[n] for n in names]

    def assume(self, *names):
        missing = set(names) - set(self.assumptions)
        if missing:
            raise InputError('Metoden kræver eksplicit antagelse: ' + ', '.join(sorted(missing)))
