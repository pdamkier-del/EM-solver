"""Deterministic EM1 text-to-problem pipeline; independent of the frozen manual UI."""
from .parser import analyze
from .runtime import solve_text
