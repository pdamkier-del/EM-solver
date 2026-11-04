import sympy as sp
from ..core.problem import InputError
from ..core.solution import solution
from ..core.validation import EPS0, MU0, vector, finite_integral, positive


def circuit_outputs(p,result,emf,t):
    result.symbolic_result['EMF']=sp.simplify(emf)
    result.units['EMF']='V'
    result.direction='Positiv EMF og strøm følger den angivne orienterede integrationsvej/normal via højrehåndsreglen. Negativt fortegn betyder modsat omløb.'
    if 'R' in p.variables:
        p.assume('negligible_self_inductance');r=p.variables['R'];positive(r,'Resistans')
        current=sp.simplify(emf/r);power=sp.simplify(emf**2/r)
        result.add('Ohms lov: I = EMF/R',current)
        result.add('Joule-effekt: P = I²R',power)
        result.symbolic_result.update(I=current,P=power);result.units.update(I='A',P='W')
        result.check('Effektbalance P = EMF I',power-emf*current)
        if 'average_bounds' in p.variables:
            lo,hi=p.variables['average_bounds'];positive(hi-lo,'Midlingsinterval')
            average=finite_integral(power,(t,lo,hi))/(hi-lo)
            result.symbolic_result['P_average']=sp.simplify(average);result.units['P_average']='W'
            result.add('Midl effekten over det angivne tidsinterval',average)
        if 'time_bounds' in p.variables:
            t0,t1=p.variables['time_bounds']
            result.add('Varmeenergien før tidsintegration',sp.Integral(power,(t,t0,t1)))
            energy=finite_integral(power,(t,t0,t1));result.symbolic_result['W']=energy
            result.add('Udfør tidsintegrationen',energy);result.units['W']='J'
    return result


def faraday(p):
    t,=p.require('time');data=p.variables|p.functions
    result=solution(p,'Magnetisk flux og Faradays lov',
        'Først integreres magnetfeltets normalprojektion over den orienterede flade. Derefter differentieres hele fluxen, også eventuelle tidsafhængige grænser eller arealer. Minusfortegnet er Lenz’ lov.',
        [r'\Phi_B=\int_S\mathbf B\cdot d\mathbf a',r'\mathcal E=-N\frac{d\Phi_B}{dt}'])
    if 'flux' in data:
        flux=data['flux'];result.add('Den eksplicit givne flux pr. vinding',flux)
    elif 'B_normal' in data and 'area' in data:
        p.assume('uniform_normal_B');flux=sp.simplify(data['B_normal']*data['area'])
        result.add('Homogent normalt felt: flux = B_n A',flux)
    elif 'flux_integrand' in data:
        integrand,bounds=p.require('flux_integrand','bounds')
        result.add('Indsæt normalprojektion og arealelement i fladeintegralet',sp.Integral(integrand,*bounds))
        flux=finite_integral(integrand,*bounds);result.add('Evaluer fladeintegralet',flux)
    elif 'surface' in data:
        surf,parameters,bounds,b=p.require('surface','parameters','bounds','B_on_surface')
        if len(parameters)!=2 or len(bounds)!=2:raise InputError('En flade kræver to parametre og grænsesæt.')
        surf=vector(surf);normal_area=surf.diff(parameters[0]).cross(surf.diff(parameters[1]))
        integrand=sp.simplify(vector(b).dot(normal_area))
        limits=[(u,*bound) for u,bound in zip(parameters,bounds)]
        result.add('Orienteret arealvektor fra parameteriseringens krydsprodukt',normal_area)
        result.add('Fluxintegralet',sp.Integral(integrand,*limits))
        flux=finite_integral(integrand,*limits)
    else:raise InputError('Angiv flux, homogent B_normal og area, flux_integrand med bounds eller parameteriseret surface.')
    turns=data.get('N',1);positive(turns,'Vindingstal')
    emf=sp.simplify(-turns*sp.diff(flux,t))
    result.symbolic_result={'Phi':flux};result.units={'Phi':'Wb'}
    result.add('Differentier den samlede flux og indsæt minusfortegnet',emf)
    result.check('Faradays/Lenz’ fortegnsrelation',emf+turns*sp.diff(flux,t))
    result.warnings.append('Strøm fra EMF/R gælder kun under den eksplicitte antagelse om negligerbar selvinduktans. Retning kræver valgt fladenormal.')
    return circuit_outputs(p,result,emf,t)


def motional_emf(p):
    source,u,bounds,v,b,t=p.require('source','parameter','bounds','v','B','time')
    source=vector(source);v,b=vector(v),vector(b)
    if 'R' in p.variables and b.has(t):raise InputError('B(t) giver også transformerinduktion; brug den samlede flux i Faradays lov til kredsstrømmen.')
    result=solution(p,'Bevægelsesinduktion',
        'Ladninger i den bevægelige leder påvirkes af v kryds B. Kraft pr. ladning integreres langs den eksplicit orienterede leder.',
        [r'\mathcal E=\int(\mathbf v\times\mathbf B)\cdot d\mathbf l'])
    cross=v.cross(b);integrand=sp.simplify(cross.dot(source.diff(u)))
    result.add('Magnetisk kraft pr. ladning',cross)
    result.add('Projektér på ledningselementet og integrer',sp.Integral(integrand,(u,*bounds)))
    emf=finite_integral(integrand,(u,*bounds))
    result=circuit_outputs(p,result,emf,t)
    if 'R' in p.variables and 'stationary_return_path' in p.assumptions:
        current=result.symbolic_result['I']
        force_integrand=current*source.diff(u).cross(b)
        force=sp.Matrix([finite_integral(c,(u,*bounds)) for c in force_integrand])
        result.add('Magnetisk kraft på den bevægelige leder: I integral dl kryds B',force)
        mechanical_power=finite_integral(-force_integrand.dot(v),(u,*bounds))
        result.symbolic_result.update(F_magnetic=force,F_external=-force,P_mechanical=sp.simplify(mechanical_power))
        result.units.update(F_magnetic='N',F_external='N',P_mechanical='W')
        result.check('Mekanisk effekt = Joule-effekt',mechanical_power-result.symbolic_result['P'])
    return result


def circuit_power(p):
    current,r,t=p.require('I','R','time');positive(r,'Resistans')
    result=solution(p,'Ohms lov og Joules lov',
        'Den ohmske effekt er I²R. Den afsatte energi er tidsintegralet af effekten.',
        [r'P=I^2R',r'W=\int P(t)dt'])
    result.symbolic_result={'P':sp.simplify(current**2*r)};result.units={'P':'W'}
    result.add('Indsæt strømmen i Joules lov',current**2*r)
    if 'time_bounds' in p.variables:
        lo,hi=p.variables['time_bounds'];integral=sp.Integral(current**2*r,(t,lo,hi))
        result.add('Den afsatte energi før integration',integral)
        energy=finite_integral(current**2*r,(t,lo,hi))
        result.symbolic_result['W']=energy;result.units['W']='J';result.add('Evaluer tidsintegralet',energy)
    return result


def feedback(p):
    # A general linear electromechanical coupling, not a particular exam circuit.
    m,r,k,vsource,fdrive,t,v0=p.require('mass','R','coupling','voltage','drive_force','time','initial_velocity')
    p.assume('constant_coefficients','negligible_self_inductance','no_friction')
    for value,name in [(m,'Masse'),(r,'Resistans'),(k*k,'Koblingskonstantens kvadrat')]:positive(value,name)
    if any(sp.sympify(a).has(t) for a in [m,r,k,vsource,fdrive,v0]):raise InputError('Feedback-løsningen kræver konstante koefficienter og drivkræfter.')
    result=solution(p,'Kredsløbsligning og Newtons anden lov',
        'Bevægelses-EMF modvirker den påtrykte spænding. Strømmen bestemmer den mekaniske kraft, så kredsløb og bevægelse løses samlet.',
        [r'I=(V-kv)/R',r'm\dot v=F_{drive}+kI',r'\tau=mR/k^2'])
    velocity=sp.Function('v')(t);ode=sp.Eq(m*sp.diff(velocity,t),fdrive+k*(vsource-k*velocity)/r)
    result.add('Sammenkæd Ohms lov og Newtons anden lov',ode)
    solved=sp.dsolve(ode,ics={velocity.subs(t,0):v0})
    v=sp.simplify(solved.rhs);current=sp.simplify((vsource-k*v)/r);tau=m*r/k**2
    result.add('Løs den lineære differentialligning med begyndelsesbetingelsen',solved)
    result.symbolic_result={'v':v,'I':current,'tau':tau,'v_infinity':sp.simplify(vsource/k+fdrive*r/k**2),
                            'acceleration_initial':sp.simplify((fdrive+k*(vsource-k*v0)/r)/m),'P':sp.simplify(current**2*r)}
    result.check('Differentialligning',m*sp.diff(v,t)-fdrive-k*current)
    result.check('Begyndelseshastighed',v.subs(t,0)-v0)
    result.check('Effektbalance',vsource*current+fdrive*v-current**2*r-sp.diff(m*v*v/2,t))
    if 'time_bounds' in p.variables:
        lo,hi=p.variables['time_bounds']
        result.symbolic_result['battery_energy']=finite_integral(vsource*current,(t,lo,hi))
        result.symbolic_result['W']=finite_integral(current**2*r,(t,lo,hi))
        result.add('Batterienergi = integral af V I(t)',sp.Integral(vsource*current,(t,lo,hi)))
    result.units={'v':'m/s','I':'A','tau':'s','v_infinity':'m/s','acceleration_initial':'m/s^2','P':'W','battery_energy':'J','W':'J'}
    result.direction='Den valgte positive bevægelsesretning skal give EMF=k v og magnetisk kraft=k I; angiv denne orientering i problemet.'
    return result


def resistance(p):
    p.assume('one_dimensional_steady_current');x,bounds,area,conductivity=p.require('coordinate','bounds','area','conductivity')
    positive(area,'Tværsnitsareal')
    result=solution(p,'Kontinuitet og lokal Ohms lov',
        'I stationær endimensional strøm er strømmen konstant. Integralet af resistivitet divideret med areal giver den samlede modstand.',
        [r'\mathbf J=\sigma\mathbf E',r'R=\int dx/(\sigma(x)A(x))'])
    integral=sp.Integral(1/(conductivity*area),(x,*bounds));r=finite_integral(1/(conductivity*area),(x,*bounds))
    if r.is_nonpositive is True:raise InputError('Resistans skal være positiv.')
    result.add('Opsæt serieintegralet af differentialmodstande',integral);result.add('Integrer modstanden',r)
    result.symbolic_result={'R':r};result.units={'R':'ohm'}
    if 'voltage' in p.variables or 'I' in p.variables:
        i=sp.simplify(p.variables['voltage']/r) if 'voltage' in p.variables else p.variables['I']
        v=p.variables.get('voltage',i*r);j=sp.simplify(i/area);e=sp.simplify(j/conductivity)
        result.symbolic_result.update(I=i,J=j,E=e,rho=EPS0*sp.diff(e,x),P=sp.simplify(i*i*r),V=sp.simplify(v));result.units.update(I='A',J='A/m^2',E='V/m',rho='C/m^3',P='W',V='V')
        if sp.sympify(area).has(x):
            result.symbolic_result.pop('rho')
            result.warnings.append('Ladningstæthed returneres ikke for varierende tværsnit; tværgående feltkomponenter og geometri mangler.')
        result.add('Ohms lov bestemmer strøm, strømtæthed og felt',sp.Tuple(i,j,e))
        result.check('Spændingsintegral',finite_integral(e,(x,*bounds))-v)
    result.warnings.append('rho=epsilon_0 dE/dx forudsætter konstant tværsnit og kartesisk endimensionalt felt; ved variabelt areal er dette kun den aksiale del af divergensen.')
    return result


def inductance_energy(p):
    result=solution(p,'Fluxkobling og feltenergi',
        'Induktans bestemmes af fluxkobling pr. kildestrøm. Feltenergi er integralet af B²/(2μ) i et lineært materiale.',
        [r'L=N\Phi/I',r'M=N_2\Phi_{21}/I_1',r'U=\frac12LI^2',r'U=\int B^2/(2\mu)\,d\tau'])
    data=p.variables|p.functions
    if 'flux' in data:
        flux,i,n=p.require('flux','I','N')
        positive(n,'Vindingstal')
        if sp.sympify(i).equals(0):raise InputError('Induktans kræver ikke-nul strøm eller en symbolsk strømparameter.')
        value=sp.simplify(n*flux/i);key='M' if data.get('mutual',False) else 'L'
        if key=='L' and value.is_negative is True:raise InputError('Selvinduktans kan ikke være negativ; kontrollér strøm- og fluxorientering.')
        result.add('Divider fluxkoblingen med kildestrømmen',value);result.symbolic_result[key]=value;result.units[key]='H'
        if key=='L':result.symbolic_result['U']=sp.simplify(value*i*i/2);result.units['U']='J'
    if 'B_squared' in data:
        b2,mu,jac,bounds=p.require('B_squared','mu','jacobian','bounds');positive(mu,'Permeabilitet')
        integral=sp.Integral(b2*jac/(2*mu),*bounds);result.add('Feltenergiintegralet',integral)
        result.symbolic_result['U']=finite_integral(b2*jac/(2*mu),*bounds);result.units['U']='J'
        if 'I' in data:result.symbolic_result['L']=sp.simplify(2*result.symbolic_result['U']/data['I']**2);result.units['L']='H'
    if data.get('per_length',False):
        if 'B_squared' not in data:raise InputError('Energi pr. længde kræver et eksplicit tværsnitsintegral af B²/(2mu).')
        if 'U' in result.symbolic_result:result.units['U']='J/m'
        if 'L' in result.symbolic_result:result.units['L']='H/m'
        result.add('Tværsnitsintegralet er energi og induktans pr. aksial længde')
    if not result.symbolic_result:raise InputError('Angiv flux, I og N eller B_squared, mu, jacobian og bounds.')
    return result


def ampere_maxwell(p):
    p.assume('uniform_axial_E','circular_symmetry','negligible_edge_effects')
    e,t,s,a=p.require('E','time','coordinate','plate_radius');positive(a,'Pladeradius');positive(s,'Radialkoordinat')
    result=solution(p,'Ampère–Maxwells lov',
        'Det tidsafhængige elektriske felt giver en forskydningsstrøm. Den cirkulære symmetri gør det magnetiske felt konstant langs en cirkulær Ampère-kurve.',
        [r'J_d=\epsilon_0\partial_tE',r'\oint\mathbf B\cdot d\mathbf l=\mu_0\epsilon_0\frac{d\Phi_E}{dt}'])
    jd=EPS0*sp.diff(e,t);id_inside=sp.pi*s*s*jd
    current=sp.Piecewise((id_inside,s<=a),(sp.pi*a*a*jd,True))
    b=sp.simplify(sp.piecewise_fold(MU0*current/(2*sp.pi*s)))
    result.add('Differentier E med hensyn til tid',jd);result.add('Integrer J_d over den omsluttede cirkelflade',current)
    result.add('Brug B 2πs = μ₀ I_d',b)
    result.symbolic_result={'J_displacement':jd,'I_displacement':current,'B':b}
    # Particular induced axial E with correction zero at s=a; required boundary is explicit.
    if 'induced_correction_zero_at_edge' in p.assumptions:
        correction=MU0*EPS0*sp.diff(e,t,2)*(s*s-a*a)/4
        result.symbolic_result['E_correction_inside']=sp.simplify(correction)
        result.add('Faraday: dE_z/ds = dB_phi/dt, med E_korrektion(a)=0',correction)
        result.check('Faradays differentiallov for korrektionen',sp.diff(correction,s)-MU0*EPS0*s*sp.diff(e,t,2)/2)
    result.units={'J_displacement':'A/m^2','I_displacement':'A','B':'T','E_correction_inside':'V/m'}
    result.direction='Positiv dE_z/dt giver positiv phi-retning for B. Korrektionen er langs z.'
    return result


def rc_transient(p):
    kind,t,r=p.require('kind','time','R');positive(r,'Resistans')
    result=solution(p,'Lineær kredsløbsdifferentialligning',
        'Kirchhoffs spændingslov sammenholdes med kondensator- eller induktorligningen. Begyndelsesbetingelsen bestemmer integrationskonstanten.',
        [r'R\dot Q+Q/C=0',r'L\dot I+RI=V'])
    if kind=='RC':
        c,q0=p.require('C','Q0');positive(c,'Kapacitans');q=sp.Function('Q')(t)
        ode=sp.Eq(r*sp.diff(q,t)+q/c,0);solved=sp.dsolve(ode,ics={q.subs(t,0):q0})
        current=-sp.diff(solved.rhs,t);tau=r*c
        result.symbolic_result={'Q':solved.rhs,'I':sp.simplify(current),'I_charge':sp.simplify(-current),'tau':tau,'I_initial':q0/tau,'U_initial':q0*q0/(2*c)}
        result.check('RC-ligning',r*sp.diff(solved.rhs,t)+solved.rhs/c)
        result.direction='I er positiv i afladningsretningen: I=-dQ/dt. Formelsamlingens ladeorienterede strøm er I_charge=dQ/dt=-I.'
    elif kind=='RL':
        l,v,i0=p.require('L','voltage','I0');positive(l,'Induktans');i=sp.Function('I')(t)
        if any(sp.sympify(value).has(t) for value in (l,v,r,i0)):raise InputError('RL-standardforløbet kræver tidsuafhængige koefficienter og spænding.')
        ode=sp.Eq(l*sp.diff(i,t)+r*i,v);solved=sp.dsolve(ode,ics={i.subs(t,0):i0});tau=l/r
        result.symbolic_result={'I':sp.simplify(solved.rhs),'tau':tau,'I_initial':i0,'I_infinity':v/r}
        target=p.variables.get('target_values',{}).get('I')
        if target is not None:
            ratio=sp.simplify((v/r-target)/(v/r-i0)).subs(p.numerical_values)
            if ratio.is_nonpositive is True or (ratio-1).is_positive is True:raise InputError('Målstrømmen kan ikke nås ved en endelig ikke-negativ tid i dette RL-forløb.')
            if ratio.is_positive is not True or (1-ratio).is_nonnegative is not True:p.assume('reachable_RL_target')
            result.symbolic_result['maintain_voltage']=sp.simplify(r*target)
            result.units['maintain_voltage']='V'
        result.check('RL-ligning',l*sp.diff(solved.rhs,t)+r*solved.rhs-v)
    else:raise InputError('Vælg RC eller RL.')
    result.add('Den lineære differentialligning',ode);result.add('Løs med begyndelsesbetingelsen',solved)
    if 'fraction' in p.variables:
        f=sp.sympify(p.variables['fraction'])
        if kind!='RC' or (f>0) is not sp.true or (f<1) is not sp.true:raise InputError('Fraktionstid gælder RC og 0 < fraction < 1.')
        result.symbolic_result['decay_time']=sp.simplify(-tau*sp.log(f))
        result.add('Løs exp(-t/tau)=fraction',result.symbolic_result['decay_time'])
    result.units.update({'Q':'C','I':'A','I_charge':'A','tau':'s','I_initial':'A','I_infinity':'A','U_initial':'J','decay_time':'s'})
    return result
