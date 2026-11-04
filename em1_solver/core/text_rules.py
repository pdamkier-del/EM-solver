"""Conservative prose extraction. Every inferred field remains visible for confirmation."""
import re
import sympy as sp
from .parsing import FUNCTIONS,expression
from .dimensions import dimension,unit_dimension


def enrich(out,extract_wanted=True):
    text=getattr(out,'normalized_text','') or out.text;lower=text.lower();d=out.data
    if re.search(r'\bslab\b',lower):out.geometry='plan'
    if re.search(r'cylindrisk|cylinder',lower):out.geometry='cylinderskal' if re.search(r'hul|skal',lower) else 'cylinder'
    if out.geometry=='Ukendt' and re.search(r'\bring\b',lower) and 'xy-plan' in lower:out.geometry='ring'
    for match in re.finditer(r'\b(rho|J|V|A|B|E|lambda)(?:\(([^=]*?)\))?\s*=\s*',text):
        name,arg=match.groups();tail=text[match.end():]
        rhs=re.split(r'\.\s|;|\n|\s+(?:for|zhat|xhat|yhat|phihat|shat|rhat|Find|Bestem|Kan|med|idet)\b',tail,maxsplit=1)[0].strip().rstrip('.')
        if not rhs or re.search(r'[^A-Za-z0-9_+*/^().,\s-]',rhs):continue
        def multiply(m):
            token=m.group(1);return token+'(' if token in FUNCTIONS else token+'*('
        rhs=re.sub(r'\b([A-Za-z_]\w*)\s*\(',multiply,rhs)
        d[name]=rhs.replace('^','**')
        if name in ('rho','J') and arg and re.fullmatch(r'[rsz]',arg):d['coordinate']=arg
        if name in ('V','A','E') and arg and all(v in ('x','y','z') for v in arg.split(',')):d['coordinates']=arg.split(',')
        if name=='B' and arg=='t':d['time']='t'
        suffix=tail[len(re.split(r'\s+(?:zhat|xhat|yhat)',tail,maxsplit=1)[0]):]
        axis=re.search(r'\b([xyz])hat\b',tail)
        if axis and name in ('A','E'):
            raw=re.split(r'\.\s|;|\n',tail,maxsplit=1)[0].rstrip('.')
            terms=re.findall(r'([+-]?\s*[^+-]+?)\s+([xyz])hat',raw)
            if len(terms)!=len(re.findall(r'\b[xyz]hat\b',raw)):
                d.pop(name,None);out.warnings.append('Vektorfeltet kunne ikke udtrækkes fuldstændigt. Angiv alle tre komponenter.');continue
            vector=['0','0','0']
            for coefficient,ax in terms:
                vector['xyz'.index(ax)]+='+('+coefficient.strip().replace('^','**')+')'
            d[name]=vector;d.setdefault('coordinates',['x','y','z'])
    query=re.split(r'\b(?:Find|Bestem|Beregn)\b',text,maxsplit=1,flags=re.I)
    if len(query)>1 and extract_wanted:
        wanted=re.findall(r'\b(E|V|B|rho|D|P)\b',query[1])
        if re.search(r'\bflux\b',query[1],re.I):wanted.append('Phi')
        if re.search(r'\bemf\b',query[1],re.I):wanted.append('EMF')
        if wanted:out.wanted=list(dict.fromkeys(wanted))
    if 'coordinate' in d and ('rho' in d or 'J' in d):
        coord=d['coordinate'];out.units.setdefault(coord,'m')
        if out.geometry in ('kugle','cylinder'):
            if out.geometry=='kugle' or d.get('extent')=='infinite':
                out.positive.append(coord)
                out.assumptions.append('spherical_symmetry' if out.geometry=='kugle' else 'infinite_cylindrical_symmetry')
                if 'J' in d:out.assumptions.append('magnetostatic')
                out.warnings.append('Metodeforslag bygger på den eksplicit radiale tæthed og kildens udstrækning. Bekræft at ingen andre kilder bryder symmetrien.')
        if 'radius' in d and re.fullmatch(r'[A-Za-z_]\w*',str(d['radius'])):
            radius=d['radius'];out.units.setdefault(radius,'m');out.positive.append(radius)
    if 'coordinates' in d:
        for c in d['coordinates']:out.units.setdefault(c,'m')
        d.setdefault('system','cartesian')
        # A supplied denominator L is only a length if dimensions/text identify it.
        if re.search(r'\bL\b',str(d.get('V',d.get('A','')))):
            out.warnings.append('L i feltfunktionen kræver en dimension; angiv den eksplicit.')
    # Infer a single multiplicative coefficient dimension, never its value or sign.
    for key,target in [('rho','C/m^3'),('J','A/m^2'),('V','V'),('A','T*m')]:
        if key not in d or not isinstance(d[key],str):continue
        names=set(re.findall(r'\b[A-Za-z_]\w*\b',d[key]))-set(FUNCTIONS)-{'pi','oo'}
        sy={n:sp.Symbol(n,positive=True) if n in out.positive else sp.Symbol(n,real=True) for n in names}
        unknown=names-set(out.units)
        if len(unknown)!=1:continue
        name=unknown.pop();symbol=sy[name]
        try:
            value=expression(d[key],sy);factor=sp.cancel(value/symbol)
            if symbol in factor.free_symbols:continue
            fd=dimension(factor,{sy[k]:v for k,v in out.units.items() if k in sy}) or (0,)*4
            dim=tuple(a-b for a,b in zip(unit_dimension(target),fd))
            out.units[name]='*'.join(f'{unit}**({power})' for unit,power in zip(['kg','m','s','A'],dim))
            out.warnings.append('Dimensionen for '+name+' er udledt fra '+key+'; ingen talværdi er antaget.')
        except (ValueError,TypeError,KeyError):pass
    if re.search(r'\binfinite\b',lower):d['extent']='infinite'
    elif re.search(r'\bfinite\b',lower):d['extent']='finite'
    if re.search(r'cylinder',lower) and 'hollow' in lower:out.geometry='cylinderskal'
    if re.search(r'\bsphere\b',lower):out.geometry='kugleskal' if 'shell' in lower else 'kugle'
    turns=re.search(r'\b(N|[0-9]+)\s+(?:turns|vindinger)\b',text)
    if turns:d['N']=turns.group(1)
    definitions=list(re.finditer(r'\b(?:rho|J)\([^)]*\)\s*=',text))
    source='rho' if 'rho' in d else 'J' if 'J' in d else None
    intervals=list(re.finditer(r'\b([A-Za-z_]\w*|0)\s*<\s*([rs])\s*<\s*([A-Za-z_]\w*)',text))
    if source and len(definitions)<=1:
        single=re.search(r'\bfor\s+([rs])\s*<\s*([A-Za-z_]\w*)',text)
        if len(intervals)==1:
            lo,coordinate,hi=intervals[0].groups();d['coordinate']=coordinate
            d['regions']=[dict(lower=lo,upper=hi,density=d[source],permittivity='epsilon_0')]
        elif not intervals and single:
            coordinate,hi=single.groups();d['coordinate']=coordinate
            d['regions']=[dict(lower='0',upper=hi,density=d[source],permittivity='epsilon_0')]
    if len(definitions)>1:out.warnings.append('Flere tæthedsdefinitioner er genkendt; kontrollér hver region i region-builderen. Ingen fælles tæthed antages.')
    plane=re.search(r'\b(xy|yz|zx)[ -]plan(?:e)?\b',lower)
    if plane:d.setdefault('orientation',{})['plane']=plane.group(1)
    if 'normal to plane' in lower:out.warnings.append('Normal på planet er genkendt; normalens fortegn skal bekræftes.')
    out.positive=list(dict.fromkeys(out.positive));out.assumptions=list(dict.fromkeys(out.assumptions))
    return out
