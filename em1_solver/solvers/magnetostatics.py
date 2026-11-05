import sympy as sp
from ..core.problem import InputError
from ..core.solution import solution
from ..core.validation import EPS0, MU0, vector, positive, finite_integral, calculus


def ampere(p):
    kind,=p.require('kind')
    result=solution(p,'Ampères lov',
        'Kun den eksplicit angivne symmetri bruges til at flytte feltstyrken uden for kurveintegralet. Højrehåndsreglen bestemmer omløbsretningen.',
        [r'\oint\mathbf B\cdot d\mathbf l=\mu_0 I_{enc}'], 'Azimutalt for aksial strøm; positiv strøm langs z giver positiv phi-retning.')
    if kind=='current_surface':
        surface,params,bounds,current=p.require('surface','parameters','bounds','J_on_surface')
        if len(params)!=2 or len(bounds)!=2:raise InputError('Strømfladen kræver to parametre og grænsesæt.')
        surface=vector(surface);normal_area=surface.diff(params[0]).cross(surface.diff(params[1]))
        integrand=sp.simplify(vector(current).dot(normal_area))
        limits=[(coord,*bound) for coord,bound in zip(params,bounds)]
        result.method='Integreret strømtæthed'
        result.reasoning='Strømmen gennem en orienteret flade er integralet af strømtæthedens normalprojektion.'
        result.equations=[r'I=\int_S\mathbf J\cdot d\mathbf a']
        result.add('Bestem den orienterede arealvektor',normal_area)
        result.add('Integrer normalprojektionen af J',sp.Integral(integrand,*limits))
        result.symbolic_result={'I_enc':finite_integral(integrand,*limits)}
        result.direction='Positiv strøm er gennem fladen i parameteriseringens normalretning.'
    elif kind=='cylinder':
        p.assume('infinite_cylindrical_symmetry','magnetostatic')
        s,=p.require('coordinate');positive(s,'Radialkoordinat')
        if not p.regions:raise InputError('Angiv strømførende radiale regioner.')
        current=sp.S.Zero
        for i,region in enumerate(p.regions):
            if any(sym.name in ('phi','theta','z','x','y') and sym!=s for sym in sp.sympify(region.density).free_symbols):raise InputError('Strømtætheden bryder den angivne radiale symmetri.')
            lo,hi=sp.sympify(region.lower),sp.sympify(region.upper)
            if lo.is_nonnegative is not True:raise InputError('Indre radius skal være ikke-negativ.')
            positive(hi-lo,'Regionsbredde')
            for other in p.regions[:i]:
                if sp.And(lo<other.upper,sp.sympify(other.lower)<hi) is not sp.false:
                    raise InputError('Strømregioner overlapper eller kan ikke ordnes.')
            integrand=2*sp.pi*s*region.density
            partial=finite_integral(integrand,(s,lo,s));total=finite_integral(integrand,(s,lo,hi))
            result.add('Omsluttet strøm før integration',sp.Integral(integrand,(s,lo,s)))
            result.add('Regionens strøm efter integration',partial)
            current+=sp.Piecewise((0,s<lo),(partial,s<=hi),(total,True))
        for radius,k in p.variables.get('surface_currents',[]):
            current+=sp.Piecewise((0,s<radius),(2*sp.pi*radius*k,True))
        b=sp.simplify(sp.piecewise_fold(MU0*current/(2*sp.pi*s)))
        result.symbolic_result={'I_enc':sp.simplify(current),'B':b}
        result.add('B 2πs = μ₀ I_enc; isolér B',b)
        result.warnings.append('B er phi-komponenten; dens grænse ved aksen skal tages før s=0 indsættes. Overfladestrømme kan give spring.')
    elif kind=='azimuthal_cylinder':
        p.assume('infinite_cylindrical_symmetry','magnetostatic','B_infinity_zero')
        coord,radius,jphi=p.require('coordinate','radius','J_phi');positive(radius,'Radius')
        integral=sp.Integral(MU0*jphi,(coord,coord,radius))
        inside=finite_integral(MU0*jphi,(coord,coord,radius))
        result.add('Ampère-rektangel: dB_z/ds = -μ₀ J_phi; integrer fra s til R',integral)
        result.symbolic_result={'B':sp.Piecewise((inside,coord<=radius),(0,True))}
        result.direction='Langs positiv z for positiv azimutal strøm; nul udenfor under den angivne fjernrandbetingelse.'
    elif kind=='wire':
        p.assume('infinite_straight_wire','magnetostatic');i,s=p.require('I','distance');positive(s,'Afstand')
        result.symbolic_result={'B':MU0*i/(2*sp.pi*s)}
        result.add('Den cirkulære Ampère-kurve har længden 2πs',2*sp.pi*s)
    elif kind=='solenoid':
        p.assume('ideal_long_solenoid','magnetostatic');n,i=p.require('turn_density','I')
        result.symbolic_result={'B':MU0*n*i}
        result.direction='Langs solenoidens positive akse for den angivne positive viklingsretning.'
        result.add('Strøm omsluttet pr. kurvelængde er nI',n*i)
    elif kind=='sheet':
        p.assume('infinite_current_sheet','magnetostatic');k,normal=p.require('K','normal');normal=vector(normal)
        if sp.simplify(normal.dot(normal)-1)!=0 or sp.simplify(vector(k).dot(normal))!=0:raise InputError('Enhedsnormal og tangentiel overfladestrøm kræves.')
        b=MU0*vector(k).cross(normal)/2
        result.symbolic_result={'B_positive':b,'B_negative':-b}
        result.direction='positive/negative betegner siden valgt af normalvektoren.'
        result.add('Springbetingelse og spejlsymmetri giver halvdelen på hver side',b)
    else:raise InputError('Ampère: cylinder, wire, solenoid eller sheet.')
    result.units={'B':'T','I_enc':'A','B_positive':'T','B_negative':'T'}
    return result


def magnetic_superposition(p):
    point,sources=p.require('point','sources');point=vector(point)
    p.assume('parallel_infinite_sources','magnetostatic')
    result=solution(p,'Ampère og magnetisk superposition',
        'Parallelle uendelige kilder behandles enkeltvis. Et hulrum repræsenteres ved en cylinder med modsat strømtæthed; felterne summeres vektorielt.',
        [r'\mathbf B_{wire}=\frac{\mu_0 I}{2\pi s^2}\hat{\mathbf z}\times\mathbf s',
         r'\mathbf B_{solid}=\frac{\mu_0J}{2}\hat{\mathbf z}\times\mathbf s\quad(s<R)'], 'Kartesiske komponenter, strøm langs positiv eller negativ z.')
    b=sp.zeros(3,1)
    for source in sources:
        center=vector(source['center']);d=sp.Matrix([point[0]-center[0],point[1]-center[1],0]);r2=sp.simplify(d.dot(d))
        cross=sp.Matrix([0,0,1]).cross(d)
        if source['kind']=='wire':
            from ..core.units import si
            numeric={k:sp.Float(str(si(v,p.numerical_units[k]).magnitude)) for k,v in p.numerical_values.items()}
            if r2.equals(0) or sp.simplify(r2.subs(numeric)).equals(0):raise InputError('Feltpunkt på en idealiseret tynd leder.')
            term=MU0*source['I']*cross/(2*sp.pi*r2)
        elif source['kind']=='cylinder':
            radius=source['radius'];positive(radius,'Cylinderradius')
            if r2.equals(0):term=sp.zeros(3,1)
            else:
                factor=sp.Piecewise((MU0*source['J']/2,r2<=radius**2),(MU0*source['J']*radius**2/(2*r2),True))
                term=factor*cross
        else:raise InputError('Kilde skal være wire eller cylinder.')
        result.add('Bidrag fra en kilde (negativ J fjerner materiale)',sp.simplify(term))
        b+=term
    if 'distribution_bounds' in p.variables:
        bounds=p.variables['distribution_bounds']
        result.add('Integrer superpositionsbidragene over den angivne kildefordeling',b)
        b=sp.Matrix([finite_integral(c,*bounds) for c in b])
    result.symbolic_result={'B':sp.simplify(b)};result.units={'B':'T'}
    return result


def biot_savart(p):
    source,parameter,bounds,current,point=p.require('source','parameter','bounds','I','point')
    source,point=vector(source),vector(point)
    result=solution(p,'Biot–Savarts lov',
        'Der er ikke tilstrækkelig symmetri til direkte Ampère-bestemmelse. Hvert orienteret ledningselement bidrager med et krydsprodukt.',
        [r'\mathbf B=\frac{\mu_0I}{4\pi}\int\frac{d\mathbf l^\prime\times(\mathbf r-\mathbf r^\prime)}{|\mathbf r-\mathbf r^\prime|^3}'],
        'Fortegnet følger parameterens voksende retning og den angivne strøm.')
    d=point-source;distance=sp.sqrt(d.dot(d));tangent=source.diff(parameter)
    result.add('Differentier den orienterede ledningskurve',tangent)
    integrand=sp.simplify(MU0*current*tangent.cross(d)/(4*sp.pi*distance**3))
    result.add('Indsæt krydsprodukt og afstand',integrand)
    b=sp.Matrix([finite_integral(v,(parameter,*bounds)) for v in integrand])
    result.symbolic_result={'B':b};result.units={'B':'T'}
    if b.has(sp.Integral):result.warnings.append('Lukket analytisk integral ikke fundet; integralet bevares.')
    return result


def lorentz_force(p):
    kind=p.variables.get('kind','force')
    result=solution(p,'Lorentzkraft',
        'Den magnetiske kraft er vinkelret på både hastighed og magnetfelt. Ved ren cirkelbevægelse leverer den centripetalkraften.',
        [r'\mathbf F=q(\mathbf E+\mathbf v\times\mathbf B)',r'q|B|v=mv^2/r'], 'Kartesiske komponenter; negativ ladning vender kraftretningen.')
    if kind=='force':
        q,v,b=p.require('q','v','B');e,=p.require('E')
        cross=vector(v).cross(vector(b));f=sp.simplify(q*(vector(e)+cross))
        result.add('Beregn v kryds B',cross);result.add('Gang med ladning og medtag elektrisk bidrag',f)
        result.symbolic_result={'F':f,'magnitude':sp.sqrt(f.dot(f)),'magnetic_power':sp.simplify(q*cross.dot(vector(v)))}
        result.check('Magnetkraft udfører intet arbejde',q*cross.dot(vector(v)))
    elif kind=='orbit':
        p.assume('nonrelativistic','velocity_perpendicular_B');mass,q,b,vacc=p.require('mass','q','B_magnitude','voltage')
        positive(mass,'Masse');positive(b,'Magnetfeltstyrke');positive(sp.Abs(q),'Ladningsstørrelse');positive(q*vacc,'Kinetisk energi qV')
        velocity=sp.sqrt(2*q*vacc/mass);radius=mass*velocity/(sp.Abs(q)*b)
        result.add('Energibevarelse: qV=mv²/2; isolér hastigheden',velocity)
        result.add('Centripetalbetingelsen giver baneradius',radius)
        result.symbolic_result={'speed':velocity,'radius':sp.simplify(radius),'diameter':sp.simplify(2*radius)}
    else:raise InputError('Lorentz: force eller orbit.')
    result.units={'F':'N','magnitude':'N','magnetic_power':'W','speed':'m/s','radius':'m','diameter':'m'}
    return result


def wire_force(p):
    kind=p.variables.get('kind','path')
    result=solution(p,'Magnetisk kraft på strøm',
        'Kraftbidragene langs den orienterede leder summeres vektorielt. I et homogent felt afhænger integralet af endepunkternes forskydning.',
        [r'd\mathbf F=I\,d\mathbf l\times\mathbf B'], 'Strømmens positive retning er den voksende kurveparameter.')
    if kind=='path':
        i,b=p.require('I','B')
        if 'paths' in p.variables:paths=p.variables['paths']
        else:
            source,u,bounds=p.require('source','parameter','bounds')
            paths=[{'source':source,'parameter':u,'bounds':bounds}]
        f=sp.zeros(3,1)
        for path in paths:
            source,u,bounds=vector(path['source']),path['parameter'],path['bounds']
            field=vector(b)
            if 'field_coordinates' in p.variables:
                field=field.subs(dict(zip(p.variables['field_coordinates'],source)),simultaneous=True)
            integrand=i*source.diff(u).cross(field);result.add('Kraftintegrand langs et orienteret lederstykke',integrand)
            f+=sp.Matrix([finite_integral(v,(u,*bounds)) for v in integrand])
        f=sp.simplify(f)
        result.symbolic_result={'F':f,'magnitude':sp.sqrt(f.dot(f))}
        if 'work_coordinate' in p.variables:
            coord,bounds,tangent=p.require('work_coordinate','work_bounds','displacement_tangent')
            integrand=-f.dot(vector(tangent))
            result.add('Ydre kvasistatisk arbejde = minus integral af magnetkraft langs flytningen',sp.Integral(integrand,(coord,*bounds)))
            result.symbolic_result['W_external']=finite_integral(integrand,(coord,*bounds))
    elif kind=='parallel':
        p.assume('parallel_infinite_wires');i1,i2,d,length=p.require('I1','I2','distance','length');positive(d,'Afstand');positive(length,'Længde')
        b=MU0*i1/(2*sp.pi*d);force=sp.simplify(i2*length*b)
        result.add('Felt fra den første leder',b);result.add('Kraft I₂ L B på den anden leder',force)
        result.symbolic_result={'F_signed_attraction':force}
        result.direction='Positivt resultat er tiltrækning, negativt er frastødning; I1 og I2 refererer til samme aksiale retning.'
    else:raise InputError('Lederkraft: path eller parallel.')
    result.units={'F':'N','magnitude':'N','F_signed_attraction':'N','W_external':'J'}
    return result


def magnetic_material(p):
    kind,=p.require('kind')
    if kind in ('bound_currents','uniform_sphere'):
        from .boundary_models import bound_currents,magnetized_sphere
        return bound_currents(p) if kind=='bound_currents' else magnetized_sphere(p)
    result=solution(p,'Magnetisering og H-felt',
        'Ampères lov for H anvender kun frie strømme. B=μ₀(H+M), mens rotation af M og dens tangentiale spring bestemmer de bundne strømme.',
        [r'\mathbf B=\mu_0(\mathbf H+\mathbf M)',r'\mathbf J_b=\nabla\times\mathbf M',r'\mathbf K_b=\mathbf M\times\hat{\mathbf n}'])
    if kind=='magnetization':
        coords,system,m=p.require('coordinates','system','M');grad,div,curl=calculus(coords,system);m=vector(m)
        if 'H' in p.variables:h=vector(p.variables['H'])
        else:
            p.assume('infinite_axial_symmetry','no_free_current','H_infinity_zero')
            if system!='cylindrical' or m[0]!=0 or m[1]!=0 or m[2].has(coords[1],coords[2]):raise InputError('H=0-reglen kræver aksial M(s) i uendelig cylindersymmetri.')
            h=sp.zeros(3,1)
            result.add('Ingen fri strøm: curl H=0. Aksial symmetri giver konstant H_z; H→0 fastlægger konstanten til nul.',h)
        result.symbolic_result={'H':h,'B':sp.simplify(MU0*(h+m)),'J_bound':curl(m)}
        result.add('Beregn rotationen af magnetiseringen',curl(m))
        if 'normal' in p.variables:
            normal=vector(p.variables['normal'])
            if sp.simplify(normal.dot(normal)-1)!=0:raise InputError('Normalen skal være en enhedsvektor.')
            result.symbolic_result['K_bound']=m.cross(normal).subs(p.variables.get('surface_substitutions',{}))
        result.warnings.append('H skal være angivet fra frie strømme og randbetingelser; H=0 antages aldrig automatisk.')
    elif kind=='magnetic_circuit':
        p.assume('negligible_leakage','uniform_cross_section');n,i,segments=p.require('N','I','segments')
        reluctance_per_area=0
        for length,mu in segments:
            positive(length,'Segmentlængde');positive(mu,'Permeabilitet');reluctance_per_area+=length/mu
        b=sp.simplify(n*i/reluctance_per_area)
        result.add('Ampères lov langs jern og eventuelt luftgab: sum B l/μ = NI',reluctance_per_area)
        result.symbolic_result={'B':b}
        for index,(_,mu) in enumerate(segments):result.symbolic_result[f'H_{index}']=sp.simplify(b/mu)
        result.direction='Langs den valgte positive magnetiske kredsløbsretning.'
    else:raise InputError('Magnetiske materialer: magnetization eller magnetic_circuit.')
    result.units={'H':'A/m','B':'T','J_bound':'A/m^2','K_bound':'A/m'}
    for key in result.symbolic_result:
        if key.startswith('H_'):result.units[key]='A/m'
    return result


def multipole(p):
    charges,=p.require('charges')
    result=solution(p,'Multipoludvikling',
        'Langt fra kilderne organiseres potentialet efter monop ol-, dipol- og eventuelt kvadrupolbidrag. Origo og fjernfeltsbetingelsen angives eksplicit.',
        [r'Q=\sum_iq_i',r'\mathbf p=\sum_iq_i\mathbf r_i',r'V\simeq\frac1{4\pi\epsilon_0}(Q/r+\mathbf p\cdot\hat{\mathbf r}/r^2)'])
    q=sum(q for q,_ in charges);dipole=sum((q*vector(pos) for q,pos in charges),sp.zeros(3,1))
    result.symbolic_result={'Q':q,'dipole':sp.simplify(dipole)}
    result.add('Ladninger vægtes med deres positionsvektorer',dipole)
    if 'r' in p.variables:
        r,theta,phi=p.require('r','theta','phi');positive(r,'Afstand')
        unit=sp.Matrix([sp.sin(theta)*sp.cos(phi),sp.sin(theta)*sp.sin(phi),sp.cos(theta)])
        result.symbolic_result['V_far']=sp.simplify((q/r+dipole.dot(unit)/r**2)/(4*sp.pi*EPS0))
        result.warnings.append('V_far er en approksimation, gyldig når r er meget større end alle kildeafstande fra origo.')
    magnetic_current=p.variables.get('magnetic_current')
    if 'transported_charge' in p.variables:
        charge,period=p.require('transported_charge','period');positive(period,'Omløbsperiode')
        magnetic_current=charge/period
        result.symbolic_result['circulation_current']=sp.simplify(charge/period)
        result.add('Konvektionsstrøm: ladning pr. omløbsperiode',charge/period)
    if magnetic_current is not None:
        area,normal=p.require('area','normal');i=magnetic_current;normal=vector(normal)
        if sp.simplify(normal.dot(normal)-1)!=0:raise InputError('Dipolnormal skal være en enhedsvektor.')
        result.symbolic_result['magnetic_dipole']=i*area*normal
    if 'current_density' in p.variables:
        position,current,jac,bounds=p.require('position','current_density','jacobian','bounds')
        integrand=vector(position).cross(vector(current))*jac/2
        result.add('Magnetisk dipolmoment: en halv integral af r kryds J',integrand)
        result.symbolic_result['magnetic_dipole']=sp.Matrix([finite_integral(v,*bounds) for v in integrand])
    if 'magnetic_field_point' in p.variables:
        p.assume('far_field')
        if 'magnetic_dipole' not in result.symbolic_result:raise InputError('Angiv en magnetisk dipolkilde.')
        pos=vector(p.variables['magnetic_field_point']);distance=sp.sqrt(pos.dot(pos))
        if distance.equals(0):raise InputError('Dipolfeltet er singulært i origo.')
        moment=result.symbolic_result['magnetic_dipole'];unit=pos/distance
        field=MU0*(3*moment.dot(unit)*unit-moment)/(4*sp.pi*distance**3)
        result.symbolic_result['B_magnetic_far']=sp.simplify(field)
        result.add('Indsæt dipolmomentet i fjernfeltsformlen',field)
        result.warnings.append('Magnetisk dipolfelt er en fjernfeltsapproksimation; kildeudstrækningen skal være lille i forhold til afstanden.')
    result.units={'Q':'C','dipole':'C*m','V_far':'V','magnetic_dipole':'A*m^2','B_magnetic_far':'T','circulation_current':'A'}
    return result


def magnetic_dipole_interaction(p):
    result=solution(p,'Magnetisk dipol i et homogent felt',
        'Krydsproduktet giver drejningsmomentets retning. Energien er minus dipolmomentets projektion på magnetfeltet.',
        [r'\boldsymbol\tau=\mathbf m\times\mathbf B',r'U=-\mathbf m\cdot\mathbf B'])
    if 'moment' in p.variables:
        moment,field=p.require('moment','B');moment,field=vector(moment),vector(field)
        torque=moment.cross(field);energy=-moment.dot(field)
        result.add('Indsæt dipol- og feltkomponenter i krydsproduktet',torque)
        result.symbolic_result={'torque':sp.simplify(torque),'U':sp.simplify(energy)}
        dot=sp.simplify(moment.dot(field));cross2=sp.simplify(torque.dot(torque))
        alignment='stable_parallel' if cross2==0 and dot.is_positive else 'unstable_antiparallel' if cross2==0 and dot.is_negative else 'neutral_zero_field_or_moment' if dot==0 and cross2==0 else 'not_equilibrium_or_symbolically_undetermined'
    else:
        magnitude,field,theta=p.require('moment_magnitude','B_magnitude','theta')
        positive(magnitude,'Dipolmomentets størrelse');positive(field,'Magnetfeltets størrelse')
        # The angle is measured from B toward m; +rotation is increasing theta.
        result.symbolic_result={'torque_magnitude':sp.simplify(sp.Abs(magnitude*field*sp.sin(theta))),
            'torque_theta':sp.simplify(-magnitude*field*sp.sin(theta)), 'U':sp.simplify(-magnitude*field*sp.cos(theta))}
        result.add('Projektér momentet på feltet og differentier energien',result.symbolic_result['U'])
        result.check('Moment = minus energiens vinkelafledte',result.symbolic_result['torque_theta']+sp.diff(-magnitude*field*sp.cos(sp.Symbol('_angle')),sp.Symbol('_angle')).subs(sp.Symbol('_angle'),theta))
        angle=sp.simplify(sp.cos(theta));alignment='stable_parallel' if angle==1 else 'unstable_antiparallel' if angle==-1 else 'not_equilibrium_or_symbolically_undetermined'
    result.symbolic_result['alignment']=alignment
    result.units={'torque':'N*m','torque_magnitude':'N*m','torque_theta':'N*m','U':'J'}
    result.direction='Vektormoment følger m kryds B. I vinkelform er torque_theta positiv mod voksende theta. Parallel er energiminimum (stabil); antiparallel er maksimum (labil); vinkelret er normalt ikke ligevægt.'
    return result
