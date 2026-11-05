"""Compile evidenced text facts to the unchanged physics engine's public input."""
import copy,re
from ..core.new_problem import Parsed,build

GEOMETRIES={'sphere':'kugle','spherical_shell':'kugleskal','cylinder':'cylinder','hollow_cylinder':'cylinderskal','slab':'plan','line':'linje','wire':'ledning','ring':'ring','arc':'bue','field':'felt'}

def compile_interpretation(interp):
    f=interp.facts;model=f['model'];source=f['source'];geometry=f['geometry']
    allowed={'field_calculus':{'E','rho','B','curl_E','div_B'},'gauss_radial':{'E','D','Q_enc','Q','V'},'ampere_radial':{'B','I','I_enc'},'coulomb_curve':{'E','V','Q'},'biot_curve':{'B'},'ampere_maxwell':{'B','I_displacement','J_displacement'},'faraday':{'Phi','EMF','I','P','W'}}
    if set(f['wanted'])-allowed.get(model,set()):raise ValueError('Den valgte relation bestemmer ikke alle søgte størrelser. Brug Avanceret / Manuel til afhængige beregningstrin.')
    d={};assumptions=[];units=copy.deepcopy(f['units']);positive=list(f['positive'])
    if model=='field_calculus':
        d={source:f['formula'],'coordinates':f['coordinates'],'system':f['system']}
        if source in ('E','A','B') and not isinstance(f['formula'],list):raise ValueError('Vektorfeltet kræver tre komponenter og en eksplicit basis.')
        if 'curl_E' in f['wanted'] and 'elektrostatisk' in interp.normalized.lower():assumptions.append('electrostatic')
    elif model in ('gauss_radial','ampere_radial'):
        rows=copy.deepcopy(f['active_regions'])
        if model=='ampere_radial':
            for row in rows:row['density']=f['axial_component']
        d={source:f.get('axial_component',f['formula']),'coordinate':f['coordinate'],'regions':rows,'extent':f['extent']}
        assumptions=['infinite_cylindrical_symmetry' if 'cylinder' in geometry else 'spherical_symmetry' if geometry in ('sphere','spherical_shell') else 'infinite_planar_symmetry']
        if model=='ampere_radial':assumptions.append('magnetostatic')
        # A declared a<b is represented by b=a+positive_gap solely inside SymPy.
        for index,(lo,hi) in enumerate(f['orders']):
            if lo=='0' or not re.fullmatch(r'[A-Za-z_]\w*',lo) or not re.fullmatch(r'[A-Za-z_]\w*',hi):continue
            gap='parser_gap_'+str(index);positive.append(gap);units[gap]='m'
            f['aliases'][gap]=(lo,hi)
            def replace(value):
                if isinstance(value,str):return re.sub(r'\b'+re.escape(hi)+r'\b','('+lo+'+'+gap+')',value)
                if isinstance(value,list):return [replace(v) for v in value]
                if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
                return value
            d=replace(d)
            # Numerical values must also preserve the stated ordering, not substitute a false gap.
            if lo in f['numbers'] and hi in f['numbers']:
                from ..core.units import si
                width=si(f['numbers'][hi],'m').magnitude-si(f['numbers'][lo],'m').magnitude
                if width<=0:raise ValueError('Talværdierne modsiger '+lo+'<'+hi)
                f['numbers'][gap]=str(width)+' m'
            elif hi in f['numbers']:raise ValueError('Talværdi for ydre grænse kræver også den indre grænse.')
    elif model in ('coulomb_curve','biot_curve'):
        u='parser_u';units[u]='m' if geometry in ('line','wire') else '1'
        if geometry in ('line','wire'):
            curve=['0','0','0'];curve['xyz'.index(f['axis'])]=u
            sign='-' if f['orientation'].get('current','+').startswith('-') else ''
            if model=='biot_curve' and f['orientation']['current'][1]!=f['axis']:raise ValueError('Strømretningen skal følge ledningens akse.')
        else:
            radius=f['roles']['radius'];plane=f['orientation']['plane'];curve=['0','0','0']
            curve['xyz'.index(plane[0])]=radius+'*cos('+u+')';curve['xyz'.index(plane[1])]=radius+'*sin('+u+')'
            sign='-' if f['orientation'].get('current_sense')=='clockwise' else ''
            if geometry=='arc':raise ValueError('En bue kræver også placeringen af startvinklen. Brug den manuelle kurveformular.')
        d=dict(source=curve,parameter=u,bounds=f['bounds'],point=f['point'])
        formula=f['formula']
        args=f['sources'][source]['args']
        if len(args)==1:formula=re.sub(r'\b'+re.escape(args[0])+r'\b',u,formula)
        d['density' if source=='lambda' else 'I']=formula if source=='lambda' else sign+'('+formula+')'
        assumptions=['magnetostatic'] if source=='I' else ['electrostatic']
    elif model=='ampere_maxwell':
        d={'solver_spec':dict(domain='DYN',family='ampere_maxwell',variables=dict(E=f['axial_component'],time=f['time'],coordinate=f['coordinate'],plate_radius=f['roles']['radius']),wanted=f['wanted'])}
        assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects']
    elif model=='faraday':
        orientation=f['orientation'];normal=orientation['normal'];plane=orientation['plane'];axis=({'xy':'z','yz':'x','zx':'y'})[plane]
        if normal[1]!=axis:raise ValueError('Normalen er ikke vinkelret på løkkens plan.')
        formula=f['formula']
        if isinstance(formula,list):
            if f['sources'][source]['basis']!='cartesian':raise ValueError('Flux kræver en kartesisk vektor eller en eksplicit normalprojektion.')
            bn=formula['xyz'.index(axis)]
        else:
            direction=orientation.get('B')
            if not direction:raise ValueError('Et skalart magnetfelt kræver en angivet feltretning.')
            bn='0' if direction[1]!=axis else ('-' if direction.startswith('-') else '')+'('+formula+')'
        if normal.startswith('-'):bn='-('+bn+')'
        if set(re.findall(r'\b(?:x|y|z|r|s|theta|phi)\b',str(formula))):raise ValueError('Ikke-uniformt felt kræver et fladeintegral; B*A er ikke tilstrækkeligt.')
        d=dict(B_normal=bn,area=f['area'],time=f['time'],N=f['turns'])
        assumptions=['uniform_normal_B']
        if f['roles'].get('resistance'):d['resistance']=f['roles']['resistance'];assumptions.append('negligible_self_inductance')
        if f.get('time_bounds'):d['time_bounds']=f['time_bounds']
    else:raise ValueError('Der findes endnu ingen sikker automatisk beregningsvej for denne model.')
    if f.get('signed_coordinate'):
        signed=f['signed_coordinate'];radial='parser_distance';units[radial]='m';positive=[v for v in positive if v!=signed]+[radial]
        from ..core.parsing import expression
        import sympy as sp
        symbol=sp.Symbol(signed,real=True);names=set(re.findall(r'\b[A-Za-z_]\w*\b',str(f['formula'])))
        symbols={n:sp.Symbol(n,real=True) for n in names};symbols[signed]=symbol
        density=expression(f['formula'],symbols)
        if sp.simplify(density-density.subs(symbol,-symbol))!=0:raise ValueError('Slab-tætheden er ikke spejlsymmetrisk.')
        d['coordinate']=radial;d['signed_coordinate']=signed
        for row in d['regions']:row['density']=re.sub(r'\b'+re.escape(signed)+r'\b',radial,row['density'])
    d['orientation']=f['orientation']
    p=Parsed(interp.original,GEOMETRIES.get(geometry,geometry),d,list(f['wanted']),copy.deepcopy(f['numbers']),units,positive,assumptions)
    if model=='gauss_radial' and set(f['wanted'])&{'Q','V'}:
        if geometry not in ('sphere','spherical_shell'):raise ValueError('Denne totale ladnings-/potentialvej kræver kuglesymmetri; angiv ellers integrationsgeometri manuelt.')
        p.data['composition']=dict(seed_wanted=['E'],targets=f['wanted'])
        if f.get('boundary_conditions',{}).get('V_infinity')=='0':p.assumptions.append('V_infinity_zero')
    if model=='ampere_radial' and 'I' in f['wanted']:p.data['composition']=dict(seed_wanted=['B'],targets=f['wanted'],current_scope=f['current_scope'])
    build(p) # Validate shape, SI dimensions and numerical positivity before declaring ready.
    return p
