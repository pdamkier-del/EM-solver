"""Coulomb, geometric integration, Gauss, conductors and potentials in SI."""
import sympy as sp
from ..core.problem import InputError
from ..core.solution import solution
from ..core.validation import EPS0, vector, finite_integral, positive, calculus


def point_charges(p):
    charges,=p.require('charges')
    force_index=p.variables.get('force_on_index')
    if force_index is not None:
        if not isinstance(force_index,int) or not 0<=force_index<len(charges):raise InputError('Ugyldigt ladningsindeks til kraftberegning.')
        point=charges[force_index][1]
        if 'point' in p.variables and vector(p.variables['point'])!=vector(point):raise InputError('Feltpunkt og valgt ladningsposition stemmer ikke overens.')
    elif 'point' in p.variables:point=p.variables['point']
    elif set(p.wanted)&{'E','V','F','E_far','V_far'} or not p.wanted:point,=p.require('point')
    else:point=None
    if point is not None:point=vector(point)
    if not charges:
        raise InputError('Angiv mindst én ladning.')
    geometry_values={}
    if 'distinct_point_sources' in p.assumptions:
        from ..core.units import si
        for symbol,value in p.numerical_values.items():
            geometry_values[symbol]=sp.Float(str(si(value,p.numerical_units[symbol]).magnitude)) if isinstance(value,str) else sp.sympify(value)
        locations=[vector(position).subs(geometry_values) for _,position in charges]
        samples=locations+([point.subs(geometry_values)] if point is not None else [])
        if any(component.is_real is False or component.is_finite is False for location in samples for component in location):raise InputError('De givne værdier giver ikke reelle, endelige koordinater.')
        for i,location in enumerate(locations):
            if any((location-other).dot(location-other).equals(0) is True for other in locations[:i]):raise InputError('De givne værdier får kildeladninger til at falde sammen.')
        if point is not None:
            sample=point.subs(geometry_values)
            if any((sample-location).dot(sample-location).equals(0) is True for i,location in enumerate(locations) if i!=force_index):raise InputError('Det givne feltpunkt falder sammen med en kilde; feltet er singulært.')

    result=solution(p,'Coulomb og superposition',
        'I vakuum summeres bidragene fra hver punktladning vektorielt. Selvfelt medtages ikke i kraften på en kilde.',
        [r'\mathbf E=\sum_i\frac{q_i(\mathbf r-\mathbf r_i)}{4\pi\epsilon_0|\mathbf r-\mathbf r_i|^3}',
         r'V=\sum_i\frac{q_i}{4\pi\epsilon_0|\mathbf r-\mathbf r_i|}',
         r'U=\sum_{i<j}\frac{q_iq_j}{4\pi\epsilon_0r_{ij}}'], 'Kartesiske komponenter; fortegn følger ladninger og forskydningsvektorer.')
    if point is None:
        result.method='Coulombs parenergi og summer over kilder'
        result.reasoning='Kildernes indbyrdes afstande bestemmer parenergien. Hvert uordnet par medtages præcis én gang; intet observationspunkt er nødvendigt.'
        result.equations=[r'U=\sum_{i<j}\frac{q_iq_j}{4\pi\epsilon_0r_{ij}}',r'Q=\sum_i q_i',r'\mathbf p=\sum_iq_i\mathbf r_i']
    e=sp.zeros(3,1); potential=sp.S.Zero; energy=sp.S.Zero; dipole=sp.zeros(3,1)
    for index,(q,pos) in enumerate(charges):
        if point is not None:
            d=point-vector(pos);norm=sp.sqrt(d.dot(d))
            self_field=norm.equals(0) and index==force_index
            if norm.equals(0) and not self_field:raise InputError('Feltpunktet falder sammen med en punktladning (singularitet).')
            term=sp.zeros(3,1) if self_field else q*d/(4*sp.pi*EPS0*norm**3)
            result.add(f'Forskydning fra ladning {index+1} og afstand',sp.Tuple(*d,norm))
            contribution=result.add(f'Coulomb-bidrag {index+1}',term,reasoning='Kildens eget singulære felt udelades ved kraftberegning på denne kilde.' if self_field else 'Forskydningen er fra kildeladningen til feltpunktet; ladningens fortegn bestemmer feltets retning.',law='Coulombs lov',validity=['Feltpunktet er adskilt fra den medtagne kilde.'] if not self_field else ['Kun de øvrige kilder bidrager til kraften.'])
            if 'distinct_point_sources' in p.assumptions and not self_field:
                observation=sp.Matrix([sp.Dummy('observation_'+axis,real=True) for axis in 'xyz'])
                delta=observation-vector(pos);length=sp.sqrt(delta.dot(delta))
                potential_kernel=q/(4*sp.pi*EPS0*length)
                field_kernel=q*delta/(4*sp.pi*EPS0*length**3)
                gradient=sp.Matrix([sp.diff(potential_kernel,axis) for axis in observation])
                divergence=sum(sp.diff(field_kernel[i],observation[i]) for i in range(3))
                result.check('Lokalt: E = -grad(V) for punktkilden',field_kernel+gradient,'Gælder væk fra kildens position; kildens parametre holdes faste.',step=contribution)
                result.check('Lokalt: div(E) = 0 væk fra punktkilden',divergence,'Delta-ladningen ved selve kilden er ikke en glat volumenladning.',step=contribution)
            e+=term
            if not self_field:potential+=q/(4*sp.pi*EPS0*norm)
        dipole+=q*vector(pos)
        for q2,pos2 in charges[:index]:
            distance=sp.sqrt((vector(pos)-vector(pos2)).dot(vector(pos)-vector(pos2)))
            if distance.equals(0): raise InputError('To kildeladninger har samme position; parenergien divergerer.')
            term_u=q*q2/(4*sp.pi*EPS0*distance)
            result.add('Parenergi (hvert par tælles én gang)',term_u)
            energy+=term_u
    result.symbolic_result={'E':sp.simplify(e),'V':sp.simplify(potential),'U':sp.simplify(energy),
                            'dipole':sp.simplify(dipole),'Q':sum(q for q,_ in charges)}
    if point is None:
        result.symbolic_result.pop('E',None);result.symbolic_result.pop('V',None)
    if 'test_charge' in p.variables:
        result.symbolic_result['F']=sp.simplify(p.variables['test_charge']*e)
    if force_index is not None:
        result.symbolic_result['F']=sp.simplify(charges[force_index][0]*e)
        result.add('Kraft på den valgte ladning uden dens selvfelt',result.symbolic_result['F'],reasoning='Den elektriske kraft er ladningen gange feltet fra de øvrige kilder; det singulære selvfelt medtages ikke.',law='Elektrisk Lorentzkraft')
        result.warnings.append('Felt og potentiale ved den valgte kildeladning udelader dens eget singulære bidrag. Parenergien omfatter fortsat hele systemet.')
    if 'free_point_charges_3D' in p.assumptions:
        result.warnings.append('Earnshaws sætning: en elektrostatisk ligevægt af frit bevægelige punktladninger i tre dimensioner kan ikke være stabil. Mekaniske bindinger eller andre kræfter er ikke medtaget.')
        result.symbolic_result['equilibrium_stability']='unstable_if_unconstrained_3D'
    result.units={'E':'V/m','E_far':'V/m','V':'V','U':'J','dipole':'C*m','Q':'C','F':'N'}
    result.add('Summér komponenterne og parenergierne',sp.Tuple(*result.symbolic_result.get('E',[]),energy))
    if 'far_coordinate' in p.variables:
        radial=p.variables['far_coordinate'];order=p.variables.get('series_order',5)
        if not isinstance(radial,sp.Symbol) or not isinstance(order,int) or not 1<=order<=8:raise InputError('Fjernfelt kræver et koordinatsymbol og heltalsorden fra 1 til 8.')
        e_far=result.symbolic_result['E'].applyfunc(lambda v:sp.series(v,radial,sp.oo,order).removeO())
        result.symbolic_result['E_far']=sp.simplify(e_far)
        result.symbolic_result['V_far']=sp.simplify(sp.series(result.symbolic_result['V'],radial,sp.oo,order).removeO())
        result.units['V_far']='V'
        result.add('Asymptotisk potentialudvikling med samme eksplicitte orden',result.symbolic_result['V_far'])
        result.add('Asymptotisk udvikling for stor positiv afstand',e_far)
        result.warnings.append('Fjernfeltsudtrykket er trunkeret og kræver afstand meget større end kildeudstrækningen.')
    if 'initial_charges' in p.variables:
        from ..core.problem import Problem
        before=point_charges(Problem('EV','point_charges',variables={'charges':p.variables['initial_charges']}|({'point':list(point)} if point is not None else {}),wanted=['U'] if point is None else []))
        result.symbolic_result['W_external']=sp.simplify(energy-before.symbolic_result['U'])
        result.add('Arbejde ved kvasistatisk omplacering = slutenergi minus startenergi',result.symbolic_result['W_external'])
        result.units['W_external']='J'
    result.warnings.append('Dipolmomentet refererer til det angivne koordinatsystems origo; for nettoladning afhænger det af origo.')
    return result


def coulomb_integral(p):
    source, parameters, bounds, density, point, kind=p.require('source','parameters','bounds','density','point','kind')
    source,point=vector(source),vector(point)
    if len(parameters)!=len(bounds): raise InputError('Parameter og integrationsgrænser passer ikke sammen.')
    if kind=='line' and len(parameters)==1:
        tangent=source.diff(parameters[0]); jac=sp.sqrt(tangent.dot(tangent))
    elif kind=='surface' and len(parameters)==2:
        normal=source.diff(parameters[0]).cross(source.diff(parameters[1])); jac=sp.sqrt(normal.dot(normal))
    elif kind=='volume' and len(parameters)==3:
        jac=sp.Abs(sp.det(source.jacobian(parameters)))
    else: raise InputError('Brug line/1, surface/2 eller volume/3 parametre.')
    result=solution(p,'Coulomb-integral',
        'Geometrien parameteriseres, og differentialelementet findes fra tangent, krydsprodukt eller Jacobi-determinant. Ingen Gauss-symmetri antages.',
        [r'V=\frac1{4\pi\epsilon_0}\int\frac{dq}{|\mathbf r-\mathbf r^\prime|}',
         r'\mathbf E=\frac1{4\pi\epsilon_0}\int\frac{(\mathbf r-\mathbf r^\prime)dq}{|\mathbf r-\mathbf r^\prime|^3}'],
         'Vektoren peger fra kilden mod feltpunktet for positiv ladning.')
    limits=[(param,*bound) for param,bound in zip(parameters,bounds)]
    d=point-source; distance=sp.sqrt(d.dot(d)); weight=sp.simplify(density*jac)
    result.add('Geometriens differentialelement (uden parameterdifferentialer)',jac)
    result.add('Indsæt ladningstæthed og differentialelement',weight)
    q=finite_integral(weight,*limits)
    v_integrand=weight/(4*sp.pi*EPS0*distance)
    result.add('Potentialintegralet før evaluering',sp.Integral(v_integrand,*limits))
    v=finite_integral(v_integrand,*limits)
    e=[]
    for i in range(3):
        integrand=sp.simplify(weight*d[i]/(4*sp.pi*EPS0*distance**3))
        result.add(f'Feltkomponent {i+1} før evaluering',sp.Integral(integrand,*limits))
        e.append(finite_integral(integrand,*limits))
    result.symbolic_result={'Q':q,'V':v,'E':sp.Matrix(e)}
    dipole=sp.Matrix([finite_integral(weight*source[i],*limits) for i in range(3)])
    result.symbolic_result['dipole']=dipole
    if 'test_charge' in p.variables:
        result.symbolic_result['U_external']=sp.simplify(p.variables['test_charge']*v)
        result.symbolic_result['F']=sp.simplify(p.variables['test_charge']*sp.Matrix(e))
    result.units={'Q':'C','V':'V','E':'V/m','dipole':'C*m','U_external':'J','F':'N'}
    if any(val.has(sp.Integral) for val in [q,v,*e]):
        result.warnings.append('Ingen lukket analytisk form fundet for alle integraler. De korrekte integraler bevares; numerisk evaluering kræver alle parameterværdier.')
    return result


def gauss_radial(p):
    coord, symmetry=p.require('coordinate','symmetry')
    if symmetry not in ('sphere','cylinder','plane'): raise InputError('Ukendt Gauss-symmetri.')
    p.assume({'sphere':'spherical_symmetry','cylinder':'infinite_cylindrical_symmetry','plane':'infinite_planar_symmetry'}[symmetry])
    positive(coord,'Radialkoordinat/positiv afstand')
    if not p.regions and not p.variables.get('surface_charges'): raise InputError('Angiv radiale områder med tæthed og permittivitet eller eksplicitte overfladeladninger.')
    # Each supplied interval is a charged/material interval; vacuum fills gaps.
    measure={'sphere':4*sp.pi*coord**2,'cylinder':2*sp.pi*coord,'plane':sp.S.One}[symmetry]
    denom={'sphere':4*sp.pi*coord**2,'cylinder':2*sp.pi*coord,'plane':sp.S.One}[symmetry]
    result=solution(p,'Gauss’ lov',
        {'sphere':'Kuglesymmetri giver et radialt felt med samme styrke på hele kuglefladen.',
         'cylinder':'Translations- og rotationssymmetri for en uendelig cylinder giver et radialt felt, konstant på Gauss-cylinderens krumme flade.',
         'plane':'Uendelig plansymmetri og spejlsymmetri giver et normalt felt på hver side af midterplanet.'}[symmetry],
        [r'\oint\mathbf D\cdot d\mathbf a=Q_{\rm fri,enc}',r'\mathbf D=\epsilon\mathbf E'],
        'Radialt i positiv koordinatretning; negativt resultat betyder modsat retning. For plan: modsat retning på den anden side.')
    points=[sp.S.Zero]; q=sp.S.Zero
    for reg in p.regions:
        lo,hi,density=map(sp.sympify,(reg.lower,reg.upper,reg.density))
        if any(sym.name in ('phi','theta','z','x','y') and sym!=coord for sym in density.free_symbols):raise InputError('Tætheden afhænger af en koordinat, som bryder den angivne radiale symmetri.')
        positive(hi-lo,'Regionsbredde')
        if lo.is_nonnegative is not True: raise InputError('Nedre radius skal være ikke-negativ.')
        if density.free_symbols & (set(p.variables.get('angular_symbols',[]))):
            raise InputError('Vinkela fhængig tæthed opfylder ikke den angivne symmetri.')
        positive(reg.permittivity,'Permittivitet')
        integral=sp.Integral(density*measure,(coord,lo,coord))
        partial=finite_integral(density*measure,(coord,lo,coord))
        total=finite_integral(density*measure,(coord,lo,hi))
        result.add(f'Indesluttet bidrag fra området [{lo}, {hi}] før integration',integral)
        result.add('Efter symbolsk integration',partial)
        q+=sp.Piecewise((0,coord<lo),(partial,coord<=hi),(total,True))
        points.extend([lo,hi])
    for radius,sigma in p.variables.get('surface_charges',[]):
        weight=sp.Rational(1,2) if symmetry=='plane' and sp.sympify(radius)==0 else 1
        q+=sp.Piecewise((0,coord<radius),(weight*sigma*measure.subs(coord,radius),True))
        points.append(radius)
    # Explicit material intervals must not overlap; otherwise epsilon is ambiguous.
    for i,a in enumerate(p.regions):
        for b in p.regions[i+1:]:
            overlap=sp.And(sp.sympify(a.lower)<b.upper,sp.sympify(b.lower)<a.upper)
            if overlap is not sp.false: raise InputError('Materialeområder overlapper eller kan ikke ordnes entydigt.')
    epsilon=sp.Piecewise(*[(reg.permittivity,sp.And(coord>=reg.lower,coord<=reg.upper)) for reg in p.regions],(EPS0,True))
    d=sp.piecewise_fold(q/denom)
    e=sp.piecewise_fold(d/epsilon)
    result.symbolic_result={'Q_enc':sp.simplify(q),'D':sp.simplify(d),'E':sp.simplify(e)}
    if symmetry=='cylinder' and 'length' in p.variables:
        length=p.variables['length'];positive(length,'Gauss-cylinderens længde')
        result.symbolic_result['Q_enc_per_length']=sp.simplify(q)
        result.symbolic_result['Q_enc']=sp.simplify(q*length)
        result.add('Gang ladning pr. længdeenhed med den angivne cylinderlængde',q*length)
    result.add('Indsæt den indesluttede ladning i Gauss’ lov',e)
    for reg in p.regions:
        # Differential identity checked away from material boundaries.
        middle=(reg.lower+reg.upper)/2
        local=sp.simplify(d.subs(coord,middle))
        result.add('Kontrolpunkt i regionen (D)',local)
    result.units={'E':'V/m','D':'C/m^2','Q_enc':{'sphere':'C','cylinder':'C/m','plane':'C/m^2'}[symmetry]}
    if symmetry=='cylinder' and 'length' in p.variables:result.units.update(Q_enc='C',Q_enc_per_length='C/m')
    result.warnings.append('Q_enc er total ladning for kugle, ladning pr. længde for cylinder og halvrums-ladning pr. areal for spejlsymmetrisk plan. Ved grænseflader angives ensidige grænser separat; punktværdien er ikke fysisk entydig ved overfladeladning.')
    return result


def field_calculus(p):
    coords, system=p.require('coordinates','system')
    grad,div,curl=calculus(coords,system)
    result=solution(p,'Gradient, divergens og rotation',
        'Maxwells differentialligninger forbinder felt, potentiale og kilder. Metriske faktorer medtages i det valgte ortogonale koordinatsystem.',
        [r'\mathbf E=-\nabla V',r'\rho=\epsilon_0\nabla\cdot\mathbf E',r'\mathbf B=\nabla\times\mathbf A',r'\mathbf J=\mu_0^{-1}\nabla\times\mathbf B'],
        'Komponenter i den ortonormale basis for det valgte koordinatsystem.')
    data=p.variables|p.functions
    # Record only laws this execution will actually apply.
    result.equations=[]
    if 'V' in data:result.equations.append(r'\mathbf E=-\nabla V')
    if 'A' in data:result.equations.append(r'\mathbf B=\nabla\times\mathbf A')
    if 'E' in data or 'V' in data:
        result.equations.extend([r'\rho_{total}=\epsilon_0\nabla\cdot\mathbf E',r'\partial_t\mathbf B=-\nabla\times\mathbf E'])
        if 'electrostatic' in p.assumptions:result.equations.append(r'\nabla\times\mathbf E=0')
    if 'B' in data or 'A' in data:
        result.equations.append(r'\nabla\cdot\mathbf B=0')
        if 'magnetostatic' in p.assumptions:result.equations.append(r'\mathbf J=\mu_0^{-1}\nabla\times\mathbf B')
    electric_step=None
    if 'V' in data:
        result.add('Differentier potentialet med koordinatsystemets skaleringsfaktorer',grad(data['V']),reasoning='Gradienten beregnes med de metriske faktorer i det givne koordinatsystem; feltet fås derefter med et minusfortegn.',law='Gradient af potentiale')
        derived=-grad(data['V'])
        if 'E' in data and any(v.equals(0) is not True for v in derived-vector(data['E'])):
            raise InputError('De angivne E og V er ikke verificeret indbyrdes konsistente: E skal være -grad(V).')
        data['E']=derived
        electric_step=result.add('Tag minus gradienten: det elektriske felt',derived,reasoning='Det elektriske felt peger mod aftagende elektrostatisk potentiale og er derfor minus gradienten.',law='Elektrisk felt fra potentiale',validity=['Glat potentiale i det angivne område.'])
        result.symbolic_result['laplacian_V']=div(grad(data['V']))
    if 'A' in data:
        result.add('Tag rotationen af vektorpotentialet',curl(data['A']),reasoning='Magnetfeltet bestemmes af definitionen B = curl(A); den angivne koordinatbasis bruges.',law='Magnetfelt fra vektorpotentiale')
        derived=curl(data['A'])
        if 'B' in data and any(v.equals(0) is not True for v in derived-vector(data['B'])):
            raise InputError('De angivne B og A er ikke verificeret indbyrdes konsistente: B skal være curl(A).')
        data['B']=derived
        result.symbolic_result['div_A']=div(data['A'])
        result.symbolic_result['laplacian_A']=sp.simplify(grad(div(data['A']))-curl(curl(data['A'])))
    if 'E' in data:
        e=vector(data['E']); divergence=div(e); rotation=curl(e)
        result.add('Beregn divergensen led for led',divergence,reasoning='Gauss differentiallov forbinder feltets divergens med den samlede lokale volumenladning.',law='Gauss differentiallov')
        result.add('Indsæt i Gauss’ differentiallov',EPS0*divergence)
        result.symbolic_result.update(E=e,rho=EPS0*divergence,curl_E=rotation,dB_dt=-rotation)
        rotation_step=result.add('Beregn rotationen af E',rotation,reasoning='Faradays differentiallov bestemmer den krævede tidsændring af B; i elektrostatik skal rotationen være nul.',law='Faradays differentiallov',validity=['Differentialkontrollen gælder i glatte områder.'])
        if electric_step is not None:result.check('Rotation af gradientfelt',rotation,step=electric_step)
        if 'electrostatic' in p.assumptions:
            result.check('Elektrostatisk rotation',rotation,step=rotation_step)
            if any(v.equals(0) is False for v in rotation):
                result.warnings.append('Feltet har rotation forskellig fra nul og kan ikke være elektrostatisk.')
        if 'volume_bounds' in data:
            a,b,_=coords
            jac={'cartesian':1,'cylindrical':a,'spherical':a*a*sp.sin(b)}[system]
            result.symbolic_result['Q']=finite_integral(EPS0*divergence*jac,*data['volume_bounds'])
    if 'B' in data:
        b=vector(data['B']); divergence=div(b)
        divergence_step=result.add('Beregn divergensen af magnetfeltet',divergence,reasoning='Et fysisk magnetfelt skal have nul divergens; kontrollen afprøver denne Maxwell-relation.',law='Gauss lov for magnetfeltet')
        result.symbolic_result.update(B=b,div_B=divergence)
        result.check('Magnetisk divergens',divergence,step=divergence_step)
        if 'magnetostatic' in p.assumptions:
            if 'time' in data:
                if not isinstance(data['time'],sp.Symbol):raise InputError('Magnetostatisk tidskontrol kræver et eksplicit tidssymbol.')
                if any(value.equals(0) is not True for value in b.diff(data['time'])):raise InputError('Det givne B afhænger af tiden og er ikke verificeret magnetostatisk.')
            current=curl(b)/sp.Symbol('mu_0',positive=True)
            if 'J' in data and any(value.equals(0) is not True for value in sp.simplify(current-vector(data['J']))):raise InputError('Givet J og B er ikke verificeret indbyrdes konsistente: magnetostatik kræver J = curl(B)/mu_0.')
            result.symbolic_result['J']=current
            current_step=result.add('Magnetostatik: beregn curl(B) og divider med μ₀',current,reasoning='I magnetostatik giver Ampères differentiallov den samlede strømtæthed. Ladningsbevarelse kræver samtidig nul divergens af denne stationære strøm.',law='Ampères differentiallov',validity=['Stationære felter; strømmen omfatter alle kilder til det angivne B.'])
            result.check('Statisk strømbevarelse: div(J)=0',div(current),'Kontinuitetsligningen reduceres til nul divergens, når ladningstætheden er stationær.',step=current_step)
    if 'E' not in data and 'B' not in data:
        raise InputError('Angiv V, E, A eller B.')
    result.units={'E':'V/m','rho':'C/m^3','B':'T','J':'A/m^2','Q':'C','dB_dt':'T/s','curl_E':'V/m^2','laplacian_V':'V/m^2','laplacian_A':'T/m','div_A':'T','div_B':'T/m'}
    result.warnings.append('Differentialkontroller gælder i glatte områder. Delta-kilder og grænseflader kræver særskilt integral-/springkontrol.')
    return result


def potential_from_field(p):
    field, coordinate, start, end=p.require('field','coordinate','start','end')
    result=solution(p,'Potentialforskel fra feltet','Potentialforskellen findes som minus feltets linjeintegral langs den angivne kurve/retning.',
                    [r'V(b)-V(a)=-\int_a^b\mathbf E\cdot d\mathbf l'])
    result.add('Indsæt feltkomponenten langs integrationsvejen',-sp.Integral(field,(coordinate,start,end)))
    v=-finite_integral(field,(coordinate,start,end))
    result.add('Evaluer integralet og grænserne',v)
    result.symbolic_result={'delta_V':v};result.units={'delta_V':'V'}
    if 'test_charge' in p.variables:
        result.symbolic_result['W_external']=sp.simplify(p.variables['test_charge']*v)
        result.add('Arbejde mod feltet = q gange potentialforskellen',result.symbolic_result['W_external'])
        result.units['W_external']='J'
    return result


def conductors(p):
    if p.variables.get('kind')=='spherical_sectors':
        p.assume('radial_dielectric_interfaces','electrostatic','no_external_sources')
        charge,radius,coordinate,sectors=p.require('charge','radius','coordinate','sectors')
        positive(radius,'Kugleradius')
        if sp.simplify(sum(angle for angle,_ in sectors)-4*sp.pi)!=0:raise InputError('Sektorernes rumvinkler skal summere til 4π.')
        weight=0
        for angle,epsilon in sectors:
            positive(angle,'Rumvinkel');positive(epsilon,'Permittivitet');weight+=angle*epsilon
        field=charge/(coordinate**2*weight)
        result=solution(p,'Randbetingelser, Gauss for D og entydighed',
            'Et fælles radialt E-felt opfylder tangentkontinuitet ved radiale dielektriske grænser og konstant potentiale på kuglen. Gauss’ lov for D fastlægger amplituden. Sammen med nul potentiale i det uendelige giver entydighedssætningen løsningen.',
            [r'Q=E(r)r^2\sum_i\epsilon_i\Omega_i',r'\sigma_{f,i}=\epsilon_i E(R)'])
        result.add('Vægt rumvinklerne med permittiviteterne',weight)
        result.symbolic_result={'E':sp.simplify(field),'V':sp.simplify(charge/(coordinate*weight))}
        for index,(angle,epsilon) in enumerate(sectors):
            result.symbolic_result[f'D_{index}']=sp.simplify(epsilon*field)
            result.symbolic_result[f'sigma_free_{index}']=sp.simplify(epsilon*field.subs(coordinate,radius))
        result.check('Gauss: total fri ladning',sum(angle*radius**2*result.symbolic_result[f'sigma_free_{i}'] for i,(angle,_) in enumerate(sectors))-charge)
        result.direction='Radialt udenfor kuglen (r>R); for positiv Q udad.'
        result.units={'E':'V/m','V':'V'}
        for key in result.symbolic_result:
            if key.startswith(('D_','sigma_free_')):result.units[key]='C/m^2'
        return result
    if p.variables.get('kind')=='boundary':
        normal,e_in,e_out,eps_in,eps_out=p.require('normal','E_inside','E_outside','epsilon_inside','epsilon_outside')
        normal=vector(normal);e_in,e_out=vector(e_in),vector(e_out)
        if sp.simplify(normal.dot(normal)-1)!=0:raise InputError('Randfladen kræver en enhedsnormal fra inde til ude.')
        result=solution(p,'Elektrostatiske springbetingelser',
            'Den normale D-komponents spring bestemmer fri overfladeladning. Det normale E-spring bestemmer den samlede overfladeladning. Forskellen er bunden ladning.',
            [r'\sigma_f=\hat n\cdot(\mathbf D_{out}-\mathbf D_{in})',r'\sigma_{total}=\epsilon_0\hat n\cdot(\mathbf E_{out}-\mathbf E_{in})'])
        sf=sp.simplify(normal.dot(eps_out*e_out-eps_in*e_in));total=sp.simplify(EPS0*normal.dot(e_out-e_in))
        result.add('Beregn spring i normal D-komponent',sf)
        result.symbolic_result={'sigma_free':sf,'sigma_total':total,'sigma_bound':sp.simplify(total-sf)}
        result.check('Kontinuitet af tangentielt E',normal.cross(e_out-e_in))
        result.direction='Normalen er fra det angivne indre til ydre medium.'
        result.units={key:'C/m^2' for key in result.symbolic_result}
        return result
    if p.variables.get('kind')=='cavity_totals':
        p.assume('electrostatic','closed_conductor','spherical_outer_surface','no_external_sources')
        enclosed,metal,radius=p.require('enclosed_charge','metal_charge','outer_radius');positive(radius,'Ydre radius')
        result=solution(p,'Gauss i en leder og ydre kuglesymmetri',
            'En Gauss-flade i metallet har nul flux og nul total omsluttet ladning. Den ydre kugleflade er ækvipotential; uden eksterne kilder er ydre felt kuglesymmetrisk.',
            [r'Q_{inner}=-q_{cavity}',r'Q_{outer}=Q_{metal}+q_{cavity}',r'V_{metal}=Q_{outer}/(4\pi\epsilon_0 R)'])
        result.symbolic_result={'Q_inner':-enclosed,'Q_outer':metal+enclosed,'V':(metal+enclosed)/(4*sp.pi*EPS0*radius)}
        result.add('Nul indesluttet ladning på Gauss-fladen i metallet',-enclosed)
        result.add('Ladningsbevarelse bestemmer den ydre overfladeladning',metal+enclosed)
        result.warnings.append('Dette bestemmer ikke lokal overfladeladning i et asymmetrisk hulrum eller feltlinjeskitsen.')
        result.units={'Q_inner':'C','Q_outer':'C','V':'V'}
        return result
    # Concentric solid sphere and/or shells; charge-free dielectric gaps.
    shells, coordinate=p.require('shells','coordinate')
    p.assume('concentric_spheres','electrostatic')
    result=solution(p,'Gauss, lederligevægt og potentialintegral',
        'Feltet er nul i metallet. Gauss-flader i hver leder bestemmer den inducerede indre ladning; resten sidder på den ydre overflade.',
        [r'\mathbf E_{metal}=0',r'Q_{inner}=-Q_{cavity}',r'\sigma=Q/(4\pi r^2)',r'V(r)=\int_r^\infty E(r^\prime)dr^\prime'])
    cumulative=sp.sympify(p.variables.get('central_charge',0))
    gap_eps=p.variables.get('gap_permittivities',[EPS0]*len(shells))
    outside_eps=p.variables.get('outside_permittivity',EPS0)
    if len(gap_eps)!=len(shells):raise InputError('Angiv én permittivitet pr. leder: i mellemrummet før lederen.')
    for value in [*gap_eps,outside_eps]:positive(value,'Permittivitet')
    surfaces=[]; fields=[]; segments=[];prev=sp.S.Zero; energy=sp.S.Zero
    t=sp.Dummy('r',positive=True)
    for idx,shell in enumerate(shells):
        a,b,q=map(sp.sympify,shell)
        if a.is_negative is not False or (b-a).is_nonnegative is not True or b.is_positive is not True:
            raise InputError('Ledere kræver 0 ≤ indre radius ≤ ydre radius og positiv ydre radius.')
        if idx and (a-prev).is_positive is not True: raise InputError('Lederne skal være ordnede med positive mellemrum.')
        if a==0 and cumulative!=0: raise InputError('En central ladning kan ikke ligge i en massiv metalkugle.')
        if a!=0:
            qi=-cumulative; surfaces.append((a,qi,qi/(4*sp.pi*a*a)))
            if idx==0 and cumulative==0:
                fields.append((0,coordinate<a))
            if idx or cumulative!=0:
                fields.append((cumulative/(4*sp.pi*gap_eps[idx]*coordinate**2),sp.And(coordinate>prev,coordinate<a)))
                segments.append((prev,a,cumulative,gap_eps[idx]))
                if prev==0 and cumulative!=0:
                    result.warnings.append('Central punktladnings selvenergi divergerer; samlet feltenergi i hulrummet beregnes ikke.')
                elif prev!=0:
                    energy+=cumulative**2/(8*sp.pi*gap_eps[idx])*(1/prev-1/a)
        else: qi=0
        qo=q-qi; surfaces.append((b,qo,qo/(4*sp.pi*b*b)))
        result.add(f'Leder {idx+1}: indre og ydre ladning',sp.Tuple(qi,qo))
        fields.append((0,sp.And(coordinate>=a,coordinate<=b)))
        cumulative+=q; prev=b
    if not shells: raise InputError('Angiv mindst én leder.')
    fields.append((cumulative/(4*sp.pi*outside_eps*coordinate**2),True))
    e=sp.Piecewise(*fields)
    v=sp.simplify(sum(q/(4*sp.pi*EPS0)*sp.Piecewise((1/r,coordinate<r),(1/coordinate,True)) for r,q,_ in surfaces)
                  + sp.sympify(p.variables.get('central_charge',0))/(4*sp.pi*EPS0*coordinate))
    if any(value!=EPS0 for value in [*gap_eps,outside_eps]):
        v=cumulative/(4*sp.pi*outside_eps)*sp.Piecewise((1/prev,coordinate<prev),(1/coordinate,True))
        for lo,hi,charge,epsilon in segments:
            if lo==0:
                term=sp.Piecewise((1/coordinate-1/hi,coordinate<hi),(0,True))
            else:
                term=sp.Piecewise((1/lo-1/hi,coordinate<=lo),(1/coordinate-1/hi,coordinate<hi),(0,True))
            v+=charge*term/(4*sp.pi*epsilon)
        v=sp.simplify(v)
    energy+=cumulative**2/(8*sp.pi*outside_eps*prev)
    result.symbolic_result={'E':e,'V':v,'surfaces':surfaces}
    if p.variables.get('central_charge',0)==0:result.symbolic_result['U']=sp.simplify(energy)
    result.add('Overfladeladningstætheder (radius, ladning, tæthed)',sp.Tuple(*[sp.Tuple(*s) for s in surfaces]))
    result.check('Samlet overfladeladning',sum(q for _,q,_ in surfaces)-sum(q for _,_,q in shells))
    result.units={'E':'V/m','V':'V','U':'J','surfaces':'(m, C, C/m^2)'}
    result.direction='Radialt udad ved positivt E. Koncentriske sfærer med eksplicitte konstante permittiviteter i mellemrummene.'
    return result


def capacitance(p):
    geometry,epsilon=p.require('kind','epsilon');positive(epsilon,'Permittivitet')
    result=solution(p,'Kapacitans fra geometri og potentialforskel',
        'Gauss’ lov giver feltet i det angivne lineære dielektrikum; spændingsforskellen findes ved integration, og C=Q/ΔV.',
        [r'C=Q/\Delta V',r'\mathbf D=\epsilon\mathbf E',r'U=Q^2/(2C)'])
    if geometry=='parallel_plates':
        p.assume('negligible_edge_effects');area,d=p.require('area','distance');positive(area,'Areal');positive(d,'Pladeafstand');c=epsilon*area/d
        result.add('Gauss giver E=Q/(epsilon A); spændingsforskel pr. ladning',d/(epsilon*area))
    elif geometry in ('sphere','cylinder'):
        a,b=p.require('inner_radius','outer_radius');positive(a,'Indre radius');positive(b-a,'Radialt mellemrum')
        r=sp.Dummy('r',positive=True)
        if geometry=='sphere':
            integrand=1/(4*sp.pi*epsilon*r*r)
        else:
            p.assume('infinite_cylindrical_symmetry');length,=p.require('length');positive(length,'Længde');integrand=1/(2*sp.pi*epsilon*length*r)
        result.add('Potentialforskel pr. ladning før integration',sp.Integral(integrand,(r,a,b)))
        inverse=finite_integral(integrand,(r,a,b));result.add('Efter integration',inverse);c=1/inverse
    else:raise InputError('Kapacitans: parallel_plates, sphere eller cylinder.')
    result.symbolic_result={'C':sp.simplify(c)}
    if 'Q' in p.variables:
        q=p.variables['Q'];result.symbolic_result.update(V=sp.simplify(q/c),U=sp.simplify(q*q/(2*c)))
    if 'V' in p.variables:
        v=p.variables['V'];result.symbolic_result.update(Q=sp.simplify(c*v),U=sp.simplify(c*v*v/2))
        if geometry=='parallel_plates':
            result.symbolic_result['E']=sp.simplify(v/d)
            if 'normal' in p.variables:
                normal=vector(p.variables['normal'])
                if sp.simplify(normal.dot(normal)-1)!=0:raise InputError('Pladenormalen skal være en enhedsvektor.')
                result.symbolic_result['E_vector']=sp.simplify(v/d*normal)
                result.direction='Normalen skal pege fra pladen med potentiale VA mod pladen med potentiale VB; V betyder VA-VB.'
            result.add('Potentialforskellen er E d; isolér feltet',v/d)
    result.units={'C':'F','Q':'C','V':'V','U':'J','E':'V/m','E_vector':'V/m'}
    return result


def polarization(p):
    coords,system=p.require('coordinates','system');grad,div,curl=calculus(coords,system)
    result=solution(p,'Polarisering og bundne ladninger',
        'Volumenladning følger af minus divergensen af polariseringen. Overfladeladning følger af normalprojektionen med udadrettet normal.',
        [r'\mathbf P=(\epsilon-\epsilon_0)\mathbf E',r'\rho_b=-\nabla\cdot\mathbf P',r'\sigma_b=\mathbf P\cdot\hat{\mathbf n}'])
    if 'P' in p.variables: pol=vector(p.variables['P'])
    else:
        e,epsilon=p.require('E','epsilon');positive(epsilon,'Permittivitet');pol=(epsilon-EPS0)*vector(e)
    result.add('Indsæt polarisationsfeltet',pol)
    rho=-div(pol);result.add('Beregn minus divergensen',rho)
    result.symbolic_result={'P':pol,'rho_bound':rho}
    if 'normal' in p.variables:
        normal=vector(p.variables['normal'])
        if sp.simplify(normal.dot(normal)-1)!=0: raise InputError('Normalvektoren skal være en enhedsvektor.')
        sigma=sp.simplify(pol.dot(normal)).subs(p.variables.get('surface_substitutions',{}))
        result.symbolic_result['sigma_bound']=sigma;result.add('Projektér på den udadrettede normal',sigma)
    result.units={'P':'C/m^2','rho_bound':'C/m^3','sigma_bound':'C/m^2'}
    return result


def images(p):
    charges,point,planes=p.require('charges','point','planes')
    if planes not in ([1],[0],[0,1]):raise InputError('Spejling understøtter jordet x=0, y=0 eller det vinkelrette hjørne x=y=0.')
    p.assume('grounded_infinite_planes')
    for q,pos in charges:
        for axis in planes:
            positive(vector(pos)[axis],'Ladningsposition i det fysiske halvrum')
    for axis in planes: positive(vector(point)[axis],'Feltpunkt i det fysiske halvrum')
    allcharges=list(charges)
    for axis in planes:
        mirrors=[]
        for q,pos in allcharges:
            pos=list(pos);pos[axis]=-pos[axis];mirrors.append((-q,pos))
        allcharges+=mirrors
    from ..core.problem import Problem
    if 'self_index' in p.variables:
        index=p.variables['self_index']
        if not isinstance(index,int) or not 0<=index<len(charges):raise InputError('Ugyldigt indeks for selvfelt.')
        if vector(charges[index][1])!=vector(point):raise InputError('Selvfelt kan kun udelades ved den valgte ladnings position.')
        allcharges.pop(index)
    inner=Problem('EV','point_charges',variables={'charges':allcharges,'point':point,**({'test_charge':p.variables['test_charge']} if 'test_charge' in p.variables else {})})
    result=point_charges(inner)
    result.recognition=p.family
    result.method='Spejlingsmetode, Coulomb og entydighed'
    result.reasoning='Spejlladningerne sikrer V=0 på de jordede planer. Entydighedssætningen giver det fysiske felt i det oprindelige halvrum.'
    result.givens=p.variables
    result.symbolic_result.pop('U',None) # Image pair energy is not physical system energy.
    result.symbolic_result.pop('dipole',None);result.symbolic_result.pop('Q',None)
    result.add('Virkelige ladninger og konstruerede spejlladninger',allcharges)
    result.warnings.append('Spejlladninger er hjælpekilder. Parenergien af det udvidede ladningssystem er ikke den fysiske energi og returneres derfor ikke.')
    return result


def laplace_legendre(p):
    r,theta,radius,coefficients=p.require('r','theta','radius','coefficients');positive(radius,'Radius')
    p.assume('axial_symmetry','charge_free_inside_outside','V_infinity_zero','finite_at_origin')
    result=solution(p,'Laplaces ligning med Legendre-polynomier',
        'Regulære indre løsninger skalerer som r^l, og ydre løsninger, som går mod nul i det uendelige, skalerer som r^(-l-1). Randværdien bestemmer koefficienterne.',
        [r'V_{in}=\sum_l a_l(r/R)^lP_l(\cos\theta)',r'V_{out}=\sum_l a_l(R/r)^{l+1}P_l(\cos\theta)'])
    inside=0;outside=0
    for degree,coefficient in coefficients:
        if not isinstance(degree,int) or degree<0:raise InputError('Legendre-grader skal være ikke-negative heltal.')
        term=coefficient*sp.legendre(degree,sp.cos(theta))
        inside+=term*(r/radius)**degree;outside+=term*(radius/r)**(degree+1)
        result.add(f'Randmode l={degree}',term)
    phi=sp.Dummy('phi',real=True);grad,div,curl=calculus([r,theta,phi],'spherical')
    result.symbolic_result={'V_inside':sp.simplify(inside),'V_outside':sp.simplify(outside),
                            'E_inside':-grad(inside),'E_outside':-grad(outside)}
    result.check('Kontinuitet af potentiale ved R',(inside-outside).subs(r,radius))
    result.check('Laplace indenfor',div(grad(inside)))
    result.check('Laplace udenfor',div(grad(outside)))
    result.add('Differentier de radiale og polære led',result.symbolic_result['E_outside'])
    result.units={'V_inside':'V','V_outside':'V','E_inside':'V/m','E_outside':'V/m'}
    result.direction='Sfærisk ortonormal basis (r-hat, theta-hat, phi-hat).'
    return result
