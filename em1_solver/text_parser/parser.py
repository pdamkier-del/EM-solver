"""Domain-specific EM1 parser. Every assumption has textual or user evidence."""
import re,copy
import sympy as sp
from .normalize import normalize,math_expression
from .schema import Interpretation,ParsedField
from . import extract
from .units import infer_units
from ..core.new_problem import Parsed,build,symbols_for
from ..core.parsing import expression,FUNCTIONS
from ..core.units import si
from ..core.validation import EPS0,MU0

SOURCE_UNITS={'rho':'C/m^3','sigma':'C/m^2','lambda':'C/m','J':'A/m^2','I':'A','V':'V','E':'V/m','A':'T*m','B':'T','P':'C/m^2','M':'A/m'}
POSITIVES={'radius','length','inner_radius','outer_radius','resistance','capacitance','inductance','permittivity','permeability','area','mass','plate_distance'}
ROLE_PATTERNS={
 'radius':r'\b(?:radius|ydre radius)\s+([A-Za-z_]\w*)',
 'inner_radius':r'\bindre radius\s+([A-Za-z_]\w*)',
 'outer_radius':r'\bydre radius\s+([A-Za-z_]\w*)',
 'length':r'\b(?:længde|længden|length|kernelængde|solenoidelængde)\s+([A-Za-z_]\w*)',
 'resistance':r'\b(?:modstand|resistans|resistor|resistance)\s+([A-Za-z_]\w*)',
 'area':r'\b(?:areal|arealet|tværsnitsareal|area)\s+([A-Za-z_]\w*)',
 'permittivity':r'\b(?:permittivitet|permittiviteten|permittivity|permitivitet)\s+([A-Za-z_]\w*)',
 'permeability':r'\b(?:permeabilitet|permeabiliteten|permeability)\s+([A-Za-z_]\w*)',
 'mass':r'\b(?:masse|massen|mass)\s+([A-Za-z_]\w*)',
 'plate_distance':r'\b(?:pladeafstand|pladeafstanden|afstand mellem pladerne)\s+([A-Za-z_]\w*)',
 'capacitance':r'\b(?:kapacitans|kapacitansen|capacitance)\s+([A-Za-z_]\w*)',
 'inductance':r'\b(?:induktans|induktansen)\s+([A-Za-z_]\w*)',
}
ROLE_UNITS={'radius':'m','inner_radius':'m','outer_radius':'m','length':'m','resistance':'ohm','area':'m^2','permittivity':'F/m','permeability':'H/m','mass':'kg','plate_distance':'m','capacitance':'F','inductance':'H'}
BAD_ROLE_WORDS={'r','på','i','og','med','som','af','for','til','fra','er','har','a','the','of','radius','konstant','uniform'}-{'r','a'}
GEOMETRY_LABELS={'sphere':'Massiv kugle','spherical_shell':'Kugleskal','cylinder':'Cylinder','hollow_cylinder':'Hul cylinder','wire':'Ledning','line':'Linjeladning','ring':'Ring/loop','arc':'Bue','plane':'Plan','slab':'Slab','disk':'Skive','point_charges':'Punktladninger','capacitor':'Kondensator','solenoid':'Solenoide','toroid':'Toroid','sliding_rod':'Glidende stang','rotating_rod':'Roterende stang','field':'Givet felt/potentiale','dipole':'Magnetisk dipol','conductor':'Leder','parameterized_line':'Parameteriseret kurve','RC':'RC-kredsløb','RL':'RL-kredsløb'}


def analyze(original,corrections=None):
    corrections=corrections or {};text=normalize(original);lower=text.lower();out=Interpretation(original,text)
    f=out.facts
    def put(key,value=None,status='GREEN',evidence=(),message='',options=(),depends=(),required=True):
        out.fields[key]=ParsedField(value,status,list(evidence),message,list(options),required,list(depends));return value
    def question(key,message,options=(),status='YELLOW',depends=()):return put(key,None,status,message=message,options=options,depends=depends)
    rows=extract.assignments(text);declared={r['name'] for r in rows}
    numbers,known_units,constants,conflicts=extract.numeric_values(rows)
    known_units.update({'epsilon_0':'F/m','mu_0':'H/m','eps0':'F/m','mu0':'H/m'})
    f.update(numbers=numbers,units=known_units,constants=constants,roles={},positive=[],orders=[],aliases={},sources={},coordinate=None,qualifiers=extract.qualifiers(text))
    for key,pattern in ROLE_PATTERNS.items():
        for match in re.finditer(pattern,text,re.I):
            name=match[1]
            if name.lower() in BAD_ROLE_WORDS:continue
            f['roles'].setdefault(key,name)
    for key,value in corrections.items():
        if key in ROLE_UNITS:f['roles'][key]=value
    for role,name in f['roles'].items():
        if re.fullmatch(r'[A-Za-z_]\w*',str(name)):
            old=f['units'].get(name)
            if old:
                try:
                    if si('1 '+old,ROLE_UNITS[role]).magnitude is None:pass
                except ValueError:conflicts.append(name)
            f['units'][name]=ROLE_UNITS[role]
            if role in POSITIVES:f['positive'].append(name)
    if '__' in text:question('notation','Programkode eller uunderstøttet identifikator i opgaven. Angiv et rent matematisk udtryk.',status='RED')
    if conflicts:question('symbol_meaning','Samme symbol har modstridende værdier eller fysiske roller: '+', '.join(sorted(set(conflicts))),status='RED')
    # Radius in an interval is an explicit geometric boundary even without the word radius.
    qualifiers=f['qualifiers'];matches=extract.geometry(text)
    if 'geometry' in corrections:matches=[(corrections['geometry'],'Brugerens valg')]
    if re.search(r'\bRC\b',text):matches=[('RC','RC')]
    elif re.search(r'\bRL\b',text):matches=[('RL','RL')]
    if re.search(r'magnetisk\w* dipol|magnetic dipole',text,re.I):matches=[('dipole','magnetisk dipol')]
    if any(n=='sphere' for n,_ in matches) and any(n=='conductor' for n,_ in matches):matches=[m for m in matches if m[0]!='sphere']
    # Multiple geometries are retained instead of a hidden highest-score winner.
    names=list(dict.fromkeys(n for n,_ in matches))
    geometry=names[0] if len(names)==1 else None
    if geometry:put('geometry',geometry,evidence=[e for _,e in matches])
    else:question('geometry','Hvilken geometri skal feltet beregnes for?',list(GEOMETRY_LABELS),status='YELLOW' if matches else 'RED')
    f['geometry']=geometry
    wanted,query=extract.wanted(text)
    if 'wanted' in corrections:wanted=re.split(r'[,;\s]+',corrections['wanted']) if isinstance(corrections['wanted'],str) else corrections['wanted']
    wanted=list(dict.fromkeys(v for v in wanted if v))
    if wanted:put('wanted',wanted,evidence=[query or 'Brugerens valg'])
    else:question('wanted','Hvad skal findes? Fx E, V, B, EMF, I, U.',status='RED')
    f['wanted']=wanted
    sources={};source_errors=[]
    extra=[]
    if 'source_formula' in corrections:
        raw=corrections['source_formula']
        extra=extract.assignments(normalize(raw))
        if not extra:
            raise ValueError('Skriv funktionen med navn og argument, fx rho(s)=k*s; størrelsen må ikke gættes.')
    if extra:
        replaced={r['name'] for r in extra}
        rows=[r for r in rows if r['name'] not in replaced]
    for row in rows+extra:
        name=extract.SOURCE_ALIASES.get(row['name'])
        if name is None and re.fullmatch(r'[EBA][0-9]+',row['name']):name=row['name'][0]
        if name is None:continue
        if row['name'] in numbers:formula=row['name'];basis=None
        else:
            try:formula,basis=extract.vector_formula(row['raw'],row['arguments'],declared)
            except ValueError as exc:source_errors.append((name,str(exc)));continue
        if name in sources and sources[name]['formula']!=formula:source_errors.append((name,'Flere forskellige definitioner af samme kilde kræver manuel regionstilknytning.'))
        sources[name]=dict(formula=formula,args=row['arguments'],basis=basis,evidence=row['evidence'],name=row['name'])
    # Named givens must occur before a request; a requested rho is not a source.
    given_text=re.split(r'\b(?:find|bestem|beregn|vis|udled|angiv|opskriv|eftervis|argumentér)\b',text,1,flags=re.I)[0]
    # Named uniform densities/currents remain symbolic, rather than assigned made-up values.
    for source,pattern in [('rho',r'volumenladning|ladningstæthed|fri\s+rho_f'),('sigma',r'overfladeladning|overfladetæthed'),('lambda',r'linjeladning|linjetæthed|konstant lambda'),('J',r'strømtæthed'),('I',r'fører\s+I\b|strøm\w*\s+(?:er\s+)?I\b'),('M',r'magnetiser\w*|magnetisering')]:
        if source in sources or not re.search(pattern,given_text,re.I):continue
        if source in ('rho','sigma','lambda','J','M') and not f['qualifiers']['uniform']:continue
        token=re.search(r'\b('+source+r'(?:_f|_0|0)?)\b(?!\s*[*/])',given_text)
        if token:sources[source]=dict(formula=math_expression(token[1]),args=[],basis=None,evidence=token.group(),name=token[1])
    if 'I' not in sources:
        for name,unit in list(f['units'].items()):
            try:
                if 'strøm' in lower and si('1 '+unit,'A') and re.search(r'\b'+re.escape(name)+r'\b',text):sources['I']=dict(formula=name,args=[],basis=None,evidence=name,name=name);break
            except ValueError:pass
    # Proportionality is only expanded when the coefficient is actually named.
    if not sources and 'proportional' in lower:
        kind='rho' if 'ladningstæthe' in lower else 'J' if 'strømtæthe' in lower else None
        constant=re.search(r'(?:konstant(?:en)?|proportionalitetskonstant(?:en)?)\s+([A-Za-z_]\w*)',text,re.I)
        power=re.search(r'proportional med\s+([rsz])(?:\*\*\(?([0-9]+)\)?)?',text,re.I)
        if kind and constant and power:sources[kind]=dict(formula=constant[1]+'*'+power[1]+'**'+(power[2] or '1'),args=[power[1]],basis=None,evidence=constant.group()+'; '+power.group(),name=kind)
    if source_errors:question('source_conflict','; '.join(error for _,error in source_errors),status='RED')
    if len(sources)>1:question('source_conflict','Flere uafhængige kilder/felter kræver en eksplicit sammenkobling. Brug Avanceret / Manuel.',status='RED')
    # Scalar B(s,t)=... zhat is a vector source; keep its axial scalar for flux methods.
    f['sources']=sources
    if geometry=='wire' and source_errors==[] and 'J' in sources and qualifiers['infinite'] and f['roles'].get('radius'):
        geometry='cylinder';f['geometry']=geometry;put('geometry',geometry,evidence=['Uendelig leder med cirkulær radius og radial J-funktion'])
    if (not geometry or re.search(r'i cylindriske koordinater',text,re.I)) and any(k in sources for k in ('E','V','A','B')):
        geometry='field';f['geometry']=geometry;put('geometry','field',evidence=['Koordinat-/feltfunktion er givet'])
    source=None
    if 'rho' in sources or 'J' in sources:source='rho' if 'rho' in sources else 'J'
    elif 'V' in sources:source='V'
    elif 'A' in sources:source='A'
    elif 'E' in sources:source='E'
    elif 'lambda' in sources:source='lambda'
    elif 'sigma' in sources:source='sigma'
    elif 'B' in sources:source='B'
    elif 'I' in sources:source='I'
    elif 'M' in sources:source='M'
    elif 'P' in sources:source='P'
    if 'source' in corrections:source=corrections['source']
    # Explicit point charges are a separate source model.
    if geometry=='point_charges':source='q'
    f['source']=source
    if source:put('source',source,evidence=[sources[source]['evidence']] if source in sources else ['Punktladninger'])
    else:question('source','Angiv den givne funktion eller ladning, fx rho(s)=alpha*s**2.',status='RED',depends=['source_formula'])
    if source in sources:
        sf=sources[source];f['formula']=sf['formula'];f['coordinate']=next((a for a in sf['args'] if a in ('r','s','z')),None)
        put('source_formula',sf['formula'],evidence=[sf['evidence']])
    elif source=='q':put('source_formula','point charges',evidence=['Diskrete ladninger'])
    else:question('source_formula','Hvilken ladnings-/strøm-/feltfunktion er givet? Skriv fx rho(s)=alpha*s**2.',status='RED')
    if source_errors and source is None:out.notes.extend(error for _,error in source_errors)
    if source in ('rho','J'):
        coordinate=corrections.get('coordinate',f['coordinate'])
        if not coordinate:
            interval=re.search(r'\b([rs])\s*[<>]',text)
            if interval:coordinate=interval[1]
        if coordinate:f['coordinate']=coordinate;f['units'][coordinate]='m';f['positive'].append(coordinate)
        else:question('coordinate','Hvilket symbol er den radiale afstand?',options=['r','s'],depends=['source_formula'])
    # Actual textual qualifiers only; no infinite wire/cylinder default.
    extent='infinite' if qualifiers['infinite'] else 'finite' if qualifiers['finite'] else None
    if 'extent' in corrections:extent=corrections['extent']
    if geometry in ('cylinder','hollow_cylinder','wire','line','plane','slab') and source in ('rho','J','I','lambda'):
        if extent:put('extent',extent,evidence=[extent if 'extent' in corrections else 'uendelig/endelig i teksten'])
        else:question('extent','Er kilden endelig eller uendelig?',options=['finite','infinite'])
    f['extent']=extent
    if source=='I' and geometry=='wire' and extent=='infinite' and set(wanted)=={'B'}:out.notes.append('En uendelig tynd leder tillader Ampères lov; retning og feltpunkt skal stadig være bestemt.')
    direction,direction_evidence=extract.orientation(text)
    for name in ('plane','normal','current','current_sense','velocity','B'):
        if name in corrections:direction[name]=corrections[name];direction_evidence[name]='Brugerens valg'
    f['orientation']=direction
    if not any(n in out.fields for n in ('orientation',)):put('orientation',direction,evidence=list(direction_evidence.values()))
    if source in ('rho','J') and source in sources and f['coordinate']:
        formula=f['formula'];active,orders=extract.regions(text,formula,f['coordinate'])
        if geometry=='slab':
            slab=re.search(r'\|'+re.escape(f['coordinate'])+r'\|\s*<\s*([A-Za-z_]\w*)',text)
            if slab:
                f['signed_coordinate']=f['coordinate'];f['roles']['radius']=slab[1];f['units'][slab[1]]='m';f['positive'].append(slab[1])
        if 'regions' in corrections:
            # Simple human notation: a<s<b; density. No Python/JSON required.
            active=[];orders=[]
            for segment in corrections['regions'].split(';'):
                match=re.fullmatch(r'\s*(\w+|0)\s*<\s*(\w+)\s*<\s*(\w+)\s*',segment)
                if match:active.append(dict(lower=match[1],upper=match[3],density=formula,permittivity='epsilon_0'));orders.append((match[1],match[3]))
        radius=f['roles'].get('radius') or f['roles'].get('outer_radius')
        if active:
            f['active_regions']=active;f['orders']=orders
            for row in active:
                for name in (row['lower'],row['upper']):
                    if name!='0' and re.fullmatch(r'[A-Za-z_]\w*',str(name)):f['units'][name]='m';f['positive'].append(name)
        elif radius and geometry in ('sphere','cylinder','slab'):
            active=[dict(lower='0',upper=radius,density=formula,permittivity='epsilon_0')];f['active_regions']=active;f['orders']=[('0',radius)]
        else:
            if geometry in ('sphere','cylinder','slab'):
                if 'radius' not in out.fields:question('radius','Hvad hedder den ydre radius/halvtykkelse?',status='RED')
                put('regions',None,'YELLOW',message='Regionen kræver den ydre grænse.',depends=['radius'])
            else:question('regions','Angiv det ladede/strømførende område, fx a<s<b.',status='RED')
        if active:
            display=[]
            for row in active:
                if row['lower']!='0' and not display:display.append(dict(lower='0',upper=row['lower'],density='0'))
                display.append({k:row[k] for k in ('lower','upper','density')})
            display.append(dict(lower=active[-1]['upper'],upper='oo',density='0'))
            put('regions',display,evidence=['Kildens geometri og eksplicitte intervaller'])
    elif source in ('E','V','A','B','I','sigma','lambda','q','M','P'):
        put('regions','model dependent',required=False,evidence=['Ikke en radial volumen-/strømtæthed'])
    else:question('regions','Kildens rumlige udstrækning er ikke bestemt.',depends=['source_formula','geometry'])
    domain='DYN' if geometry in ('RC','RL','sliding_rod','rotating_rod','capacitor') and any(w in wanted for w in ('I','EMF','Phi','P','W','v','tau','B')) or source=='B' and any(w in wanted for w in ('EMF','Phi','I','P','W')) else 'BA' if source in ('J','I','A','M') or geometry=='dipole' else 'EV'
    f['domain']=domain;put('domain',domain,evidence=['Kildetype og søgt fysisk relation'])
    f['model']=None
    # Method identification uses physical structure, never task-specific refusal templates.
    if (source in ('V','E','A') or source=='B' and 'div_B' in wanted) and source in sources and geometry not in ('capacitor','RC','RL'):
        f['model']='field_calculus';put('method','Gradient / divergens / rotation',evidence=['Eksplicit felt eller potentiale'])
        arguments=sources[source]['args']
        basis=sources[source]['basis'] or ('cartesian' if arguments and set(arguments)<=set(['x','y','z']) else 'spherical' if geometry in ('sphere','spherical_shell') else 'cylindrical' if geometry in ('cylinder','hollow_cylinder') else 'cartesian')
        if not sources[source]['basis'] and any(a in ('r','s','theta','phi') for a in sources[source]['args']) and geometry=='field':question('coordinate_system','Hvilket koordinatsystem er potentialet angivet i?',options=['cartesian','cylindrical','spherical'])
        if 'coordinate_system' in corrections:basis=corrections['coordinate_system'];put('coordinate_system',basis,evidence=['Brugerens valg'])
        f['system']=basis
        f['coordinates']=arguments if len(arguments)==3 else ['r','theta','phi'] if basis=='spherical' else ['s','phi','z'] if basis=='cylindrical' else ['x','y','z']
        for c,u in zip(f['coordinates'],{'cartesian':['m','m','m'],'spherical':['m','1','1'],'cylindrical':['m','1','m']}[basis]):f['units'][c]=u
        put('orientation',basis+' component basis',evidence=['Funktionens koordinater / basisvektorer'])
        standard={'cartesian':{'x','y','z'},'spherical':{'r','theta','phi'},'cylindrical':{'s','phi','z'}}[basis]
        if arguments and len(arguments)!=3 and set(arguments)-standard-{'t'}:question('coordinate_mapping','Funktionsargumenterne passer ikke til koordinatsystemets rumlige koordinater. Angiv hele koordinatkortet i Avanceret / Manuel.',status='RED')
        if set(arguments)&{'R','a','b'}:question('boundary_model','Potentialet er angivet ved en fast grænse, ikke som felt i hele rummet. Brug en randværdimodel i Avanceret / Manuel.',status='RED')
    elif source in ('rho','J') and geometry in ('sphere','spherical_shell','cylinder','hollow_cylinder','slab'):
        if geometry in ('cylinder','hollow_cylinder','slab') and extent!='infinite':
            if extent=='finite':f['model']='volume_integral';put('method','Coulomb-integral',evidence=['Endelig kilde, ingen direkte Gauss']);out.notes.append('Fuld rumlig kildeparameterisering kræves for den generelle integralvej.')
            else:put('method',None,'YELLOW',message='Metoden afhænger af kildens udstrækning.',depends=['extent'])
        else:
            f['model']='ampere_radial' if source=='J' else 'gauss_radial'
            put('method','Ampère' if source=='J' else 'Gauss',evidence=['Radial tæthed og tilstrækkelig kildeudstrækning'])
            if isinstance(f.get('formula'),str) and f.get('coordinate'):
                other=set(re.findall(r'\b(?:x|y|z|r|s|theta|phi)\b',f['formula']))-{f['coordinate']}
                if other:question('method','Tætheden bryder den krævede radiale symmetri. Fuld integralmodel er nødvendig.',status='RED')
            if source=='rho':put('orientation','radial' if geometry!='slab' else 'normal / odd mirror field',evidence=['Den erklærede symmetri'])
            else:
                sf=sources[source]
                axial=sf['basis']=='cartesian' and isinstance(sf['formula'],list) and sf['formula'][0]=='0' and sf['formula'][1]=='0'
                if axial:
                    f['axial_component']=sf['formula'][2]
                    for row in f.get('active_regions',[]):row['density']=sf['formula'][2]
                    put('orientation','current +z; B follows right-hand rule',evidence=[sf['evidence']])
                elif direction.get('current') in ('+z','-z'):f['axial_component']=sf['formula'] if direction['current']=='+z' else '-('+sf['formula']+')'
                else:question('current','Hvilken retning har den aksiale strøm?',options=['+z','-z'])
    elif source in ('lambda','I') and geometry in ('line','wire','ring','arc','parameterized_line'):
        f['model']='biot_curve' if source=='I' else 'coulomb_curve';put('method','Biot–Savart' if source=='I' else 'Coulomb-integral',evidence=['Orienteret linjekilde'])
        if geometry in ('line','wire'):
            axis=re.search(r'langs\s+([xyz])(?:-aksen)?',text,re.I)
            if 'axis' in corrections:f['axis']=corrections['axis']
            elif axis:f['axis']=axis[1].lower()
            else:question('axis','Hvilken akse følger linjen/ledningen?',options=['x','y','z'])
            limits=re.search(r'fra\s+(-[A-Za-z_]\w*|[0-9.]+)\s+til\s+([+]?[A-Za-z_]\w*|[0-9.]+)',text,re.I)
            if limits:f['bounds']=[limits[1],limits[2].lstrip('+')]
            elif extent=='infinite':f['bounds']=['-oo','oo']
            elif 'bounds' in corrections:f['bounds']=[s.strip() for s in corrections['bounds'].split(',')]
            else:question('bounds','Hvad er linjens start- og slutkoordinat? Fx -L,L.',status='RED')
        else:
            if not direction.get('plane'):question('plane','Hvilket plan ligger kurven i?',options=['xy','yz','zx'])
            radius=f['roles'].get('radius')
            if not radius:question('radius','Hvad hedder ringens/buens radius?',status='RED')
            f['bounds']=['0','pi'] if re.search(r'halvcirkel|semicircle',text,re.I) else ['0','2*pi'] if geometry=='ring' else None
            if geometry=='arc':question('arc_start','Buens absolutte startvinkel og orientering kræver manuel kurveparameterisering.',status='RED')
            if geometry=='arc' and not f['bounds']:
                angle=re.search(r'(?:vinkel|vinklen)\s+([A-Za-z_]\w*)',text,re.I)
                if angle:f['bounds']=['0',angle[1]];f['units'][angle[1]]='1';f['positive'].append(angle[1])
                elif 'bounds' in corrections:f['bounds']=[v.strip() for v in corrections['bounds'].split(',')]
                else:question('bounds','Hvad er buens start- og slutvinkel i radianer?',status='RED')
        point=re.search(r'(?:punktet|punkt|point|\bi)\s*\(([^()]*)\)',text,re.I)
        if re.search(r'\bi centrum\b|\bi origo\b|at (?:the )?cent(?:re|er)',text,re.I):f['point']=['0','0','0']
        elif point:
            values=[v.strip() for v in point[1].split(',')]
            if len(values)==3:f['point']=values
        if 'point' in corrections:f['point']=[v.strip() for v in corrections['point'].strip('[]()').split(',')]
        if geometry in ('ring','arc') and not re.search(r'\bi centrum\b|\bi origo\b|centrum.{0,20}origo|at (?:the )?cent(?:re|er)',text,re.I) and corrections.get('center')!='origin':question('center','Er kurvens centrum i koordinatsystemets origo?',options=['origin','other'])
        if 'point' not in f:question('point','Hvor skal feltet/potentialet findes? Angiv x,y,z.',status='RED')
        if source=='I':
            if geometry in ('ring','arc'):
                if 'current_sense' not in direction:question('current_sense','Strømretning set fra planets positive normal?',options=['counterclockwise','clockwise'])
            elif direction.get('current') not in ('+x','-x','+y','-y','+z','-z'):question('current','Hvilken retning har strømmen?',options=['+x','-x','+y','-y','+z','-z'])
        elif geometry in ('line','wire') and f.get('axis'):put('orientation','line along '+f['axis'],evidence=['Linjens akse og feltpunkt'])
    elif source=='B' and any(w in wanted for w in ('Phi','EMF','I','P','U','W')):
        f['model']='faraday';put('domain','DYN');f['domain']='DYN';put('method','Fluxintegral og Faraday',evidence=['Tidsafhængigt magnetfelt / flux'])
        sf=sources['B'];f['time']=next((a for a in sf['args'] if a=='t'),'t' if re.search(r'\bt\b',str(sf['formula'])) else None)
        if 'time' in corrections:f['time']=corrections['time']
        if not f['time']:question('time','Hvilket symbol er tiden?',status='RED')
        else:f['units'][f['time']]='s'
        if not direction.get('plane'):question('plane','Hvilket plan ligger løkken i?',options=['xy','yz','zx'])
        if not isinstance(sf['formula'],list) and not direction.get('B'):question('B','Hvilken retning har magnetfeltet?',options=['+x','-x','+y','-y','+z','-z'])
        if not direction.get('normal'):question('normal','Hvilken normal definerer den positive flux/EMF?',options=['+x','-x','+y','-y','+z','-z'],depends=['plane'])
        nmatch=re.search(r'\b(N\d*|\d+)\s+(?:vindinger|turns)',text)
        if nmatch:f['turns']=nmatch[1]
        elif re.search(r'\b(?:en|1|enkelt|single)\s+(?:vinding|turn)\b',text,re.I):f['turns']='1'
        elif 'turns' in corrections:f['turns']=corrections['turns']
        else:question('turns','Hvor mange vindinger er der?',status='RED')
        if geometry=='ring' and f['roles'].get('radius'):f['area']='pi*('+f['roles']['radius']+')**2'
        elif f['roles'].get('area'):f['area']=f['roles']['area']
        elif re.search(r'kvadratisk|square',text,re.I):
            side=re.search(r'\b(?:side|sidelængde|sidelængden)\s+([A-Za-z_]\w*)',text,re.I)
            variable=next((r for r in rows if r['arguments']==['t'] and r['name'] not in extract.SOURCE_ALIASES),None)
            if variable:f['area']='('+math_expression(variable['raw'],declared=declared)+')**2'
            elif side:f['area']='('+side[1]+')**2';f['units'][side[1]]='m';f['positive'].append(side[1])
        if 'area' in corrections:f['area']=math_expression(corrections['area'],declared=declared)
        if 'area' not in f:question('area','Hvad er løkkens areal som funktion af tiden? Fx (a+v*t)**2.',status='RED')
        for symbol in ('I','P','U','W'):
            if symbol in wanted and 'resistance' not in f['roles']:question('resistance','Hvad er kredsens modstand?',status='RED')
        if any(w in wanted for w in ('I','P','U','W')):
            if corrections.get('negligible_inductance')=='no':question('method','Strømberegningen kræver en kredsløbsmodel med selvinduktans. Brug Avanceret / Manuel.',status='RED')
            if not re.search(r'negliger\w* selvinduktans|ses bort fra.*selvinduktans',text,re.I) and corrections.get('negligible_inductance')!='yes':question('negligible_inductance','Kan kredsens selvinduktans negligeres?',options=['yes','no'])
        if any(w in wanted for w in ('U','W')):
            if 'time_bounds' in corrections:f['time_bounds']=[v.strip() for v in corrections['time_bounds'].split(',')]
            else:question('time_bounds','Hvilket tidsinterval skal varmen integreres over? Fx 0,T.',status='RED')
    elif geometry=='capacitor' and source=='E' and 'B' in wanted:
        f['model']='ampere_maxwell';put('domain','DYN');f['domain']='DYN';put('method','Ampère–Maxwell')
    elif geometry in ('RC','RL'):
        f['model']=geometry;put('domain','DYN');f['domain']='DYN';put('method','Kirchhoff og differentialligning')
    else:question('method','Denne kombination er ikke sikkert dækket af automatisk metodevalg. Brug Avanceret / Manuel.',status='RED',depends=['geometry','source_formula'])
    if f.get('model')=='field_calculus':
        scope=re.search(r'(?<!\w)(0|[A-Za-z_]\w*)\s*<\s*([rsxyz])\s*<\s*([A-Za-z_]\w*)',text)
        if scope:f['scope']=scope.group();put('regions',scope.group(),evidence=[scope.group()])
    if source in ('rho','J','I','V') and source in sources:
        sf=sources[source]
        if 't' in sf['args'] or re.search(r'\bt\b',str(sf['formula'])):question('time_model','Tidsafhængige kilder/potentialer kræver yderligere Maxwell-relationer. En statisk direkte metode vælges ikke automatisk.',status='RED')
    for row in rows:
        if row['arguments'] and row['name'] in f['roles'].values():question('moving_geometry','En geometriparameter er en funktion. Dens afhængighed skal indgå eksplicit i beregningen; brug Avanceret / Manuel.',status='RED')
    # Attach only role-driven dimensions; names alone never imply a physical unit.
    if f.get('time'):f['units'][f['time']]='s'
    if f.get('axis'):pass
    for b in f.get('bounds') or []:
        if b in ('0','pi','2*pi','-oo','oo'):continue
        if re.fullmatch(r'[+-]?[A-Za-z_]\w*',b):f['units'][b.lstrip('+-')]='1' if geometry in ('ring','arc') else 'm';f['positive'].append(b.lstrip('+-'))
    for x in f.get('point',[]):
        if re.fullmatch(r'[A-Za-z_]\w*',x):f['units'][x]='m'
    f['positive']=list(dict.fromkeys(f['positive']))
    # Declared dimensionless counts can be literal numbers or named symbols.
    if f.get('turns') and re.fullmatch(r'[A-Za-z_]\w*',f['turns']):f['units'][f['turns']]='1';f['positive'].append(f['turns'])
    expressions=[]
    for name,sf in sources.items():
        if name not in SOURCE_UNITS:continue
        values=sf['formula'] if isinstance(sf['formula'],list) else [sf['formula']]
        for value in values:expressions.append((value,SOURCE_UNITS[name]))
    for name,value in constants.items():
        if any(re.search(r'\b'+re.escape(name)+r'\b',str(sf['formula'])) for sf in sources.values()):question('constant_values','Tal uden enheder kræver eksplicit bekræftelse af enhed og værdi for '+name+'. Tilføj enhed i opgaveteksten.',status='RED')
    if f.get('area'):expressions.append((f['area'],'m^2'))
    if 'units' in corrections:
        for entry in corrections['units'].split(';'):
            name,unit=entry.split(':',1);f['units'][name.strip()]=unit.strip()
    try:
        f['units'],missing=infer_units(expressions,f['units'])
        if missing:question('units','Angiv enheder for '+', '.join(missing)+' som navn:enhed; navn:enhed.',status='YELLOW')
        else:put('units',f['units'],evidence=['Angivne enheder og dimensionelle ligninger'])
    except (ValueError,KeyError,TypeError) as exc:question('units','Enhedskontrol: '+str(exc),status='RED',depends=['source_formula'])
    if f.get('model') in ('RC','RL','ampere_maxwell','volume_integral'):
        # These profiles are recognized, but missing structure is exposed explicitly.
        from .profiles import complete_profile
        complete_profile(out,corrections,put,question)
    if qualifiers['finite'] and qualifiers['infinite']:question('extent_conflict','Både endelig og uendelig nævnes. Knyt udstrækningen til den relevante kilde i manuel mode.',status='RED')
    if re.search(r'Legendre|Laplace|på (?:kugle)?skallen|på overfladen|randbeting|grænsebeting',text,re.I):question('boundary_model','Et randpotentiale er ikke et potentiale i hele rummet. Separation af variable eller andre randbetingelser skal vælges eksplicit i Avanceret / Manuel.',status='RED')
    if re.search(r'dielektr|dieletr|permitiv|permittiv|perminitiv|permeabil|magnetisk material|jordet|hulrum|polariser|magnetiser|lederoverflade|ekstern|ydre felt|external field',lower):question('boundary_model','Materialer, eksterne felter eller randbetingelser kræver en særskilt model. Brug Avanceret / Manuel.',status='RED')
    if source=='rho' and re.search(r'\bmetal\w*|\bledende\b|\bleder\b',lower):question('boundary_model','Volumenladningen og den ledende materialebeskrivelse kræver kontrol af overflade- og randbetingelser. Brug Avanceret / Manuel.',status='RED')
    if re.search(r'\b[a-d]\)\s',text):question('subproblem','Indsæt én delopgave ad gangen med de nødvendige givne oplysninger.',status='RED')
    if re.search(r'angivet.{0,10}(?:på|i) figur|som vist|se figuren|retningen.{0,20}figuren',text,re.I):question('figure','Figuren bærer fysiske oplysninger, som ikke sikkert kan udledes af teksten. Beskriv dem i teksten eller brug Avanceret / Manuel.',status='RED')
    material='dielectric' if re.search(r'dielektr|permittivitet',lower) else 'conductor' if re.search(r'ledende|leder',lower) else 'unspecified'
    put('material',material,required=False,evidence=['Materialeord i teksten'])
    put('symmetry',f.get('model') if f.get('model') in ('gauss_radial','ampere_radial') else 'not established',required=False,evidence=['Geometri, udstrækning og funktionens afhængighed'])
    if all(not v.required or v.status=='GREEN' for v in out.fields.values()):
        try:
            from .compile import compile_interpretation
            out.problem=compile_interpretation(out)
        except (ValueError,KeyError,TypeError) as exc:question('validation','Kan ikke bestemme modellen entydigt: '+str(exc),status='RED')
    return out
