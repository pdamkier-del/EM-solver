from dataclasses import dataclass, field
from typing import Any
import sympy as sp
import hashlib,json


@dataclass
class Step:
    text: str
    expression: Any = None
    id: str = ''
    title: str = ''
    reasoning: str = ''
    law: str = ''
    assumptions: list[str] = field(default_factory=list)
    validity: list[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    intermediates: list = field(default_factory=list)


@dataclass
class Check:
    name: str
    residual: Any = None
    passed: bool | None = None
    detail: str = ''
    step_id: str | None = None


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
    method_id: str = ''
    source_assumptions: list[str] = field(default_factory=list)

    def add(self, text, expression=None, *, title='', reasoning='', law='', validity=(), intermediates=()):
        # Capture the ACTUAL execution context here, before combined solutions merge.
        context=dict(method_id=self.method_id,method=self.method,reasoning=self.reasoning,equations=list(self.equations),assumptions=list(self.source_assumptions))
        payload=json.dumps([context,text,sp.srepr(expression) if expression is not None else None],sort_keys=True,ensure_ascii=False)
        digest=hashlib.sha256(payload.encode()).hexdigest()[:20]
        occurrence=sum(step.id.startswith('step-'+digest+'-') for step in self.steps)
        step=Step(text,expression,'step-'+digest+'-'+str(occurrence),title or text,reasoning,law,list(self.source_assumptions),list(validity),context,list(intermediates))
        self.steps.append(step)
        return step

    def check(self, name, residual, detail='', *, step=None):
        residual = sp.simplify(residual)
        values = list(residual) if isinstance(residual, sp.MatrixBase) else [residual]
        states = [v.equals(0) for v in values]
        passed = True if all(x is True for x in states) else False if any(x is False for x in states) else None
        self.checks.append(Check(name, residual, passed, detail,step.id if step is not None else None))


def solution(problem, method, reasoning, equations, direction=''):
    return Solution(problem.family + ' / ' + problem.geometry, method, reasoning,
                    problem.variables | problem.functions | ({'regions': problem.regions} if problem.regions else {}) | ({'numerical_values':problem.numerical_values,'input_units':problem.numerical_units} if problem.numerical_values else {}),
                    problem.wanted, equations, direction=direction,method_id=problem.family,source_assumptions=list(problem.assumptions))
