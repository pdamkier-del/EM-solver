"""Independent analytic references, evaluated only AFTER the GUI execution.

No imports of production physics, units, registries or historical answers.
SymPy is used solely to read expressions emitted by the app for comparison.
"""
import json,math,hashlib
from pathlib import Path
import sympy as sp
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/generalization/evaluation20'
assert (OUT/'execution.json').is_file(),'Run every app calculation before deriving references.'
run=json.loads((OUT/'execution.json').read_text());questions=json.loads((OUT/'questions_and_inputs.json').read_text())
eps=8.8541878128e-12;mu=1.25663706212e-6;k=1/(4*math.pi*eps)
refs={}
def add(id,values,inputs,law):refs[id]=dict(values=values,inputs_SI=inputs,independent_derivation=law)
q=4e-9;a=.09;d=.03
add('EV1',dict(F=[-k*q*q/(4*a*a),0,0],E=[k*q*(1-1/9)/(a*a),0,0]),dict(q=q,a=a,d=d),'Reflect q across x=d to -q at x=d-a. Exclude real self-field for force; field distances at d+2a are a and 3a.')
q=4e-9;a=.03;d=.11
add('EV2',dict(F=[0,0,-k*q*q*a*d/(d*d-a*a)**2],Q_induced=-q*a/d),dict(q=q,a=a,d=d),'Sphere image q_im=-qa/d at a²/d; separation d-a²/d. Coulomb force q*q_im/separation²; grounded net image charge equals conductor charge.')
q=-2e-9;a=.05;d=.16;qs=1e-9;qc=qs+q*a/d
add('EV3',dict(F=[0,0,-k*q*q*a*d/(d*d-a*a)**2+k*q*qc/d**2],V_sphere=k*qc/a),dict(q=q,a=a,d=d,Qs=qs),'Off-center image -qa/d cancels boundary variation. Central image Qs+qa/d fixes net charge; its boundary potential is k*qc/a.')
q=2e-9;a=.03;b=.04;distance=math.hypot(a,b)
add('EV4',dict(E=[3*k*q*a/distance**3,-k*q*b/distance**3,0],V=-k*q/distance),dict(q=q,a=a,b=b),'Vector sum k*q*(a,b,0)/D³ + k*(-2q)*(-a,b,0)/D³; scalar potentials add.')
a=.1;r=a/3;rho=15e-9;q=2e-9
field=rho/eps*(r/3-r*r/(4*a));potential=rho/eps*(a*a/6-r*r/6+r**3/(12*a))
add('EV5',dict(E=field,V=potential,Q=math.pi*rho*a**3/3,test_force=q*field,test_energy=q*potential),dict(a=a,r=r,rho0=rho,q=q),'Qenc=4pi*rho0*(r³/3-r⁴/(4a)). E=Qenc/(4pi eps r²); integrate inward from V(a)=rho0*a²/(12eps). Test force qE and test potential energy qV.')
k0=3000;rad=.04;z=.06
add('EV6',dict(E=[-2*k0*rad*z,0,-k0*rad**2],rho=-4*eps*k0*z),dict(k=k0,s=rad,phi=0,z=z),'Cylindrical gradient gives Es=-2ksz and Ez=-ks²; Laplacian (1/s)d(s*dV/ds)/ds+d²V/dz²=4kz, rho=-eps*laplacian.')
k0=2400;b=.02
add('BA1',dict(J_bound=[k0,0,0],K_bound=[0,k0*b,0]),dict(k=k0,b=b,x=0,y=b,z=0),'curl(0,0,ky)=(k,0,0); M×ex=(0,ky,0), evaluated at y=b. No H or B inferred.')
m=350;a=.06
add('BA2',dict(B_inside=[2*mu*m/3,4*mu*m/3,0],B=[-mu*m/81,-2*mu*m/81,0],J_bound=[0,0,0]),dict(m=m,a=a),'Demagnetizing H=-M/3, Binside=2mu*M/3. Moment=4pi*a³*M/3; at z=3a and M perpendicular to z, B=-mu*M/81.')
j=700;a=.008;s=.016;current=1.5*math.pi*j*a*a
add('BA3',dict(B=mu*current/(2*math.pi*s),I=current),dict(J0=j,a=a,s=s),'I=integral_0^a 2pi*s*J0*(1+s²/a²)ds=3pi*J0*a²/2. Outside B=mu*I/(2pi*s).')
i=3;a=.04;b=.03
add('BA4',dict(B=[0,mu*i*a/(math.pi*(a*a+b*b)),0]),dict(I=i,a=a,b=b),'At (0,b), x components of opposite z currents cancel; y components add to mu*I*a/[pi(a²+b²)].')
i=2.4;a=.07
add('BA5',dict(B=[0,0,mu*i/(8*a)]),dict(I=i,a=a),'A circular arc subtending pi/2 produces mu*I*angle/(4pi*a), oriented +z by dl×r. Return wire excluded in question.')
r=8;l=.06;v=-4;i0=.2;tau=l/r
zero=tau*math.log((i0-v/r)/(-v/r))
add('DYN1',dict(initial_slope=(v-r*i0)/l,zero_time=zero),dict(R=r,L=l,voltage=v,I0=i0),'Solve L Iprime+R I=V: I=V/R+(I0-V/R)exp(-t/tau). Initial slope from KVL; zero from exponential ratio, positive and finite.')
r=6;l=.12;v=9;t=.03;tau=l/r
add('DYN2',dict(extremum_times=tau,I=v/l*t*math.exp(-t/tau)),dict(R=r,L=l,v0=v,t=t),'Integrating factor exp(t/tau) gives I=(v0/L)t exp(-t/tau). Derivative vanishes at tau; second derivative there is -v0*R*exp(-1)/L²<0, a local maximum.')
r=20;c=.002;beta=5;t=.08;tau=r*c
add('DYN3',dict(Q=beta*c*(t-tau*(1-math.exp(-t/tau))),I=beta*c*(1-math.exp(-t/tau)),I_initial=0),dict(R=r,C=c,beta=beta,t=t),'Integrating factor for Qprime+Q/(RC)=beta*t/R gives Q=beta*C*(t-tau+tau exp(-t/tau)); differentiate for positive charging current.')
n=5;b=.12;area=.0008;tt=.6;r=3;t=.3;emf=-n*b*area/tt
add('DYN4',dict(EMF=emf,I=emf/r),dict(N=n,B0=b,A0=area,T=tt,R=r,t=t),'B(t)*A(t)=B0*A0*(1+t/T); both time dependences are included before differentiation. emf=-N*B0*A0/T, I=emf/R, negative: clockwise viewed from +z.')
alpha=.4;r=4;l=.2;t=.1;tau=l/r;i=alpha/r*(1-math.exp(-t/tau))
heat=alpha**2/r*(t-2*tau*(1-math.exp(-t/tau))+tau/2*(1-math.exp(-2*t/tau)))
add('DYN5',dict(EMF=alpha,coil_current=i,joule_power=r*i*i,heat=heat),dict(alpha=alpha,R=r,L=l,T=t,t=t),'emf=alpha. Current from integrating-factor RL solution. Joule power=R*I²; integrate (alpha²/R)(1-2e^-t/tau+e^-2t/tau) from 0 to T.')
a=.15;w=12;b=.2
add('DYN6',dict(EMF=b*w*a*a/2),dict(a=a,omega=w,B0=b),'v=(0,omega*u,0), B=(0,0,B0), v×B=(omega*u*B0,0,0); integral from 0 to a is positive B0*omega*a²/2, tip positive.')

refs['EV7']=dict(values={},inputs_SI={},independent_derivation='Well-posed exterior Laplace/Poisson boundary problem with zero potential on six finite faces, decay at infinity and a point-charge singularity. The planar-image solution does not satisfy all cube faces; a separately validated numerical boundary solver is required. No value invented.')
refs['BA6']=dict(values={},inputs_SI={},independent_derivation='Ampere fixes average H=NI/ell, but without a material relation and hysteresis state B is not unique. At the same H, distinct remanent states can give different B.')
refs['DYN7']=dict(values={},inputs_SI=dict(R=2,L=1,C=.01,Q0=1,I0=0),independent_derivation='KVL gives Qsecond+2Qprime+100Q=0. Roots -1 +/- i*sqrt(99). Q(t)=exp(-t)*(cos(sqrt(99)*t)+sin(sqrt(99)*t)/sqrt(99)) C, Icharge=dQ/dt=-100*exp(-t)*sin(sqrt(99)*t)/sqrt(99) A. Q(0)=1, I(0)=0; no matching model card was forced onto it.')

# Functional references validate entire time-dependent answers, not one number.
def functional(id,t,p):
 if id=='DYN1':return {'I':p['voltage']/p['R']+(p['I0']-p['voltage']/p['R'])*math.exp(-p['R']*t/p['L'])}
 if id=='DYN2':return {'I':p['v0']/p['L']*t*math.exp(-p['R']*t/p['L'])}
 if id=='DYN3':
  tau=p['R']*p['C'];return dict(Q=p['beta']*p['C']*(t-tau*(1-math.exp(-t/tau))),I=p['beta']*p['C']*(1-math.exp(-t/tau)))
 return {}

def numeric(expression,p):
 sy={name:sp.Symbol(name,real=True) for name in p};sy.update(epsilon_0=sp.Float(eps),mu_0=sp.Float(mu))
 value=sp.sympify(expression,locals=sy)
 value=value.subs({sym:p[sym.name] for sym in value.free_symbols if sym.name in p})
 if isinstance(value,sp.MatrixBase):return [float(x.evalf()) for x in value]
 return float(value.evalf())

def close(a,b):
 if isinstance(b,list):return isinstance(a,list) and len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
 return math.isfinite(a) and abs(a-b)<=max(1e-18,abs(b)*2e-7)

rows=[]
for case in run['cases']:
 id=case['id'];reference=refs.get(id);reply=case.get('assisted_response');raw=case.get('automatic_response') or {};checks=[]
 automatic_grade='abstained';automatic_checks=[]
 if raw.get('solution') and reference:
  raw_results=raw['solution']['results']
  for key,expected in reference['values'].items():
   try:
    actual=numeric(raw_results[key]['expression'],reference['inputs_SI'])
    automatic_checks.append(dict(result=key,passed=close(actual,expected),actual=actual,expected=expected))
   except Exception as exc:automatic_checks.append(dict(result=key,passed=False,error=str(exc)))
  if not all(c['passed'] for c in automatic_checks):automatic_grade='wrong'
  elif not all(key in raw['solution'].get('numerical',{}) for key in reference['values']):automatic_grade='partial'
  else:automatic_grade='fully_correct'
 if reference and reply and reply.get('subproblems') and reply['subproblems'][0].get('solution'):
  sol=reply['subproblems'][0]['solution'];results=sol['results']
  for key,expected in reference['values'].items():
   try:
    actual=numeric(results[key]['expression'],reference['inputs_SI']);passed=close(actual,expected)
    checks.append(dict(result=key,expected=expected,actual=actual,passed=passed))
   except Exception as exc:checks.append(dict(result=key,passed=False,error=str(exc)))
  for time in (0,.013,.047,.11):
   for key,expected in functional(id,time,reference['inputs_SI']).items():
    actual=numeric(results[key]['expression'],reference['inputs_SI']|{'t':time})
    checks.append(dict(result=key,time=time,expected=expected,actual=actual,passed=close(actual,expected)))
  failures=[c for c in checks if not c['passed']]
  grade='fully_correct' if not failures and not case.get('math_display_errors') else 'wrong' if failures else 'partial'
 else:grade='abstained'
 rows.append(dict(id=id,domain=case['domain'],grade=grade,mode='assisted' if grade!='abstained' else 'no_solution',model=case['model'],automatic_grade=automatic_grade,automatic_checks=automatic_checks,assistance_action_count=case['assistance_action_count'],extra_result_unit_rows=case.get('extra_result_unit_rows',[]),checks=checks,reason=case.get('no_matching_card_reason','')))
counts={g:sum(r['grade']==g for r in rows) for g in ('fully_correct','partial','wrong','abstained')}
assert sum(counts.values())==20
summary=dict(total=20,counts=counts,fully_correct_percent=counts['fully_correct']/20*100,automatic_fully_correct=sum(r['automatic_grade']=='fully_correct' for r in rows),automatic_partial=sum(r['automatic_grade']=='partial' for r in rows),automatic_wrong=sum(r['automatic_grade']=='wrong' for r in rows),automatic_abstained=sum(r['automatic_grade']=='abstained' for r in rows),assisted_fully_correct=counts['fully_correct'],references_generated_after_execution=True,external_blind_test=False,cases=rows)
(OUT/'references.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n')
(OUT/'grading.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
lines=['# Evaluering af 20 nye opgaver','',f"Fuldt korrekte: {counts['fully_correct']}/20 ({summary['fully_correct_percent']}%). Delvise: {counts['partial']}; forkerte: {counts['wrong']}; afstået: {counts['abstained']}.",'','Automatisk fuldt: 0/20. Råtekstvejen gav én delvist korrekt symbolsk løsning (EV6), men indsatte ikke hele det angivne feltpunkt numerisk; de øvrige 19 var afståelser. Ingen automatiske fejlsvar. Assisteret: '+str(counts['fully_correct'])+' fuldt korrekte. Disse tal gælder de konstruerede opgaver, ikke hele pensum eller et uafhængigt eksamenssæt.','', 'Ingen fysisk model blev ændret under evalueringen. Referencesvar blev først genereret og anvendt efter alle appberegninger. De er afledt med separate analytiske formler uden engine-imports; samme forfatter valgte opgaverne, så evalueringen er ikke eksternt uafhængig.','', '| Opgave | Model | Resultat | Assisterede formularhandlinger |','|---|---|---|---|']
for row in rows:lines.append(f"| {row['id']} | {row['model'] or 'intet passende kort'} | {row['grade']} | {row['assistance_action_count']} |")
lines+=['','## Brugerhjælp og begrænsninger','','Alle løste opgaver krævede bekræftet model, givne felter, symbolenheder og betingelser. Handlingstal er semantiske formularhandlinger, ikke observerede menneskelige klik; se protocol.md. Den nye taloverførsel blev kontrolleret i regressionstesten, men denne evaluering anvendte eksplicit fuld indtastning for at logge alle data.','', 'EV5 krævede desuden enhedsangivelse for de beregnede E- og V-referencer, fordi formularens symbolscanner medtager dem. Testværktøjet blev udvidet til at indtaste disse kendte enheder, efter evalueringen standsede på formulartrinnet; hverken fysikmotor, spørgsmål eller givne tal blev ændret, og de første fire registrerede svar blev ikke genberegnet. Dette er ekstra brugerhjælp og en kendt formularbegrænsning.','', 'Manglende emner: generelle leder-randværdiproblemer (kuben), ikke-lineære/hysteretiske materialer uden tilstandsdata og serielle RLC-systemer med to begyndelsesbetingelser. Ingen numerisk løsning eller materialetilstand blev gættet.','', 'Næste prioritering: mindre formulararbejde og sikker overførsel af beregnede resultatreferencer; bredere deterministisk forståelse af tekst og figuroplysninger; generaliseret lineær kredsløbs-ODE af anden orden; generelle randværdiproblemer kræver egen valideret numerisk metode.','', 'Verificeret på Linux med faktisk PySide6 MainWindow, QProcess, beregningsworker og tre visningsfaner. Native Windows er ikke testet.']
(OUT/'report.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='cases'},indent=2))
for row in rows:
 if row['grade']=='wrong':print(row['id'],[c for c in row['checks'] if not c['passed']])
