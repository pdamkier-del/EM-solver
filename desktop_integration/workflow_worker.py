"""Text-to-review adapter over existing kernels; all SymPy stays in a killable process.

No historical recipes, answers, network, LLM, or new physics model is used here.
"""
import json,re,sys,copy
import sympy as sp
from em1_solver.core.dimensions import unit_dimension,dimension
from em1_solver.core.task_runtime import block_network
from em1_solver.text_parser.normalize import normalize,math_expression
from em1_solver.text_parser.extract import assignments,UNITS
from em1_solver.text_parser.units import infer_units
from em1_solver.core.units import si
from em1_solver.core.parsing import expression,FUNCTIONS
from em1_solver.assisted_backend import MODELS,respond


def text_normalize(text):
    # Valid one-letter TeX arguments used by ordinary exam prose. Canonicalize,
    # then delegate to the existing restricted parser (never run TeX).
    text=re.sub(r'\\(mathbf|mathrm)\s+([A-Za-z])',r'\\\1{\2}',text)
    text=re.sub(r'(?<=[A-Za-z0-9_}])\s*(?=\\frac)', '*',text)
    return normalize(text)


def names(expr):return set(re.findall(r'\b[A-Za-z_]\w*\b',expr))-set(FUNCTIONS)-{'pi','oo'}


def quantity(raw):
    raw=re.sub(r'(?<=/)(m|cm|mm)([23])\b',r'\1**\2',raw)
    match=re.match(r'([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*('+UNITS+r')(?![\w*/])',raw)
    if not match:return None
    value=match[1]+' '+match[2];si(value);return value


def suggest(text,edits=None):
    if not isinstance(text,str) or not text.strip() or len(text)>16000:raise ValueError('Indsæt en opgave på højst 16000 tegn.')
    edits=edits or {};normal=text_normalize(text);rows=assignments(normal);low=normal.lower()
    potential=[r for r in rows if r['name']=='V' and not r['arguments'] or r['name']=='V' and r['arguments'] not in (['oo'],['infinity'])]
    current=[r for r in rows if r['name']=='J' and len(r['arguments'])==1]
    if potential and current:raise ValueError('Teksten indeholder både V og J. Indsæt ét sammenhængende delproblem ad gangen, eller brug den manuelle solver til kombinationen.')
    base=dict(text=text,normalized=normal,issues=[],quantities={},unit_edits=edits.get('units',{}),evidence=[],wanted=[])
    nums={};conflicts=[]
    for row in rows:
        if row['arguments']:continue
        value=quantity(row['raw'])
        if value:
            if row['name'] in nums and nums[row['name']]!=value:conflicts.append(row['name'])
            nums[row['name']]=value
    if potential and not current:
        if re.search(r'fri\w*\s+ladning|free charge',low):raise ValueError('Denne gennemgang beregner samlet ladning, rho_total=epsilon_0*div(E). Fri ladning i et materiale kræver D-feltet eller materialedata i manuel solver.')
        if len(potential)!=1:raise ValueError('Flere potentialfunktioner er angivet. Indsæt ét delspørgsmål ad gangen.')
        source=edits.get('source',potential[0]['raw']);source=math_expression(source)
        coordinates=potential[0]['arguments'] or ['x','y','z']
        if coordinates!=['x','y','z']:raise ValueError('Denne gennemgang gælder V(x,y,z). Brug manuel solver til andre koordinatsystemer.')
        if 't' in names(source):raise ValueError('Tidsafhængigt potentiale kræver yderligere oplysninger om vektorpotentialet. Vælg en DYN-model manuelt.')
        wanted=[]
        query=re.split(r'\b(?:find|bestem|beregn|søges)\b',normal,flags=re.I)[-1]
        if re.search(r'\bE\b|elektrisk\w* felt',query):wanted.append('E')
        if re.search(r'\brho\b|ladningstæthed',query):wanted.append('rho')
        base.update(kind='potential',model='potential_field',title='Elektrisk felt og ladning fra potentiale',source=source,wanted=wanted,
            reasoning='Funktionen V er givet. E findes med -grad(V), og samlet volumenladning med epsilon_0*div(E).',
            physical_conditions='Elektrostatisk model; kartesiske koordinater x,y,z i meter. rho er samlet volumenladningstæthed, ikke kun fri ladning i et materiale.',
            assumptions=list(MODELS['potential_field']['assumptions']),positive=[],evidence=[potential[0]['evidence']])
        known={n:'m' for n in coordinates};known.update(edits.get('units',{}))
        for n in names(source):
            if n in nums:known[n]=str(si(nums[n]).units)
        inferred,missing=infer_units([(source,'V')],known)
        base['units']={n:inferred[n] for n in names(source)|set(coordinates) if n in inferred}
        for n in missing:base['issues'].append(dict(field='unit:'+n,label='Enhed for '+n,reason='Enheden kan ikke bestemmes entydigt ud fra V alene. Angiv den fra opgaven.'))
        base['quantities']={n:nums[n] for n in names(source)|set(coordinates) if n in nums}
        for row in rows:
            if row['name'] in names(source) and not row['arguments'] and row['name'] not in nums and re.fullmatch(r'[-+]?\d+(?:\.\d+)?',row['raw']):
                base['quantities'][row['name']]=row['raw'];base['issues'].append(dict(field='quantity:'+row['name'],label=row['name'],reason='Tallet er oplyst uden enhed. Tilføj enheden; tallet bruges ikke som en gættet SI-værdi.'))
        base["notes"]=["Gauss’ lov for E giver samlet ladning med epsilon_0; der kræves ingen gættet permittivitet eller vakuumantagelse."]
    elif current and re.search(r'cylind|cylinder',low):
        if len(current)!=1:raise ValueError('Flere J-funktioner er angivet. Brug regionsformularen i manuel solver.')
        coordinate=current[0]['arguments'][0]
        radius_match=re.search(r'\bradius\s+([A-Za-z_]\w*)\b',normal,re.I)
        radius=edits.get('radius_symbol',radius_match[1] if radius_match else '')
        source=edits.get('source',current[0]['raw']);source=re.split(r'\bzhat\b',source)[0].strip().rstrip('*, ')
        try:source=math_expression(source)
        except ValueError:source=''
        if not radius:base['issues'].append(dict(field='radius_symbol',label='Radiussymbol',reason='Radius er nødvendig for strømfordelingens ydergrænse.'))
        try:
            expression(source,{n:sp.Symbol(n,real=True) for n in names(source)})
        except ValueError:source=''
        if not source or re.search(r'[!"?]',source):
            source='';base['issues'].append(dict(field='source',label='J('+coordinate+')',reason='Tæthedsformlen kan ikke aflæses sikkert fra teksten. Ret formlen fra opgave/PDF; ingen parenteser gættes.'))
        if re.search(r'\bendelig(?:e|t)?\s+(?:(?:massiv|lang|cylindrisk)\s+)*(?:cylinder\w*|leder\w*|ledning\w*)|\bendelig\s+længde|\bikke\s+uendelig|\bhul\w*\s+cylinder|\bfinite\b',low):raise ValueError('Denne gennemgang kan ikke bruge en endelig eller hul cylinder som en uendelig massiv cylinder. Brug manuel model.')
        query=' '.join(re.split(r'\b(?:find|bestem|beregn|angiv)\b',normal,flags=re.I)[1:])
        wanted=['B'] if re.search(r'magnetfelt|\bB\s*\(|feltets',query,re.I) else []
        if re.search(r'\bI\s*\(',query):wanted.append('I_enc')
        if re.search(r'totale? strøm|samlet strøm',query,re.I):wanted.append('I')
        base.update(kind='cylinder',model='ampere_regions',title='Cylindrisk strømfordeling – integration og Ampères lov',source=source,coordinate=coordinate,radius_symbol=radius,wanted=wanted,
            reasoning='Strømtætheden integreres over tværsnittet. En eventuel ukendt amplitude bestemmes fra den oplyste samlede strøm. Feltet beregnes i hver region.',
            physical_conditions='Uendelig massiv cylinder, stationær aksial strøm og ikke-magnetisk medium (mu=mu_0). Fortegn angives relativt til +z.',
            assumptions=list(MODELS['ampere_regions']['assumptions']),positive=[coordinate]+([radius] if radius else []),evidence=[current[0]['evidence']])
        if not re.search(r'uendelig|infinite',low):base.setdefault('notes',[]).append('Teksten siger ikke uendelig. Bekræft kun idealmodellen, hvis en lang cylinder må tilnærmes sådan.')
        if re.search(r'permeabilitet|mu_r|ferromagnet|jern',normal,re.I):raise ValueError('Materialets permeabilitet kræver en anden model end mu_0. Brug manuel solver.')
        if not re.search(r'vakuum|ikke.magnetisk|mu_0',low):base.setdefault('notes',[]).append('Permeabiliteten er ikke oplyst. Bekræft kun mu_0 nedenfor, hvis lederen er ikke-magnetisk.')
        base['direction']=edits.get('direction') or ('+z' if re.search(r'positiv\s+z|\+\s*z',normal,re.I) else '-z' if re.search(r'negativ\s+z|-\s*z.retning',normal,re.I) else '')
        if not base['direction'] and re.search(r'længderetning',low):
            base['direction']='+z';base.setdefault('notes',[]).append('Koordinatkonvention: +z vælges langs den oplyste strømretning i lederens længderetning. Der gættes ingen retning i en figur.')
        if base['direction'] not in ('+z','-z'):base['direction']=''
        if not base['direction']:base['issues'].append(dict(field='direction',label='Strømretning',reason='Fortegnet af B kræver strømretning. Vælg +z eller -z.'))
        if radius in nums:base['quantities'][radius]=nums[radius]
        # Coordinate repetitions in part (c) are evaluation points, not conflicting givens.
        points=[]
        for row in rows:
            if row['name']==coordinate and not row['arguments']:
                value=quantity(row['raw'])
                if value and value not in points:points.append(value)
                elif not value:
                    try:
                        point=math_expression(row['raw'])
                        if names(point)<={radius} and point not in points:points.append('0 m' if point=='0' else point)
                    except ValueError:pass
        base['points']=edits.get('points',points)
        known={coordinate:'m'}
        if radius:known[radius]='m'
        density_numbers={n for n,v in nums.items() if unit_dimension(str(si(v).units))==unit_dimension('A/m^2')}
        for n in names(source)|density_numbers:
            if n in nums and n!=coordinate:known[n]=str(si(nums[n]).units);base['quantities'][n]=nums[n]
        known.update(edits.get('units',{}))
        inferred,missing=infer_units([(source,'A/m^2')],known) if source else (known,[])
        base['units']={n:inferred[n] for n in names(source)|{coordinate,radius} if n and n in inferred}
        for n in missing:base['issues'].append(dict(field='unit:'+n,label='Enhed for '+n,reason='Angiv denne kildestørrelses enhed; den kan ikke udledes entydigt.'))
        unknowns=sorted(names(source)-set(base['quantities'])-{coordinate,radius})
        if 'I' in nums or edits.get('total_current'):
            base['total_current']=edits.get('total_current',nums.get('I',''));base['normalization_symbol']=edits.get('normalization_symbol',unknowns[0] if len(unknowns)==1 else '')
            if not base['normalization_symbol']:base['issues'].append(dict(field='normalization_symbol',label='Ukendt amplitude',reason='Vælg hvilken af tæthedens konstanter der bestemmes fra totalstrømmen.'))
        else:
            base['normalization_symbol']=''
            if re.search(r'bestem\s+konstanten',query,re.I) and unknowns:
                base['issues'].append(dict(field='total_current',label='Samlet strøm',reason='En ukendt amplitude kræver totalstrømmen eller en anden uafhængig normaliseringsbetingelse.'))
        if not base['wanted'] and base.get('normalization_symbol'):base['wanted']=['density_amplitude']
        if radius and radius not in nums:base.setdefault('notes',[]).append('Radius er symbolsk. Ingen talværdi gættes; den symbolske løsning kan stadig findes.')
    else:raise ValueError('Ingen sikker gennemgang for denne opgave. Brug Vælg fysisk model eller den eksisterende direkte solver. Ingen fysisk model er valgt automatisk.')
    for n in conflicts:
        if base.get('coordinate')==n:continue
        base['quantities'][n]=edits.get('quantities',{}).get(n,'')
        base['issues'].append(dict(field='quantity:'+n,label=n,reason='Teksten angiver forskellige værdier for samme størrelse. Ret værdien ud fra opgaven.'))
    base['quantities'].update(edits.get('quantities',{}))
    for name,unit in base['units'].items():
        for simple in ('V/m^2','A/m^2','V','m','A','1'):
            if unit_dimension(unit)==unit_dimension(simple):base['units'][name]=simple;break
    def unresolved(issue):
        if issue['field'].startswith('quantity:'):
            name=issue['field'].split(':',1)[1]
            try:si(base['quantities'][name],base['units'][name]);return False
            except (ValueError,KeyError):pass
        return True
    base['issues']=[i for i in base['issues'] if unresolved(i)]
    base['wanted']=edits.get('wanted',base['wanted'])
    if not base['wanted']:base['issues'].append(dict(field='wanted',label='Søgt størrelse',reason='Vælg hvad opgaven beder om; der beregnes ikke et gættet delmål.'))
    return base


def request_for(proposal):
    p=proposal;units=dict(p['units']);numbers=dict(p['quantities']);operations=[]
    for name,value in numbers.items():si(value,units[name])
    if p['kind']=='potential':
        variables=dict(V=p['source'],coordinates=['x','y','z'],system='cartesian');wanted=list(p['wanted'])
    else:
        s=p['coordinate'];radius=p['radius_symbol'];variables=dict(coordinate=s,regions=[dict(lower='0',upper=radius,density=p['source'])]);wanted=list(p['wanted'])
        if p.get('total_current'):
            unknown=p['normalization_symbol'];units['I_given']='A';value=si(p['total_current'],'A')
            signed=-abs(value.magnitude) if p['direction']=='-z' else value.magnitude
            numbers['I_given']=str(signed)+' A';units[unknown]=units.get(unknown,'A/m^2')
            operations=[dict(kind='solve',id='density_amplitude',result='I',variable=unknown,value='I_given',domain='real')]
            if 'B' in wanted:operations.append(dict(kind='evaluate',id='normalized_B',result='B',variable=unknown,value='density_amplitude'))
            wanted=['density_amplitude','normalized_B'] if 'B' in wanted else ['density_amplitude']
            field='normalized_B'
        else:field='B'
        for i,value in enumerate(p.get('points',[]) if 'B' in p['wanted'] else []):
            name='evaluation_radius_'+str(i+1)
            try:
                point=si(value,'m').magnitude;units[name]='m';numbers[name]=value;argument=name
            except ValueError:
                argument=math_expression(value)
                symbols={n:sp.Symbol(n,positive=True) if n in p['positive'] else sp.Symbol(n,real=True) for n in units}
                expr=expression(argument,symbols)
                if expr!=0 and dimension(expr,{symbols[n]:u for n,u in units.items()})!=unit_dimension('m'):raise ValueError('Et evalueringspunkt har ikke længdeenhed: '+value)
                point=expr.subs({symbols[n]:sp.Float(str(si(v,units[n]).magnitude)) for n,v in numbers.items() if n in symbols})
                if point.is_nonnegative is not True:raise ValueError('Evalueringsafstanden er ikke vist ikke-negativ: '+value)
            if point<0:raise ValueError('Radial afstand kan ikke være negativ.')
            operations.append(dict(kind='limit' if point==0 else 'evaluate',id='B_point_'+str(i+1),result=field,variable=s,value='0' if point==0 else argument))
        if len(operations)>8:raise ValueError('For mange evalueringspunkter; vælg højst seks ad gangen.')
    request=dict(schema_version='assisted-1.0',text=p['text'],confirmed=True,variables=variables,units=units,numbers=numbers,positive=p['positive'],assumptions=p['assumptions'],
        subproblems=[dict(id='a',model=p['model'],wanted=wanted,orientation_confirmed=True)])
    if operations:request['subproblems'][0]['operations']=operations
    return request


def main():
    block_network()
    try:
        data=json.loads(sys.stdin.read(32000));proposal=suggest(data['text'],data.get('edits'))
        if data.get('mode')=='solve':
            blockers=[i for i in proposal['issues'] if i['field'] not in ('source',) or not proposal['source']]
            # Explicit edits resolve issues through a new deterministic parse;
            # missing units/source/geometry are never passed to a kernel.
            if blockers:raise ValueError('; '.join(i['label']+': '+i['reason'] for i in blockers))
            request=request_for(proposal);reply=respond(request,solve=True)
            print(json.dumps(dict(proposal=proposal,request=request,reply=reply),ensure_ascii=False))
        else:print(json.dumps(dict(proposal=proposal),ensure_ascii=False))
    except (ValueError,TypeError,KeyError) as exc:print(json.dumps(dict(error=str(exc)),ensure_ascii=False))

if __name__=='__main__':main()
