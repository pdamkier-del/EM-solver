"""Fast explicit geometry forms. Presets are visible modelling choices, not inferred facts."""
from dataclasses import dataclass
import copy,re,json
import sympy as sp
from .new_problem import Parsed,build,symbols_for
from .problem import InputError
from .parsing import expression,FUNCTIONS
from .dimensions import dimension,unit_dimension,check_inputs
from .solution import solution
from .units import si

@dataclass(frozen=True)
class Field:
    key:str
    label:str
    default:str
    unit:str='1'
    positive:bool=False

@dataclass(frozen=True)
class Preset:
    label:str
    domain:str
    family:str
    source:str
    fields:tuple
    assumptions:tuple=()
    regions:bool=False
    geometry:str='Ukendt'

def F(k,label,default,unit='1',positive=False):return Field(k,label,default,unit,positive)
P={}
def add(key,label,domain,family,source,fields,assumptions=(),regions=False,geometry='Ukendt'):
    P[key]=Preset(label,domain,family,source,tuple(fields),tuple(assumptions),regions,geometry)
coord=F('coordinate','Koordinat','s','m',True);radius=F('radius','Radius','R','m',True)
point=F('point','Feltpunkt (x,y,z)','[0,0,z]','m');param=F('parameter','Kurveparameter','u')
bounds=[F('lower','Fra','0'),F('upper','Til','2*pi')]
time=F('time','Tid','t','s');B=F('B','Magnetfelt','B0','T');Z=F('R','Modstand','Z','ohm',True)
for key,label,geometry,sym in [('sphere','Massiv kugle','kugle','spherical_symmetry'),('shell','Kugleskal','kugleskal','spherical_symmetry'),('cylinder','Uendelig massiv cylinder','cylinder','infinite_cylindrical_symmetry'),('hollow','Uendelig hul cylinder','cylinderskal','infinite_cylindrical_symmetry'),('slab','Slab','plan','infinite_planar_symmetry')]:
    c=F('coordinate','Radial afstand','r' if 'kugle' in geometry else 's','m',True)
    add('ev_'+key,label,'EV','gauss_radial','rho',[F('function','Ladningstæthed','rho0','C/m^3'),c], [sym],True,geometry)
add('ev_plane','Uendeligt plan','EV','gauss_radial','sigma',[F('function','Overfladeladning','sigma0','C/m^2'),coord],['infinite_planar_symmetry'],False,'plan')
add('ev_infinite_line','Uendelig linje','EV','coulomb_integral','lambda',[F('function','Linjeladning','lambda0','C/m'),F('source','Kildekurve','[0,0,u]','m'),F('parameter','Parameter','u','m'),F('lower','Fra','-oo','m'),F('upper','Til','oo','m'),F('point','Feltpunkt','[s,0,0]','m')],geometry='linje')
for prefix,domain,source in [('ev','EV','lambda'),('ba','BA','I')]:
    for key,label,curve,lo,hi,pu in [('line','Endelig linje' if prefix=='ev' else 'Endelig ledning','[u,0,0]','-L','L','m'),('ring','Ring' if prefix=='ev' else 'Strømloop','[R*cos(u),R*sin(u),0]','0','2*pi','1'),('arc','Bue','[R*cos(u),R*sin(u),0]','0','theta','1')]:
        add(prefix+'_'+key,label,domain,'coulomb_integral' if prefix=='ev' else 'biot_savart',source,[F('function','Linjeladning' if prefix=='ev' else 'Strøm','lambda0' if prefix=='ev' else 'I','C/m' if prefix=='ev' else 'A'),F('source','Kildekurve i valgt plan',curve,'m'),F('parameter','Parameter','u',pu),F('lower','Fra',lo,pu),F('upper','Til (større end Fra)',hi,pu,True),point],['magnetostatic'] if prefix=='ba' else [],geometry='generel parameteriseret linje')
add('ev_points','Punktladninger','EV','point_charges','q',[point],geometry='punktladninger')
add('ev_conductor','Leder (kugleskal)','EV','conductors','q',[F('inner','Indre radius','a','m',True),F('outer','Ydre radius','a+h','m',True),F('function','Lederladning','Q','C'),F('coordinate','Radialkoordinat','r','m',True)],['concentric_spheres','electrostatic'],geometry='leder')
add('ev_capacitor','Kondensator (parallelplader)','EV','capacitance','q',[F('area','Pladeareal','Area','m^2',True),F('distance','Pladeafstand','d','m',True),F('epsilon','Permittivitet','epsilon_0','F/m',True)],['negligible_edge_effects'],geometry='leder')
add('ev_potential','Potentiale / elektrisk felt','EV','field_calculus','V',[F('function','Potentiale','V0*x*y/L^2','V')],geometry='Ukendt')
add('ev_field','Givet elektrisk felt / kontrol','EV','field_calculus','E',[F('function','E-komponenter','[alpha*y,beta*z,gamma*x]','V/m')],['electrostatic'])
add('ev_polarization','Dielektrikum / polarisering','EV','polarization','P',[F('function','P-komponenter','[k*x,k*y,k*z]','C/m^2')],geometry='leder')
add('ba_wire','Uendelig ledning','BA','ampere','I',[F('function','Strøm','I','A'),F('distance','Afstand','s','m',True)],['infinite_straight_wire','magnetostatic'],geometry='ledning')
add('ba_cylinder','Uendelig cylindrisk leder','BA','ampere','J',[F('function','Aksial strømtæthed','J0','A/m^2'),coord],['infinite_cylindrical_symmetry','magnetostatic'],True,'cylinder')
add('ba_sheet','Strømplan','BA','ampere','I',[F('function','Overfladestrøm','K0','A/m')],['infinite_current_sheet','magnetostatic'],geometry='plan')
add('ba_solenoid','Lang solenoide','BA','ampere','I',[F('function','Strøm','I','A'),F('turn_density','Vindinger pr. længde','n','1/m',True)],['ideal_long_solenoid','magnetostatic'],geometry='spole')
add('ba_toroid','Toroid / luftgab','BA','magnetic_material','I',[F('function','Strøm','I','A'),F('N','Vindingstal','N','1',True),F('length','Kernelængde','ell','m',True),F('mu','Kernepermeabilitet','mu','H/m',True),F('gap','Luftgab','g','m',True)],['negligible_leakage','uniform_cross_section'],geometry='toroid')
add('ba_material','Magnetisk materiale','BA','magnetic_material','M',[F('function','Aksial magnetisering','M0','A/m')],['infinite_axial_symmetry','no_free_current','H_infinity_zero'],geometry='cylinder')
add('ba_vector_potential','Vektorpotentiale','BA','field_calculus','A',[F('function','A-komponenter','[0,0,B0*x*y/L]','T*m')])
add('ba_lorentz','Lorentzkraft','BA','lorentz_force','q',[F('q','Ladning','q','C'),F('E','Elektrisk felt','E0','V/m'),B,F('speed','Hastighed','v','m/s')])
add('ba_dipole','Magnetisk dipol','BA','magnetic_dipole_interaction','M',[F('moment','Dipolmomentets størrelse','m0','A*m^2',True),F('B','Magnetfeltets størrelse','B0','T',True),F('theta','Vinkel theta (rad)','theta')])
for key,label in [('fixed','Fast loop'),('moving','Bevægelig loop')]:
    add('dyn_'+key,label,'DYN','faraday','B',[F('function','Normalt magnetfelt','B0*cos(omega*t)','T'),F('area','Orienteret areal','Area' if key=='fixed' else '(a+v*t)^2','m^2',True),time,F('N','Vindingstal','1'),Z],['uniform_normal_B','negligible_self_inductance'],geometry='strømloop')
for key,label in [('sliding','Glidende stang'),('rotating','Roterende stang')]:
    add('dyn_'+key,label,'DYN','motional_emf','B',[B,F('length','Stanglængde','ell','m',True),F('speed','Hastighed' if key=='sliding' else 'Vinkelhastighed','v' if key=='sliding' else 'omega','m/s' if key=='sliding' else '1/s'),time,Z],['negligible_self_inductance','stationary_return_path'],geometry='bevægelig stang')
add('dyn_capacitor','Kondensator / forskydningsstrøm','DYN','ampere_maxwell','E',[F('function','Aksialt E(t)','E0*t^2','V/m'),time,coord,radius],['uniform_axial_E','circular_symmetry','negligible_edge_effects'],geometry='disk')
add('dyn_solenoid','Solenoide / induktans','DYN','inductance_energy','I',[F('function','Strøm','I','A'),F('N','Vindingstal','N','1',True),F('length','Solenoidelængde','ell','m',True),F('area','Tværsnitsareal','Area','m^2',True)],['ideal_long_solenoid','magnetostatic'],geometry='spole')
for kind in ['RL','RC']:
    add('dyn_'+kind.lower(),kind+'-kredsløb','DYN','rc_transient','I' if kind=='RL' else 'q',[Z,time,F('L' if kind=='RL' else 'C','Induktans' if kind=='RL' else 'Kapacitans','Ind' if kind=='RL' else 'C','H' if kind=='RL' else 'F',True),F('function','Påtrykt spænding' if kind=='RL' else 'Initial ladning','V0' if kind=='RL' else 'Q0','V' if kind=='RL' else 'C')],geometry='leder')

UNITS={'x':'m','y':'m','z':'m','r':'m','s':'m','R':'m','a':'m','b':'m','h':'m','L':'m','ell':'m','d':'m','g':'m','t':'s','tau':'s','omega':'1/s','phi':'1','theta':'1','q':'C','Q':'C','Q0':'C','Area':'m^2','Z':'ohm','C':'F','Ind':'H','N':'1','I':'A','J0':'A/m^2','rho0':'C/m^3','lambda0':'C/m','sigma0':'C/m^2','V0':'V','B0':'T','E0':'V/m','v':'m/s','n':'1/m','mu':'H/m','M0':'A/m','m0':'A*m^2','epsilon_0':'F/m','mu_0':'H/m'}
AXES={'+x':[1,0,0],'-x':[-1,0,0],'+y':[0,1,0],'-y':[0,-1,0],'+z':[0,0,1],'-z':[0,0,-1]}
ORIENT={'plane':'xy','normal':'+z','current':'+x','velocity':'+x','B':'+z','E':'+x','moment':'+x'}
WANTS={'gauss_radial':['E','D','V','P'],'coulomb_integral':['E','V','Q'],'point_charges':['E','V','F','U'],'conductors':['E','V'],'capacitance':['C','V','U'],'polarization':['P','rho_bound','sigma_bound'],'ampere':['B','B_positive','B_negative','I_enc'],'biot_savart':['B'],'field_calculus':['E','rho','B','curl_E','div_B'],'magnetic_material':['B','H','H_0','H_1','J_bound','K_bound'],'lorentz_force':['F'],'magnetic_dipole_interaction':['torque','torque_magnitude','torque_theta','U','alignment'],'faraday':['Phi','EMF','I','P','W'],'motional_emf':['EMF','I','P','F_magnetic','F_external'],'ampere_maxwell':['B','J_displacement'],'inductance_energy':['L','U'],'rc_transient':['I','Q','tau','I_charge','U_initial']}

def default_regions(key):
    density=P[key].fields[0].default
    return [dict(lower='a' if key in ('ev_shell','ev_hollow') else '0',upper='a+h' if key in ('ev_shell','ev_hollow') else 'R',density=density,permittivity='epsilon_0')]

def defaults(key,parsed=None):
    preset=P[key];values={f.key:f.default for f in preset.fields}
    if parsed:
        d=parsed.data
        for f in preset.fields:
            if f.key in d and not isinstance(d[f.key],dict):values[f.key]=('['+','.join(map(str,d[f.key]))+']') if isinstance(d[f.key],list) else str(d[f.key])
        if 'function' in values:
            candidate=d.get(preset.source,d.get('density'))
            if candidate is not None:values['function']=('['+','.join(map(str,candidate))+']') if isinstance(candidate,list) else str(candidate)
    return values

def compile_problem(key,values,regions,wanted,orientation=None,assumptions=None,original='',numbers=None,units=None,positive=None,method=None,charges=None):
    if re.search(r'\bendelig\b|\bfinite\b',original,re.I) and key in ('ev_cylinder','ev_hollow','ba_cylinder','ba_wire','ba_solenoid','ev_infinite_line'):
        raise InputError('Endelig kilde er angivet. Dette uendelige preset kan ikke anvende Gauss/Ampère direkte. Vælg en endelig kilde eller en fuld Coulomb-/Biot–Savart-parameterisering under specialiseret metode.')
    preset=P[key];o=ORIENT|dict(orientation or {});assumptions=list(preset.assumptions if assumptions is None else assumptions)
    if key=='ev_infinite_line' and 'V' in wanted:raise InputError('V(infinity)=0 findes ikke for en uendelig linjeladning. Vælg E eller angiv en endelig potentialreference i avanceret struktur.')
    if preset.domain=='EV' and o['plane'] not in ('xy','yz','zx'):raise InputError('Vælg et kartesisk plan.')
    p=Parsed(original,preset.geometry,{},list(wanted),dict(numbers or {}),UNITS|dict(units or {}),list(positive or ['r','s','R','a','b','h','L','ell','d','g','Area','Z','C','Ind','N','mu','B0','m0']),assumptions)
    optional=[]
    if key=='ev_capacitor' and set(wanted)&{'V','U'}:optional.append(F('charge','Given ladning','Q','C'))
    if key=='ev_points' and 'F' in wanted:optional.append(F('test_charge','Testladning','q_test','C'))
    if key in ('dyn_fixed','dyn_moving') and 'W' in wanted:optional.extend([F('time_start','Starttid','0','s'),F('time_end','Sluttid','T','s',True)])
    allfields=[*preset.fields,*optional]
    v={}
    for field in allfields:
        raw=str(values.get(field.key,field.default if field in optional else '')).strip()
        if not raw:raise InputError('Mangler '+field.label)
        if field.key in ('coordinate','parameter','time') and (not re.fullmatch(r'[A-Za-z_]\w*',raw) or raw in FUNCTIONS or raw in ('pi','oo','epsilon_0','mu_0')):raise InputError(field.label+' skal være et variabelnavn, ikke et tal. Angiv evalueringstal i Numeriske værdier med enheder.')
        if field.key=='function' and '=' in raw:raw=raw.split('=',1)[1].strip()
        if field.key=='time_start' and raw=='0':v[field.key]='0';continue
        if re.fullmatch(r'[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?:\s+.+)?',raw) and field.unit!='1':
            quantity=raw if re.search(r'\s',raw) else raw+' '+field.unit
            actual=si(quantity,field.unit)
            if field.positive and actual.magnitude<=0:raise InputError(field.label+' skal være positiv.')
            name='given_'+field.key;p.units[name]=field.unit;p.quantities[name]=quantity
            if field.positive:p.positive.append(name)
            raw=name
        elif re.fullmatch(r'[A-Za-z_]\w*',raw):
            p.units.setdefault(raw,field.unit)
            if field.positive:p.positive.append(raw)
        v[field.key]=raw
    def vector(mag,axis):return [f'({mag})*({component})' for component in AXES[axis]]
    family=method or preset.family
    data={};variables={};use_plain=False
    plane_normal={'xy':'+z','yz':'+x','zx':'+y'}[o['plane']]
    if key in ('ev_plane','ev_slab','ev_line','ev_ring','ev_arc','ba_line','ba_ring','ba_arc','ba_sheet','dyn_fixed','dyn_moving'):
        if abs(sum(x*y for x,y in zip(AXES[o['normal']],AXES[plane_normal])))!=1:raise InputError('Normalen passer ikke til det valgte plan.')
    if preset.regions:
        for spatial in ('r','s','z'):
            if spatial!=v['coordinate'] and re.search(r'\b'+spatial+r'\b',v['function']):raise InputError('Tæthedens koordinat '+spatial+' matcher ikke den angivne integrationskoordinat '+v['coordinate']+'. Ret funktionen eller koordinatnavnet.')
    if 'time' in v and v['time']!='t' and 'function' in v and re.search(r'\bt\b',v['function']):raise InputError('Tidsvariablen matcher ikke t i funktionen. Ret variabelnavnet eller funktionen før differentiation.')
    if family!=preset.family:
        if family=='coulomb_integral' and preset.domain=='EV' or family=='biot_savart' and preset.domain=='BA':
            if not all(k in v for k in ('source','parameter','lower','upper','point')):raise InputError('Integralmetoden kræver kildekurve, parameter, grænser og feltpunkt. Vælg linje/ring/bue eller avanceret struktur.')
        else:raise InputError('Denne metode kræver en anden inputstruktur. Vælg den tilsvarende geometri/preset eller avanceret struktur.')
    if preset.regions:
        if not regions:raise InputError('Der mangler regioner med tæthed og materiale.')
        data=dict(coordinate=v['coordinate'],regions=copy.deepcopy(regions))
        for row in data['regions']:
            if row.get('density')=='@source':row['density']=v['function']
        for i,row in enumerate(data['regions']):
            numeric_bounds={}
            for name,unit in [('lower','m'),('upper','m'),('density','C/m^3' if preset.domain=='EV' else 'A/m^2'),('permittivity','F/m')]:
                raw=str(row.get(name,'epsilon_0' if name=='permittivity' else '')).strip()
                if raw=='0':row[name]='0';numeric_bounds[name]=0;continue
                if re.fullmatch(r'[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?:\s+.+)?',raw):
                    quantity=raw if re.search(r'\s',raw) else raw+' '+unit
                    actual=si(quantity,unit)
                    if actual.magnitude==0:row[name]='0';numeric_bounds[name]=0;continue
                    symbol=f'given_region_{i}_{name}';p.units[symbol]=unit;p.quantities[symbol]=quantity
                    if actual.magnitude>0:p.positive.append(symbol)
                    row[name]=symbol;numeric_bounds[name]=float(actual.magnitude)
            if 'lower' in numeric_bounds and 'upper' in numeric_bounds and numeric_bounds['lower']!=0:
                width=numeric_bounds['upper']-numeric_bounds['lower']
                if width<=0:raise InputError('Regionens øvre grænse skal være større end den nedre.')
                gap=f'given_region_{i}_width';p.units[gap]='m';p.quantities[gap]=str(width)+' m';p.positive.append(gap)
                row['upper']='('+str(row['lower'])+')+'+gap
        if preset.domain=='EV':data.update(rho=v['function'])
        else:data.update(J=v['function'])
        if 'cylinder' in preset.geometry or preset.domain=='BA':data['extent']='infinite'
        if preset.domain=='BA':data['extent']='infinite'
        if preset.domain=='EV' and 'P' in wanted and 'linear_isotropic_dielectric' not in p.assumptions:raise InputError('Bekræft linear_isotropic_dielectric under fysiske vilkår før P beregnes.')
        use_plain=True
    elif family in ('coulomb_integral','biot_savart'):
        curve=v['source']
        if o['normal'].startswith('-'):
            components=expression(curve,{n:sp.Symbol(n) for n in re.findall(r'\b[A-Za-z_]\w*\b',curve) if n not in FUNCTIONS});curve='['+','.join([str(components[0]),'-('+str(components[1])+')',str(components[2])])+']'
        if o['plane']=='yz':curve=curve.replace('[','[',1);components=expression(curve,{n:sp.Symbol(n) for n in re.findall(r'\b[A-Za-z_]\w*\b',curve) if n not in FUNCTIONS});curve=[str(components[2]),str(components[0]),str(components[1])]
        elif o['plane']=='zx':
            components=expression(curve,{n:sp.Symbol(n) for n in re.findall(r'\b[A-Za-z_]\w*\b',curve) if n not in FUNCTIONS});curve=[str(components[1]),str(components[2]),str(components[0])]
        data=dict(source=curve,parameter=v['parameter'],bounds=[v['lower'],v['upper']],point=v['point'])
        data['density' if preset.domain=='EV' else 'I']=('-('+v['function']+')') if preset.domain=='BA' and o['current']=='-parameter' else v['function']
        p.units[v['parameter']]=next(f.unit for f in preset.fields if f.key=='parameter')
        use_plain=True
    elif key=='ev_plane':variables=dict(coordinate=v['coordinate'],symmetry='plane',surface_charges=[[0,v['function']]]);data['regions']=[]
    elif key=='ev_points':variables=dict(charges=charges or [],point=v['point'])
    elif key=='ev_conductor':variables=dict(shells=[[v['inner'],v['outer'],v['function']]],coordinate=v['coordinate'])
    elif key=='ev_capacitor':variables=dict(kind='parallel_plates',epsilon=v['epsilon'],area=v['area'],distance=v['distance'])
    elif key in ('ev_potential','ev_field','ba_vector_potential'):variables=dict(coordinates=['x','y','z'],system='cartesian',**{preset.source:v['function']})
    elif key=='ev_polarization':variables=dict(coordinates=['x','y','z'],system='cartesian',P=v['function'],normal=AXES[o['normal']])
    elif key=='ba_wire':variables=dict(kind='wire',I=v['function'],distance=v['distance'])
    elif key=='ba_sheet':variables=dict(kind='sheet',K=vector(v['function'],o['current']),normal=AXES[o['normal']])
    elif key=='ba_solenoid':variables=dict(kind='solenoid',I=v['function'],turn_density=v['turn_density'])
    elif key=='ba_toroid':variables=dict(kind='magnetic_circuit',N=v['N'],I=v['function'],segments=[[v['length'],v['mu']],[v['gap'],'mu_0']])
    elif key=='ba_material':variables=dict(kind='magnetization',coordinates=['s','phi','z'],system='cylindrical',M=[0,0,v['function']],normal=[1,0,0])
    elif key=='ba_lorentz':variables=dict(kind='force',q=v['q'],v=vector(v['speed'],o['velocity']),B=vector(v['B'],o['B']),E=vector(v['E'],o['E']))
    elif key=='ba_dipole':variables=dict(moment=str(values['moment_vector']),B=str(values['B_vector'])) if 'moment_vector' in values else dict(moment_magnitude=v['moment'],B_magnitude=v['B'],theta=v['theta'])
    elif key.startswith('dyn_') and key in ('dyn_fixed','dyn_moving'):
        if o['normal']!=o['B'] and AXES[o['normal']]!=[-x for x in AXES[o['B']]]:raise InputError('Fluxpreset kræver normalt B. Angiv projektion/fuld flade i avanceret struktur.')
        sign=sum(a*b for a,b in zip(AXES[o['normal']],AXES[o['B']]))
        variables=dict(time=v['time'],N=v['N'],B_normal=f'({sign})*({v["function"]})',area=v['area'])
        if values.get('R','').strip() not in ('','uden'):variables['R']=v['R']
    elif key in ('dyn_sliding','dyn_rotating'):
        velocity=vector(v['speed'],o['velocity']) if key=='dyn_sliding' else [0,f'({v["speed"]})*u',0]
        variables=dict(source=[0,'u',0] if key=='dyn_sliding' else ['u',0,0],parameter='u',bounds=[0,v['length']],v=velocity,B=vector(v['B'],o['B']),time=v['time'],R=v['R']);p.units['u']='m'
    elif key=='dyn_capacitor':variables=dict(E=v['function'],time=v['time'],coordinate=v['coordinate'],plate_radius=v['radius'])
    elif key=='dyn_solenoid':
        # Two existing rules: ideal-solenoid B followed by flux linkage.
        variables=dict(flux=f'mu_0*({v["N"]})*({v["function"]})*({v["area"]})/({v["length"]})',I=v['function'],N=v['N'])
    elif key in ('dyn_rl','dyn_rc'):
        variables=dict(kind='RL' if key=='dyn_rl' else 'RC',time=v['time'],R=v['R'])
        variables.update(dict(L=v['L'],voltage=v['function'],I0=0) if key=='dyn_rl' else dict(C=v['C'],Q0=v['function']))
    else:raise InputError('Preset mangler en struktureret beregningsvej.')
    if key=='ev_capacitor' and 'charge' in v:variables['Q']=v['charge']
    if key=='ev_points' and 'test_charge' in v:variables['test_charge']=v['test_charge']
    if 'time_start' in v:variables['time_bounds']=[v['time_start'],v['time_end']]
    if not use_plain:data={'solver_spec':dict(domain=preset.domain,family=family,variables=variables,regions=data.get('regions',[]),wanted=list(wanted))}
    # Single-coefficient dimensions follow the declared physical role, never a numeric guess.
    p.data=data
    inference=list(allfields)
    for i,row in enumerate(data.get('regions',[])):
        name='region_density_'+str(i);v[name]=str(row['density']);inference.append(F(name,name,v[name],'C/m^3' if preset.domain=='EV' else 'A/m^2'))
    for field in inference:
        raw=v[field.key]
        if field.unit=='1' or field.key in ('source','point','lower','upper','parameter','coordinate'):continue
        try:
            sy=symbols_for(p);value=expression(raw,sy)
            entries=value if isinstance(value,list) else [value]
            for entry in entries:
                explicit=set(units or {})|set(p.quantities)
                coefficients={x for x in entry.free_symbols if str(x) not in explicit and (str(x) not in UNITS or str(x).endswith('0')) and str(x) not in ('epsilon_0','mu_0')}
                unknown=coefficients if len(coefficients)==1 else entry.free_symbols-{sy[n] for n in p.units if n in sy}
                if len(unknown)!=1:continue
                symbol=next(iter(unknown));factor=sp.cancel(entry/symbol)
                if symbol in factor.free_symbols:continue
                fd=dimension(factor,{sy[n]:u for n,u in p.units.items() if n in sy}) or (0,)*4
                dim=tuple(a-b for a,b in zip(unit_dimension(field.unit),fd))
                p.units[str(symbol)]='*'.join(f'{u}**({power})' for u,power in zip(['kg','m','s','A'],dim))
        except (ValueError,TypeError,AttributeError):pass
    if preset.regions or key=='ba_wire':visible={'source_axis':'+z','field_basis':'+phi'} if preset.domain=='BA' else {'field_basis':'radial'}
    else:visible={}
    if preset.geometry=='plan':visible={'plane':o['plane'],'normal':o['normal']}
    if family in ('coulomb_integral','biot_savart'):visible={'plane':o['plane'],'normal':o['normal'],'current':o['current'] if preset.domain=='BA' else 'not applicable'}
    if key in ('dyn_fixed','dyn_moving','ba_sheet'):visible={k:o[k] for k in ('plane','normal','B' if preset.domain=='DYN' else 'current')}
    if key=='dyn_sliding':visible={'rod':'+y','velocity':o['velocity'],'B':o['B']}
    if key=='dyn_rotating':visible={'rod':'+x','rotation_axis':'+z','B':o['B']}
    if key=='ba_lorentz':visible={k:o[k] for k in ('E','B','velocity')}
    if key=='ba_material':visible={'M_axis':'+z','outward_normal':'+s'}
    if key=='ba_dipole':visible={'theta':'from B toward m','components':'Cartesian'}
    p.data['orientation']=visible
    return p


def validate(parsed):
    """Cheap preflight; no integration or differential equation solving in the UI."""
    problem=build(parsed)
    from .validation import positive
    requirements={'gauss_radial':{'sphere':['spherical_symmetry'],'cylinder':['infinite_cylindrical_symmetry'],'plane':['infinite_planar_symmetry']} }
    if problem.family=='gauss_radial':problem.assume(*requirements['gauss_radial'][problem.variables['symmetry']])
    if problem.family=='ampere':
        kind=problem.variables['kind'];problem.assume(*{'wire':['infinite_straight_wire','magnetostatic'],'cylinder':['infinite_cylindrical_symmetry','magnetostatic'],'sheet':['infinite_current_sheet','magnetostatic'],'solenoid':['ideal_long_solenoid','magnetostatic']}.get(kind,[]))
    if problem.family=='biot_savart':problem.assume('magnetostatic')
    if problem.family=='capacitance':problem.assume('negligible_edge_effects')
    if problem.family=='magnetic_material':problem.assume(*(['negligible_leakage','uniform_cross_section'] if problem.variables['kind']=='magnetic_circuit' else ['infinite_axial_symmetry','no_free_current','H_infinity_zero']))
    if problem.family=='faraday':problem.assume('uniform_normal_B')
    for i,region in enumerate(problem.regions):
        positive(region.upper-region.lower,'Regionsbredde '+str(i+1))
        if problem.family=='gauss_radial':positive(region.permittivity,'Permittivitet')
        if sp.sympify(region.lower).is_nonnegative is not True:raise InputError('En radial regions nedre grænse skal være ikke-negativ.')
        for other in problem.regions[:i]:
            if sp.And(region.lower<other.upper,other.lower<region.upper) is not sp.false:raise InputError('Regioner overlapper eller kan ikke ordnes. Brug fx ydre radius a+h med h>0.')
    if problem.family=='field_calculus' and 'E' in problem.variables and 'electrostatic' in problem.assumptions:
        from .validation import calculus
        field=sp.Matrix(problem.variables['E']);curl=calculus(problem.variables['coordinates'],problem.variables['system'])[2](field)
        if any(c.equals(0) is not True for c in curl):raise InputError('Fysisk afvisning: feltets curl er ikke verificeret nul. Feltet kan ikke bekræftes elektrostatisk uden yderligere betingelser: '+str(curl))
    if 'time_bounds' in problem.variables:
        low,high=problem.variables['time_bounds'];numeric={k:sp.Float(str(si(val,problem.numerical_units[k]).magnitude)) for k,val in problem.numerical_values.items()}
        positive(sp.simplify((high-low).subs(numeric)),'Tidsintervallets længde')
    for name in {'capacitance':['epsilon','area','distance'],'lorentz_force':[], 'magnetic_dipole_interaction':['moment_magnitude','B_magnitude'],'rc_transient':['R','L','C'],'motional_emf':['R'],'ampere_maxwell':['plate_radius'],'faraday':['R']}.get(problem.family,[]):
        if name in problem.variables:positive(problem.variables[name],name)
    if problem.family=='magnetic_material':
        for length,mu in problem.variables.get('segments',[]):positive(length,'Segmentlængde');positive(mu,'Permeabilitet')
    available=None
    v=problem.variables
    if problem.family=='capacitance':available={'C'}|({'V','U'} if 'Q' in v else set())|({'Q','U','E','E_vector'} if 'V' in v else set())
    if problem.family=='point_charges':available={'E','V','U','Q','dipole'}|({'F'} if 'test_charge' in v or 'force_on_index' in v else set())
    if problem.family=='gauss_radial':available={'E','D','Q_enc','P'}
    if problem.family=='faraday':available={'Phi','EMF'}|({'I','P'} if 'R' in v else set())|({'W'} if 'time_bounds' in v else set())
    if problem.family=='magnetic_material':available={'B','H_0','H_1'} if v['kind']=='magnetic_circuit' else {'B','H','J_bound','K_bound'}
    if problem.family=='field_calculus':available={'E','rho','curl_E'} if ('E' in v or 'V' in v) else {'B','div_B','J'}
    if available is not None and set(problem.wanted)-available:raise InputError('Den valgte model mangler oplysninger til '+', '.join(sorted(set(problem.wanted)-available))+'. Tilføj de relevante givne størrelser, eller vælg en anden model/søgt størrelse.')
    answer=solution(problem,'Forhåndskontrol','',[])
    check_inputs(problem,answer)
    failed=[c for c in answer.checks if c.passed is False]
    unknown=[c for c in answer.checks if c.passed is not True]
    if failed:raise InputError('; '.join(c.name+': '+c.detail for c in failed))
    return problem,[c.name+': '+c.detail for c in unknown]
