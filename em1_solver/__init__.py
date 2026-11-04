"""Offline, deterministic EM1 physics. No network or language model."""
from .core.problem import Problem, Region, InputError
from .core.solution import Solution
from .core.registry import solve

__all__ = ['Problem', 'Region', 'Solution', 'InputError', 'solve']
