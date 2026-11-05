"""Explicit EV/BA forms over existing solvers. No inferred physical givens."""
MODELS={}
for key,geometry,symmetry,condition,orientation in [
    ('sphere_regions','kugle','sphere','spherical_symmetry','r>0; E og D er signerede radiale komponenter.'),
    ('cylinder_regions','cylinder','cylinder','infinite_cylindrical_symmetry','Uendelig cylinder langs z; s>0; feltet er radialt.'),
    ('plane_regions','plan','plane','infinite_planar_symmetry','Spejlsymmetri om z=0; s=|z|>0. E er på +z-siden; modsatrettet på -z-siden.')]:
    MODELS[key]=dict(domain='EV',family='gauss_radial',geometry=geometry,required=['coordinate','regions'],optional=['surface_charges'],
        fixed={'symmetry':symmetry},assumptions=[condition,'linear_isotropic_medium','vacuum_outside_regions'],orientation=orientation,
        tables={'regions':{'lower':'m','upper':'m','density':'C/m^3','permittivity':'F/m'}})
MODELS['cylinder_regions']['optional'].append('length')
MODELS.update({
 'concentric_conductors':dict(domain='EV',family='conductors',geometry='leder',required=['shells','coordinate','central_charge','gap_permittivities','outside_permittivity'],optional=[],
    assumptions=['concentric_spheres','electrostatic','no_external_sources','potential_zero_infinity','linear_isotropic_medium'],
    orientation='Koncentriske sfæriske ledere; central ladning ligger i centrum. E er radialt; V(infinity)=0. Angiv alle lederladninger og permittiviteter eksplicit.',
    tables={'shells':{'inner':'m','outer':'m','charge':'C'}}),
 'conductor_cavity_totals':dict(domain='EV',family='conductors',required=['enclosed_charge','metal_charge','outer_radius'],optional=[],fixed={'kind':'cavity_totals'},
    assumptions=['electrostatic','closed_conductor','spherical_outer_surface','no_external_sources','vacuum_exterior','potential_zero_infinity'],
    orientation='Kun totale indre/ydre overfladeladninger og lederpotentiale. Lokal ladningsfordeling/felt i et asymmetrisk hulrum bestemmes ikke.'),
 'potential_field':dict(domain='EV',family='field_calculus',required=['V','coordinates','system'],optional=['volume_bounds'],
    assumptions=['electrostatic'],orientation='Komponenter følger den angivne ortonormale koordinatbasis; E=-grad(V).'),
 'electric_field_charge':dict(domain='EV',family='field_calculus',required=['E','coordinates','system'],optional=['volume_bounds'],
    assumptions=['electrostatic','vacuum_medium'],orientation='E-komponenter følger koordinatbasen. rho er samlet lokal volumenladning i et glat område; singulariteter kræver særskilt kontrol.'),
 'potential_difference':dict(domain='EV',family='potential_from_field',required=['field','coordinate','start','end'],optional=['test_charge'],
    assumptions=['electrostatic'],orientation='field er E dot dr/dq langs kurven, inklusive målestok i krumme koordinater. Resultatet er V(end)-V(start), ikke et absolut potentiale.'),
 'ampere_wire':dict(domain='BA',family='ampere',required=['I','distance'],optional=[],fixed={'kind':'wire'},
    assumptions=['infinite_straight_wire','magnetostatic','nonmagnetic_medium'],orientation='Strøm I er signeret langs +z. B er +phi-komponenten ved positiv afstand.'),
 'ampere_regions':dict(domain='BA',family='ampere',geometry='cylinder',required=['coordinate','regions'],optional=['surface_currents'],fixed={'kind':'cylinder'},
    assumptions=['infinite_cylindrical_symmetry','magnetostatic','nonmagnetic_medium'],orientation='Uendelig aksial strøm J_z(s). B er +phi-komponenten; udeladte regioner er strømfri.',
    tables={'regions':{'lower':'m','upper':'m','density':'A/m^2'}}),
 'biot_savart_curve':dict(domain='BA',family='biot_savart',required=['source','parameter','bounds','I','point'],optional=[],evaluate_integrals=True,
    assumptions=['magnetostatic','nonmagnetic_medium'],orientation='Kartesisk kildekurve og feltpunkt. Positiv strøm følger stigende kurveparameter. Endelig/uendelig kilde fastlægges af de eksplicitte grænser.'),
 'vector_potential_field':dict(domain='BA',family='field_calculus',required=['A','coordinates','system'],optional=['time'],
    assumptions=['magnetostatic','nonmagnetic_medium'],orientation='A og B har komponenter i den angivne koordinatbasis. B=curl(A).')
})
UNITS={'V':'V','A':'T*m','field':'V divideret med koordinatenheden, inklusive kurvens målestok','distance':'m','I':'A','point':'m (vektor)',
    'length':'m','volume_bounds':'liste [koordinat,nedre,øvre] med korrekt koordinatenhed',
    'central_charge':'C','enclosed_charge':'C','metal_charge':'C','outer_radius':'m','test_charge':'C',
    'gap_permittivities':'F/m (liste)','outside_permittivity':'F/m','coordinates':'koordinatnavne (liste)',
    'system':'cartesian / cylindrical / spherical','start':'enhed som koordinaten','end':'enhed som koordinaten',
    'surface_charges':'liste [radius, signeret overfladeladning]','surface_currents':'liste [radius, signeret overfladestrøm]'}

# Boundary geometry and material definitions use the same registered kernels.
charge_table={'charge':'C','x':'m','y':'m','z':'m'}
for key,kind,required,assumptions,orientation in [
 ('image_plane','grounded_plane',['normal','offset'],['grounded_infinite_plane','vacuum_medium','electrostatic'],
  'Planet er normal dot r=offset. Normalen er enhedsvektor ind i det fysiske halvrum. Alle virkelige ladninger og feltpunktet ligger i dette halvrum.'),
 ('image_sphere_grounded','grounded_sphere',['center','radius'],['grounded_sphere','vacuum_medium','electrostatic','no_other_external_sources'],
  'Jordet kugle med angivet centrum og radius; alle virkelige ladninger og feltpunktet er udenfor. V=0 på kuglen og i det uendelige.'),
 ('image_sphere_isolated','isolated_sphere',['center','radius','sphere_charge'],['isolated_conducting_sphere','vacuum_medium','electrostatic','no_other_external_sources'],
  'Isoleret sfærisk leder med eksplicit nettoladning (0 for neutral), ikke jordet. Kilder og feltpunkt er udenfor; V(infinity)=0.')]:
    MODELS[key]=dict(domain='EV',family='images',required=['charges']+required,optional=['point']+(['surface_point'] if kind=='grounded_plane' else []),fixed={'kind':kind},
        assumptions=assumptions,orientation=orientation,tables={'charges':charge_table})
MODELS['magnetization_currents']=dict(domain='BA',family='magnetic_material',required=['M','coordinates','system','normal'],optional=['surface_coordinate','surface_value','H'],fixed={'kind':'bound_currents'},
    assumptions=['magnetostatic'],orientation='M og normal har komponenter i samme ortonormale basis. Normalen peger ud af materialet. J_b er bulkstrømmen; K_b gælder den valgte flade. H/B beregnes kun hvis H er givet.')
MODELS['magnetized_sphere']=dict(domain='BA',family='magnetic_material',required=['M','radius','center'],optional=['point','normal'],fixed={'kind':'uniform_sphere'},
    assumptions=['uniform_magnetization','spherical_body','no_free_current','no_applied_field','vacuum_exterior'],
    orientation='Foreskrevet konstant M i kartesisk basis i kuglen. K_bound vises på overfladen; uden angivet normal bruges theta_surface og phi_surface. B(point) er regionalt inde/ude.')
MODELS['point_superposition']=dict(domain='EV',family='point_charges',required=['charges'],optional=['point','test_charge'],
    assumptions=['electrostatic','vacuum_medium','distinct_point_sources'],orientation='Kartesiske positioner og signerede ladninger. F er kraft på en separat testladning i feltpunktet, ikke et selvfelt.',tables={'charges':charge_table})
MODELS['magnetic_wires']=dict(domain='BA',family='magnetic_superposition',required=['wires','point'],optional=[],
    assumptions=['parallel_infinite_sources','magnetostatic','nonmagnetic_medium'],orientation='Parallelle uendelige ledere langs z ved de givne (x,y). Strøm er signeret langs +z; felterne summeres vektorielt.',tables={'wires':{'I':'A','x':'m','y':'m'}})
MODELS['magnetic_cylinders']=dict(domain='BA',family='magnetic_superposition',required=['cylinders','point'],optional=[],
    assumptions=['parallel_infinite_sources','magnetostatic','nonmagnetic_medium'],orientation='Uendelige parallelle cylindre med uniform signeret J_z pr. cylinder; negativt J kan repræsentere et hulrum ved superposition.',tables={'cylinders':{'J':'A/m^2','radius':'m','x':'m','y':'m'}})
MODELS['RL_driven']=dict(domain='DYN',family='rc_transient',required=['time','R','L','voltage','I0'],optional=[],fixed={'kind':'RL_general'},
    assumptions=['constant_coefficients'],orientation='L*dI/dt+R*I=V(t), I(0)=I0. R og L er konstante; den eksplicit givne spænding må afhænge af tiden.')
MODELS['RC_driven']=dict(domain='DYN',family='rc_transient',required=['time','R','C','voltage','Q0'],optional=[],fixed={'kind':'RC_general'},
    assumptions=['constant_coefficients'],orientation='R*dQ/dt+Q/C=V(t), Q(0)=Q0. I=dQ/dt er positiv opladningsstrøm; dette er modsat I i det gamle RC-afladningskort.')
UNITS.update({'normal':'1 (enhedsvektor)','offset':'m','center':'m (vektor)','radius':'m','sphere_charge':'C','surface_point':'m (vektor)',
    'M':'A/m (vektor)','H':'A/m (vektor)','surface_coordinate':'koordinatnavn','surface_value':'samme enhed som overfladekoordinaten'})
