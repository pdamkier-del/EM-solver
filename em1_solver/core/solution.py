from dataclasses import dataclass, field
from typing import Any
import sympy as sp


@dataclass
class Step:
    text: str
    expression: Any = None


@dataclass
class Check:
    name: str
    residual: Any = None
    passed: bool | None = None
    detail: str = ''


@dataclass
class Solution:
    recognition: str
    method: str
    reasoning: str
    givens: dict
    wanted: list[str]
    equations: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    symbolic_result: dict = field(default_factory=dict)
    numerical_result: dict = field(default_factory=dict)
    units: dict = field(default_factory=dict)
    direction: str = ''
    checks: list[Check] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stable: bool = False

    def add(self, text, expression=None):
        self.steps.append(Step(text, expression))

    def check(self, name, residual, detail=''):
        residual = sp.simplify(residual)
        values = list(residual) if isinstance(residual, sp.MatrixBase) else [residual]
        states = [v.equals(0) for v in values]
        passed = True if all(x is True for x in states) else False if any(x is False for x in states) else None
        self.checks.append(Check(name, residual, passed, detail))


def solution(problem, method, reasoning, equations, direction=''):
    return Solution(problem.family + ' / ' + problem.geometry, method, reasoning,
                    problem.variables | problem.functions | ({'regions': problem.regions} if problem.regions else {}) | ({'numerical_values':problem.numerical_values,'input_units':problem.numerical_units} if problem.numerical_values else {}),
                    problem.wanted, equations, direction=direction)
