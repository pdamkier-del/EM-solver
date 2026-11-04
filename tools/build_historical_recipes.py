"""Reviewed recipe definitions. Expected formulas are transcribed, never solver-generated."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data/historical_problems';DEST.mkdir(exist_ok=True)
REG={r['id']:r for r in json.loads((ROOT/'data/exam_problem_registry.json').read_text())}
def E(x):return {'expr':str(x)}
def M(x):return {'matrix':[[E(v)] for v in x]}
def wrap(x):
 if isinstance(x,str):return E(x)
 if isinstance(x,list):return [wrap(v) for v in x]
 return x
DEFAULT={'x':'m','y':'m','z':'m','r':'m','s':'m','a':'m','b':'m','d':'m','R':'m','L':'m','h':'m','q':'C','Q':'C','I':'A','J':'A/m^2','V':'V','B':'T','rho':'C/m^3','sigma':'C/m^2','t':'s','omega':'1/s','tau':'s','m':'kg','v':'m/s','epsilon_r':'1','theta':'1','phi':'1','N':'1','k':'1'}
LABELS={'kind','system','symmetry'}
def variables(d):return {k:v if k in LABELS or isinstance(v,(bool,int,dict)) else wrap(v) for k,v in d.items()}
def check(key,value,unit=None,**extra):return {'step':'solve','result':key,'value':M(value) if isinstance(value,list) else E(value),**({'unit':unit} if unit else {}),**extra}
def put(ids,family,data,checks,domain='EV',assumptions=(),regions=(),units=None,status='executable',path=None,notes=''):
 for id in ids.split():
  row=REG[id]; dims=DEFAULT|{'epsilon_0':'F/m','mu_0':'H/m'}|(units or {})
  symbols={name:({'real':True} if name in ('x','y','z','t','theta','phi','u') else {'positive':True}) for name in dims}
  steps=path or [{'id':'solve','problem':{'domain':domain,'family':family,'geometry':row['geometry'],'variables':variables(data),'regions':[{k:E(v) for k,v in r.items()} for r in regions],'assumptions':list(assumptions),'wanted':list(dict.fromkeys(c['result'] for c in checks))}}]
  recipe={'schema_version':1,'id':id,'status':status,'geometry':row['geometry'],'source':{'pdf':row['source_pdf'],'page':row['source_page'],'answer':row['answer_reference']},
   'given_source':row['given'],'wanted_source':row['wanted'],'symbols':symbols,'symbol_units':dims,'path':steps,'expected':checks,
   'orientation':'Fortegn gælder den eksplicit angivne basis og orientering; se direction i Solution.','notes':notes}
  (DEST/(id.replace(':','_p').replace('-','_')+'.json')).write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n')
# Defaults are honest migration states, not invented executable input.
for id,row in REG.items():
 (DEST/(id.replace(':','_p').replace('-','_')+'.json')).write_text(json.dumps({'schema_version':1,'id':id,'status':'qualitative/manual' if id=='2021-06:1b' else 'not_migrated','geometry':row['geometry'],'source':{'pdf':row['source_pdf'],'page':row['source_page'],'answer':row['answer_reference']},'given_source':row['given'],'wanted_source':row['wanted'],'symbols':{},'symbol_units':{},'path':[],'expected':[]},ensure_ascii=False,indent=2)+'\n')
# Differential problems, preserving original coordinates and coefficient dimensions.
def calc(ids,data,checks,system='cartesian',coords=['x','y','z'],units=None,assumptions=()):
 put(ids,'field_calculus',{'coordinates':coords,'system':system,**data},checks,units=units,assumptions=assumptions)
calc('2021-06:5a 2021-06:5c',{'E':['k*y^2','k*(2*x*y+z^2)','2*k*y*z'],'volume_bounds':[['x','0','L'],['y','0','L'],['z','0','L']]},[check('curl_E',['0','0','0']),check('rho','2*epsilon_0*k*(x+y)','C/m^3'),check('Q','2*epsilon_0*k*L^4','C')],units={'k':'V/m^3'})
calc('2022-02:5a',{'E':['-2*V*x*y/R^3','-V*x^2/R^3','0']},[check('rho','-2*epsilon_0*V*y/R^3','C/m^3'),check('curl_E',['0','0','0'])])
calc('2022-11:2a 2022-11:2b',{'E':['V*(2*r^2/R^2-r/R)','0','0'],'volume_bounds':[['r','0','R'],['theta','0','pi'],['phi','0','2*pi']]},[check('rho','epsilon_0*V*(8*r/R^2-3/R)','C/m^3'),check('Q','4*pi*R^2*epsilon_0*V','C')],system='spherical',coords=['r','theta','phi'],units={'V':'V/m'})
calc('2023-11:3a 2023-11:3b',{'E':['V*(x^2+z^2)/a^2','V*(y^2+x^2)/a^2','V*(z^2+y^2)/a^2'],'volume_bounds':[['x','0','a'],['y','0','a'],['z','0','a']]},[check('rho','2*epsilon_0*V*(x+y+z)/a^2','C/m^3'),check('Q','3*epsilon_0*V*a^2','C'),check('dB_dt',['-2*V*y/a^2','-2*V*z/a^2','-2*V*x/a^2'],'T/s')],units={'V':'V/m'})
calc('2025-01:1b',{'E':['a+b*x','0','0']},[check('rho','epsilon_0*b','C/m^3',numeric={'values':{'b':50},'value':4.4270939064e-10,'tolerance':1e-20})],units={'a':'V/m','b':'V/m^2'})
put('2025-01:1a','potential_from_field',{'coordinate':'x','field':'a+b*x','start':'0','end':'L'},[check('delta_V','-a*L-b*L^2/2','V',numeric={'values':{'a':500,'b':50,'L':20},'value':-20000,'tolerance':1e-8})],units={'a':'V/m','b':'V/m^2'})
calc('2025-11:2a 2025-11:2b 2025-11:2c',{'V':'-a*log(r/R)','volume_bounds':[['r','0','R'],['theta','0','pi'],['phi','0','2*pi']]},[check('E',['a/r','0','0'],'V/m'),check('rho','epsilon_0*a/r^2','C/m^3'),check('Q','4*pi*epsilon_0*a*R','C',numeric={'values':{'a':134,'R':5},'value':74.547e-9,'tolerance':.01e-9})],system='spherical',coords=['r','theta','phi'],units={'a':'V'})
calc('2023-02:4a',{'A':['3*k*z*y','-2*k*z*y','k*z^2']},[check('B',['2*k*y','3*k*y','-3*k*z'],'T'),check('J',['0','0','-2*k/mu_0'],'A/m^2')],units={'k':'T/m'},assumptions=['magnetostatic'])
calc('2021-11:4b',{'B':['0','k*s^2','0']},[check('J',['0','0','3*k*s/mu_0'],'A/m^2')],system='cylindrical',coords=['s','phi','z'],units={'k':'T/m^2'},assumptions=['magnetostatic'])
# All supplied Lorentz variants, with actual numerical references.
put('2021-06:4a','lorentz_force',{'kind':'orbit','mass':'m','q':'q','B_magnitude':'B','voltage':'V'},[check('diameter','2*sqrt(2*m*V/q)/B','m',numeric={'values':{'m':12*1.66054e-27,'q':1.602176634e-19,'B':2.5,'V':40000},'value':.0798,'tolerance':.0001})],domain='BA',assumptions=['nonrelativistic','velocity_perpendicular_B'])
put('2021-11:4a','lorentz_force',{'q':'q','v':['v*cos(theta)','v*sin(theta)','0'],'B':['0','k*a^2','0'],'E':['0','0','0']},[check('F',['0','0','q*k*a^2*v*cos(theta)'],'N')],domain='BA',units={'k':'T/m^2'})
put('2025-01:4a','lorentz_force',{'q':'q','v':['3*v','4*v','-3*v'],'B':['4*B','3*B','2*B'],'E':['0','0','0']},[check('F',['17*q*v*B','-18*q*v*B','-7*q*v*B'],'N'),check('magnitude','sqrt(662)*q*v*B','N',numeric={'values':{'q':6e-6,'v':1e6,'B':1},'value':154.44,'tolerance':.1})],domain='BA')
# Legendre: one actual problem has three lettered outputs.
put('2026-01:5a 2026-01:5b 2026-01:5c','laplace_legendre',{'r':'r','theta':'theta','radius':'R','coefficients':[[2,'2*V']]},[check('V_inside','V*(3*cos(theta)^2-1)*(r/R)^2','V'),check('V_outside','V*(3*cos(theta)^2-1)*(R/r)^3','V'),check('E_outside',['3*V*R^3*(3*cos(theta)^2-1)/r^4','6*V*R^3*cos(theta)*sin(theta)/r^4','0'],'V/m')],assumptions=['axial_symmetry','charge_free_inside_outside','V_infinity_zero','finite_at_origin'])
# Driven rod: the same complete path supports the four actual questions.
put('2025-11:5a 2025-11:5b 2025-11:5c 2025-11:5d','feedback',{'mass':'m','R':'R','coupling':'B*d','voltage':'V','drive_force':'0','time':'t','initial_velocity':'0','time_bounds':['0','oo']},[check('acceleration_initial','B*d*V/(R*m)','m/s^2',sign=1),check('v_infinity','V/(B*d)','m/s',sign=1),check('v','V/(B*d)*(1-exp(-B^2*d^2*t/(m*R)))','m/s'),check('battery_energy','m*V^2/(B^2*d^2)','J'),check('W','m*V^2/(2*B^2*d^2)','J')],domain='DYN',assumptions=['constant_coefficients','negligible_self_inductance','no_friction'],units={'R':'ohm'},notes='Positiv bevægelsesakse mod venstre som på opgavens figur. V² kontrolleret mod originalfacit.')
put('2023-11:5c','feedback',{'mass':'m','R':'R','coupling':'A*B*k','voltage':'0','drive_force':'m*g','time':'t','initial_velocity':'0'},[check('v_infinity','m*g*R/(A*B*k)^2','m/s',sign=1)],domain='DYN',assumptions=['constant_coefficients','negligible_self_inductance','no_friction'],units={'R':'ohm','A':'m^2','k':'1/m','g':'m/s^2'},notes='Positiv hastighed nedad. Kobling A B k; felt Bz=B(1-kz).')
put('2023-11:5d','feedback',{'mass':'m','R':'R','coupling':'-A*B*k','voltage':'0','drive_force':'m*g','time':'t','initial_velocity':'0'},[check('v_infinity','m*g*R/(A*B*k)^2','m/s'),check('I','m*g/(A*B*k)*(1-exp(-A^2*B^2*k^2*t/(m*R)))','A')],domain='DYN',assumptions=['constant_coefficients','negligible_self_inductance','no_friction'],units={'R':'ohm','A':'m^2','k':'1/m','g':'m/s^2'},notes='Reverseret gradient; positiv hastighed stadig nedad. Strøm vender, dæmpningen er uændret.')
# Faraday actual geometries and signed loops.
put('2022-02:6a','faraday',{'time':'t','B_normal':'B*sin(omega*t)','area':'pi*a^2','R':'R','at':{'map':[[E('t'),E('pi/(3*omega)')]]}},[check('I','-pi*a^2*B*omega/(2*R)','A',sign=-1)],domain='DYN',assumptions=['uniform_normal_B','negligible_self_inductance'],units={'R':'ohm'})
put('2022-11:6a','faraday',{'time':'t','flux_integrand':'B*(x^2+y^2)*exp(-t/tau)/L^2','bounds':[['x','0','L'],['y','0','L']],'R':'R'},[check('I','2*B*L^2*exp(-t/tau)/(3*tau*R)','A',sign=1)],domain='DYN',assumptions=['negligible_self_inductance'],units={'R':'ohm'})
put('2023-02:5b 2023-02:5c','faraday',{'time':'t','flux':'C*I*cos(omega*t)','R':'R'},[check('EMF','C*I*omega*sin(omega*t)','V'),check('P','C^2*I^2*omega^2*sin(omega*t)^2/R','W')],domain='DYN',assumptions=['negligible_self_inductance'],units={'C':'H','R':'ohm'},notes='C est la constante géométrique établie en 5a; donnée du sous-problème 5b.')
put('2026-01:3a 2026-01:3b 2026-01:3c','faraday',{'time':'t','flux_integrand':'k*s^2*sin(phi)^2*cos(t/T)','bounds':[['s','0','S'],['phi','0','2*pi']],'R':'R','time_bounds':['0','2*pi*T']},[check('Phi','k*pi*S^3*cos(t/T)/3','Wb'),check('I','k*pi*S^3*sin(t/T)/(3*R*T)','A'),check('W','pi^3*k^2*S^6/(9*R*T)','J'),check('I','k*pi*S^3*sin(5)/(3*R*T)','A',subs={'t':E('5*T')},sign=-1)],domain='DYN',assumptions=['negligible_self_inductance'],units={'k':'T/m','R':'ohm','S':'m','T':'s'})
# RC actual 2026 problem, with given constants retained as named symbols.
put('2026-01:2c','rc_transient',{'kind':'RC','time':'t','R':'R','C':'C','Q0':'Q0','fraction':'1/100'},[check('I','Q0/(R*C)*exp(-t/(R*C))','A'),check('decay_time','R*C*log(100)','s',numeric={'values':{'R':.25,'C':.091},'value':.105,'tolerance':.001}),check('I_initial','Q0/(R*C)','A',numeric={'values':{'R':.25,'C':.091,'Q0':5.7},'value':250.55,'tolerance':.1})],domain='DYN',units={'R':'ohm','C':'F','Q0':'C'})
# Gauss actual nonuniform cylinder; exterior and interior explicitly checked.
put('2024-11:2a 2024-11:2b','gauss_radial',{'coordinate':'s','symmetry':'cylinder','length':'L'},[check('Q_enc','pi*alpha*L*(a/2)^4/2','C',subs={'s':E('a/2')}),check('E','alpha*(a/2)^3/(4*epsilon_0)','V/m',subs={'s':E('a/2')}),check('E','alpha*a^3/(8*epsilon_0)','V/m',subs={'s':E('2*a')})],assumptions=['infinite_cylindrical_symmetry'],regions=[{'lower':'0','upper':'a','density':'alpha*s^2','permittivity':'epsilon_0'}],units={'alpha':'C/m^5'})
# Capacitance: exact arbitrary positive gap parameterization, not fixed radius ratios.
put('2021-11:2b 2021-11:2d','capacitance',{'kind':'sphere','epsilon':'epsilon_0*epsilon_r','inner_radius':'b','outer_radius':'b+d'},[check('C','4*pi*epsilon_0*epsilon_r*b*(b+d)/d','F')],units={'d':'m'},notes='b=indre ydre lederradius, b+d=ydre indre radius. For 2b indsættes epsilon_r=1.',status='partial')
put('2021-11:6a','capacitance',{'kind':'parallel_plates','epsilon':'epsilon_0','area':'pi*a^2','distance':'d','V':'V*cos(omega*t)','normal':['0','0','1']},[check('E_vector',['0','0','V*cos(omega*t)/d'],'V/m')],assumptions=['negligible_edge_effects'])
print(sum(json.loads(p.read_text())['status']=='executable' for p in DEST.glob('*.json')),'executable recipes')
# Correctly distinguish vacuum/dielectric capacitance subproblems.
put('2021-11:2b','capacitance',{'kind':'sphere','epsilon':'epsilon_0','inner_radius':'b','outer_radius':'b+d'},[check('C','4*pi*epsilon_0*b*(b+d)/d','F')])
put('2021-11:2d','capacitance',{'kind':'sphere','epsilon':'epsilon_0*epsilon_r','inner_radius':'b','outer_radius':'b+d'},[check('C','4*pi*epsilon_0*epsilon_r*b*(b+d)/d','F',numeric={'values':{'b':.1,'d':.4,'epsilon_r':3.8},'value':53e-12,'tolerance':1e-12})])
# Actual 2026 capacitance inverse and energy, no hand-entered derived area.
put('2026-01:2a','capacitance',{'kind':'parallel_plates','epsilon':'epsilon_0*epsilon_r','area':'A','distance':'d','solve_for':'A','target_values':{'C':E('C')}},[check('solved_A','C*d/(epsilon_0*epsilon_r)','m^2',numeric={'values':{'C':.091,'d':1e-7,'epsilon_r':9.6},'value':107,'tolerance':1})],assumptions=['negligible_edge_effects'],units={'A':'m^2','C':'F'})
put('2026-01:2b','capacitance',{'kind':'parallel_plates','epsilon':'epsilon_0','area':'C*d/epsilon_0','distance':'d','Q':'Q0'},[check('V','Q0/C','V',numeric={'values':{'Q0':5.7,'C':.091},'value':62.6,'tolerance':.1}),check('U','Q0^2/(2*C)','J',numeric={'values':{'Q0':5.7,'C':.091},'value':179,'tolerance':1})],assumptions=['negligible_edge_effects'],units={'C':'F','Q0':'C'},notes='Areal valgt algebraisk så C er den givne kapacitans; geometrien bruges kun til relationen V=Q/C.')
# Ampere cylinder and its real non-uniform profile.
put('2024-02:4a 2024-02:4b','ampere',{'kind':'cylinder','coordinate':'s'},[check('I_enc','pi*J*R^2/3','A',subs={'s':E('R')}),check('B','mu_0*J*R/6','T',subs={'s':E('R')}),check('B','mu_0*J*R/12','T',subs={'s':E('2*R')})],domain='BA',assumptions=['infinite_cylindrical_symmetry','magnetostatic'],regions=[{'lower':'0','upper':'R','density':'J*(1-s/R)'}],notes='R er opgavens S. Numerisk strømfacitfejl dokumenteret særskilt; symbolsk facit bruges.')
put('2025-11:4a','ampere',{'kind':'cylinder','coordinate':'s'},[check('B','mu_0*J*R/4','T',subs={'s':E('R/2')}),check('B','mu_0*J*R/4','T',subs={'s':E('2*R')})],domain='BA',assumptions=['infinite_cylindrical_symmetry','magnetostatic'],regions=[{'lower':'0','upper':'R','density':'J'}])
# End-to-end CMS: field -> flux/inductance -> RL time, with actual supplied values.
step1={'id':'field','problem':{'domain':'BA','family':'ampere','variables':variables({'kind':'solenoid','turn_density':'N/L','I':'I'}),'assumptions':['ideal_long_solenoid','magnetostatic']}}
step2={'id':'inductance','bindings':{'B_field':{'ref':'field.B'}},'problem':{'domain':'DYN','family':'inductance_energy','variables':variables({'flux':'B_field*pi*a^2','I':'I','N':'N'})}}
step3={'id':'solve','bindings':{'L_ind':{'ref':'inductance.L'}},'problem':{'domain':'DYN','family':'rc_transient','variables':variables({'kind':'RL','time':'t','R':'R','L':'L_ind','voltage':'V','I0':'0','solve_for':'t','target_values':{'I':E('I')}})}}
put('2022-11:3c','rc_transient',{},[check('solved_t','-mu_0*N^2*pi*a^2/(L*R)*log(1-R*I/V)','s',numeric={'values':{'N':2180,'a':3,'L':12.5,'R':75e-6,'I':18200,'V':26},'value':2.70*3600,'tolerance':40})],domain='DYN',path=[step1,step2,step3],units={'R':'ohm','L_ind':'H','B_field':'T'},notes='ES=RI følger fra samme stationære Ohm-relation; denne opskrift validerer opladningstiden.',status='partial')
step3['problem']['variables']['target_values']={'I':E('I')}
step3['problem']['assumptions']=['reachable_RL_target']
put('2022-11:3c','rc_transient',{},[check('solved_t','-mu_0*N^2*pi*a^2/(L*R)*log(1-R*I/V)','s',numeric={'values':{'N':2180,'a':3,'L':12.5,'R':75e-6,'I':18200,'V':26},'value':2.70*3600,'tolerance':40}),check('maintain_voltage','R*I','V',numeric={'values':{'R':75e-6,'I':18200},'value':1.365,'tolerance':1e-8})],domain='DYN',path=[step1,step2,step3],units={'R':'ohm','L_ind':'H','B_field':'T'})
# Actual point-charge fields and energies, reusing general Coulomb machinery.
put('2025-11:1a','point_charges',{'charges':[['q',['a/2','a/2','0']],['q',['-a/2','a/2','0']]],'force_on_index':0},[check('F',['q^2/(4*pi*epsilon_0*a^2)','0','0'],'N'),check('U','q^2/(4*pi*epsilon_0*a)','J')])
put('2026-01:1a','point_charges',{'charges':[['q',['-a/2','sqrt(3)*a/2','0']],['-q',['a/2','sqrt(3)*a/2','0']]],'point':['0','0','0']},[check('E',['q/(4*pi*epsilon_0*a^2)','0','0'],'V/m'),check('U','-q^2/(4*pi*epsilon_0*a)','J')])
put('2024-02:1a','point_charges',{'charges':[['Q',['-a','0','0']]],'point':['0','0','0']},[check('E',['Q/(4*pi*epsilon_0*a^2)','0','0'],'V/m')])
put('2024-02:1b','point_charges',{'charges':[['Q/5',['-a*cos(theta)','a*sin(theta)','0']] for theta in []],'point':['0','0','0']},[],status='not_migrated') if False else None
# Same exact point distances and listed angles, no statistical parser.
arc=[['Q/5',[f'-a*cos({angle})',f'a*sin({angle})','0']] for angle in ['-pi/2','-pi/4','0','pi/4','pi/2']]
put('2024-02:1b','point_charges',{'charges':arc,'point':['0','0','0']},[check('E',['Q*(1+sqrt(2))/(20*pi*epsilon_0*a^2)','0','0'],'V/m')])
# Actual semicircular distribution and potential for three geometries.
put('2024-02:1c','coulomb_integral',{'kind':'line','source':['a*cos(u)','a*sin(u)','0'],'parameters':['u'],'bounds':[['pi/2','3*pi/2']],'density':'Q/(pi*a)','point':['0','0','0']},[check('E',['Q/(2*pi^2*epsilon_0*a^2)','0','0'],'V/m'),check('V','Q/(4*pi*epsilon_0*a)','V')],units={'u':'1'})
# Symbolic dipole on axis, actual 2022 source positions.
put('2022-02:1a 2022-02:1b','point_charges',{'charges':[['q',['-a','0','0']],['q',['0','-a','0']],['q',['a','0','0']],['-q',['0','a','0']]],'point':['0','0','z']},[check('U','0','J'),check('E',['0','2*q*a/(4*pi*epsilon_0*(a^2+z^2)^(3/2))','2*q*z/(4*pi*epsilon_0*(a^2+z^2)^(3/2))'],'V/m')])
# Self-image force is executable without manually constructing mirror charges.
put('2024-11:1b','images',{'charges':[['q',['a','a','0']]],'point':['a','a','0'],'planes':[0,1],'self_index':0,'test_charge':'q'},[check('F',['-q^2*(4-sqrt(2))/(64*pi*epsilon_0*a^2)','-q^2*(4-sqrt(2))/(64*pi*epsilon_0*a^2)','0'],'N')],assumptions=['grounded_infinite_planes'])
put('2025-11:1b','images',{'charges':[['q',['a/2','a/2','0']],['q',['-a/2','a/2','0']]],'point':['a/2','a/2','0'],'planes':[1],'self_index':0,'test_charge':'q'},[check('F',['q^2/(4*pi*epsilon_0*a^2)*(1-1/(2*sqrt(2)))','-q^2/(4*pi*epsilon_0*a^2)*(1+1/(2*sqrt(2)))','0'],'N')],assumptions=['grounded_infinite_planes'])
print('Final:',sum(json.loads(p.read_text())['status']=='executable' for p in DEST.glob('*.json')),'executable')
calc('2021-11:3a',{'E':['k*y','-k*x','k*d']},[check('curl_E',['0','0','-2*k'],'V/m^2')],units={'k':'V/m^2'},assumptions=['electrostatic'])
calc('2021-11:3b',{'V':'k*r^2*(2*cos(theta)^2-sin(theta)^2)'},[check('laplacian_V','0','V/m^2')],system='spherical',coords=['r','theta','phi'],units={'k':'V/m^2'})
put('2022-02:5b','potential_from_field',{'coordinate':'theta','field':'V*(2*cos(theta)*sin(theta)^2-cos(theta)^3)','start':'0','end':'pi/6','test_charge':'Q'},[check('W_external','3*Q*V/8','J')])
# Exact cylindrical vector Laplacian, in separate smooth regions.
calc('2022-02:7a 2022-02:7b',{'A':['0','0','-mu_0*I*s^2/(4*pi*R^2)']},[check('B',['0','mu_0*I*s/(2*pi*R^2)','0'],'T'),check('div_A','0'),check('laplacian_A',['0','0','-mu_0*I/(pi*R^2)'])],system='cylindrical',coords=['s','phi','z'],status='partial') if False else None
# Region-complete path with inner/outer fields and matching C, rather than a sampled radius.
outside={'id':'outer','problem':{'domain':'BA','family':'field_calculus','variables':variables({'coordinates':['s','phi','z'],'system':'cylindrical','A':['0','0','C*log(s/R)-mu_0*I/(4*pi)']}),'assumptions':['magnetostatic']}}
inside={'id':'inner','problem':{'domain':'BA','family':'field_calculus','variables':variables({'coordinates':['s','phi','z'],'system':'cylindrical','A':['0','0','-mu_0*I*s^2/(4*pi*R^2)']}),'assumptions':['magnetostatic']}}
matching={'id':'solve','problem':{'domain':'BA','family':'field_calculus','variables':variables({'coordinates':['s','phi','z'],'system':'cylindrical','A':['0','0','C*log(s/R)-mu_0*I/(4*pi)'],'at':{'map':[[E('s'),E('R')]]},'solve_for':'C','target_values':{'B':M(['0','mu_0*I/(2*pi*R)','0'])}}),'assumptions':['magnetostatic']}}
# C must be allowed negative: modify the symbol declaration after writing.
for id in ['2022-02:7a','2022-02:7b']:
 cs=[dict(check('B',['0','mu_0*I*s/(2*pi*R^2)','0'],'T'),step='inner'),dict(check('B',['0','-C/s','0'],'T'),step='outer'),dict(check('laplacian_A',['0','0','-mu_0*I/(pi*R^2)']),step='inner'),check('solved_C','-mu_0*I/(2*pi)','T*m')]
 put(id,'field_calculus',{},cs,domain='BA',path=[inside,outside,matching],units={'C':'T*m'})
 fp=DEST/(id.replace(':','_p').replace('-','_')+'.json');payload=json.loads(fp.read_text());payload['symbols']['C']={'real':True};fp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
calc('2026-01:4a',{'A':['-k*y','k*x','0']},[check('B',['0','0','2*k'],'T')],units={'k':'T'},assumptions=['magnetostatic'])
# Actually two vector-potential representations in 4a: attach the second to the same path.
fp=DEST/'2026_01_p4a.json';payload=json.loads(fp.read_text());payload['path'].append({'id':'cylindrical','problem':{'domain':'BA','family':'field_calculus','variables':variables({'coordinates':['s','phi','z'],'system':'cylindrical','A':['0','k*s','0']}),'assumptions':['magnetostatic']}});payload['expected'].append(dict(check('B',['0','0','2*k'],'T'),step='cylindrical'));fp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
# Full dynamical exponential coil and dissipated heat.
put('2025-01:6a 2025-01:6b','faraday',{'time':'t','B_normal':'B*(1-exp(-t/tau))+B_offset','area':'pi*a^2','N':'N','R':'R','time_bounds':['0','T']},[check('EMF','-N*pi*a^2*B*exp(-t/tau)/tau','V',sign=-1),check('W','(N*pi*a^2*B)^2*(1-exp(-2*T/tau))/(2*tau*R)','J',numeric={'values':{'N':12,'a':.2,'B':5,'tau':60,'R':1.2,'T':55},'value':.33,'tolerance':.01})],domain='DYN',assumptions=['uniform_normal_B','negligible_self_inductance'],units={'R':'ohm','B_offset':'T','T':'s'})
# Current and power in a falling ring: normal +z, positive velocity downward.
put('2023-11:5a 2023-11:5b','faraday',{'time':'t','B_normal':'B*(1+k*v*t)','area':'A','R':'R'},[check('EMF','-A*B*k*v','V',sign=-1),check('P','(A*B*k*v)^2/R','W')],domain='DYN',assumptions=['uniform_normal_B','negligible_self_inductance'],units={'A':'m^2','k':'1/m','R':'ohm'})
# Magnetic material tests preserve free vs bound source distinction.
put('2022-11:5a','magnetic_material',{'kind':'magnetization','coordinates':['s','phi','z'],'system':'cylindrical','M':['0','0','k*s^2'],'H':['0','0','0'],'normal':['1','0','0'],'surface_substitutions':{'map':[[E('s'),E('R')]]}},[check('J_bound',['0','-2*k*s','0'],'A/m^2'),check('K_bound',['0','k*R^2','0'],'A/m')],domain='BA',units={'k':'A/m^3'})
# Original exact power-law Gauss sphere with dielectric.
put('2023-02:2a 2023-02:2b','gauss_radial',{'coordinate':'r','symmetry':'sphere'},[check('Q_enc','pi*k*R^4','C',subs={'r':E('R')}),check('E','k*R^2/(16*epsilon_0*epsilon_r)','V/m',subs={'r':E('R/2')}),check('E','k*R^2/(16*epsilon_0)','V/m',subs={'r':E('2*R')})],assumptions=['spherical_symmetry'],regions=[{'lower':'0','upper':'R','density':'k*r','permittivity':'epsilon_0*epsilon_r'}],units={'k':'C/m^4'})
put('2023-02:2c','polarization',{'coordinates':['r','theta','phi'],'system':'spherical','E':['k*r^2/(4*epsilon_0*epsilon_r)','0','0'],'epsilon':'epsilon_0*epsilon_r'},[check('P',['(epsilon_r-1)*k*r^2/(4*epsilon_r)','0','0'],'C/m^2')],units={'k':'C/m^4'})
# Surface and volume polarization in all six faces: normals and evaluation points are explicit.
for id in ['2024-02:2a','2024-02:2b']:
 pth=[];ex=[]
 for axis,coordinate in enumerate(['x','y','z']):
  for sign in [-1,1]:
   normal=['0','0','0'];normal[axis]=str(sign);name=f'face{axis}_{"p" if sign==1 else "m"}'
   data={'coordinates':['x','y','z'],'system':'cartesian','P':['k*x','k*y','k*z'],'normal':normal,'surface_substitutions':{'map':[[E(coordinate),E(f'{sign}*L/2')]]}}
   pth.append({'id':name,'problem':{'domain':'EV','family':'polarization','variables':variables(data)}})
   ex.append(dict(check('sigma_bound','k*L/2','C/m^2'),step=name));ex.append(dict(check('rho_bound','-3*k','C/m^3'),step=name))
 put(id,'polarization',{},ex,path=pth,units={'k':'C/m^3'})
print('Reviewed executable:',sum(json.loads(p.read_text())['status']=='executable' for p in DEST.glob('*.json')))
# Numerical givens are separate from the symbolic problem and from expected answers.
# These constants were transcribed above from the source, not computed by solvers.
for fp in DEST.glob('*.json'):
 payload=json.loads(fp.read_text());given={}
 for c in payload['expected']:
  for name,value in c.get('numeric',{}).get('values',{}).items():
   if name in given and given[name]!=value:raise ValueError('Conflicting source constants for '+payload['id'])
   given[name]=value
 payload['given_values']=given
 payload['given_units']={name:payload['symbol_units'][name] for name in given}
 fp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
# Close the full RC -> current -> force chain in January 2026 2d.
rcstep={'id':'discharge','problem':{'domain':'DYN','family':'rc_transient','variables':variables({'kind':'RC','time':'t','R':'R','C':'C','Q0':'Q0'})}}
force_step={'id':'solve','bindings':{'I_discharge':{'ref':'discharge.I'}},'problem':{'domain':'BA','family':'wire_force','variables':variables({'kind':'parallel','I1':'I_discharge','I2':'-I_discharge','distance':'d','length':'L'}),'assumptions':['parallel_infinite_wires']}}
put('2026-01:2d','wire_force',{},[check('F_signed_attraction','-mu_0*L/(2*pi*d)*(Q0/(R*C))^2*exp(-2*t/(R*C))','N',sign=-1)],domain='BA',path=[rcstep,force_step],units={'R':'ohm','C':'F','Q0':'C','I_discharge':'A'},notes='De parallelle stænger fører modsat rettede strømme; negativ F_signed_attraction betyder frastødning.')
put('2021-11:6b','ampere_maxwell',{'E':'V*cos(omega*t)/d','time':'t','coordinate':'s','plate_radius':'a'},[check('J_displacement','-epsilon_0*V*omega*sin(omega*t)/d','A/m^2'),check('I_displacement','-pi*(a/2)^2*epsilon_0*V*omega*sin(omega*t)/d','A',subs={'s':E('a/2')}),check('B','-mu_0*epsilon_0*V*omega*a*sin(omega*t)/(4*d)','T',subs={'s':E('a/2')})],domain='DYN',assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects'])
put('2023-02:6a','ampere_maxwell',{'E':'V*sin(omega*t)','time':'t','coordinate':'s','plate_radius':'R'},[check('J_displacement','epsilon_0*V*omega*cos(omega*t)','A/m^2'),check('I_displacement','pi*(R/2)^2*epsilon_0*V*omega*cos(omega*t)','A',subs={'s':E('R/2')}),check('B','mu_0*epsilon_0*V*omega*R*cos(omega*t)/4','T',subs={'s':E('R/2')})],domain='DYN',assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects'],units={'V':'V/m'})
base={'id':'correction','problem':{'domain':'DYN','family':'ampere_maxwell','variables':variables({'E':'V*cos(omega*t)','time':'t','coordinate':'s','plate_radius':'a'}),'assumptions':['uniform_axial_E','circular_symmetry','negligible_edge_effects','induced_correction_zero_at_edge']}}
threshold={'id':'solve','problem':{'domain':'DYN','family':'ampere_maxwell','variables':variables({'E':'V*cos(omega*t)','time':'t','coordinate':'s','plate_radius':'a','at':{'map':[[E('s'),E('0')],[E('t'),E('0')]]},'solve_for':'omega','target_values':{'E_correction_inside':E('V/100')}}),'assumptions':['uniform_axial_E','circular_symmetry','negligible_edge_effects','induced_correction_zero_at_edge']}}
put('2021-11:6c','ampere_maxwell',{},[dict(check('E_correction_inside','mu_0*epsilon_0*omega^2*(a^2-s^2)*V*cos(omega*t)/4','V/m'),step='correction'),check('solved_omega','1/(5*a*sqrt(mu_0*epsilon_0))','1/s',numeric={'values':{'a':.01},'value':5.99584916e9,'tolerance':1e5})],domain='DYN',path=[base,threshold],units={'V':'V/m'},notes='Den efterspurgte frekvens nu=omega/(2pi), cirka 0,954 GHz. Eksplicit E_korrektion(a)=0 randbetingelse.')
# Finalize numerical source values after every definition, including late paths.
for fp in DEST.glob('*.json'):
 payload=json.loads(fp.read_text());given=dict(payload.get('given_values',{}))
 for c in payload['expected']:
  given.update(c.get('numeric',{}).get('values',{}))
 if payload['id']=='2026-01:2d':given.update(R=.25,C=.091,Q0=5.7,L=.83,d=.052)
 payload['given_values']=given
 payload['given_units']={name:payload['symbol_units'][name] for name in given}
 fp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
print('Executable total:',sum(json.loads(p.read_text())['status']=='executable' for p in DEST.glob('*.json')))
