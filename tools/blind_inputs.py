"""Human-assisted input transcriptions. No gold values are inserted as solver outputs."""
from em1_solver.core.new_problem import Parsed

A=['EV01','EV04','EV05','EV06','EV09','EV11','EV16','EV19','BA01','BA02','BA05','BA10','BA15','DYN01','DYN02','DYN03','DYN07','DYN13','GEN02','GEN04']
BASE={'r':'m','s':'m','z':'m','x':'m','y':'m','R':'m','a':'m','b':'m','h':'m','L':'m','l':'m','g':'m','rho0':'C/m^3','rho_f':'C/m^3','epsilon':'F/m','eps':'F/m','J0':'A/m^2','I':'A','lambda0':'C/m','lam':'C/m','u':'1','phi':'1','theta':'1','B0':'T','N':'1','mu':'H/m','mu0':'H/m','t':'s','tau':'s','a0':'m','v':'m/s','V1':'V','V2':'V','F0':'N','m':'kg'}
POS=['r','s','R','a','b','h','L','l','g','tau','a0','m','epsilon','eps','mu']

def plain(geometry,data,wanted,assumptions=(),units=None,positive=None):return dict(geometry=geometry,data=data,wanted=wanted,assumptions=list(assumptions),units=BASE|dict(units or {}),positive=POS if positive is None else positive)
def typed(domain,family,variables,wanted,assumptions=(),regions=None,units=None):
 return plain('manuelt specificeret',{'solver_spec':dict(domain=domain,family=family,variables=variables,regions=regions or [],wanted=wanted)},wanted,assumptions,units)

S={}
S['EV01']=plain('kugle',dict(rho='rho0*(1-r/R)',coordinate='r',radius='R'),['E'],['spherical_symmetry'])
S['EV04']=plain('cylinder',dict(rho='rho0*(1-s/R)',coordinate='s',radius='R',extent='infinite'),['E'],['infinite_cylindrical_symmetry'])
S['EV05']=plain('cylinderskal',dict(rho='k*s',coordinate='s',extent='infinite',regions=[dict(lower='a',upper='a+h',density='k*s')]),['E'],['infinite_cylindrical_symmetry'],{'k':'C/m^4'})
S['EV06']=plain('plan',dict(rho='rho0*z**2',coordinate='z',radius='a'),['E'],['infinite_planar_symmetry'],{'rho0':'C/m^5'},POS+['z'])
S['EV09']=plain('linje',dict(source=['u',0,0],parameter='u',bounds=['-L','L'],point=[0,'a',0],density='lam'),['V','E'],units={'u':'m'})
S['EV11']=plain('ring',dict(source=['R*cos(phi)','R*sin(phi)',0],parameter='phi',bounds=[0,'2*pi'],point=[0,0,0],density='lambda0*(1+cos(phi))'),['V','E'])
S['EV16']=plain('cylinder',dict(rho='rho_f',coordinate='s',extent='infinite',regions=[dict(lower=0,upper='R',density='rho_f',permittivity='eps')]),['D','E','P'],['infinite_cylindrical_symmetry'])
S['EV19']=typed('EV','laplace_legendre',dict(r='r',theta='theta',radius='R',coefficients=[[1,'V1'],[2,'V2']]),['V_inside','V_outside'],['axial_symmetry','charge_free_inside_outside','V_infinity_zero','finite_at_origin'])
S['BA01']=plain('cylinder',dict(J='J0*(1-s/R)',coordinate='s',radius='R',extent='infinite'),['B'],['infinite_cylindrical_symmetry','magnetostatic'])
S['BA02']=plain('cylinderskal',dict(J='k/s',coordinate='s',extent='infinite',regions=[dict(lower='a',upper='a+h',density='k/s')]),['B'],['infinite_cylindrical_symmetry','magnetostatic'],{'k':'A/m'})
S['BA05']=plain('ledning',dict(source=[0,0,'u'],parameter='u',bounds=['-L','L'],point=['a',0,0],I='I'),['B'],['magnetostatic'],{'u':'m'})
S['BA10']=plain('Ukendt',dict(A=[0,0,'B0*x*y/L'],coordinates=['x','y','z'],system='cartesian'),['B'])
S['BA15']=typed('BA','magnetic_material',dict(kind='magnetic_circuit',N='N',I='I',segments=[['l','mu'],['g','mu0']]),['B','H_0','H_1'])
S['DYN01']=typed('DYN','faraday',dict(time='t',N=1,flux_integrand='2*pi*beta*t*s**2',bounds=[['s',0,'R']]),['Phi','EMF'],units={'beta':'T/(m*s)'})
S['DYN02']=plain('strømloop',dict(B='B0*exp(-t/tau)',area='(a0+v*t)**2',time='t',N=1),['Phi','EMF'],['uniform_normal_B'])
S['DYN03']=typed('DYN','ampere_maxwell',dict(E='E0*t**2',time='t',coordinate='s',plate_radius='R'),['B'],['uniform_axial_E','circular_symmetry','negligible_edge_effects'],units={'E0':'V/(m*s^2)'})
S['DYN07']=typed('DYN','feedback',dict(mass='m',R='Z',coupling='B*l',voltage=0,drive_force='F0',time='t',initial_velocity=0),['v_infinity','tau','v'],['constant_coefficients','negligible_self_inductance','no_friction'],units={'Z':'ohm','B':'T'})
S['DYN13']=typed('DYN','faraday',dict(time='t',coordinate='s',field_radius='R',dB_dt='dBdt'),['E_phi'],['circular_symmetry','uniform_axial_B_inside'],units={'dBdt':'T/s'})
S['GEN02']=plain('Ukendt',dict(E=['alpha*y','beta*z','gamma*x'],coordinates=['x','y','z'],system='cartesian'),['curl_E'],['electrostatic'],{'alpha':'V/m^2','beta':'V/m^2','gamma':'V/m^2'})
S['GEN04']=plain('cylinder',dict(rho='rho0',coordinate='s',radius='R',extent='finite'),['E'])


def assisted(row):
 spec=S[row['id']]
 return Parsed(text=row['problem'],quantities={},warnings=[],**spec)

S['EV06']['data']=dict(rho='rho0*s**2',coordinate='s',radius='a',signed_coordinate='z')
S['EV06']['positive']=POS
S['EV16']['assumptions'].append('linear_isotropic_dielectric')

S['BA15']['assumptions']=['negligible_leakage','uniform_cross_section']
S['DYN07']['positive']=POS+['Z','B']

# Remaining Tier B transcriptions. Composite paths use genuine source data,
# existing solvers, and named physical relations between computed outputs.
BASE.update({'epsilon_0':'F/m','mu_0':'H/m','q':'C','Q':'C','d':'m','V0':'V','A0':'T*m','K0':'A/m','J0':'A/m^2','I1':'A','I2':'A','R1':'m','R2':'m','N1':'1','N2':'1','ell':'m','sigma0':'S/m','C':'F','Q0':'C','Z':'ohm','B':'T','omega':'1/s'})
POS.extend(['Z','B','C','d','R1','R2','N','N1','N2','ell','sigma0'])

def graph(steps,wanted,units=None,positive=None):
 from em1_solver.examples import LABELS
 allunits=BASE|dict(units or {})
 def encode(v,key=''):
  if key=='output_units':return v
  if isinstance(v,str):return v if key in LABELS else {'expr':v}
  if isinstance(v,list):return [encode(x,key) for x in v]
  if isinstance(v,dict):
   if set(v)&{'ref','matrix','expr','map','piecewise','relation'}:return v
   return {k:encode(x,k) for k,x in v.items()}
  return v
 path=[]
 for step in steps:
  name,domain,family,variables,*rest=step
  opts=rest[0] if rest else {};spec=dict(domain=domain,family=family,variables=encode(variables),regions=encode(opts.get('regions',[])),assumptions=opts.get('assumptions',[]),wanted=[])
  path.append(dict(id=name,problem=spec,bindings=opts.get('bindings',{})))
 recipe=dict(status='executable',geometry='manual confirmed dependency path',symbols={n:{'positive':True} if n in (positive or POS) or n in ('epsilon_0','mu_0') else {'real':True} for n in allunits},symbol_units=allunits,path=path,expected=[])
 return plain('Ukendt',{'recipe':recipe},wanted,units=units,positive=positive)

S['EV02']=graph([
 ('field','EV','gauss_radial',dict(coordinate='r',symmetry='sphere'),dict(regions=[dict(lower=0,upper='R',density='rho0*(1-r/R)')],assumptions=['spherical_symmetry'])),
 ('potential','EV','potential_from_field',dict(field={'ref':'field.E'},coordinate='r',start='oo',end='r'))],['delta_V'])
S['EV03']=plain('kugleskal',dict(rho='k/r**2',coordinate='r',regions=[dict(lower='a',upper='a+h',density='k/r**2')]),['E'],['spherical_symmetry'],{'k':'C/m'})
for id,formula in [('EV07','V0*(x**2-y**2)/L**2'),('EV08','V0*x*y*z/L**3')]:S[id]=plain('Ukendt',dict(V=formula,coordinates=['x','y','z']),['E','rho'],['electrostatic'],{'V0':'V'})
S['EV10']=plain('bue',dict(source=['R*cos(phi)','R*sin(phi)',0],parameter='phi',bounds=[0,'pi'],point=[0,0,0],density='lam'),['V','E'])
S['EV12']=graph([
 ('cap','EV','capacitance',dict(kind='sphere',epsilon='epsilon_0',inner_radius='a',outer_radius='a+h',Q='Q')),
 ('field','EV','gauss_radial',dict(coordinate='r',symmetry='sphere',surface_charges=[['a','Q/(4*pi*a**2)'],['a+h','-Q/(4*pi*(a+h)**2)']]),dict(regions=[dict(lower=0,upper='a+h',density=0)],assumptions=['spherical_symmetry']))],['C','V','E'])
for id,variables,combine in [('EV13',[dict(kind='parallel_plates',epsilon='eps1',area='Area/2',distance='d'),dict(kind='parallel_plates',epsilon='eps2',area='Area/2',distance='d')],'C1+C2'),('EV14',[dict(kind='parallel_plates',epsilon='eps1',area='Area',distance='d1'),dict(kind='parallel_plates',epsilon='eps2',area='Area',distance='d2')],'1/(1/C1+1/C2)')]:
 S[id]=graph([('c1','EV','capacitance',variables[0],dict(assumptions=['negligible_edge_effects'])),('c2','EV','capacitance',variables[1],dict(assumptions=['negligible_edge_effects'])),('network','EV','algebra',dict(outputs={'C':combine},output_units={'C':'F'}),dict(bindings={'C1':{'ref':'c1.C'},'C2':{'ref':'c2.C'}}))],['C'],{'eps1':'F/m','eps2':'F/m','Area':'m^2','d1':'m','d2':'m'},POS+['eps1','eps2','Area','d1','d2'])
S['EV15']=graph([
 ('bound','EV','polarization',dict(coordinates=['s','phi','z'],system='cylindrical',P=['k*s',0,0],normal=[1,0,0],surface_substitutions={'map':[[{'expr':'s'},{'expr':'R'}]]})),
 ('charges','EV','algebra',dict(outputs={'lambda_volume':'rhob*pi*R**2','lambda_surface':'sigmab*2*pi*R','lambda_total':'rhob*pi*R**2+sigmab*2*pi*R'},output_units={'lambda_volume':'C/m','lambda_surface':'C/m','lambda_total':'C/m'}),dict(bindings={'rhob':{'ref':'bound.rho_bound'},'sigmab':{'ref':'bound.sigma_bound'}}))],['rho_bound','sigma_bound','lambda_total'],{'k':'C/m^3'})
S['EV17']=graph([('image','EV','images',dict(charges=[['q',['d',0,0]]],point=['d',0,0],planes=[0],self_index=0,test_charge='q'),dict(assumptions=['grounded_infinite_planes'])),('energy','EV','algebra',dict(outputs={'U':'q*Vimage/2'},output_units={'U':'J'}),dict(bindings={'Vimage':{'ref':'image.V'}}))],['F','U'])
S['EV18']=typed('EV','point_charges',dict(charges=[['q',['a',0,0]],['q',['-a',0,0]],['-2*q',[0,0,0]]],point=[0,0,'z'],far_coordinate='z',series_order=4),['V_far'],units={'q':'C'})
S['BA03']=typed('BA','ampere',dict(kind='sheet',K=['K0',0,0],normal=[0,0,1]),['B_positive','B_negative'],['infinite_current_sheet','magnetostatic'],units={'K0':'A/m'})
S['BA04']=graph([('upper','BA','ampere',dict(kind='sheet',K=['K0',0,0],normal=[0,0,1]),dict(assumptions=['infinite_current_sheet','magnetostatic'])),('lower','BA','ampere',dict(kind='sheet',K=['-K0',0,0],normal=[0,0,1]),dict(assumptions=['infinite_current_sheet','magnetostatic'])),('combine','BA','algebra',dict(outputs={'B_above':'upPlus+loPlus','B_between':'upMinus+loPlus','B_below':'upMinus+loMinus'},output_units={'B_above':'T','B_between':'T','B_below':'T'}),dict(bindings={'upPlus':{'ref':'upper.B_positive'},'loPlus':{'ref':'lower.B_positive'},'upMinus':{'ref':'upper.B_negative'},'loMinus':{'ref':'lower.B_negative'}}))],['B_above','B_between','B_below'],{'K0':'A/m'})
for id,point,upper in [('BA06',[0,0,0],'2*pi'),('BA07',[0,0,'z'],'2*pi'),('BA08',[0,0,0],'theta')]:S[id]=typed('BA','biot_savart',dict(source=['R*cos(phi)','R*sin(phi)',0],parameter='phi',bounds=[0,upper],I='I',point=point),['B'],['magnetostatic'])
S['BA09']=graph([('one','BA','biot_savart',dict(source=['R1*cos(phi)','R1*sin(phi)',0],parameter='phi',bounds=[0,'2*pi'],I='I1',point=[0,0,0])),('two','BA','biot_savart',dict(source=['R2*cos(phi)','R2*sin(phi)',0],parameter='phi',bounds=[0,'2*pi'],I='-I2',point=[0,0,0])),('combine','BA','algebra',dict(outputs={'B':'B1+B2'},output_units={'B':'T'}),dict(bindings={'B1':{'ref':'one.B'},'B2':{'ref':'two.B'}}))],['B'])
S['BA11']=typed('BA','field_calculus',dict(coordinates=['s','phi','z'],system='cylindrical',A=[0,'A0*s**2',0]),['B'],units={'A0':'T/m'})
S['BA12']=graph([('force','BA','lorentz_force',dict(kind='force',q='q',v=['vx','vy','vz'],E=['E0',0,0],B=[0,0,'B0'],solve_for=['vx','vy'],target_values={'F':{'matrix':[0,0,0]}}))],['solved_vx','solved_vy'],{'vx':'m/s','vy':'m/s','vz':'m/s','E0':'V/m'})
S['BA13']=typed('BA','wire_force',dict(kind='parallel',I1='I1',I2='I2',distance='d',length='l'),['F_signed_attraction'],['parallel_infinite_wires'])
S['BA14']=typed('BA','magnetic_dipole_interaction',dict(moment=['m0*sin(theta)',0,'m0*cos(theta)'],B=[0,0,'B0']),['torque','U'],units={'m0':'A*m^2'})
S['BA16']=graph([('inside','BA','magnetic_material',dict(kind='magnetization',coordinates=['s','phi','z'],system='cylindrical',M=[0,0,'M0'],normal=[1,0,0]),dict(assumptions=['infinite_axial_symmetry','no_free_current','H_infinity_zero'])),('outside','BA','magnetic_material',dict(kind='magnetization',coordinates=['s','phi','z'],system='cylindrical',M=[0,0,0]),dict(assumptions=['infinite_axial_symmetry','no_free_current','H_infinity_zero']))],['inside.B','outside.B','J_bound','K_bound'],{'M0':'A/m'})
S['DYN04']=typed('DYN','inductance_energy',dict(B_squared='(mu_0*I/(2*pi*s))**2',mu='mu_0',jacobian='2*pi*s',bounds=[['s','a','a+h']],I='I'),['L','U'])
S['DYN05']=typed('DYN','resistance',dict(coordinate='x',bounds=[0,'L'],area='Area',conductivity='sigma0*(1+x/L)',I='I'),['R','E','rho'],['one_dimensional_steady_current'],units={'Area':'m^2'})
S['DYN06']=plain('strømloop',dict(B='B*cos(omega*t)',area='Area',time='t',N=1),['Phi','EMF'],['uniform_normal_B'],{'Area':'m^2'})
S['DYN08']=typed('DYN','motional_emf',dict(source=[0,'u',0],parameter='u',bounds=[0,'l'],v=['v',0,0],B=[0,0,'B'],time='t',R='Z'),['EMF','I','F'],['negligible_self_inductance'],units={'u':'m'})
for id,turns,mutual in [('DYN09','N',False),('DYN10','N1',True)]:
 S[id]=graph([('field','BA','ampere',dict(kind='solenoid',turn_density=turns+'/ell',I='I'),dict(assumptions=['ideal_long_solenoid','magnetostatic'])),('inductance','DYN','inductance_energy',dict(flux='Bfield*Area',I='I',N='N2' if mutual else 'N',mutual=mutual),dict(bindings={'Bfield':{'ref':'field.B'}}))],['M' if mutual else 'L'],{'Area':'m^2'})
S['DYN11']=graph([('current','DYN','rc_transient',dict(kind='RL',time='t',R='Z',L='Ind',voltage='V0',I0=0)),('energy','DYN','algebra',dict(outputs={'U_infinity':'Ind*Iinf**2/2'},output_units={'U_infinity':'J'}),dict(bindings={'Iinf':{'ref':'current.I_infinity'}}))],['I','tau','U_infinity'],{'Ind':'H'},POS+['Ind'])
S['DYN12']=graph([('discharge','DYN','rc_transient',dict(kind='RC',time='t',R='Z',C='C',Q0='Q0')),('energy','DYN','algebra',dict(outputs={'U':'charge**2/(2*C)'},output_units={'U':'J'}),dict(bindings={'charge':{'ref':'discharge.Q'}}))],['Q','I_charge','U'])
S['DYN14']=typed('DYN','motional_emf',dict(source=['u',0,0],parameter='u',bounds=[0,'L'],v=[0,'omega*u',0],B=[0,0,'B'],time='t'),['EMF'],units={'u':'m'})
S['DYN15']=typed('DYN','faraday',dict(time='t',flux_integrand='B0*(x0+v*t+u)*a/L',bounds=[['u',0,'a']],N=1),['Phi','EMF'],units={'u':'m','x0':'m'})
S['GEN01']=plain('generel parameteriseret linje',dict(source=['a*cos(phi)','b*sin(phi)',0],parameter='phi',bounds=[0,'2*pi'],point=[0,0,0],density='lam'),['V'])
S['GEN03']=plain('Ukendt',dict(B=['alpha*x','alpha*y','alpha*z'],coordinates=['x','y','z']),['div_B'],units={'alpha':'T/m'})
S['GEN05']=plain('ledning',{},['B'])

S['DYN08']['data']['solver_spec']['wanted']=['EMF','I','F_magnetic']
S['DYN08']['data']['solver_spec']['variables']['R']='Z'
S['DYN08']['assumptions'].append('stationary_return_path')
S['EV18']['data']['solver_spec']['wanted']=['V']

S['DYN04']['data']['solver_spec']['variables']['per_length']=True
S['DYN05']['positive']=POS+['Area']

S['EV18']['data']['solver_spec']['wanted']=['V_far']
