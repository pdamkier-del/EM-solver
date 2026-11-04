"""Migration of remaining supplied exams using existing general solver operations.

Expected formulas are independent transcriptions. No solver is called by this
builder, so expected values cannot be accidentally recorded from an implementation.
"""
import json
from build_historical_recipes import E,M,wrap,variables,check,put,DEST,REG,DEFAULT,LABELS

LABELS.update({'field_unit','substitute_results'})

def step(id,family,data,domain='EV',assumptions=(),bindings=None,regions=()):
 return {'id':id,'bindings':bindings or {},'problem':{'domain':domain,'family':family,'variables':variables(data),'assumptions':list(assumptions),'regions':[{k:E(v) for k,v in reg.items()} for reg in regions]}}
def ck(stepid,key,value,unit=None,**kwargs):return dict(check(key,value,unit,**kwargs),step=stepid)
def ref(s,key,*indices):return {'ref':s+'.'+key,**({'indices':list(indices)} if indices else {})}
def real(id,*names):
 p=DEST/(id.replace(':','_p').replace('-','_')+'.json');j=json.loads(p.read_text())
 for name in names:j['symbols'][name]={'real':True}
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def pw(entries):return {'piecewise':entries}
def lt(a,b):return {'relation':'lt','left':E(a),'right':E(b)}
def le(a,b):return {'relation':'le','left':E(a),'right':E(b)}
# EV: charges, conductor equilibrium and boundary conditions.
put('2021-06:1a 2021-06:1c','conductors',{'kind':'cavity_totals','enclosed_charge':'q','metal_charge':'3*q','outer_radius':'R'},[check('Q_inner','-q','C'),check('Q_outer','4*q','C'),check('V','q/(pi*epsilon_0*R)','V')],assumptions=['electrostatic','closed_conductor','spherical_outer_surface','no_external_sources'])
tetra=[['Q',['0','0','0']],['Q',['a','0','0']],['Q',['a/2','sqrt(3)*a/2','0']],['Q',['a/2','a/(2*sqrt(3))','sqrt(2/3)*a']]]
put('2021-06:2a','point_charges',{'charges':tetra,'point':['0','0','2*a']},[check('U','6*Q^2/(4*pi*epsilon_0*a)','J')])
put('2021-06:5b','units',{'field_unit':'V/m','coordinate_power':2},[{'step':'solve','result':'coefficient_unit','value':'volt / meter ** 3'}])
# Ordered arbitrary radii: b=a+d, c=a+d+h are aliases, never fixed ratios.
shells=[['0','a','Q'],['a+d','a+d+h','q']]
conditions=[E('0'),E('Q/(4*pi*epsilon_0*r^2)'),E('0'),E('(Q+q)/(4*pi*epsilon_0*r^2)')]
field=pw([[conditions[0],lt('r','a')],[conditions[1],lt('r','a+d')],[conditions[2],le('r','a+d+h')],[conditions[3],True]])
base_checks=[dict(check('E','0'),value=field),check('U','(Q^2*(1/a-1/(a+d))+(Q+q)^2/(a+d+h))/(8*pi*epsilon_0)','J')]
base_checks += [check('surfaces',value,'C/m^2',indices=[idx,2]) for idx,value in enumerate(['Q/(4*pi*a^2)','-Q/(4*pi*(a+d)^2)','(Q+q)/(4*pi*(a+d+h)^2)'])]
# Piecewise endpoints inside metals differ only at the charged surfaces: compare
# the four open physical regions, not an arbitrary point value at an ideal sheet.
base_checks[0:1]=[check('E','0','V/m',subs={'r':E('a/2')}),check('E','Q/(4*pi*epsilon_0*(a+d/2)^2)','V/m',subs={'r':E('a+d/2')}),check('E','0','V/m',subs={'r':E('a+d+h/2')}),check('E','(Q+q)/(4*pi*epsilon_0*(a+d+h+L)^2)','V/m',subs={'r':E('a+d+h+L')})]
put('2025-01:2a 2025-01:2b 2025-01:2c','conductors',{'coordinate':'r','shells':shells},base_checks,assumptions=['concentric_spheres','electrostatic'],notes='Kildens b=a+d og c=a+d+h med positive frie mellemrum d,h. Alle fire regioner og alle overflader kontrolleres.')
put('2021-11:2a','conductors',{'coordinate':'r','shells':[['a','a+d','Q'],['a+d+h','a+d+h+L','q']]},[check('surfaces',v,'C/m^2',indices=[i,2]) for i,v in enumerate(['0','Q/(4*pi*(a+d)^2)','-Q/(4*pi*(a+d+h)^2)','(Q+q)/(4*pi*(a+d+h+L)^2)'])],assumptions=['concentric_spheres','electrostatic'])
# Free, bound and total charges at every metal/dielectric interface.
boundary_steps=[];boundary_checks=[]
for name,radius,normal,eout,epsilon in [('inner','a',1,'0','epsilon_0'),('gap1','a+d',1,'Q/(4*pi*epsilon_0*epsilon_r*(a+d)^2)','epsilon_0*epsilon_r'),('gap2','a+d+h',-1,'Q/(4*pi*epsilon_0*epsilon_r*(a+d+h)^2)','epsilon_0*epsilon_r'),('outer','a+d+h+L',1,'(Q+q)/(4*pi*epsilon_0*(a+d+h+L)^2)','epsilon_0')]:
 boundary_steps.append(step(name,'conductors',{'kind':'boundary','normal':[str(normal),'0','0'],'E_inside':['0','0','0'],'E_outside':[eout,'0','0'],'epsilon_inside':'epsilon_0','epsilon_outside':epsilon}))
 if name=='inner':free=total=bound='0'
 elif name=='outer':free=total=f'(Q+q)/(4*pi*({radius})^2)';bound='0'
 else:
  free=f'{normal}*Q/(4*pi*({radius})^2)';total=f'{normal}*Q/(4*pi*epsilon_r*({radius})^2)';bound=f'-{normal}*(epsilon_r-1)*Q/(4*pi*epsilon_r*({radius})^2)'
 boundary_checks += [ck(name,'sigma_free',free,'C/m^2'),ck(name,'sigma_total',total,'C/m^2'),ck(name,'sigma_bound',bound,'C/m^2')]
put('2021-11:2c','conductors',{},boundary_checks,path=boundary_steps,notes='Fri og bunden ladning adskilt. Facit viser kun den samlede lokale tæthed i dielektriktilfældet; se afvigelsesrapport.')
# Grounded inner sphere solved for an unknown real charge, both gap materials.
for id,epsilon,expected in [('2025-11:3a','epsilon_0','-Q/2'),('2025-11:3b','epsilon_0*epsilon_r','-epsilon_r*Q/(1+epsilon_r)')]:
 put(id,'conductors',{'coordinate':'a','shells':[['0','a','q_unknown'],['2*a','2*a','Q']],'gap_permittivities':['epsilon_0',epsilon],'solve_for':'q_unknown','target_values':{'V':E('0')},'substitute_results':['V']},[check('solved_q_unknown',expected,'C'),check('at_solution_V','0','V')],assumptions=['concentric_spheres','electrostatic'],units={'q_unknown':'C'});real(id,'q_unknown')
put('2023-11:4a 2023-11:4b 2023-11:4c','conductors',{'kind':'spherical_sectors','charge':'Q','radius':'R','coordinate':'r','sectors':[['2*pi','epsilon_1'],['2*pi','epsilon_2']]},[check('E','Q/(2*pi*(epsilon_1+epsilon_2)*r^2)','V/m'),check('D_0','epsilon_1*Q/(2*pi*(epsilon_1+epsilon_2)*r^2)','C/m^2'),check('D_1','epsilon_2*Q/(2*pi*(epsilon_1+epsilon_2)*r^2)','C/m^2'),check('sigma_free_0','Q*epsilon_1/(2*pi*R^2*(epsilon_1+epsilon_2))','C/m^2'),check('sigma_free_1','Q*epsilon_2/(2*pi*R^2*(epsilon_1+epsilon_2))','C/m^2')],assumptions=['radial_dielectric_interfaces','electrostatic','no_external_sources'],units={'epsilon_1':'F/m','epsilon_2':'F/m'})
# General coaxial charged rod + thin conducting shell; actual free line charges.
gapvars={'coordinate':'s','symmetry':'cylinder','surface_charges':[['a+d','-lam/(2*pi*(a+d))']]}
rodregions=[{'lower':'0','upper':'a','density':'2*lam/(pi*a^2)','permittivity':'epsilon_0'}]
put('2022-02:2a','gauss_radial',gapvars,[check('E','lam/(pi*epsilon_0*(a+d/2))','V/m',subs={'s':E('a+d/2')})],assumptions=['infinite_cylindrical_symmetry'],regions=rodregions,units={'lam':'C/m'})
pth=[];cs=[]
for name,sign,field in [('inner',-1,'lam/(pi*epsilon_0*b)'),('outer',1,'lam/(2*pi*epsilon_0*b)')]:
 pth.append(step(name,'conductors',{'kind':'boundary','normal':[str(sign),'0','0'],'E_inside':['0','0','0'],'E_outside':[field,'0','0'],'epsilon_inside':'epsilon_0','epsilon_outside':'epsilon_0'}))
 cs.append(ck(name,'sigma_free',f'{2 if sign<0 else 1}*{sign}*lam/(2*pi*b)','C/m^2'))
put('2022-02:2b','conductors',{},cs,path=pth,units={'lam':'C/m'})
gapregions=rodregions+[{'lower':'a','upper':'a+d','density':'0','permittivity':'epsilon_0*epsilon_r'}]
put('2022-02:2c','potential_from_field',{},[check('delta_V','lam*log((a+d)/a)/(pi*epsilon_0*epsilon_r)','V',numeric={'values':{'lam':90e-9,'a':.001,'d':.003,'epsilon_r':4.2},'value':1100,'tolerance':50})],path=[step('gauss','gauss_radial',gapvars,assumptions=['infinite_cylindrical_symmetry'],regions=gapregions),step('solve','potential_from_field',{'field':'field_gap','coordinate':'s','start':'a+d','end':'a'},bindings={'field_gap':ref('gauss','E')})],units={'lam':'C/m'})
# Point charge roots, quasistatic work, equilibrium and energy.
charges=[['-6*q',['0','0','0']],['3*q',['d','0','0']]]
put('2022-11:1a','point_charges',{'charges':charges,'point':['x','0','0'],'solve_for':'x','target_values':{'V':E('0')}},[{'step':'solve','result':'solution_branches','value':[{'map':[[E('x'),E('2*d/3')]]},{'map':[[E('x'),E('2*d')]]}]}],notes='d=12 cm; q=1 microC. Rødderne er 8 cm og 24 cm.')
put('2022-11:1b','point_charges',{'charges':charges,'point':['x','0','0'],'solve_for':'x','target_values':{'E':M(['0','0','0'])}},[check('solved_x','(2+sqrt(2))*d','m',numeric={'values':{'d':.12,'q':1e-6},'value':.410,'tolerance':.001})])
put('2022-11:1c','point_charges',{'charges':[['-6*q',['0','0','0']],['3*q',['2*d','0','0']]],'initial_charges':charges,'point':['0','0','L']},[check('W_external','9*q^2/(4*pi*epsilon_0*d)','J',numeric={'values':{'d':.12,'q':1e-6},'value':.674,'tolerance':.002})])
put('2024-11:1a','point_charges',{'charges':[['q',['a','a','0']],['q',['-a','-a','0']],['-q',['a','-a','0']],['-q',['-a','a','0']]],'force_on_index':0},[check('F',['-q^2*(4-sqrt(2))/(64*pi*epsilon_0*a^2)','-q^2*(4-sqrt(2))/(64*pi*epsilon_0*a^2)','0'],'N')])
for id,include in [('2023-02:1a',False),('2023-02:1b',True),('2023-02:1c',True)]:
 data=[['-3*q',['0','0','0']],['2*q',['a','0','0']]]+([['4*q',['a/2','sqrt(3)*a/2','0']]] if include else [])
 force=['(12 if include else 6)'] # expected values below are independent Coulomb references
 cs=[check('F',[f'{12 if include else 6}*q^2/(4*pi*epsilon_0*a^2)',('6*sqrt(3)*q^2/(4*pi*epsilon_0*a^2)' if include else '0'),'0'],'N')]
 if id.endswith('1c'):cs=[check('U','-10*q^2/(4*pi*epsilon_0*a)','J',numeric={'values':{'q':1e-6,'a':.2},'value':-.45,'tolerance':.01})]
 put(id,'point_charges',{'charges':data,'force_on_index':0},cs)
quad=[['q',['-a','0','0']],['q',['0','-a','0']],['q',['a','0','0']],['-q',['0','a','0']]]
put('2022-02:1c','multipole',{'charges':quad,'r':'r','theta':'theta','phi':'phi'},[check('dipole',['0','-2*q*a','0'],'C*m'),check('V_far','2*q/(4*pi*epsilon_0)*(1/r-a*sin(theta)*sin(phi)/r^2)','V')])
for id in ['2023-11:1a','2023-11:1b','2023-11:1c']:
 configs=[('line',[['q',['-a/2','0','0']],['Q_unknown',['0','0','0']],['q',['a/2','0','0']]],'-q/4','q*(4*Q_unknown+q)/(4*pi*epsilon_0*a)'),('square',[['q',['-a/2','-a/2','0']],['q',['a/2','-a/2','0']],['q',['a/2','a/2','0']],['q',['-a/2','a/2','0']],['Q_unknown',['0','0','0']]],'-(2*sqrt(2)+1)*q/4','q*(4*sqrt(2)*Q_unknown+(4+sqrt(2))*q)/(4*pi*epsilon_0*a)')]
 pth=[];cs=[]
 for name,data,qeq,energy in configs:
  pth.append(step(name,'point_charges',{'charges':data,'force_on_index':0,'solve_for':'Q_unknown','target_values':{'F':M(['0','0','0'])},'substitute_results':['U','F']},assumptions=['free_point_charges_3D']))
  cs += [ck(name,'solved_Q_unknown',qeq,'C'),ck(name,'U',energy,'J'),ck(name,'at_solution_U','0','J'),ck(name,'at_solution_F',['0','0','0'],'N')]
  cs.append({'step':name,'result':'equilibrium_stability','value':'unstable_if_unconstrained_3D'})
 put(id,'point_charges',{},cs,path=pth,units={'Q_unknown':'C'});real(id,'Q_unknown')
# Continuous distributions: independent integrals and actual units.
put('2021-11:1a 2021-11:1b','coulomb_integral',{'kind':'surface','source':['R*sin(theta)*cos(phi)','R*sin(theta)*sin(phi)','R*cos(theta)'],'parameters':['theta','phi'],'bounds':[['pi/2','pi'],['0','2*pi']],'density':'sigma','point':['0','0','0'],'test_charge':'Q'},[check('U_external','R*sigma*Q/(2*epsilon_0)','J',numeric={'values':{'R':.22,'sigma':.00046,'Q':.75e-6},'value':4.3,'tolerance':.1}),check('F',['0','0','sigma*Q/(4*epsilon_0)'],'N')],notes='Original-PDF siger microC, ikke det fejlagtigt tekstudtrukne milliC.')
put('2025-01:3a 2025-01:3b','coulomb_integral',{'kind':'surface','source':['s*cos(phi)','s*sin(phi)','0'],'parameters':['s','phi'],'bounds':[['a','a+d'],['0','2*pi']],'density':'sigma','point':['0','0','z']},[check('V','sigma/(2*epsilon_0)*(sqrt((a+d)^2+z^2)-sqrt(a^2+z^2))','V'),check('E',['0','0','sigma*z/(2*epsilon_0)*(1/sqrt(a^2+z^2)-1/sqrt((a+d)^2+z^2))'],'V/m')],notes='Kildens ydre radius b=a+d. Planegrænsen kontrolleres separat i variationstesten.')
# Potentials of all three geometries in the 2024 arc question.
p1=step('one','point_charges',{'charges':[['Q',['-a','0','0']]],'point':['0','0','0']})
arc=[['Q/5',[f'-a*cos({angle})',f'a*sin({angle})','0']] for angle in ['-pi/2','-pi/4','0','pi/4','pi/2']]
p2=step('five','point_charges',{'charges':arc,'point':['0','0','0']})
p3=step('arc','coulomb_integral',{'kind':'line','source':['a*cos(theta)','a*sin(theta)','0'],'parameters':['theta'],'bounds':[['pi/2','3*pi/2']],'density':'Q/(pi*a)','point':['0','0','0']})
put('2024-02:1d','coulomb_integral',{},[ck(name,'V','Q/(4*pi*epsilon_0*a)','V') for name in ['one','five','arc']],path=[p1,p2,p3])
# Piecewise signed half-circle: total field and dipole in a single general integral.
angular_density=pw([[E('-2*q/(pi*a)'),lt('theta','pi/2')],[E('2*q/(pi*a)'),True]])
circle=step('arc','coulomb_integral',{'kind':'line','source':['a*cos(theta)','a*sin(theta)','0'],'parameters':['theta'],'bounds':[['0','pi']],'density':angular_density,'point':['0','0','0']})
dipole=step('points','multipole',{'charges':[['q',['-a/2','sqrt(3)*a/2','0']],['-q',['a/2','sqrt(3)*a/2','0']]]})
put('2026-01:1b','coulomb_integral',{},[ck('arc','E',['q/(pi^2*epsilon_0*a^2)','0','0'],'V/m')],path=[circle])
put('2026-01:1c','multipole',{},[ck('arc','dipole',['-4*q*a/pi','0','0'],'C*m'),ck('points','dipole',['-q*a','0','0'],'C*m')],path=[circle,dipole])
# BA: Ampere, exact cross-section currents and magnetic superposition.
put('2021-06:3a','ampere',{'kind':'cylinder','coordinate':'s','surface_currents':[['a+d','-3*I/(8*pi*(a+d))']]},[check('B','mu_0*I/(2*pi*(a+d/2))','T',subs={'s':E('a+d/2')}),check('B','mu_0*I/(8*pi*(a+d+L))','T',subs={'s':E('a+d+L')})],domain='BA',assumptions=['infinite_cylindrical_symmetry','magnetostatic'],regions=[{'lower':'0','upper':'a','density':'I/(pi*a^2)'}])
put('2021-06:3b','wire_force',{'kind':'parallel','I1':'I/4','I2':'I','distance':'d','length':'L'},[check('F_signed_attraction','mu_0*I^2*L/(8*pi*d)','N',sign=1)],domain='BA',assumptions=['parallel_infinite_wires'],notes='F/L er den efterspurgte kraft pr. længde; positivt fortegn betyder tiltrækning.')
put('2021-11:5a','ampere',{'kind':'azimuthal_cylinder','coordinate':'s','radius':'a','J_phi':'rho*omega*s'},[check('B','3*mu_0*rho*omega*a^2/8','T',subs={'s':E('a/2')}),check('B','0','T',subs={'s':E('2*a')})],domain='BA',assumptions=['infinite_cylindrical_symmetry','magnetostatic','B_infinity_zero'])
# Displaced bore area is integrated on its actual translated disk.
full=step('full','ampere',{'kind':'current_surface','surface':['s*cos(phi)','s*sin(phi)','0'],'parameters':['s','phi'],'bounds':[['0','R'],['0','2*pi']],'J_on_surface':['0','0','J']},domain='BA')
hole=step('hole','ampere',{'kind':'current_surface','surface':['R/4+s*cos(phi)','s*sin(phi)','0'],'parameters':['s','phi'],'bounds':[['0','R/2'],['0','2*pi']],'J_on_surface':['0','0','-J']},domain='BA')
merge=step('solve','algebra',{'outputs':{'I':E('I_full+I_hole')},'output_units':{'I':'A'}},domain='BA',bindings={'I_full':ref('full','I_enc'),'I_hole':ref('hole','I_enc')})
put('2022-02:4a','ampere',{},[check('I','3*pi*R^2*J/4','A')],domain='BA',path=[full,hole,merge])
put('2022-02:4b','magnetic_superposition',{'point':['3*R/4','0','0'],'sources':[{'kind':'cylinder','center':wrap(['0','0','0']),'radius':E('R'),'J':E('J')},{'kind':'cylinder','center':wrap(['R/4','0','0']),'radius':E('R/2'),'J':E('-J')}]},[check('B',['0','mu_0*J*R/8','0'],'T')],domain='BA',assumptions=['parallel_infinite_sources','magnetostatic'])
# Lens cavity, arbitrary separation d with both evaluation points guaranteed inside.
# R=d+a and b=a/2 parameterize the open overlap without fixing d/R.
for id,point in [('2025-11:4b',['0','0','0']),('2025-11:4c',['0','a/2','0'])]:
 put(id,'magnetic_superposition',{'point':point,'sources':[{'kind':'cylinder','center':wrap(['-d','0','0']),'radius':E('d+a'),'J':E('J')},{'kind':'cylinder','center':wrap(['d','0','0']),'radius':E('d+a'),'J':E('-J')}]},[check('B',['0','mu_0*J*d','0'],'T')],domain='BA',assumptions=['parallel_infinite_sources','magnetostatic'],notes='R=d+a og b=a/2 sikrer overlap; separation d er fri. Generel punktuafhængighed verificeres ved to forskellige linjer og i variationstest.')
put('2025-01:5a','magnetic_superposition',{'point':['0','0','0'],'sources':[{'kind':'wire','center':wrap(['-a','0','0']),'I':E('I')}]},[check('B',['0','mu_0*I/(2*pi*a)','0'],'T')],domain='BA',assumptions=['parallel_infinite_sources','magnetostatic'])
sources=[{'kind':'wire','center':wrap([f'-a*cos({angle})',f'a*sin({angle})','0']),'I':E('I/5')} for angle in ['-pi/2','-pi/4','0','pi/4','pi/2']]
put('2025-01:5b','magnetic_superposition',{'point':['0','0','0'],'sources':sources},[check('B',['0','mu_0*I*(1+sqrt(2))/(10*pi*a)','0'],'T')],domain='BA',assumptions=['parallel_infinite_sources','magnetostatic'])
put('2025-01:5c','magnetic_superposition',{'point':['0','0','0'],'sources':[{'kind':'wire','center':wrap(['a*cos(phi)','a*sin(phi)','0']),'I':E('I/pi')}],'distribution_bounds':[['phi','pi/2','3*pi/2']]},[check('B',['0','mu_0*I/(pi^2*a)','0'],'T')],domain='BA',assumptions=['parallel_infinite_sources','magnetostatic'])
put('2024-11:3a 2024-11:3b','magnetic_superposition',{'point':['b+d','0','0'],'sources':[{'kind':'wire','center':wrap(['s','0','0']),'I':E('I/d')}],'distribution_bounds':[['s','0','d']],'limits':{'B':[E('d'),E('0')]}},[check('B',['0','mu_0*I*log((b+d)/b)/(2*pi*d)','0'],'T'),check('limit_B',['0','mu_0*I/(2*pi*b)','0'],'T')],domain='BA',assumptions=['parallel_infinite_sources','magnetostatic'],notes='Kildens båndbredde w betegnes d; b er afstanden til nærmeste kant.')
# Force on a bent wire: both actual curve segments, automatically summed.
paths=[{'source':wrap(['s','0','0']),'parameter':E('s'),'bounds':wrap(['0','L'])},{'source':wrap(['3*L/2-L*cos(theta)/2','L*sin(theta)/2','0']),'parameter':E('theta'),'bounds':wrap(['0','pi'])}]
put('2022-02:3a','wire_force',{'paths':paths,'I':'I','B':['0','0','B']},[check('F',['0','-2*I*L*B','0'],'N'),check('magnitude','2*I*L*B','N',numeric={'values':{'B':.45,'L':.23,'I':7.6},'value':1.6,'tolerance':.03})],domain='BA')
# Rotating charges, full volume integral for the disk's dipole moment.
put('2022-11:4a','multipole',{'charges':[],'transported_charge':'2*pi*rho*R*b*h','period':'2*pi/omega','area':'pi*R^2','normal':['0','0','1']},[check('circulation_current','rho*omega*R*b*h','A'),check('magnetic_dipole',['0','0','pi*rho*omega*b*h*R^3'],'A*m^2')],domain='BA')
put('2022-11:4b','multipole',{'charges':[],'position':['s*cos(phi)','s*sin(phi)','z'],'current_density':['-rho*omega*s*sin(phi)','rho*omega*s*cos(phi)','0'],'jacobian':'s','bounds':[['s','0','R'],['phi','0','2*pi'],['z','-h/2','h/2']]},[check('magnetic_dipole',['0','0','pi*rho*omega*h*R^4/4'],'A*m^2')],domain='BA')
put('2023-02:3a','point_charges',{'charges':[['q',['0','0','d']],['q',['0','0','-d']],['-2*q',['0','0','0']]],'point':['0','0','z_far'],'far_coordinate':'z_far','series_order':5},[check('E_far',['0','0','6*q*d^2/(4*pi*epsilon_0*z_far^4)'],'V/m')],units={'z_far':'m'},notes='E=3*Theta/(4pi epsilon0 z^4), Theta=2qd²; Fjernfeltsbetingelsen z>>d er eksplicit tilnærmelse.')
# Actual current through the tilted disk, obtained from A -> B -> J first.
avec=step('field','field_calculus',{'coordinates':['x','y','z'],'system':'cartesian','A':['3*k*z*y','-2*k*z*y','k*z^2']},domain='BA',assumptions=['magnetostatic'])
# e1=(1,-1,0)/sqrt2; e2=n cross e1=(-1,-1,-2)/sqrt6, e1 cross e2=n.
surface=['s*cos(phi)/sqrt(2)-s*sin(phi)/sqrt(6)','-s*cos(phi)/sqrt(2)-s*sin(phi)/sqrt(6)','-2*s*sin(phi)/sqrt(6)']
current=step('solve','ampere',{'kind':'current_surface','surface':surface,'parameters':['s','phi'],'bounds':[['0','R'],['0','2*pi']],'J_on_surface':ref('field','J')},domain='BA')
put('2023-02:4b','ampere',{},[check('I_enc','2*k*pi*R^2/(sqrt(3)*mu_0)','A')],domain='BA',path=[avec,current],units={'k':'T/m'})
# Known nonuniform resistor and resulting charge on both endplates.
resistor=step('resistor','resistance',{'coordinate':'x','bounds':['0','d'],'area':'A','conductivity':'1/(b*x)','voltage':'V'},domain='DYN',assumptions=['one_dimensional_steady_current'])
put('2024-11:4a','resistance',{},[ck('resistor','R','b*d^2/(2*A)','ohm'),ck('resistor','J','2*V/(b*d^2)','A/m^2')],domain='DYN',path=[resistor],units={'A':'m^2','b':'ohm'})
left=step('left','conductors',{'kind':'boundary','normal':['1','0','0'],'E_inside':['0','0','0'],'E_outside':['0','0','0'],'epsilon_inside':'epsilon_0','epsilon_outside':'epsilon_0'})
right=step('right','conductors',{'kind':'boundary','normal':['-1','0','0'],'E_inside':['0','0','0'],'E_outside':['2*V/d','0','0'],'epsilon_inside':'epsilon_0','epsilon_outside':'epsilon_0'})
put('2024-11:4b','resistance',{},[ck('resistor','E','2*V*x/d^2','V/m'),ck('resistor','rho','2*epsilon_0*V/d^2','C/m^3'),ck('left','sigma_free','0','C/m^2'),ck('right','sigma_free','-2*epsilon_0*V/d','C/m^2')],domain='DYN',path=[resistor,left,right],units={'A':'m^2','b':'ohm'})
put('2025-01:6c','resistance',{'coordinate':'x','bounds':['0','2*pi*a*N'],'area':'A','conductivity':'1/rho_res','solve_for':'A','target_values':{'R':E('R')}},[check('solved_A','2*pi*a*N*rho_res/R','m^2',numeric={'values':{'a':.2,'N':12,'rho_res':2.8e-8,'R':1.2},'value':.35e-6,'tolerance':.01e-6})],domain='DYN',assumptions=['one_dimensional_steady_current'],units={'A':'m^2','rho_res':'ohm*m','R':'ohm'})
# CMS field, self-inductance, energy and resistive power reuse the actual chain.
fieldcms=step('field','ampere',{'kind':'solenoid','turn_density':'N/L','I':'I'},domain='BA',assumptions=['ideal_long_solenoid','magnetostatic'])
induct=step('inductance','inductance_energy',{'flux':'B_field*pi*a^2','I':'I','N':'N'},domain='DYN',bindings={'B_field':ref('field','B')})
put('2022-11:3a','ampere',{},[ck('field','B','mu_0*N*I/L','T',numeric={'values':{'N':2180,'I':18200,'L':12.5},'value':3.99,'tolerance':.01})],domain='BA',path=[fieldcms])
put('2022-11:3b','inductance_energy',{},[ck('inductance','L','mu_0*N^2*pi*a^2/L','H',numeric={'values':{'N':2180,'a':3,'L':12.5},'value':13.5,'tolerance':.1}),ck('inductance','U','mu_0*N^2*pi*a^2*I^2/(2*L)','J',numeric={'values':{'N':2180,'a':3,'L':12.5,'I':18200},'value':2.24e9,'tolerance':.01e9})],domain='DYN',path=[fieldcms,induct],units={'B_field':'T'})
put('2022-11:3d','resistance',{'coordinate':'x','bounds':['0','2*pi*a*N'],'area':'A','conductivity':'1/rho_res','I':'I'},[check('P','2*pi*a*N*rho_res*I^2/A','W',numeric={'values':{'a':3,'N':2180,'rho_res':2.65e-8,'A':.03*.0266,'I':18200},'value':452e6,'tolerance':2e6})],domain='DYN',assumptions=['one_dimensional_steady_current'],units={'A':'m^2','rho_res':'ohm*m'})
# Sliding rod with the given positive loop orientation and stationary return path.
rod=step('solve','motional_emf',{'source':['0','s','0'],'parameter':'s','bounds':['0','L'],'v':['v','0','0'],'B':['0','0','B'],'time':'t','R':'R','time_bounds':['0','d/v']},domain='DYN',assumptions=['negligible_self_inductance','stationary_return_path'])
rodchecks=[check('I','-B*L*v/R','A',sign=-1),check('F_external',['B^2*L^2*v/R','0','0'],'N'),check('P_mechanical','B^2*L^2*v^2/R','W'),check('W','B^2*L^2*v*d/R','J',numeric={'values':{'B':1.2,'L':.2,'v':3.4,'R':.3,'d':1.2},'value':.78,'tolerance':.01})]
put('2021-06:6a 2021-06:6b 2021-06:6c 2021-06:6d','motional_emf',{},rodchecks,domain='DYN',path=[rod],units={'R':'ohm'},notes='Positiv kurve langs +y i den bevægelige stang. I<0; den fysiske omløbsretning svarer til figurens Lenz-retning.')
# No free current + axial symmetry + the far boundary determine H, not a hardcoded answer.
mag_assumptions=['infinite_axial_symmetry','no_free_current','H_infinity_zero']
mi=step('inside','magnetic_material',{'kind':'magnetization','coordinates':['s','phi','z'],'system':'cylindrical','M':['0','0','k*s^2'],'normal':['1','0','0'],'surface_substitutions':{'map':[[E('s'),E('R')]]}},domain='BA',assumptions=mag_assumptions)
mo=step('outside','magnetic_material',{'kind':'magnetization','coordinates':['s','phi','z'],'system':'cylindrical','M':['0','0','0']},domain='BA',assumptions=mag_assumptions)
put('2022-11:5b','magnetic_material',{},[ck('inside','H',['0','0','0'],'A/m'),ck('inside','B',['0','0','mu_0*k*s^2'],'T'),ck('outside','H',['0','0','0'],'A/m'),ck('outside','B',['0','0','0'],'T')],domain='BA',path=[mi,mo],units={'k':'A/m^3'})
# Wire -> rectangular-loop flux -> mutual inductance; all source limits explicit.
flux=step('flux','faraday',{'time':'t','flux_integrand':'mu_0*I*b/(2*pi*x)','bounds':[['x','a','a+h']]},domain='DYN')
mutual=step('mutual','inductance_energy',{'flux':'phi_loop','I':'I','N':1,'mutual':True},domain='DYN',bindings={'phi_loop':ref('flux','Phi')})
put('2023-02:5a','inductance_energy',{},[ck('mutual','M','mu_0*b*log((a+h)/a)/(2*pi)','H'),ck('mutual','M','mu_0*b*log(2)/(2*pi)','H',subs={'h':E('a')},sign=1)],domain='DYN',path=[flux,mutual])
# Mean-power inverse problem. C is a positive geometric coefficient from 5a.
# It is calculated first, then the unique positive amplitude is expressed in C.
inv=step('inverse','faraday',{'time':'t','flux':'C*I*cos(omega*t)','R':'R','average_bounds':['0','2*pi/omega'],'solve_for':'I','target_values':{'P_average':E('P_avg')}},domain='DYN',assumptions=['negligible_self_inductance'])
# Substitute the independently computed geometric coefficient only after solving.
amp=step('solve','algebra',{'outputs':{'I_amplitude':E('I_solved')},'output_units':{'I_amplitude':'A'}},domain='DYN',bindings={'I_solved':{'ref':'inverse.solved_I','substitute':{'C':ref('mutual','M')}}})
put('2023-02:5d','faraday',{},[ck('inverse','solved_I','sqrt(2*R*P_avg)/(C*omega)','A'),check('I_amplitude','sqrt(2*R*P_avg)/(mu_0*b*log((a+h)/a)*omega/(2*pi))','A',numeric={'values':{'R':.01,'P_avg':1.9e-5,'a':.05,'h':.1,'b':.14,'omega':314.1592653589793},'value':64,'tolerance':1})],domain='DYN',path=[flux,mutual,inv,amp],units={'C':'H','P_avg':'W','phi_loop':'Wb','R':'ohm'},notes='C er positiv fordi log((a+h)/a)>0. Symbolsk amplitudeløsning bruger C, hvis geometriske værdi er beregnet i tidligere led.')
# Two current sheets: the actual three spatial regions are sums of the two sheets.
bottom=step('bottom','ampere',{'kind':'sheet','K':['-I/b','0','0'],'normal':['0','1','0']},domain='BA',assumptions=['infinite_current_sheet','magnetostatic'])
top=step('top','ampere',{'kind':'sheet','K':['I/b','0','0'],'normal':['0','1','0']},domain='BA',assumptions=['infinite_current_sheet','magnetostatic'])
combine=step('fields','algebra',{'outputs':{'B_between':E('B_bottom_p+B_top_m'),'B_above':E('B_bottom_p+B_top_p'),'B_below':E('B_bottom_m+B_top_m')},'output_units':{n:'T' for n in ['B_between','B_above','B_below']}},domain='BA',bindings={'B_bottom_p':ref('bottom','B_positive'),'B_bottom_m':ref('bottom','B_negative'),'B_top_p':ref('top','B_positive'),'B_top_m':ref('top','B_negative')})
put('2023-11:2a','ampere',{},[ck('fields','B_between',['0','0','-mu_0*I/b'],'T'),ck('fields','B_above',['0','0','0'],'T'),ck('fields','B_below',['0','0','0'],'T')],domain='BA',path=[bottom,top,combine])
energy=step('solve','inductance_energy',{'B_squared':'B_between.dot(B_between)' if False else 'B_scalar^2','mu':'mu_0','jacobian':'b*L','bounds':[['x','0','h']],'I':'I'},domain='DYN',bindings={'B_scalar':ref('fields','B_between',2)})
put('2023-11:2b','inductance_energy',{},[check('U','mu_0*I^2*h*L/(2*b)','J',numeric={'values':{'I':9500,'h':.012,'L':4,'b':.3},'value':9.07,'tolerance':.01}),check('L','mu_0*h*L/b','H',numeric={'values':{'h':.012,'L':4,'b':.3},'value':201e-9,'tolerance':1e-9})],domain='DYN',path=[bottom,top,combine,energy])
# The 2024 loop has four oriented pieces; no net-force formula is fed to the solver.
wirepaths=[{'source':wrap(['b-s','d','0']),'parameter':E('s'),'bounds':wrap(['0','b'])},{'source':wrap(['0','d+s','0']),'parameter':E('s'),'bounds':wrap(['0','a'])},{'source':wrap(['s','d+a','0']),'parameter':E('s'),'bounds':wrap(['0','b'])},{'source':wrap(['b','d+a-s','0']),'parameter':E('s'),'bounds':wrap(['0','a'])}]
put('2024-02:3a 2024-02:3b','wire_force',{'paths':wirepaths,'I':'I2','B':['0','0','mu_0*I1/(2*pi*y)'],'field_coordinates':['x','y','z'],'work_coordinate':'d','work_bounds':['d','d/5'],'displacement_tangent':['0','1','0']},[check('F',['0','mu_0*I1*I2*a*b/(2*pi*d*(d+a))','0'],'N'),check('magnitude','mu_0*I1*I2*a*b/(2*pi*d*(d+a))','N',numeric={'values':{'a':.24,'b':.38,'d':.14,'I1':15,'I2':1.8},'value':9.3e-6,'tolerance':.1e-6}),check('W_external','mu_0*b*I1*I2*log((d/5+a)/((d+a)/5))/(2*pi)','J',numeric={'values':{'a':.24,'b':.38,'d':.14,'I1':15,'I2':1.8},'value':2.6e-6,'tolerance':.1e-6})],domain='BA',units={'I1':'A','I2':'A'})
# Expanding equilateral triangle, relations from exact geometry before induction.
geometry=step('geometry','algebra',{'outputs':{'height_residual':E('ell*sin(pi/3)-v*t'),'area':E('sqrt(3)*ell^2/4'),'resistance':E('3*r_line*ell')},'output_units':{'height_residual':'m','area':'m^2','resistance':'ohm'},'solve_for':'ell','target_values':{'height_residual':E('0')},'substitute_results':['area','resistance']},domain='DYN')
induction=step('induction','faraday',{'time':'t','area':'area_triangle','B_normal':'-B','R':'R_triangle','time_bounds':['0','T']},domain='DYN',assumptions=['uniform_normal_B','negligible_self_inductance'],bindings={'area_triangle':ref('geometry','at_solution_area'),'R_triangle':ref('geometry','at_solution_resistance')})
reaction=step('reaction','motional_emf',{'source':['v*t','s','0'],'parameter':'s','bounds':['-v*t/sqrt(3)','v*t/sqrt(3)'],'v':['v','0','0'],'B':['0','0','-B'],'time':'t','R':'R_triangle'},domain='DYN',assumptions=['negligible_self_inductance','stationary_return_path'],bindings={'R_triangle':ref('geometry','at_solution_resistance')})
for id in ['2024-02:5a','2024-02:5b','2024-02:5c','2024-02:5d']:
 put(id,'faraday',{},[ck('geometry','solved_ell','2*v*t/sqrt(3)','m'),ck('induction','EMF','2*B*v^2*t/sqrt(3)','V',sign=1),ck('induction','I','B*v/(3*r_line)','A',sign=1),ck('induction','W','B^2*v^3*T^2/(3*sqrt(3)*r_line)','J'),ck('reaction','F_external',['2*B^2*v^2*t/(3*sqrt(3)*r_line)','0','0'],'N')],domain='DYN',path=[geometry,induction,reaction],units={'r_line':'ohm/m','T':'s','ell':'m'},notes='Trekantens geometri: højde vt, side=2 vt/sqrt3, areal=sqrt3 side²/4. Relationer er eksplicitte geometriinput og kan kontrolleres før fysiktrinene.')
 fp=DEST/(id.replace(':','_p').replace('-','_')+'.json');j=json.loads(fp.read_text());j['symbols']['t']={'positive':True};fp.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
# Two coupled small loops: source dipole -> axial/equatorial field -> flux -> M -> induced I.
axis=step('axis','multipole',{'charges':[],'magnetic_current':'I','area':'pi*a^2','normal':['0','0','1'],'magnetic_field_point':['0','0','b']},domain='BA',assumptions=['far_field'])
equator=step('equator','multipole',{'charges':[],'magnetic_current':'I','area':'pi*a^2','normal':['0','0','1'],'magnetic_field_point':['b','0','0']},domain='BA',assumptions=['far_field'])
axisM=step('M_AB','inductance_energy',{'flux':'B_axis*pi*a^2','I':'I','N':1,'mutual':True},domain='DYN',bindings={'B_axis':ref('axis','B_magnetic_far',2)})
equatM=step('M_AC','inductance_energy',{'flux':'B_equator*pi*a^2','I':'I','N':1,'mutual':True},domain='DYN',bindings={'B_equator':ref('equator','B_magnetic_far',2)})
pB=step('current_B','faraday',{'time':'t','flux':'M_B*dI_dt*t','R':'R'},domain='DYN',assumptions=['negligible_self_inductance'],bindings={'M_B':ref('M_AB','M')})
pC=step('current_C','faraday',{'time':'t','flux':'M_C*dI_dt*t','R':'R'},domain='DYN',assumptions=['negligible_self_inductance'],bindings={'M_C':ref('M_AC','M')})
put('2024-11:5a 2024-11:5b 2024-11:5c','inductance_energy',{},[ck('M_AB','M','mu_0*pi*a^4/(2*b^3)','H',sign=1),ck('M_AC','M','-mu_0*pi*a^4/(4*b^3)','H',sign=-1),ck('current_B','I','-mu_0*pi*a^4*dI_dt/(2*b^3*R)','A',sign=-1),ck('current_C','I','mu_0*pi*a^4*dI_dt/(4*b^3*R)','A',sign=1)],domain='DYN',path=[axis,equator,axisM,equatM,pB,pC],units={'R':'ohm','dI_dt':'A/s'},notes='Fjernfeltsapproksimation a<<b fra opgaven. Positiv normal +z for begge modtagerspoler.')
# Toroid: parameterize the positive iron and air-gap lengths independently.
whole=step('whole','magnetic_material',{'kind':'magnetic_circuit','N':'N','I':'I','segments':[['L+d','mu_0*mu_r']]},domain='BA',assumptions=['negligible_leakage','uniform_cross_section'])
gapped=step('gapped','magnetic_material',{'kind':'magnetic_circuit','N':'N','I':'I','segments':[['L','mu_0*mu_r'],['d','mu_0']]},domain='BA',assumptions=['negligible_leakage','uniform_cross_section'])
air=step('air','magnetic_material',{'kind':'magnetic_circuit','N':'N','I':'I','segments':[['L+d','mu_0']]},domain='BA',assumptions=['negligible_leakage','uniform_cross_section'])
ratio=step('solve','algebra',{'outputs':{'H_gap_over_H_iron':E('H_gap/H_iron'),'B_without_iron':E('B_air'),'enhancement':E('B_gap/B_air')},'output_units':{'H_gap_over_H_iron':'1','B_without_iron':'T','enhancement':'1'}},domain='BA',bindings={'H_gap':ref('gapped','H_1'),'H_iron':ref('gapped','H_0'),'B_air':ref('air','B'),'B_gap':ref('gapped','B')})
for id in ['2024-11:6a','2024-11:6b','2024-11:6c']:
 put(id,'magnetic_material',{},[ck('whole','H_0','N*I/(L+d)','A/m'),ck('whole','B','mu_0*mu_r*N*I/(L+d)','T'),check('H_gap_over_H_iron','mu_r','1'),check('B_without_iron','mu_0*N*I/(L+d)','T',numeric={'values':{'L':1.4391326206513048,'d':.006,'N':620,'I':8.5},'value':.0046,'tolerance':.0001}),check('enhancement','(L+d)/(L/mu_r+d)','1',numeric={'values':{'L':1.4391326206513048,'d':.006,'mu_r':3000},'value':223,'tolerance':1})],domain='BA',path=[whole,gapped,air,ratio],units={'mu_r':'1'},notes='L=2pi R-d er jernlængden efter åbning af gabet; d er gablængden. R=23 cm, d=6 mm.')
# SI numbers are kept separate, with explicitly declared source units.
for fp in DEST.glob('*.json'):
 payload=json.loads(fp.read_text());given=dict(payload.get('given_values',{}))
 for c in payload['expected']:
  for name,value in c.get('numeric',{}).get('values',{}).items():
   if name in given and given[name]!=value:raise ValueError('Conflicting source constants: '+payload['id']+' '+name)
   given[name]=value
 payload['given_values']=given;payload['given_units']={name:payload['symbol_units'][name] for name in given}
 fp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print('Migration:',Counter(json.loads(p.read_text())['status'] for p in DEST.glob('*.json')))
