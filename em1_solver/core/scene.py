"""Serializable source objects and explicit spatial relations, not exam presets."""
from dataclasses import dataclass,field,asdict
from .problem import InputError

@dataclass(frozen=True)
class PhysicalObject:
    id:str
    kind:str
    value:str
    position:tuple[str,str,str]
    label:str=''
    evidence:str=''

@dataclass
class Scene:
    coordinate_system:str
    objects:list[PhysicalObject]
    relations:list[dict]=field(default_factory=list)
    conditions:list[str]=field(default_factory=list)

    def validate(self):
        if self.coordinate_system!='cartesian':raise InputError('Punktgeometrien kræver et eksplicit kartesisk koordinatsystem.')
        ids=[obj.id for obj in self.objects]
        if len(ids)!=len(set(ids)) or not ids:raise InputError('Scene-objekter skal have entydige identifikatorer.')
        for obj in self.objects:
            if len(obj.position)!=3 or not all(isinstance(v,str) and v for v in obj.position):raise InputError('Objektets tre koordinater mangler.')
        for relation in self.relations:
            if any(part not in ids for part in relation.get('objects',[])):raise InputError('En relation refererer til et ukendt objekt.')
        return self

    def to_dict(self):
        import json
        return json.loads(json.dumps(asdict(self.validate()),allow_nan=False))
