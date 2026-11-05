import json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent
heads=[
 dict(number=1,domain='EV',title='Kuglesymmetrisk volumenladning',common='En kugle med radius a=7,0 cm har rho(r)=rho0*(r/a)**2 for 0<r<a og nul udenfor. rho0=22 nC/m^3. Fordelingen er kuglesymmetrisk og statisk. Der er vakuum overalt og ingen fladeladning. V(infinity)=0.',parts=[('a','Bestem kuglens totale ladning Q symbolsk og numerisk.'),('b','Bestem E(r) i begge regioner og angiv retningen.'),('c','Bestem potentialet i centrum og ved r=2a, både symbolsk og numerisk.')]),
 dict(number=2,domain='EV',title='Punktladning ved jordet plan',common='Et uendeligt jordet lederplan ligger ved z=0. En punktladning q=-5,0 nC holdes ved (0,0,d), d=11 cm. Området z>0 er vakuum og der er ingen andre kilder.',parts=[('a','Bestem kraften på punktladningen og den samlede inducerede ladning på planet, symbolsk og numerisk.'),('b','Ladningen flyttes kvasistatisk fra højden d til højden 2d. Bestem det arbejde en ydre kraft udfører. Forklar fortegnet.')]),
 dict(number=3,domain='BA',title='Ikke-uniform cylindrisk strøm',common='En uendeligt lang, massiv cylindrisk leder med radius a=6,0 cm fører samlet strøm I=5,5 A i positiv z-retning. Strømmen er stationær og mediet er ikke-magnetisk, mu=mu_0. Strømtætheden er J(s)=J0*(1-s**2/a**2) langs z, hvor s er afstanden fra aksen.',parts=[('a','Bestem J0 ud fra den samlede strøm, symbolsk og numerisk.'),('b','Bestem B(s) inde i og udenfor lederen og angiv retningen.'),('c','Beregn feltets størrelse ved s=3,0 cm og s=18,0 cm.')]),
 dict(number=4,domain='BA',title='Magnetisering og randbetingelser',common='En uendelig cylinder med radius a=2,5 cm har foreskrevet magnetisering M(s)=M0*(s/a)**2 langs positiv z, M0=600 A/m. Udenfor er der vakuum. Der er ingen frie strømme, og H går mod nul i det uendelige. Tilstanden er stationær.',parts=[('a','Bestem den bundne volumenstrømtæthed J_b(s) og overfladestrømtætheden K_b ved s=a. Angiv retningerne.'),('b','Bestem H og B i begge regioner ud fra de frie strømme og randbetingelserne.')]),
 dict(number=5,domain='DYN',title='Varierende flux og induktiv kreds',common='En spole med N=3 vindinger har et homogent påtrykt normalfelt B(t)=B0*(1+t/T) og areal A(t)=A0*(1+t/(2*T)) for t>=0. B0=0,08 T, A0=20 cm^2, T=0,70 s. Positiv normal er +z og positiv strøm er mod uret set fra +z. Kredsen har R=7,0 ohm og L=140 mH med I(0)=0. Selvinduktansen må ikke negligeres. Koefficienterne er konstante.',parts=[('a','Bestem den ydre flux pr. vinding og den ydre inducerede emf som funktioner af t. Angiv emf-fortegnet.'),('b','Brug den fundne emf til at bestemme I(t), I(T) og den samlede Joule-varme fra t=0 til t=T. Forklar strømretningen.')]),
 dict(number=6,domain='DYN',title='Glidende stang med mekanisk tilbagekobling',common='En ledende stang med længde ell=18 cm og masse m=35 g glider uden friktion langs to vandrette skinner. Stangen er langs y, bevægelsen er langs +x og et homogent B=0,60 T peger langs +z. Hele kredsens modstand er R=0,45 ohm, selvinduktansen negligeres, og ingen spændingskilde er tilsluttet. Fra t=0 påvirkes stangen af en konstant kraft F0=0,012 N langs +x; v(0)=0. Positiv strøm langs stangen er +y. T=0,80 s.',parts=[('a','Bestem v(t), tidskonstanten og terminalhastigheden. Angiv også terminalhastigheden numerisk.'),('b','Bestem I(t) med fortegn og den samlede Joule-varme afsat fra t=0 til t=T.')])]
base_units=dict(r='m',a='m',rho0='C/m^3')
def req(model,variables,wanted,units,positive=(),numbers=None,extra=(),operations=None):
 p=dict(id='a',model=model,wanted=wanted,orientation_confirmed=True)
 if operations:p['operations']=operations
 return dict(schema_version='assisted-1.0',confirmed=True,variables=variables,units=units,positive=list(positive),numbers=numbers or {},extra_assumptions=list(extra),subproblems=[p])
plans={}
sphere=dict(coordinate='r',regions=[dict(lower='0',upper='a',density='rho0*(r/a)**2',permittivity='epsilon_0')])
for key,wanted in [('1a',['Q']),('1b',['E'])]:plans[key]=dict(route='manual',request=req('sphere_regions',sphere,wanted,base_units,['r','a'],dict(a='7 cm',rho0='22 nC/m^3')))
plans['1c']=dict(route='manual',request=req('sphere_regions',sphere,['V_center','V_far'],base_units,['r','a'],dict(a='7 cm',rho0='22 nC/m^3'),['V_infinity_zero'],[dict(kind='limit',id='V_center',result='V',variable='r',value='0'),dict(kind='evaluate',id='V_far',result='V',variable='r',value='2*a')]))
plane=dict(charges=[['q',['0','0','d']]],normal=['0','0','1'],offset='0')
plans['2a']=dict(route='manual',request=req('image_plane',plane,['F','Q_induced'],dict(q='C',d='m'),['d'],dict(q='-5 nC',d='11 cm')))
plans['2b']=dict(route='manual_unsupported',request=req('image_plane',plane,['W'],dict(q='C',d='m'),['d'],dict(q='-5 nC',d='11 cm')),limitation='Billedkortet tilbyder ikke fysisk arbejde/energi ved flytning af den virkelige ladning. Ingen halvfaktor eller beregnet kraftkomponent indtastes som et forventet svar.')
for k in ('3a','3b','3c'):plans[k]=dict(route='guided_shared',head=3)
mvars=dict(M=['0','0','M0*(s/a)**2'],coordinates=['s','phi','z'],system='cylindrical',normal=['1','0','0'],surface_coordinate='s',surface_value='a')
for key,wanted in [('4a',['J_bound','K_bound']),('4b',['H','B'])]:plans[key]=dict(route='manual' if key=='4a' else 'manual_unsupported',request=req('magnetization_currents',mvars,wanted,dict(M0='A/m',s='m',a='m',phi='1',z='m'),['s','a'],dict(M0='600 A/m',a='2.5 cm')))
plans['4b']['limitation']='Det generelle M-kort kræver et oplyst H for at returnere B. H=0, som skal udledes fra randproblemet, bliver ikke skrevet ind som et facitsvar.'
fluxunits=dict(t='s',N='1',B0='T',A0='m^2',T='s')
fluxnum=dict(N='3',B0='0.08 T',A0='20 cm^2',T='0.70 s')
plans['5a']=dict(route='manual',request=req('faraday_uniform',dict(time='t',B_normal='B0*(1+t/T)',area='A0*(1+t/(2*T))',N='N'),['Phi','EMF'],fluxunits,['N','B0','A0','T'],fluxnum,['positive_area_on_interval']))
plans['5b']=dict(route='manual_dependency',dependency=dict(part='5a',result='EMF',target='voltage'),request=req('RL_driven',dict(time='t',R='R',L='L',voltage='__FROM_APP_5a_EMF__',I0='0'),['I','heat'],fluxunits|dict(R='ohm',L='H',I='A'),['R','L','N','B0','A0','T'],fluxnum|dict(R='7 ohm',L='140 mH',t='0.70 s'),operations=[dict(kind='transform',id='heat_rate',result='I',variable='t',value='R*I**2',unit='W'),dict(kind='integrate',id='heat',result='heat_rate',variable='t',lower='0',upper='T')]),help='Overfør kun appens beregnede EMF fra 5a. Angiv Joules lov P=R I² og tidsintegralet; ingen strøm- eller varmeværdi indtastes.')
fb=dict(mass='m',R='R',coupling='B*ell',voltage='0',drive_force='F0',time='t',initial_velocity='0')
fbu=dict(m='kg',R='ohm',B='T',ell='m',F0='N',t='s',T='s');fbn=dict(m='35 g',R='0.45 ohm',B='0.60 T',ell='18 cm',F0='0.012 N',T='0.80 s')
plans['6a']=dict(route='manual',request=req('feedback',fb,['v','tau','v_infinity'],fbu,['m','R','B','ell'],fbn),help='Vælg kobling k=B*ell fra geometri og orientering; positiv I er +y og I=-k*v/R uden spændingskilde.')
plans['6b']=dict(route='manual',request=req('feedback',fb|dict(time_bounds=['0','T']),['I','W'],fbu,['m','R','B','ell','T'],fbn),help=plans['6a']['help'])
questions=[];lines=['# EM1 mock-eksamen – nyt konstrueret sæt','', '6 hovedopgaver, 14 delopgaver. SI internt. Ingen facit bruges som solverinput.','']
for head in heads:
 lines+=['## Opgave '+str(head['number'])+' – '+head['title'],'',head['common'],'']
 full=head['common']+'\n'+'\n'.join(letter+') '+text for letter,text in head['parts'])
 for letter,text in head['parts']:
  id=str(head['number'])+letter
  questions.append(dict(id=id,head=head['number'],domain=head['domain'],common=head['common'],question=text,text=head['common']+'\n'+letter+') '+text,full_head=full,plan=plans[id]));lines.append(letter+') '+text)
 lines.append('')
(OUT/'exam.md').write_text('\n'.join(lines)+'\n');p=OUT/'questions_and_inputs.json';p.write_text(json.dumps(questions,ensure_ascii=False,indent=2)+'\n')
(OUT/'seal.json').write_text(json.dumps(dict(source_commit='59b4decefd119b12c44230f8b18b0b6db6889a8e',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),heads=6,subproblems=14,protocol='Self-authored mock, not an externally independent blind examination. Question text and manual plans sealed before calculations. No model changes during test. All subproblems count. References generated only after GUI execution. Standard physical laws and transferring actual earlier app results are allowed assistance; expected reference values are not.'),indent=2)+'\n')
print('Sealed',len(questions),'subproblems',hashlib.sha256(p.read_bytes()).hexdigest())
