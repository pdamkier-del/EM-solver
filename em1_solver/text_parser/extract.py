"""Lexical facts with source spans. No solver answers or problem identifiers are read."""
import re
from .lexicon import GEOMETRY,QUALIFIERS,WANTED
from .normalize import math_expression
from ..core.units import si
UNIT_ATOM=r'(?:kg|cm|mm|um|m|nC|uC|mC|C|mA|kA|A|mT|uT|T|kV|V|ohm|uF|mF|F|mH|uH|H|ms|us|s|rad|Tesla|volt)'
UNITS=UNIT_ATOM+r'(?:\*\*\(?[-+]?\d+\)?)?(?:\s*[*/]\s*'+UNIT_ATOM+r'(?:\*\*\(?[-+]?\d+\)?)?)*'

SOURCE_ALIASES={'I':'I','rho':'rho','rho_f':'rho','sigma':'sigma','lambda':'lambda','J':'J','V':'V','E':'E','A':'A','B':'B','P':'P','M':'M'}
STOP=r'\b(?:for|og|med|har|hvor|er|som|langs|along|rettet|idet|find|bestem|beregn|vis|udled|kan|på|under|over|mellem|begge|der|the|where|with|find|til|fra|zhat|xhat|yhat|shat|rhat|phihat|thetahat)\b'


def rhs(text,start):
    depth=0;end=start
    for i in range(start,len(text)):
        c=text[i]
        if c in '([':depth+=1
        elif c in ')]':
            depth-=1
            if depth<0:break
        if depth==0 and (c in ';\n' or c=='.' and not (i>0 and i+1<len(text) and text[i-1].isdigit() and text[i+1].isdigit())):break
        if depth==0 and c==',' and not (i>0 and i+1<len(text) and text[i-1].isdigit() and text[i+1].isdigit()):break
        end=i+1
    raw=text[start:end].strip()
    # Vector expressions retain basis labels; scalar prose stops at the first direction.
    vector=bool(re.search(r'\b(?:[xyzrs]|phi|theta)hat\b',raw))
    if not vector:raw=re.split(STOP,raw,1,flags=re.I)[0].strip()
    else:raw=re.split(r'\b(?:Find|Bestem|Beregn|Vis|Udled|Kan|for|hvor|idet|mellem|vinkelret|langs|med|og|er|is)\b',raw,1)[0].strip()
    return raw


def assignments(text):
    rows=[]
    for m in re.finditer(r'(?<![\w<>])([A-Za-z_]\w*)\s*(?:\(([^=]*?)\))?\s*=\s*(?!=)',text):
        if m[2] and not re.fullmatch(r'[A-Za-z_,\s]+',m[2]):continue
        value=rhs(text,m.end())
        rows.append(dict(name=m[1],arguments=[v.strip() for v in (m[2] or '').split(',') if v.strip()],raw=value,evidence=text[m.start():m.end()+len(value)]))
    return rows


def numeric_values(rows):
    values={};units={};constants={};conflicts=[]
    for row in rows:
        raw=row['raw'];name=row['name']
        raw=re.sub(r'(?<=/)(m|cm|mm)([23])\b',r'\1**\2',raw)
        m=re.match(r'([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*('+UNITS+r')(?![A-Za-z0-9_*/])\s*$',raw)
        if m:
            quantity=m[1]+' '+m[2].replace('Tesla','T').replace('volt','V')
            try:q=si(quantity)
            except ValueError:continue
            if name in values and values[name]!=quantity:conflicts.append(name)
            values[name]=quantity;units[name]=str(q.units)
        elif re.fullmatch(r'[-+]?\d+(?:\.\d+)?',raw):constants[name]=raw
    return values,units,constants,conflicts


def geometry(text):
    lower=text.lower();matches=[]
    for name,pattern in GEOMETRY:
        m=re.search(pattern,lower)
        if m:matches.append((name,m.group()))
    names=[n for n,_ in matches]
    shadows={'sphere':'spherical_shell','cylinder':'hollow_cylinder','wire':'cylinder','plane':'current_sheet','ring':'disk'}
    matches=[(n,e) for n,e in matches if not (n in shadows and shadows[n] in names)]
    # A sliding rod is a more specific description than the rails/wires in it.
    if any(n in names for n in ('sliding_rod','rotating_rod')):matches=[x for x in matches if x[0] in ('sliding_rod','rotating_rod')]
    return matches


def qualifiers(text):return {k:bool(re.search(p,text,re.I)) for k,p in QUALIFIERS.items()}


def wanted(text):
    clauses=re.split(r'\b(?:find|bestem|beregn|vis|udled|angiv|fastlæg|undersøg|opsæt|opstil|opskriv|eftervis|argumentér|calculate|determine)\b',text,flags=re.I)
    query=' '.join(clauses[1:]) if len(clauses)>1 else ''
    query=query.split('Opstillingen ændres')[0]
    results=[]
    if re.search(r'kan.{0,25}elektrostatisk',text,re.I):results.append('curl_E')
    if re.search(r'kan.{0,30}fysisk magnetfelt',text,re.I):results.append('div_B')
    for symbol,pattern in WANTED:
        if re.search(pattern,query,re.I):results.append(symbol)
    for symbol in re.findall(r'\b(E|V|rho|B|F|Q|D|P|U|W|C|L|M|I|Phi|EMF|tau)\b',query):
        if symbol not in results:results.append(symbol)
    if 'inductance' in results and ('L' in results or 'M' in results):results.remove('inductance')
    if 'magnetisk dipol' in text.lower() and 'torque' in results:pass
    return results,query


def vector_formula(raw,args,declared):
    basis=re.findall(r'\b([xyzrs]|phi|theta)hat\b',raw)
    if not basis:
        formula=math_expression(raw,args[0] if len(args)==1 else None,declared)
        for coordinate in args:formula=math_expression(formula,coordinate,declared)
        return formula,None
    system='cylindrical' if 's' in basis or 'phi' in basis and 'theta' not in basis else 'spherical' if 'r' in basis or 'theta' in basis else 'cartesian'
    axes={'cartesian':['x','y','z'],'cylindrical':['s','phi','z'],'spherical':['r','theta','phi']}[system]
    raw=raw.strip();factor='1'
    # A common multiplier times a fully parenthesized sum of basis terms.
    m=re.fullmatch(r'([A-Za-z_]\w*|[-+]?\d+)\s*\((.*)\)',raw)
    if m:factor=m[1];raw=m[2]
    terms=list(re.finditer(r'\b([xyzrs]|phi|theta)hat\b',raw))
    values=['0','0','0'];start=0
    for i,term in enumerate(terms):
        coefficient=raw[start:term.start()].strip();axis=term[1];start=term.end()
        if i and not coefficient.startswith(('+','-')):raise ValueError('Der mangler et + eller - mellem vektorkomponenter.')
        if axis not in axes:raise ValueError('Blandede koordinatbaser i vektorfeltet.')
        coefficient=coefficient.rstrip('*').strip()
        if coefficient in ('','+','-'):coefficient+='1'
        coefficient=math_expression(coefficient,args[0] if len(args)==1 else None,declared)
        for coordinate in axes:coefficient=math_expression(coefficient,coordinate,declared)
        values[axes.index(axis)]+='+('+factor+')*('+coefficient+')'
    if raw[start:].strip():raise ValueError('Vektoren kunne ikke læses fuldstændigt.')
    return values,system


def regions(text,source,coordinate):
    if not coordinate:return [],[]
    c=re.escape(coordinate);rows=[];orders=[]
    for m in re.finditer(r'(?<!\w)([A-Za-z_]\w*|0)\s*<\s*'+c+r'\s*<\s*([A-Za-z_]\w*|[0-9.]+)',text):
        lo,hi=m.groups();rows.append(dict(lower=lo,upper=hi,density=source,permittivity='epsilon_0'));orders.append((lo,hi))
    if not rows:
        for m in re.finditer(r'\bfor\s+'+c+r'\s*<\s*([A-Za-z_]\w*)',text):
            rows.append(dict(lower='0',upper=m[1],density=source,permittivity='epsilon_0'));orders.append(('0',m[1]))
    unique=[]
    for row in rows:
        if row not in unique:unique.append(row)
    return unique,orders


def orientation(text):
    result={};evidence={}
    plane=re.search(r'\b(xy|yz|xz|zx)[ -]plan(?:e)?(?:t|et)?\b',text,re.I)
    if plane:result['plane']='zx' if plane[1].lower()=='xz' else plane[1].lower();evidence['plane']=plane.group()
    for key,pattern in [('velocity',r'(?:hastighed|velocity|bevæges|bevaeges|bevæger sig)'),('current',r'(?:strøm|strom|current)'),('B',r'(?:magnetfelt|\bB\b)'),('normal',r'(?:normal)')]:
        m=re.search(pattern+r'[^.;,\n]{0,55}?(?:langs|i|mod|along|=)\s*(?:den\s+)?([+-])\s*([xyz])',text,re.I)
        if m:
            prefix=m.group()[:-2]
            foreign={'current':r'normal|magnetfelt|hastighed|\bB\s*[=(]','B':r'normal|strøm|hastighed','normal':r'magnetfelt|strøm|hastighed','velocity':r'normal|magnetfelt|strøm'}[key]
            if re.search(foreign,prefix,re.I):continue
            result[key]=m[1]+m[2].lower();evidence[key]=m.group()
    if re.search(r'counter[- ]?clockwise|mod uret',text,re.I):result['current_sense']='counterclockwise';evidence['current_sense']='counterclockwise / mod uret'
    elif re.search(r'clockwise|med uret',text,re.I):result['current_sense']='clockwise';evidence['current_sense']='clockwise / med uret'
    if re.search(r'ud af (?:papiret|siden|figurens plan)|out of (?:the )?page',text,re.I):result['page_direction']='out';evidence['page_direction']='ud af siden'
    elif re.search(r'ind i (?:papiret|siden|figurens plan)|into (?:the )?page',text,re.I):result['page_direction']='in';evidence['page_direction']='ind i siden'
    return result,evidence
