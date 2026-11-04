"""Deterministic Danish keyword/assignment parser and explicit confirmation contract."""
import ast,json,re
from dataclasses import dataclass,field
import sympy as sp
from .problem import Problem,Region,InputError
from .parsing import expression,FUNCTIONS
from .units import si,numerical
from .registry import solve
from .engine import derive
from .curve import line_integrals
from .dimensions import check_solution
from .text_parser_v2 import normalize_text,enrich_v2

GEOMETRIES=['Ukendt','punktladninger','linje','ring','bue','plan','disk','kugle','kugleskal','cylinder','cylinderskal','leder','hulrum','ledning','strømloop','spole','toroid','parallelle ledere','bevægelig stang','generel parameteriseret linje']
WANTED=['E','V','rho','B','force','EMF','current','power','energy','inductance','D','P','Phi','curl_E','div_B']
ALIASES={'force':'F','current':'I','power':'P','energy':'W','inductance':'L'}
@dataclass
class Parsed:
    text:str
    geometry:str='Ukendt'
    data:dict=field(default_factory=dict)
    wanted:list=field(default_factory=list)
    quantities:dict=field(default_factory=dict)
    units:dict=field(default_factory=dict)
    positive:list=field(default_factory=list)
    assumptions:list=field(default_factory=list)
    warnings:list=field(default_factory=list)
    confidence:dict=field(default_factory=dict)
    normalized_text:str=''


def parse(text,known='',geometry='Ukendt',wanted=None):
    if len(text)+len(known)>16000:raise InputError('Teksten er for lang; højst 16000 tegn.')
    normalized=normalize_text(text);normalized_known=normalize_text(known)
    out=Parsed(text,geometry,wanted=list(wanted or []),normalized_text=normalized);lower=normalized.lower()
    patterns=[('bevægelig stang',r'ledende stang|bevægelig stang'),('parallelle ledere',r'parallelle ledere'),('generel parameteriseret linje',r'parameteriseret'),('cylinderskal',r'cylinderskal|hul cylinder'),('kugleskal',r'kugleskal'),('cylinder',r'cylinder'),('kugle',r'kugle'),('ring',r'\bring\b'),('bue',r'\bbue\b'),('plan',r'\bplan\b'),('disk',r'\bdisk\b'),('toroid',r'toroid'),('spole',r'spole'),('punktladninger',r'punktladning'),('ledning',r'ledning')]
    matches=[g for g,p in patterns if re.search(p,lower)]
    if geometry=='Ukendt' and matches:
        # Overlapping shell/base nouns are one geometry, distinct sources remain ambiguous.
        matches=[g for g in matches if not (g=='cylinder' and 'cylinderskal' in matches) and not (g=='kugle' and 'kugleskal' in matches)]
        if len(matches)==1:out.geometry=matches[0]
        else:out.warnings.append('Flere geometrier nævnes: '+', '.join(matches)+'. Vælg den relevante geometri manuelt.')
    if wanted is None or not wanted:
        for key,pattern in [('E',r'elektriske? felt'),('V',r'potential'),('B',r'magnetfelt|magnetiske? felt'),('EMF',r'elektromotorisk|\bemf\b'),('current',r'bestem strømmen|find strømmen'),('force',r'bestem kraft|find kraft')]:
            if re.search(r'(find|bestem|beregn).*'+pattern,lower):out.wanted.append(key)
    # Assignments occupy their own line or semicolon clause. Prose is deliberately not evaluated.
    for chunk in re.split(r'[;\n]',known+'\n'+text):
        m=re.fullmatch(r'\s*([A-Za-z_]\w*)(?:\(([A-Za-z_]\w*)\))?\s*=\s*(.+?)\s*[.]?\s*',chunk)
        if not m:continue
        name,arg,rhs=m.groups()
        if name in out.data:out.warnings.append('Gentaget størrelse '+name+'; den sidste definition kræver kontrol.')
        numeric=re.fullmatch(r'([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s+(.+)',rhs)
        if numeric:
            try:
                quantity=si(rhs);out.quantities[name]=rhs;out.units[name]=str(quantity.units);out.data[name]=name
            except InputError:out.data[name]=rhs;out.warnings.append('Kunne ikke læse enhed for '+name)
        else:out.data[name]=rhs
        if arg:out.data.setdefault('coordinate' if name in ('rho','J') else 'time' if name=='B' else 'argument',arg)
    if re.search(r'\bradius\s+([A-Za-z_]\w*)',text):out.data['radius']=re.search(r'\bradius\s+([A-Za-z_]\w*)',text).group(1)
    if re.search(r'modstand\s+([A-Za-z_]\w*)',text):out.data['resistance']=re.search(r'modstand\s+([A-Za-z_]\w*)',text).group(1)
    if 'cylinder' in out.geometry and not re.search(r'uendelig|endelig',lower):out.warnings.append('Endelig eller uendelig cylinder er ikke angivet. Dette afgør, om Gauss/Ampère kan anvendes direkte.')
    if any(word in lower for word in ['dielektrikum','jordet','vektorpotentiale','overfladeladning','linjeladning','strømtæthed','vindinger','tidsafhængigt']):out.warnings.append('Materialer, randbetingelser, vindingstal, kildeart og tidsafhængighed skal verificeres i de strukturerede felter.')
    if 'vektorpotentiale' in lower:out.warnings.append('Vektorpotentiale kræver alle tre A-komponenter, coordinates og system.')
    if 'jordet' in lower:out.warnings.append('Jordet leder: V=0-randbetingelsen er genkendt; den kræver en særskilt conductor/images-model.')
    if 'uendelig' in lower:out.data['extent']='infinite'
    elif 'endelig' in lower:out.data['extent']='finite'
    if not out.wanted:out.warnings.append('Søgt størrelse kunne ikke genkendes; vælg den eksplicit.')
    from .text_rules import enrich
    out=enrich(out,extract_wanted=not wanted)
    return enrich_v2(out,extract_wanted=not wanted)


def symbols_for(parsed):
    names=set(re.findall(r'\b[A-Za-z_]\w*\b',json.dumps(parsed.data)))|set(parsed.units)|set(parsed.quantities)
    names-=set(FUNCTIONS)|{'pi','oo'}
    symbols={name:sp.Symbol(name,positive=True) if name in parsed.positive else sp.Symbol(name,real=True) for name in names}
    from .validation import EPS0,MU0
    symbols.update(epsilon_0=EPS0,mu_0=MU0,eps0=EPS0,mu0=MU0)
    return symbols


def build(parsed):
    """Only confirmed data enters a solver. No defaults for missing physical data."""
    d=parsed.data
    if not isinstance(d,dict) or not isinstance(parsed.units,dict) or not isinstance(parsed.quantities,dict):raise InputError('Problemdata, symbolenheder og numeriske værdier skal være JSON-objekter.')
    if not isinstance(parsed.wanted,list) or not isinstance(parsed.assumptions,list):raise InputError('Søges og antagelser skal være lister.')
    symbols=symbols_for(parsed)
    def ex(value):
        if isinstance(value,list):return [ex(v) for v in value]
        if isinstance(value,(int,float)):return sp.Rational(str(value))
        return expression(value,symbols)
    def need(*keys):
        missing=[k for k in keys if k not in d]
        if missing:raise InputError('Kan ikke afgøre problemet entydigt. Mangler: '+', '.join(missing))
        return [ex(d[k]) for k in keys]
    wanted=[ALIASES.get(w,w) for w in parsed.wanted]
    if not wanted:raise InputError('Angiv mindst én søgt størrelse.')
    assumptions=parsed.assumptions;units={symbols[k]:v for k,v in parsed.units.items() if k in symbols}
    common=dict(geometry=parsed.geometry,wanted=wanted,assumptions=assumptions,symbol_units=units)
    if parsed.geometry=='ledning' and 'source' not in d and 'solver_spec' not in d and 'recipe' not in d:
        raise InputError('Ledningsgeometri mangler: længde og feltpunkt samt strømretning kræves til Biot–Savart. En uendelig leder antages ikke.')
    if parsed.geometry=='cylinder' and d.get('extent')=='finite' and 'E' in wanted and 'source' not in d and 'solver_spec' not in d:
        raise InputError('Gauss-loven gælder, men en endelig cylinder har ikke tilstrækkelig symmetri til direkte bestemmelse af E ved et generelt punkt. Angiv fuld Coulomb-/potentialparameterisering.')
    if 'recipe' in d:
        p=Problem('EV','composite',variables={'recipe':d['recipe']},**common)
    elif 'solver_spec' in d:
        spec=d['solver_spec']
        from ..examples import LABELS,INTEGER_FIELDS
        def decode(value,key=''):
            if isinstance(value,dict):return {k:decode(v,k) for k,v in value.items()}
            if isinstance(value,list):return [decode(v,key) for v in value]
            if isinstance(value,str):return value if key in LABELS else ex(value)
            return value
        variables=decode(spec.get('variables',{}))
        if 'coefficients' in variables:variables['coefficients']=[(int(n),c) for n,c in variables['coefficients']]
        p=Problem(spec['domain'],spec['family'],variables=variables,regions=[Region(**decode(r)) for r in spec.get('regions',[])],**(common|{'wanted':spec.get('wanted',wanted)}))
    elif 'charges' in d:
        charges,point=need('charges','point')
        if 'positions' in d:charges=list(zip(charges,ex(d['positions'])))
        variables=dict(charges=charges,point=point)
        if 'test_charge' in d:variables['test_charge']=ex(d['test_charge'])
        p=Problem('EV','point_charges',variables=variables,**common)
    elif 'source' in d:
        source,u,bounds,point=need('source','parameter','bounds','point')
        if 'lambda' in d or 'density' in d:
            density,=need('lambda' if 'lambda' in d else 'density');p=Problem('EV','coulomb_integral',variables=dict(source=source,parameter=u,bounds=bounds,point=point,density=density),**common)
        else:
            current,=need('I');p=Problem('BA','biot_savart',variables=dict(source=source,parameter=u,bounds=bounds,point=point,I=current),**common)
    elif 'rho' in d or 'J' in d:
        coord,=need('coordinate')
        if parsed.geometry not in ('cylinder','cylinderskal','kugle','kugleskal','plan'):
            raise InputError('Ingen tilstrækkelig radial symmetri. Angiv source, parameter, bounds, point og linjetæthed/strøm for integral-fallback.')
        symmetry='cylinder' if 'cylinder' in parsed.geometry else 'sphere' if 'kugle' in parsed.geometry else 'plane'
        if symmetry=='cylinder' and d.get('extent')!='infinite':raise InputError('Uendelig cylinder er ikke bekræftet. Endelig kilde kræver fuld parameterisering til integral-fallback.')
        if coord.is_positive is not True:raise InputError('Radialkoordinaten skal erklæres positiv i symbolantagelserne.')
        if 'regions' in d:
            regions=[Region(ex(r['lower']),ex(r['upper']),ex(r['density']),ex(r.get('permittivity','epsilon_0'))) for r in d['regions']]
        else:
            radius,density=need('radius','rho' if 'rho' in d else 'J')
            if 'skal' in parsed.geometry:raise InputError('Hul geometri kræver regions med indre og ydre radius.')
            regions=[Region(0,radius,density)]
        if 'J' in d:
            if symmetry!='cylinder':raise InputError('Direkte Ampère kræver aksial cylindersymmetri; angiv kurven for Biot–Savart.')
            p=Problem('BA','ampere',variables={'coordinate':coord,'kind':'cylinder'},regions=regions,**common)
        else:p=Problem('EV','gauss_radial',variables={'coordinate':coord,'symmetry':symmetry},regions=regions,**common)
    elif 'V' in d or 'A' in d or 'E' in d or ('B' in d and 'coordinates' in d):
        coordinates,=need('coordinates');variables={'coordinates':coordinates,'system':d.get('system','cartesian')}
        for k in ('V','A','E','B'):
            if k in d:variables[k]=ex(d[k])
        p=Problem('BA' if 'A' in d else 'EV','field_calculus',variables=variables,**common)
    elif 'B' in d or 'B_normal' in d or 'flux' in d:
        time,N=need('time','N');variables={'time':time,'N':N}
        if 'flux' in d:variables['Phi']=ex(d['flux'])
        else:
            B,area=need('B_normal' if 'B_normal' in d else 'B','area');variables.update(B_normal=B,area=area)
        if 'resistance' in d:variables['R']=ex(d['resistance'])
        if 'time_bounds' in d:variables['time_bounds']=ex(d['time_bounds'])
        p=Problem('DYN','dependency',variables=variables,**common)
    else:raise InputError('Ingen sikker beregningsvej. Angiv ladninger, rho/J og regioner, V/E/A eller B/flux med geometri. Parameteriserede linjer kræver source, parameter, bounds og point.')
    p.numerical_values={symbols[k]:v for k,v in parsed.quantities.items()};p.numerical_units={symbols[k]:parsed.units[k] for k in parsed.quantities}
    import math
    for symbol,value in p.numerical_values.items():
        number=float(si(value,p.numerical_units[symbol]).magnitude)
        if not math.isfinite(number):raise InputError('Numerisk værdi skal være endelig: '+str(symbol))
        if symbol.is_positive is True and number<=0:raise InputError('Talværdien modsiger positiv symbolantagelse: '+str(symbol))
    return p


def execute(parsed,evaluate_integrals=False,budget=2):
    p=build(parsed)
    if p.family=='composite':
        from .historical import run
        from .solution import solution
        recipe=p.variables['recipe']
        if recipe.get('expected'):raise InputError('En ny beregningsvej må ikke indeholde facitchecks som input til løsning.')
        results=run(recipe).solutions
        out=solution(p,'Sammensat fysisk beregningsvej','Hvert led bruger den eksisterende registrerede solver og eksplicitte afhængigheder; ingen testbank eller facit anvendes under løsning.',[])
        for name,answer in results.items():
            out.add('Beregningsled '+name+': '+answer.method)
            out.steps.extend(answer.steps);out.equations.extend(answer.equations);out.checks.extend(answer.checks);out.warnings.extend(answer.warnings)
            out.symbolic_result.update(answer.symbolic_result);out.units.update(answer.units)
            out.symbolic_result.update({name+'.'+k:v for k,v in answer.symbolic_result.items()});out.units.update({name+'.'+k:v for k,v in answer.units.items()})
        out.direction='; '.join(name+': '+a.direction for name,a in results.items() if a.direction)
    elif p.family=='faraday' and 'dB_dt' in p.variables:
        out=induced_e(p)
    elif p.family in ('coulomb_integral','biot_savart') and 'parameter' in p.variables:
        out=line_integrals(p,evaluate_integrals,budget)
    elif p.family=='dependency':
        out=derive(p);out.units={'Phi':'Wb','EMF':'V','I':'A','P':'W','W':'J'};check_solution(out,p.symbol_units)
        unresolved=set(p.wanted)-set(out.symbolic_result)
        if unresolved:raise InputError('Mangler for '+', '.join(sorted(unresolved))+': kontrollér uniform_normal_B, orienteret areal/flux, N, resistance og negligible_self_inductance; energy kræver time_bounds.')
    else:out=solve(p)
    if p.family=='gauss_radial':
        if 'P' in p.wanted:
            p.assume('linear_isotropic_dielectric')
            from .validation import EPS0
            out.symbolic_result['P']=sp.simplify(out.symbolic_result['D']-EPS0*out.symbolic_result['E']);out.units['P']='C/m^2'
            out.add('Linjært isotropt dielektrikum: P = D − epsilon_0 E',out.symbolic_result['P']);out.equations.append(r'\mathbf P=\mathbf D-\epsilon_0\mathbf E')
            check_solution(out,p.symbol_units)
        if 'signed_coordinate' in parsed.data:
            from .parsing import expression
            signed=expression(parsed.data['signed_coordinate'],symbols_for(parsed));radial=p.variables['coordinate']
            if p.variables['symmetry']!='plane' or signed.is_real is not True or signed.is_positive is True:raise InputError('Fortegnsudvidelse kræver plansymmetri og en reel koordinat med begge fortegn.')
            for key in ('E','D'):
                out.symbolic_result[key]=sp.sign(signed)*out.symbolic_result[key].subs(radial,sp.Abs(signed))
            out.add('Spejlsymmetri: anvend afstanden |z| og feltets ulige fortegn',out.symbolic_result['E'])
            check_solution(out,p.symbol_units)
    missing=set(p.wanted)-set(out.symbolic_result)
    if missing:raise InputError('Denne beregningsvej bestemmer ikke '+', '.join(sorted(missing))+'. Angiv en anden fysisk relation eller referencebetingelse.')
    if p.numerical_values:numerical(out,p.numerical_values,p.numerical_units)
    if parsed.data.get('numeric_integrals'):
        if p.family not in ('coulomb_integral','biot_savart'):raise InputError('Numerisk integralvalg gælder kun kurvekilder.')
        p.assume('off_source')
        from .curve import numerical_curve
        substitutions={k:sp.Float(str(si(v,p.numerical_units[k]).magnitude)) for k,v in p.numerical_values.items()}
        out.numerical_result.update(numerical_curve(out,substitutions))
    if 'orientation' in parsed.data:
        out.direction='Angivet orientering: '+', '.join(k+'='+str(v) for k,v in parsed.data['orientation'].items())+'. '+out.direction
    return out


def induced_e(p):
    from .solution import solution
    from .validation import positive
    p.assume('circular_symmetry','uniform_axial_B_inside')
    coord,radius,rate=p.require('coordinate','field_radius','dB_dt')
    positive(coord,'Radialkoordinat');positive(radius,'Feltområdets radius')
    enclosed=sp.Piecewise((sp.pi*coord**2,coord<=radius),(sp.pi*radius**2,True))
    emf=-rate*enclosed;e=sp.piecewise_fold(emf/(2*sp.pi*coord))
    out=solution(p,'Faradays lov for induceret elektrisk felt','Cirkulær symmetri gør tangentialfeltet konstant på integrationscirklen; kun det omsluttede magnetiske areal bidrager.',[r'\oint\mathbf E\cdot d\mathbf l=-d\Phi_B/dt',r'E_\phi 2\pi s=-\dot B A_{enc}'],'Positiv phi følger normalens højrehåndsregel. Positiv dB/dt giver negativ phi-retning (Lenz).')
    out.add('Omsluttet areal, indre og ydre region',enclosed);out.add('Faradays cirkulationslov',e)
    out.symbolic_result={'E_phi':e,'EMF':emf};out.units={'E_phi':'V/m','EMF':'V'}
    out.check('Faradays/Lenz relation',e*2*sp.pi*coord+rate*enclosed)
    check_solution(out,p.symbol_units)
    return out
