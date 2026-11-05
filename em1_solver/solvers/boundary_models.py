"""Boundary-value geometry rules, superposition, and bound-current definitions.

No exam IDs, numerical answers or fitted problem-specific formulas.
"""
import sympy as sp
from ..core.problem import InputError
from ..core.solution import solution
from ..core.validation import EPS0,MU0,vector,positive,calculus
from ..core.units import si


def _numeric(p):
    return {k:sp.Float(str(si(v,p.numerical_units[k]).magnitude)) for k,v in p.numerical_values.items()}


def _positive(value,p,label):
    value=sp.simplify(value);sample=sp.simplify(value.subs(_numeric(p)))
    if sample.is_nonpositive is True:raise InputError(label+' skal være positiv.')
    if value.is_positive is not True and sample.is_positive is not True:
        # It is a declared domain restriction, never a guessed numeric value.
        return label+': '+str(value)+' > 0'
    return None


def _field(charges,point,p):
    e=sp.zeros(3,1);v=sp.S.Zero
    for q,position in charges:
        delta=point-vector(position);distance2=sp.simplify(delta.dot(delta))
        if distance2.equals(0) or sp.simplify(distance2.subs(_numeric(p))).equals(0):raise InputError('Feltpunkt sammenfalder med en kilde; selvfeltet er singulært.')
        v+=q/(4*sp.pi*EPS0*sp.sqrt(distance2));e+=q*delta/(4*sp.pi*EPS0*distance2**sp.Rational(3,2))
    return sp.simplify(v),sp.simplify(e)


def image_boundary(p):
    kind,charges=p.require('kind','charges')
    if not isinstance(charges,list) or not 1<=len(charges)<=8:raise InputError('Angiv 1–8 virkelige punktladninger.')
    real=[(q,vector(pos)) for q,pos in charges]
    if any(not sp.sympify(q).is_real for q,_ in real):raise InputError('Ladninger skal være reelle.')
    for i,(_,pos) in enumerate(real):
        for _,other in real[:i]:
            d=pos-other
            if sp.simplify(d.dot(d)).equals(0) or sp.simplify(d.dot(d).subs(_numeric(p))).equals(0):raise InputError('To virkelige ladninger falder sammen.')
    result=solution(p,'Billedladninger, Coulomb-superposition og entydighed',
        'Hjælpeladninger konstrueres så lederens randbetingelse opfyldes. I det specificerede fysiske område giver entydighedssætningen den elektrostatiske løsning. Selvfeltet udelades ved kraft på en virkelig ladning.',
        [r'V=\sum_i\frac{q_i}{4\pi\epsilon_0|\mathbf r-\mathbf r_i|}',r'\mathbf E=-\nabla V',r'\mathbf F_i=q_i\mathbf E_{andre}(\mathbf r_i)'])
    images=[];conditions=[]
    if kind=='grounded_plane':
        normal,offset=p.require('normal','offset');normal=vector(normal)
        if sp.simplify(normal.dot(normal)-1)!=0:raise InputError('Planets normal skal være en enhedsvektor.')
        result.add('Planets ligning er n dot r = h; spejl positionen normalt til planet',sp.Eq(sp.Symbol('n_dot_r'),offset))
        for q,pos in real:
            height=sp.simplify(normal.dot(pos)-offset)
            restriction=_positive(height,p,'Kilden skal være i det valgte fysiske halvrum')
            if restriction:conditions.append(restriction)
            mirror=sp.simplify(pos-2*height*normal);images.append((-q,mirror))
            result.add('Spejlladning og position',sp.Tuple(-q,*mirror),law='Spejling i et jordet plan')
            w=sp.Matrix(sp.symbols('boundary_x boundary_y boundary_z',real=True));surface=w-(normal.dot(w)-offset)*normal
            result.check('Lige kildeafstande på lederplanet',sp.expand((surface-pos).dot(surface-pos)-(surface-mirror).dot(surface-mirror)))
            result.check('Modsat ladning sikrer V=0 på planet',q+images[-1][0])
        induced=-sum(q for q,_ in real)
        if 'point' in p.variables:
            restriction=_positive(normal.dot(vector(p.variables['point']))-offset,p,'Feltpunktet skal være i det fysiske halvrum')
            if restriction:conditions.append(restriction)
        if 'surface_point' in p.variables:
            surface=vector(p.variables['surface_point'])
            if sp.simplify(normal.dot(surface)-offset)!=0:raise InputError('Overfladepunktet ligger ikke på planet.')
            sigma=0
            for q,pos in real:
                h=normal.dot(pos)-offset;delta=surface-pos
                sigma-=q*h/(2*sp.pi*delta.dot(delta)**sp.Rational(3,2))
            result.symbolic_result['sigma_induced']=sp.simplify(sigma);result.units['sigma_induced']='C/m^2'
    elif kind in ('grounded_sphere','isolated_sphere'):
        center,radius=p.require('center','radius');center=vector(center)
        restriction=_positive(radius,p,'Kugleradius')
        if restriction:conditions.append(restriction)
        theta,phi=sp.symbols('boundary_theta boundary_phi',real=True)
        unit=sp.Matrix([sp.sin(theta)*sp.cos(phi),sp.sin(theta)*sp.sin(phi),sp.cos(theta)])
        boundary=center+radius*unit
        for q,pos in real:
            delta=pos-center;d2=sp.simplify(delta.dot(delta));d=sp.sqrt(d2)
            restriction=_positive(d-radius,p,'Virkelig kilde skal være uden for kuglen')
            if restriction:conditions.append(restriction)
            if d2.equals(0):raise InputError('Ekstern kilde kan ikke ligge i kuglecentrum.')
            mirror=center+radius**2*delta/d2;iq=-radius*q/d
            images.append((iq,mirror));result.add('Sfærisk billedladning og placering',sp.Tuple(iq,*mirror),law='Kuglens konstante potentiale')
            result.check('Sfærisk rand: de skalerede afstande er ens',sp.trigsimp(sp.expand((boundary-mirror).dot(boundary-mirror)-radius**2/d2*(boundary-pos).dot(boundary-pos))))
            result.check('Kilde og billede annullerer randpotentialet',sp.simplify(q+iq*d/radius))
        if kind=='isolated_sphere':
            total,=p.require('sphere_charge');central=sp.simplify(total-sum(q for q,_ in images))
            images.append((central,center));induced=total
            result.symbolic_result['V_sphere']=sp.simplify(central/(4*sp.pi*EPS0*radius));result.units['V_sphere']='V'
            result.add('Isoleret kugle: central hjælpeladning sikrer den givne nettoladning',central)
            result.check('Kuglens givne nettoladning',sum(q for q,_ in images)-total)
        else:induced=sp.simplify(sum(q for q,_ in images));result.symbolic_result['V_sphere']=sp.S.Zero;result.units['V_sphere']='V'
        if 'point' in p.variables:
            point_delta=vector(p.variables['point'])-center
            restriction=_positive(sp.sqrt(point_delta.dot(point_delta))-radius,p,'Feltpunktet skal være uden for kuglen')
            if restriction:conditions.append(restriction)
    else:raise InputError('Ukendt billedladningsgeometri.')
    if 'point' in p.variables:
        potential,field=_field(real+images,vector(p.variables['point']),p)
        result.symbolic_result.update(V=potential,E=field);result.units.update(V='V',E='V/m')
        result.add('Summér potentiale og felt fra virkelige kilder og hjælpekilder',sp.Tuple(potential,*field))
    forces=[]
    for i,(q,pos) in enumerate(real):
        _,field=_field(real[:i]+real[i+1:]+images,pos,p);forces.append(sp.simplify(q*field))
    result.symbolic_result['forces']=sp.Matrix.hstack(*forces);result.units['forces']='N'
    if len(forces)==1:result.symbolic_result['F']=forces[0];result.units['F']='N'
    result.symbolic_result['Q_conductor']=induced;result.units['Q_conductor']='C'
    result.symbolic_result['Q_induced']=sp.S.Zero if kind=='isolated_sphere' else induced;result.units['Q_induced']='C'
    if kind=='isolated_sphere':result.warnings.append('Q_conductor er kuglens givne nettoladning; Q_induced er ændringen i nettoladning og er nul for en isoleret kugle. Omfordelingen kan lokalt være forskellig fra nul.')
    result.add('Kraft på virkelige ladninger uden deres selvfelt',result.symbolic_result['forces'])
    result.direction='Kartesiske komponenter. Kraftkolonner følger de virkelige ladningers rækkefølge; hjælpeladninger er ikke fysiske kilder.'
    result.warnings += conditions
    result.warnings.append('Parenergien af virkelige og fiktive ladninger er ikke den fysiske energi og returneres ikke. Formlerne gælder kun i det deklarerede fysiske område.')
    return result


def bound_currents(p):
    coordinates,system,m,normal=p.require('coordinates','system','M','normal');m=vector(m);normal=vector(normal)
    if sp.simplify(normal.dot(normal)-1)!=0:raise InputError('Overfladenormalen skal være en enhedsvektor i den angivne basis.')
    grad,div,curl=calculus(coordinates,system)
    result=solution(p,'Magnetiseringens bundne strømme',
        'Rotationen af magnetiseringen giver volumenstrømmen. Magnetiseringens tangentiale spring ved grænsen giver overfladestrømmen. M alene bestemmer ikke generelt H eller B.',
        [r'\mathbf J_b=\nabla\times\mathbf M',r'\mathbf K_b=\mathbf M\times\hat{\mathbf n}',r'\mathbf B=\mu_0(\mathbf H+\mathbf M)'])
    current=sp.simplify(curl(m));surface=sp.simplify(m.cross(normal))
    if 'surface_coordinate' in p.variables or 'surface_value' in p.variables:
        coordinate,value=p.require('surface_coordinate','surface_value')
        if coordinate not in coordinates:raise InputError('Overfladekoordinaten skal være en af de angivne koordinater.')
        surface=surface.subs(coordinate,value)
    result.symbolic_result.update(J_bound=current,K_bound=surface);result.units.update(J_bound='A/m^2',K_bound='A/m')
    result.add('Beregn curl(M) med koordinatsystemets korrekte målestokke',current)
    result.add('Beregn M kryds den udadrettede enhedsnormal på fladen',surface)
    result.check('Bundne volumenstrømmes kontinuitet i glatte områder',div(current))
    result.check('Overfladestrømmen er tangentiel',sp.simplify(normal.dot(m.cross(normal))))
    if 'H' in p.variables:
        h=vector(p.variables['H']);b=sp.simplify(MU0*(h+m))
        result.symbolic_result.update(H=h,B=b);result.units.update(H='A/m',B='T')
        result.add('Brug det eksplicit givne H i materialerelationen',b)
        result.check('Magnetisk divergens for det givne H og M',div(b))
    else:result.warnings.append('H og B bestemmes ikke af M alene uden yderligere geometri, frie strømme og randbetingelser.')
    result.direction='Komponenterne følger den angivne ortonormale koordinatbasis. Normalen skal pege ud af det magnetiserede materiale.'
    return result


def magnetized_sphere(p):
    m,radius,center=p.require('M','radius','center');m=vector(m);center=vector(center);positive(radius,'Kugleradius')
    if any(sym.name in ('x','y','z') for component in m for sym in component.free_symbols):raise InputError('Kuglemodellen kræver rumligt uniform magnetisering.')
    result=solution(p,'Magnetiseret kugle fra randbetingelser og entydighed',
        'Uniform magnetisering har nul volumen-curl. Symmetrien tillader konstant indre H og et ydre dipolfelt. Kontinuitet af normal B og tangentiel H uden fri overfladestrøm bestemmer koefficienterne.',
        [r'\mathbf J_b=\nabla\times\mathbf M=0',r'\mathbf K_b=\mathbf M\times\hat{\mathbf n}',r'B_{n,in}=B_{n,out}',r'H_{t,in}=H_{t,out}'])
    c,d=sp.symbols('H_factor moment_factor',real=True)
    equations=[sp.Eq(1+c,2*d/(4*sp.pi*radius**3)),sp.Eq(c,-d/(4*sp.pi*radius**3))]
    result.add('Randbetingelser for normal B og tangentiel H',sp.Tuple(*equations))
    coefficients=sp.solve(equations,[c,d],dict=True)[0]
    h=sp.simplify(coefficients[c]*m);b=sp.simplify(MU0*(h+m));moment=sp.simplify(coefficients[d]*m)
    if 'normal' in p.variables:normal=vector(p.variables['normal'])
    else:
        theta,phi=sp.symbols('theta_surface phi_surface',real=True);p.symbol_units.update({theta:'1',phi:'1'})
        normal=sp.Matrix([sp.sin(theta)*sp.cos(phi),sp.sin(theta)*sp.sin(phi),sp.cos(theta)])
    if sp.simplify(normal.dot(normal)-1)!=0:raise InputError('Normalen skal være enhedsnormal på kuglefladen.')
    surface=sp.simplify(m.cross(normal))
    result.symbolic_result.update(B_inside=b,H_inside=h,J_bound=sp.zeros(3,1),K_bound=surface,dipole=moment)
    result.units.update(B_inside='T',H_inside='A/m',J_bound='A/m^2',K_bound='A/m',dipole='A*m^2')
    result.add('Løs randligningerne og indsæt i H og B',sp.Tuple(*h,*b))
    result.add('Beregn det ydre dipolmoment fra samme randløsning',moment)
    result.add('Overfladestrøm på den sfæriske flade',surface)
    result.check('Normal B-kontinuitet',sp.simplify((1+coefficients[c])-2*coefficients[d]/(4*sp.pi*radius**3)))
    result.check('Tangentiel H-kontinuitet',sp.simplify(coefficients[c]+coefficients[d]/(4*sp.pi*radius**3)))
    result.check('K_bound dot n = 0',sp.simplify(surface.dot(normal)))
    if 'point' in p.variables:
        delta=vector(p.variables['point'])-center;r2=sp.simplify(delta.dot(delta))
        if r2.equals(0):field=b
        else:
            outside=sp.simplify(MU0/(4*sp.pi)*(3*delta*moment.dot(delta)/r2**sp.Rational(5,2)-moment/r2**sp.Rational(3,2)))
            field=sp.Matrix([sp.Piecewise((inner,r2<radius**2),(outer,True)) for inner,outer in zip(b,outside)])
        result.symbolic_result['B']=field;result.units['B']='T';result.add('Evaluér den regionale indre/ydre løsning i det givne punkt',field)
    result.direction='Kartesiske komponenter. Indre B er parallel med M; ydre B er dipolfeltet. Punktværdien præcis på en strømførende grænse er ensidig.'
    result.warnings.append('Kun uniform foreskrevet M i en sfære, ingen frie strømme eller påtrykte ydre felter. Vinkelparametrene theta_surface og phi_surface beskriver normalretningen, hvis normal ikke angives.')
    return result
