"""Evidence-preserving local suggestions. No solver, network or language model."""
import re
from .units import si

# Only explicitly written assignments are collected; prose geometry is not a datum.
NUMBER=r'[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?'
UNIT=r'(?:V/m\^2|C/m\^3|A/m\^2|A/m|V/m|mT|uT|µT|μT|T|mH|uH|µH|H|mF|uF|µF|μF|F|mA|kA|A|nC|uC|µC|μC|mC|C|kV|mV|V|ohm|Ω|ms|s|cm|mm|um|µm|μm|m|kg)'

def suggest(text):
    givens=[];conflicts=[];seen={}
    for match in re.finditer(r'\b([A-Za-z_]\w*)\s*=\s*('+NUMBER+r')\s*('+UNIT+r')(?![\w/])',text):
        name,number,unit=match.groups();number=number.replace(',','.');unit=unit.replace('μ','µ').replace('Ω','ohm')
        raw=number+' '+unit
        try:quantity=si(raw)
        except ValueError:continue
        value=dict(name=name,quantity=raw,unit=str(quantity.units),evidence=match.group(),start=match.start(),end=match.end(),status='explicit_assignment_requires_confirmation')
        if name in seen and seen[name]!=raw:conflicts.append(name)
        seen[name]=raw;givens.append(value)
    # All conflicting occurrences stay visible, and none can be transferred.
    for value in givens:
        if value['name'] in conflicts:value['status']='conflict_do_not_transfer'
    functions=[]
    for match in re.finditer(r'\b([A-Za-z_]\w*)\(([A-Za-z_]\w*)\)\s*=\s*([^;\n]+)',text):
        functions.append(dict(name=match[1],variable=match[2],expression=match[3].strip().rstrip('.'),evidence=match.group(),status='unparsed_expression_requires_confirmation'))
    wanted=[]
    for key,pattern in {'E':r'elektrisk\w* felt','V':r'potential','B':r'magnetfelt|magnetisk\w* felt','I':r'strømmen|strømstyrk','EMF':r'\bemf\b|elektromotorisk','F':r'kraft','tau':r'tidskonstant','initial_slope':r'startafled|begyndelsesafled','zero_time':r'nulpassage','extremum_times':r'ekstremum|maksimum|minimum'}.items():
        if re.search(r'(?:find|bestem|beregn|søges)[^.\n]*?(?:'+pattern+r')',text,re.I):wanted.append(key)
    return dict(givens=givens,functions=functions,wanted= wanted,conflicts=sorted(set(conflicts)),assumptions_confirmed=[],note='Kun eksplicitte tildelinger er udtrukket. Geometri, koordinater, antagelser og orientering skal stadig bekræftes.')
