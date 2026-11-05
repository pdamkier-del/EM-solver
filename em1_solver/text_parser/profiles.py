"""Physics prerequisites for advanced profiles. Each prerequisite needs evidence."""
import re

def complete_profile(out,corrections,put,question):
    f=out.facts;text=out.normalized
    if f['model']=='ampere_maxwell':
        sf=f['sources']['E'];formula=sf['formula']
        if sf['basis']!='cartesian' or not isinstance(formula,list) or formula[:2]!=['0','0']:
            question('orientation','Ampère–Maxwell kræver et eksplicit aksialt elektrisk felt, fx E(t)=E0*t zhat.',status='RED');return
        if not re.search(r'cirkulær|circular',text,re.I):question('plate_shape','Er pladerne cirkulære? Dette skal angives eksplicit.',status='RED')
        if not f['qualifiers']['uniform'] or f['qualifiers']['nonuniform']:question('field_symmetry','Uniformt E mellem pladerne er ikke angivet.',status='RED')
        if not re.search(r'randeffekter.{0,35}(?:ignorer|negliger)|(?:ignor|neglig|ses bort fra).{0,35}randeffekter',text,re.I|re.S):question('edge_effects','Er randeffekter negligeret? Angiv dette eksplicit.',status='RED')
        if 't' not in sf['args']:question('time','Feltets tidsafhængighed skal angives som E(t).',status='RED')
        f['time']='t';f['units']['t']='s'
        matches=re.findall(r'\bB\s*\(([^)]*)\)',text)
        radial=next((x.strip() for args in matches for x in args.split(',') if x.strip() in ('s','r')),None)
        if not radial:question('coordinate','Angiv den radiale observationsafstand i B(s,t) eller B(r,t).',status='RED')
        else:f['coordinate']=radial;f['positive'].append(radial);f['units'][radial]='m'
        if not f['roles'].get('radius'):question('radius','Pladernes radius mangler.',status='RED')
        f['axial_component']=formula[2]
        put('method','Ampère–Maxwell',evidence=['Cirkulær geometri og aksialt homogent E; de øvrige forudsætninger kontrolleres særskilt.'])
        return
    messages={'RC':'RC-kredsløbet kræver begyndelsesladning, kobling og komponentværdier.','RL':'RL-kredsløbet kræver begyndelsesstrøm, spændingskilde og kobling.','volume_integral':'Den endelige kilde kræver fulde rumlige integrationsgrænser og feltpunkt.'}
    question('method',messages[f['model']]+' Brug Avanceret / Manuel; automatisk kompilering af denne profil er endnu ikke understøttet.',status='RED')
