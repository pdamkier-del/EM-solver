"""Conservative point-source clauses. Every source position must be explicit."""
import re
from .normalize import math_expression
from ..core.scene import Scene,PhysicalObject

WORDS=r'\bpunktladning(?:en)?\b'
BAD={'er','med','har','ligger','sidder','placeret','i','en','to','tre','fire'}

def tuple_at(text,start):
    if text[start]!='(':return None
    depth=0;parts=[];begin=start+1
    for i in range(start,len(text)):
        if text[i]=='(':depth+=1
        elif text[i]==')':
            depth-=1
            if depth==0:
                parts.append(text[begin:i].strip())
                return ([math_expression(v) for v in parts],i+1) if len(parts)==3 else None
        elif text[i]==',' and depth==1:parts.append(text[begin:i].strip());begin=i+1
    return None


def complete(out,put,question):
    f=out.facts;text=out.normalized
    given=re.split(r'\b(?:find|bestem|beregn|vis|udled|angiv|opskriv)\b',text,1,flags=re.I)[0]
    if re.search(r'bevæger|hastighed|roter|testladning|ydre felt|eksternt felt|\bvand\b|medium',given,re.I):
        question('source_environment','Bevægelse, testladninger eller et ekstra medium/felt kræver en udvidet model; disse oplysninger ignoreres ikke.',status='RED');return
    from .extract import assignments
    definitions={row['name']:row for row in assignments(given)}
    anchors=list(re.finditer(WORDS,given,re.I));objects=[];incomplete=False
    if len(anchors)>16:
        question('source_budget','Denne beregningsprofil understøtter højst 16 eksplicitte punktkilder. Ingen kilder udelades automatisk.',status='RED');return
    # A plural or unspecified group is not silently reduced to the recognized subset.
    if re.search(r'\bpunktladninger\b',given,re.I):incomplete=True
    for index,anchor in enumerate(anchors):
        end=anchors[index+1].start() if index+1<len(anchors) else len(given)
        clause=given[anchor.end():end];name=re.match(r'\s*([+-]?\s*(?:\d+\s*\*?\s*)?[A-Za-z_]\w*)',clause)
        if not name or name[1].strip().lower() in BAD:incomplete=True;continue
        place=re.search(r'\b(?:ved|i|placeret i|sidder i)\s+(?:punktet\s*)?(?=\(|origo\b)',clause,re.I)
        if not place:incomplete=True;continue
        prefix=clause[name.end():place.start()].strip()
        label=re.sub(r'\s+','',name[1])
        if label in definitions and label not in f['numbers']:incomplete=True;continue
        if prefix.startswith('=') and label in f['numbers']:
            compact=re.sub(r'\s+','',prefix[1:]);quantity=re.sub(r'\s+','',f['numbers'][label])
            if not compact.startswith(quantity):incomplete=True;continue
            prefix=compact[len(quantity):]
        if not re.fullmatch(r'(?:er|sidder|ligger|står|placeret|anbragt|befinder|sig|\s)*',prefix,re.I):incomplete=True;continue
        start=place.end()
        point=(['0','0','0'],start+5) if clause[start:].startswith('origo') else tuple_at(clause,start)
        if not point or any(re.search(r'\bt\b',v) for v in point[0]):incomplete=True;continue
        charge=math_expression(name[1]);label=re.sub(r'\s+','',name[1])
        objects.append(PhysicalObject('charge_'+str(len(objects)+1),'point_charge',charge,tuple(point[0]),label,anchor.group()+clause[:point[1]]))
    if incomplete or not objects:
        question('charge_positions','Alle kildeladninger og deres positioner skal fremgå, fx punktladning q1 ved (a,0,0). Grupper/figurer kræver manuel afklaring.',status='RED');return
    explicit=bool(re.search(r'kartesisk|cartesian|xyz|xy-plan|yz-plan|xz-plan',text,re.I))
    if not explicit:
        question('coordinate_frame','Angiv at koordinaterne er kartesiske; koordinattypen gættes ikke.',status='RED');return
    query=re.split(r'\b(?:find|bestem|beregn|vis|udled|angiv|opskriv)\b',text,maxsplit=1,flags=re.I)
    query=query[1] if len(query)==2 else ''
    points=[]
    if re.search(r'\bi origo\b',query,re.I):points.append(['0','0','0'])
    for match in re.finditer(r'\b(?:punktet|punkt|ved|i)\s*\(',query,re.I):
        position=tuple_at(query,query.index('(',match.start()))
        if position and position[0] not in points:points.append(position[0])
    force=re.search(r'kraft\w*\s+på\s+([A-Za-z_]\w*)',query,re.I);force_index=None
    if 'F' in f['wanted']:
        matches=[i for i,obj in enumerate(objects) if force and obj.label==force[1]]
        if len(matches)==1:force_index=matches[0]
        else:question('force_target','Angiv entydigt hvilken kildeladning kraften søges på, fx kraften på q1.',status='RED')
    needs_point=bool(set(f['wanted'])&{'E','V'})
    if needs_point and force_index is None:
        if len(points)==1:f['point']=points[0]
        else:question('point','Angiv præcis ét kartesisk feltpunkt eller origo. Flere feltpunkter skal løses separat.',status='RED')
    if force_index is not None:
        if points and (len(points)!=1 or points[0]!=list(objects[force_index].position)):question('point_conflict','Feltpunkt og kraftens mål er ikke samme position.',status='RED')
        f['force_on_index']=force_index
    source_objects=list(objects)
    relations=[dict(kind='pair_interaction',objects=[a.id,b.id]) for i,a in enumerate(source_objects) for b in source_objects[:i]]
    if force_index is not None:relations.append(dict(kind='force_on',objects=[source_objects[force_index].id]))
    elif f.get('point'):
        observer=PhysicalObject('observation','observation_point','',tuple(f['point']),'feltpunkt',query)
        objects.append(observer)
        relations.extend(dict(kind='contributes_to_field_at',objects=[obj.id,observer.id]) for obj in source_objects)
    scene=Scene('cartesian',objects,relations,['Der anvendes vakuum uden andre eksterne kilder.','Punktladningerne er stationære og rumligt adskilte; koordinaterne er reelle og endelige.','Feltpunktet ligger uden for kilderne; ved kraft på en kilde udelades selvfeltet.'])
    f['scene']=scene.to_dict();f['charges']=[[obj.value,list(obj.position)] for obj in source_objects];f['model']='point_sources'
    put('source_formula',f['charges'],evidence=[obj.evidence for obj in objects]);put('orientation','cartesian component basis',evidence=['Eksplicit koordinatsystem og kildepositioner'])
    put('method','Coulomb og superposition',evidence=['Diskrete stationære ladninger med eksplicitte positioner'])
