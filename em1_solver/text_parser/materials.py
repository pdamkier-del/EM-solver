"""Recognize a complete scalar constitutive model, never fill an unknown medium."""
import re

def dielectric(f,text):
    if f.get('model')!='gauss_radial' or f.get('source')!='rho' or f.get('wanted')==['Q']:return None
    regions=f.get('active_regions',[])
    if f.get('geometry') not in ('sphere','cylinder') or len(regions)!=1 or regions[0]['lower']!='0':return None
    if re.search(r'negativ\w*.{0,20}permittiv|permittiv.{0,40}negativ',text,re.I|re.S):return None
    if not re.search(r'lineær\w*',text,re.I) or re.search(r'ikke[- ]lineær|anisotrop|ikke[- ]isotrop',text,re.I):return None
    if not re.search(r'isotrop\w*',text,re.I) or not re.search(r'fri\w* (?:volumen)?ladning|volumentæthed af frie ladninger|fri\s+rho_f',text,re.I):return None
    if not re.search(r'vakuum.{0,25}udenfor|udenfor.{0,25}vakuum|omgivet af vakuum',text,re.I|re.S):return None
    if re.search(r'overfladeladning|fladeladning|hulrum|jordet|leder|ekstern|ydre felt|permeabil',text,re.I):return None
    absolute=f['roles'].get('permittivity');relative=f['roles'].get('relative_permittivity')
    if bool(absolute)==bool(relative):return None # conflicting or absent material parameter
    name=absolute or relative
    if not re.fullmatch(r'[A-Za-z_]\w*',name):return None
    return dict(kind='linear_isotropic_dielectric',permittivity=name if absolute else 'epsilon_0*'+name,parameter=name,exterior_permittivity='epsilon_0',source_kind='free_volume_charge',evidence=['Lineært isotropt medium, givet fri ladning og eksplicit vakuum udenfor.'],validity=['Permittiviteten er positiv og skalar; der er ingen yderligere frie fladeladninger.'])
