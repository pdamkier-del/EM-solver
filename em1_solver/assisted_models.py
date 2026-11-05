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
    assumptions=['electrostatic','vacuum_medium'],orientation='Komponenter følger den angivne ortonormale koordinatbasis; E=-grad(V).'),
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
