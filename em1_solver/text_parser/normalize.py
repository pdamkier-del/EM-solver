"""Explicit lexical normalization, without eval, LLMs, network or numerical guesses."""
import re,unicodedata
from ..core.parsing import FUNCTIONS
GREEK={'ρ':'rho','α':'alpha','β':'beta','γ':'gamma','δ':'delta','ε':'epsilon','ϵ':'epsilon','λ':'lambda','σ':'sigma','τ':'tau','ω':'omega','φ':'phi','ϕ':'phi','θ':'theta','μ':'mu','µ':'mu','π':'pi','Φ':'Phi','Ω':'Omega'}
SUPER=str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺','0123456789-+')
SUB=str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789')


def normalize(text):
    if len(text)>24000:raise ValueError('Opgaven må højst indeholde 24000 tegn.')
    text=re.sub(r'([A-Za-zæøåÆØÅ]{3,})-\s*\n\s*([a-zæøå])',r'\1\2',text)
    text=re.sub(r'([xyzrs])\u0302',r' \1hat ',text)
    text=text.replace('φ̂',' phihat ').replace('ϕ̂',' phihat ').replace('θ̂',' thetahat ')
    text=re.sub(r'([A-Za-zρσλβφϕεϵμ])([₀₁₂₃₄₅₆₇₈₉]+)',lambda m:m[1]+'_'+m[2].translate(SUB),text)
    text=re.sub(r'[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+',lambda m:'**('+m[0].translate(SUPER)+')',text)
    text=text.replace('−','-').replace('–','-').replace('·','*').replace('∞','oo').replace('Ω','ohm')
    text=re.sub(r'(?<=\d)\s*[µμ](?=[mCAVTFH]\b)',' u',text)
    text=re.sub(r'\b([+-]?\d+),(\d+)(?=\s*(?:cm|mm|m|nC|uC|µC|A|mA|V|mT|T|F|uF|H|s|ohm)\b)',r'\1.\2',text)
    text=re.sub(r'(=\s*[+-]?\d+),(\d+)',r'\1.\2',text)
    for greek,name in GREEK.items():
        text=re.sub(r'(?<=[A-Za-z0-9)])'+re.escape(greek), '*'+greek,text)
        text=re.sub(re.escape(greek)+r'(?=[A-Za-zα-ω])',greek+'*',text)
        text=text.replace(greek,name)
    text=unicodedata.normalize('NFKC',text)
    for name in GREEK.values():text=text.replace('\\'+name,name)
    text=text.replace('\\cdot','*').replace('\\infty','oo').replace('^','**')
    text=re.sub(r'\bln\s*\(', 'log(',text)
    return text


def math_expression(text,coordinate=None,declared=()):
    text=normalize(text).strip().strip('$').replace('{','(').replace('}',')')
    if re.search(r'\b(?:DiracDelta|Heaviside|delta|Piecewise)\s*\(',text):raise ValueError('Fordelinger og stykvise funktioner kræver en eksplicit specialmodel.')
    if re.search(r'__|\b(?:open|eval|exec|import|compile|globals|locals)\b',text):raise ValueError('Programkode er ikke tilladt i matematiske udtryk.')
    if re.search(r'\)\s*\d',text):raise ValueError('Tal efter en parentes er tvetydigt: skriv eksplicit * eller **.')
    atoms=re.findall(r'\*\*|(?:\d+(?:\.\d*)?(?:[eE][-+]?\d+)?|[A-Za-z_]\w*|[()+*/\-,\[\]])',text)
    compact=re.sub(r'\s+','',text)
    if ''.join(atoms)!=compact:raise ValueError('Ukendt matematisk notation: '+text)
    expanded=[]
    for token in atoms:
        if token=='lambda':token='lam'
        if coordinate and token not in set(declared)|set(FUNCTIONS)|{'pi','oo'} and token.endswith(coordinate) and token!=coordinate:
            prefix=token[:-len(coordinate)]
            if len(prefix)==1 or prefix in GREEK.values() or prefix in declared:expanded.extend([prefix,coordinate]);continue
        expanded.append(token)
    result=[]
    for token in expanded:
        if result:
            previous=result[-1]
            left=re.fullmatch(r'[A-Za-z_]\w*|\d+(?:\.\d*)?(?:[eE][-+]?\d+)?',previous) or previous in (')',']')
            right=re.fullmatch(r'[A-Za-z_]\w*|\d+(?:\.\d*)?(?:[eE][-+]?\d+)?',token) or token in ('(','[')
            if token=='(' and re.fullmatch(r'[A-Za-z_]\w*',previous) and previous not in FUNCTIONS:
                if not re.fullmatch(r'(?:[A-Za-z]|rho|lambda|sigma|alpha|beta|gamma|epsilon|mu)_?\d+',previous):raise ValueError('Ukendt funktionsanvendelse '+previous+'(...). Skriv eksplicit * hvis symbolet er en konstant faktor.')
            function_call=token=='(' and previous in FUNCTIONS
            if left and right and not function_call:result.append('*')
        result.append(token)
    return ''.join(result)
