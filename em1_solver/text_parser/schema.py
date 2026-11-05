from dataclasses import dataclass,field,asdict
from typing import Any

@dataclass
class ParsedField:
    value:Any=None
    status:str='RED'
    evidence:list[str]=field(default_factory=list)
    message:str=''
    options:list[str]=field(default_factory=list)
    required:bool=True
    depends_on:list[str]=field(default_factory=list)

@dataclass
class Interpretation:
    original:str
    normalized:str
    fields:dict[str,ParsedField]=field(default_factory=dict)
    facts:dict=field(default_factory=dict)
    problem:Any=None
    notes:list[str]=field(default_factory=list)

    @property
    def questions(self):return {k:v for k,v in self.fields.items() if v.required and v.status!='GREEN' and not any(d in self.fields and self.fields[d].status!='GREEN' for d in v.depends_on)}
    @property
    def ready(self):return self.problem is not None and all(not v.required or v.status=='GREEN' for v in self.fields.values())
    def snapshot(self):
        return dict(fields={k:asdict(v) for k,v in self.fields.items()},facts=self.facts,ready=self.ready,notes=self.notes)
