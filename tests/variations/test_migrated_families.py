"""Additional independent physical checks only for concrete certification gaps."""
import pytest
import sympy as s
from em1_solver import Problem,Region,solve,InputError
from em1_solver.core.validation import EPS0 as eps,MU0 as mu,regional_limit
from em1_solver.core.dimensions import check_solution
x,y,z,t,phi,theta=s.symbols('x y z t phi theta',real=True)
r,a,b,d,L,q,Q,I,J,V,B,k=s.symbols('r a b d L q Q I J V B k',positive=True)
U={x:'m',y:'m',z:'m',r:'m',a:'m',b:'m',d:'m',L:'m',q:'C',Q:'C',I:'A',J:'A/m^2',V:'V',B:'T',k:'1',t:'s',phi:'1',theta:'1'}
def eq(a,b):
 v=s.simplify(s.expand(a-b));assert all(w.equals(0) for w in v) if isinstance(v,s.MatrixBase) else v.equals(0)
def dims(o):
 assert check_solution(o,U) or not any('inconsistency' in w for w in o.warnings),o.warnings

@pytest.mark.variation(family='ampere')
@pytest.mark.parametrize('sign',[-1,1])
def test_ampere_boundary_direction_and_axis_limits(sign):
 out=solve(Problem('BA','ampere',variables={'kind':'cylinder','coordinate':r},regions=[Region(0,a,sign*J)],assumptions=['infinite_cylindrical_symmetry','magnetostatic'],symbol_units=U))
 eq(regional_limit(out.symbolic_result['B'],r,a,'-'),sign*mu*J*a/2)
 eq(regional_limit(out.symbolic_result['B'],r,a,'+'),sign*mu*J*a/2)
 eq(regional_limit(out.symbolic_result['B'],r,0,'+'),0)

@pytest.mark.variation(family='ampere')
def test_ampere_invalid_symmetry_and_angular_density():
 with pytest.raises(InputError):solve(Problem('BA','ampere',variables={'kind':'cylinder','coordinate':r},regions=[Region(0,a,J)]))
 with pytest.raises(InputError):solve(Problem('BA','ampere',variables={'kind':'cylinder','coordinate':r},regions=[Region(0,a,J*s.cos(phi))],assumptions=['infinite_cylindrical_symmetry','magnetostatic']))

@pytest.mark.variation(family='faraday')
def test_faraday_resistive_energy_and_reversed_normal():
 tau=s.Symbol('tau',positive=True)
 for sign in [-1,1]:
  o=solve(Problem('DYN','faraday',variables={'time':t,'flux':sign*B*a*a*s.exp(-t/tau),'R':b,'time_bounds':[0,s.oo]},assumptions=['negligible_self_inductance'],symbol_units=U|{b:'ohm',tau:'s'}))
  eq(o.symbolic_result['W'],B*B*a**4/(2*b*tau));eq(o.symbolic_result['I'],sign*B*a*a*s.exp(-t/tau)/(b*tau))
  assert all(c.passed for c in o.checks)

@pytest.mark.variation(family='point_charges')
@pytest.mark.parametrize('sign,scale',[(-1,1),(1,1),(1,3)])
def test_point_superposition_energy_and_charge_scaling(sign,scale):
 o=solve(Problem('EV','point_charges',variables={'charges':[(sign*scale*q,[-a,0,0]),(sign*scale*q,[a,0,0])],'point':[0,0,0]},symbol_units=U))
 eq(o.symbolic_result['E'],s.zeros(3,1));eq(o.symbolic_result['V'],sign*scale*q/(2*s.pi*eps*a))
 eq(o.symbolic_result['U'],scale**2*q*q/(8*s.pi*eps*a))

@pytest.mark.variation(family='point_charges')
def test_point_singular_and_invalid_index_rejected():
 with pytest.raises(InputError):solve(Problem('EV','point_charges',variables={'charges':[(q,[0,0,0])],'point':[0,0,0]}))
 with pytest.raises(InputError):solve(Problem('EV','point_charges',variables={'charges':[(q,[0,0,0])],'force_on_index':4}))

@pytest.mark.variation(family='field_calculus')
@pytest.mark.parametrize('system,coordinates,potential,expected',[
 ('cartesian',[x,y,z],V*x/a,[-V/a,0,0]),
 ('cylindrical',[r,phi,z],V*r*r/a**2,[-2*V*r/a**2,0,0]),
 ('spherical',[r,theta,phi],V/r*a,[V*a/r**2,0,0])])
def test_field_curvilinear_gradient_consistency(system,coordinates,potential,expected):
 o=solve(Problem('EV','field_calculus',variables={'coordinates':coordinates,'system':system,'V':potential},assumptions=['electrostatic'],symbol_units=U))
 eq(o.symbolic_result['E'],s.Matrix(expected));eq(o.symbolic_result['curl_E'],s.zeros(3,1))
 assert all(c.passed for c in o.checks)

@pytest.mark.variation(family='field_calculus')
def test_field_invalid_contradictory_potential_rejected():
 with pytest.raises(InputError):solve(Problem('EV','field_calculus',variables={'coordinates':[x,y,z],'system':'cartesian','V':V*x/a,'E':[V/a,0,0]}))

@pytest.mark.variation(family='conductors')
@pytest.mark.parametrize('charge',[-q,0,q])
def test_conductor_regions_total_charge_and_potential_continuity(charge):
 o=solve(Problem('EV','conductors',variables={'coordinate':r,'shells':[(0,a,Q),(a+b,a+b+d,charge)]},assumptions=['concentric_spheres','electrostatic'],symbol_units=U))
 eq(o.symbolic_result['E'].subs(r,a/2),0);eq(o.symbolic_result['E'].subs(r,a+b+d/2),0)
 eq(sum(v[1] for v in o.symbolic_result['surfaces']),Q+charge)
 eq(regional_limit(o.symbolic_result['V'],r,a+b,'-'),regional_limit(o.symbolic_result['V'],r,a+b,'+'))
 eq(-s.diff(o.symbolic_result['V'],r).subs(r,a+b+d+L),o.symbolic_result['E'].subs(r,a+b+d+L))

@pytest.mark.variation(family='conductors')
@pytest.mark.parametrize('er',[1,2,7])
def test_conductor_boundary_free_and_bound_charges(er):
 o=solve(Problem('EV','conductors',variables={'kind':'boundary','normal':[1,0,0],'E_inside':[0,0,0],'E_outside':[V/a,0,0],'epsilon_inside':eps,'epsilon_outside':er*eps},symbol_units=U))
 eq(o.symbolic_result['sigma_free'],er*eps*V/a);eq(o.symbolic_result['sigma_bound'],(1-er)*eps*V/a)

@pytest.mark.variation(family='conductors')
def test_conductor_invalid_shell_order_and_normal_rejected():
 with pytest.raises(InputError):solve(Problem('EV','conductors',variables={'coordinate':r,'shells':[(a,0,Q)]},assumptions=['concentric_spheres','electrostatic']))
 with pytest.raises(InputError):solve(Problem('EV','conductors',variables={'kind':'boundary','normal':[2,0,0],'E_inside':[0,0,0],'E_outside':[V/a,0,0],'epsilon_inside':eps,'epsilon_outside':eps}))

@pytest.mark.variation(family='magnetic_superposition')
@pytest.mark.parametrize('height',[0,a/4,-a/4])
def test_magnetic_cavity_offset_invariance(height):
 o=solve(Problem('BA','magnetic_superposition',variables={'point':[0,height,0],'sources':[{'kind':'cylinder','center':[-d,0,0],'radius':d+a,'J':J},{'kind':'cylinder','center':[d,0,0],'radius':d+a,'J':-J}]},assumptions=['parallel_infinite_sources','magnetostatic'],symbol_units=U))
 eq(o.symbolic_result['B'],s.Matrix([0,mu*J*d,0]))

@pytest.mark.variation(family='magnetic_superposition')
def test_magnetic_superposition_exact_cancellation():
 sources=[{'kind':'cylinder','center':[0,0,0],'radius':a,'J':sgn*J} for sgn in [-1,1]]
 for point in ([a/2,0,0],[2*a,0,0]):
  o=solve(Problem('BA','magnetic_superposition',variables={'point':point,'sources':sources},assumptions=['parallel_infinite_sources','magnetostatic'],symbol_units=U));eq(o.symbolic_result['B'],s.zeros(3,1))

@pytest.mark.variation(family='magnetic_superposition')
def test_magnetic_wire_direction_and_radial_decay():
 o=solve(Problem('BA','magnetic_superposition',variables={'point':[a,0,0],'sources':[{'kind':'wire','center':[0,0,0],'I':I}]},assumptions=['parallel_infinite_sources','magnetostatic'],symbol_units=U))
 eq(o.symbolic_result['B'],s.Matrix([0,mu*I/(2*s.pi*a),0]))

@pytest.mark.variation(family='magnetic_superposition')
def test_magnetic_singular_wire_rejected():
 with pytest.raises(InputError):solve(Problem('BA','magnetic_superposition',variables={'point':[0,0,0],'sources':[{'kind':'wire','center':[0,0,0],'I':I}]},assumptions=['parallel_infinite_sources','magnetostatic']))

@pytest.mark.variation(family='coulomb_integral')
@pytest.mark.parametrize('sign',[-1,1])
def test_continuous_full_ring_symmetry_and_potential(sign):
 o=solve(Problem('EV','coulomb_integral',variables={'kind':'line','source':[a*s.cos(phi),a*s.sin(phi),0],'parameters':[phi],'bounds':[[0,2*s.pi]],'density':sign*q/(2*s.pi*a),'point':[0,0,0]},symbol_units=U))
 eq(o.symbolic_result['E'],s.zeros(3,1));eq(o.symbolic_result['V'],sign*q/(4*s.pi*eps*a));eq(o.symbolic_result['Q'],sign*q)

@pytest.mark.variation(family='coulomb_integral')
@pytest.mark.parametrize('radius',[a,2*a])
def test_continuous_sphere_shell_inside_and_far_scaling(radius):
 o=solve(Problem('EV','coulomb_integral',variables={'kind':'surface','source':[radius*s.sin(theta)*s.cos(phi),radius*s.sin(theta)*s.sin(phi),radius*s.cos(theta)],'parameters':[theta,phi],'bounds':[[0,s.pi],[0,2*s.pi]],'density':q/(4*s.pi*radius**2),'point':[0,0,0]},symbol_units=U))
 eq(o.symbolic_result['E'],s.zeros(3,1));eq(o.symbolic_result['V'],q/(4*s.pi*eps*radius))

@pytest.mark.variation(family='coulomb_integral')
def test_continuous_line_midpoint_symmetry():
 o=solve(Problem('EV','coulomb_integral',variables={'kind':'line','source':[x,0,0],'parameters':[x],'bounds':[[-a,a]],'density':q/(2*a),'point':[0,b,0]},symbol_units=U))
 eq(o.symbolic_result['E'][0],0);eq(o.symbolic_result['E'][2],0)
 eq(o.symbolic_result['E'][1],q/(4*s.pi*eps*b*s.sqrt(a*a+b*b)))

@pytest.mark.variation(family='coulomb_integral')
def test_continuous_invalid_parameterization_rejected():
 with pytest.raises(InputError):solve(Problem('EV','coulomb_integral',variables={'kind':'surface','source':[x,0,0],'parameters':[x],'bounds':[[0,a]],'density':q/a**2,'point':[0,b,0]}))

@pytest.mark.variation(family='potential_from_field')
@pytest.mark.parametrize('power',[0,1,2])
def test_potential_reference_and_reverse_path(power):
 c=s.Symbol('coefficient',positive=True)
 for start,end,sign in [(0,a,1),(a,0,-1)]:
  o=solve(Problem('EV','potential_from_field',variables={'coordinate':x,'field':c*x**power,'start':start,'end':end},symbol_units=U|{c:f'V/m^{power+1}'}))
  eq(o.symbolic_result['delta_V'],-sign*c*a**(power+1)/(power+1))

@pytest.mark.variation(family='potential_from_field')
def test_potential_divergent_reference_rejected():
 with pytest.raises(InputError):solve(Problem('EV','potential_from_field',variables={'coordinate':r,'field':V/r,'start':0,'end':a}))

@pytest.mark.variation(family='algebra')
@pytest.mark.parametrize('sign',[-1,1])
def test_algebra_vector_superposition_and_energy_units(sign):
 o=solve(Problem('BA','algebra',variables={'outputs':{'B_total':s.Matrix([B,0,0])+sign*s.Matrix([B,0,0])},'output_units':{'B_total':'T'}},symbol_units=U))
 eq(o.symbolic_result['B_total'],s.Matrix([(1+sign)*B,0,0]))

@pytest.mark.variation(family='algebra')
def test_algebra_missing_units_rejected():
 with pytest.raises(InputError):solve(Problem('EV','algebra',variables={'outputs':{'E':V/a},'output_units':{}}))

@pytest.mark.variation(family='gauss_radial')
@pytest.mark.parametrize('power',[0,2])
def test_gauss_sphere_boundary_scaling(power):
 coeff=s.Symbol('rho_coeff',positive=True)
 o=solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'sphere'},regions=[Region(0,a,coeff*r**power)],assumptions=['spherical_symmetry'],symbol_units=U|{coeff:f'C/m^{3+power}'}))
 eq(o.symbolic_result['E'].subs(r,a/2),coeff*(a/2)**(power+1)/(eps*(power+3)))
 eq(regional_limit(o.symbolic_result['E'],r,a,'-'),regional_limit(o.symbolic_result['E'],r,a,'+'))

@pytest.mark.variation(family='gauss_radial')
def test_gauss_invalid_angular_density_rejected():
 with pytest.raises(InputError):solve(Problem('EV','gauss_radial',variables={'coordinate':r,'symmetry':'sphere'},regions=[Region(0,a,q/a**3*s.cos(theta))],assumptions=['spherical_symmetry']))

@pytest.mark.variation(family='coulomb_integral')
def test_continuous_uniform_volume_sphere_center():
 o=solve(Problem('EV','coulomb_integral',variables={'kind':'volume','source':[r*s.sin(theta)*s.cos(phi),r*s.sin(theta)*s.sin(phi),r*s.cos(theta)],'parameters':[r,theta,phi],'bounds':[[0,a],[0,s.pi],[0,2*s.pi]],'density':3*q/(4*s.pi*a**3),'point':[0,0,0]},symbol_units=U))
 eq(o.symbolic_result['Q'],q);eq(o.symbolic_result['E'],s.zeros(3,1));eq(o.symbolic_result['V'],3*q/(8*s.pi*eps*a))

@pytest.mark.variation(family='wire_force')
@pytest.mark.parametrize('sign',[-1,1])
def test_wire_orientation_and_endpoint_force(sign):
 o=solve(Problem('BA','wire_force',variables={'source':[a*s.cos(theta),a*s.sin(theta),0],'parameter':theta,'bounds':[0,sign*s.pi],'I':I,'B':[0,0,B]},symbol_units=U))
 # Both half-circles have the same displacement (-2a,0,0).
 eq(o.symbolic_result['F'],s.Matrix([0,2*I*a*B,0]))

@pytest.mark.variation(family='wire_force')
def test_closed_wire_uniform_field_cancellation():
 o=solve(Problem('BA','wire_force',variables={'source':[a*s.cos(theta),a*s.sin(theta),0],'parameter':theta,'bounds':[0,2*s.pi],'I':I,'B':[0,0,B]},symbol_units=U))
 eq(o.symbolic_result['F'],s.zeros(3,1))

@pytest.mark.variation(family='wire_force')
def test_wire_invalid_distance_rejected():
 with pytest.raises(InputError):solve(Problem('BA','wire_force',variables={'kind':'parallel','I1':I,'I2':-I,'distance':0,'length':a},assumptions=['parallel_infinite_wires']))

@pytest.mark.variation(family='motional_emf')
@pytest.mark.parametrize('sign',[-1,1])
def test_motional_translation_Lenz_and_power(sign):
 v=s.Symbol('v',positive=True);res=s.Symbol('resistance',positive=True)
 o=solve(Problem('DYN','motional_emf',variables={'source':[0,r,0],'parameter':r,'bounds':[0,a],'v':[sign*v,0,0],'B':[0,0,B],'time':t,'R':res},assumptions=['negligible_self_inductance','stationary_return_path'],symbol_units=U|{v:'m/s',res:'ohm'}))
 eq(o.symbolic_result['EMF'],-sign*B*a*v);eq(o.symbolic_result['F_external'][0],sign*B*B*a*a*v/res)
 assert all(c.passed for c in o.checks)

@pytest.mark.variation(family='motional_emf')
def test_motional_rotating_rod_integrated_power():
 omega,res=s.symbols('omega res',positive=True)
 o=solve(Problem('DYN','motional_emf',variables={'source':[r,0,0],'parameter':r,'bounds':[0,a],'v':[0,omega*r,0],'B':[0,0,B],'time':t,'R':res},assumptions=['negligible_self_inductance','stationary_return_path'],symbol_units=U|{omega:'1/s',res:'ohm'}))
 eq(o.symbolic_result['EMF'],B*omega*a*a/2);eq(o.symbolic_result['P_mechanical'],B*B*omega*omega*a**4/(4*res))
 assert all(c.passed for c in o.checks)

@pytest.mark.variation(family='motional_emf')
def test_motional_invalid_transformer_term_rejected():
 with pytest.raises(InputError):solve(Problem('DYN','motional_emf',variables={'source':[r,0,0],'parameter':r,'bounds':[0,a],'v':[0,a,0],'B':[0,0,B*t],'time':t,'R':b},assumptions=['negligible_self_inductance']))

@pytest.mark.variation(family='polarization')
@pytest.mark.parametrize('scale',[0,1,3])
def test_polarization_linear_and_uniform_limits(scale):
 coeff=s.Symbol('pol_coeff',positive=True)
 o=solve(Problem('EV','polarization',variables={'coordinates':[x,y,z],'system':'cartesian','P':[scale*coeff*x,scale*coeff*y,scale*coeff*z],'normal':[1,0,0],'surface_substitutions':{x:a}},symbol_units=U|{coeff:'C/m^3'}))
 eq(o.symbolic_result['rho_bound'],-3*scale*coeff);eq(o.symbolic_result['sigma_bound'],scale*coeff*a)

@pytest.mark.variation(family='polarization')
def test_polarization_invalid_normal_rejected():
 with pytest.raises(InputError):solve(Problem('EV','polarization',variables={'coordinates':[x,y,z],'system':'cartesian','P':[q/a**2,0,0],'normal':[2,0,0]}))

@pytest.mark.variation(family='images')
@pytest.mark.parametrize('sign',[-1,1])
def test_image_plane_boundary_and_self_force(sign):
 o=solve(Problem('EV','images',variables={'charges':[(sign*q,[a,0,0])],'point':[a,0,0],'planes':[0],'self_index':0,'test_charge':sign*q},assumptions=['grounded_infinite_planes'],symbol_units=U))
 eq(o.symbolic_result['F'],s.Matrix([-q*q/(16*s.pi*eps*a*a),0,0]));assert 'U' not in o.symbolic_result
 bnd=solve(Problem('EV','images',variables={'charges':[(sign*q,[a,0,0])],'point':[r,b,0],'planes':[0],'limits':{'V':[r,0]}},assumptions=['grounded_infinite_planes'],symbol_units=U))
 eq(bnd.symbolic_result['limit_V'],0)

@pytest.mark.variation(family='images')
def test_image_corner_symmetric_force():
 o=solve(Problem('EV','images',variables={'charges':[(q,[a,a,0])],'point':[a,a,0],'planes':[0,1],'self_index':0,'test_charge':q},assumptions=['grounded_infinite_planes'],symbol_units=U))
 eq(o.symbolic_result['F'][0],o.symbolic_result['F'][1]);assert o.symbolic_result['F'][0].is_negative

@pytest.mark.variation(family='images')
def test_image_invalid_physical_halfspace_rejected():
 with pytest.raises(InputError):solve(Problem('EV','images',variables={'charges':[(q,[a,0,0])],'point':[-a,b,0],'planes':[0]},assumptions=['grounded_infinite_planes']))

@pytest.mark.variation(family='inductance_energy')
@pytest.mark.parametrize('turns',[1,7])
def test_inductance_current_independence_and_energy(turns):
 lc=s.Symbol('L_ref',positive=True)
 o=solve(Problem('DYN','inductance_energy',variables={'flux':lc*I/turns,'I':I,'N':turns},symbol_units=U|{lc:'H'}))
 eq(o.symbolic_result['L'],lc);eq(o.symbolic_result['U'],lc*I*I/2)

@pytest.mark.variation(family='inductance_energy')
def test_mutual_orientation_can_be_negative():
 lc=s.Symbol('M_ref',positive=True)
 o=solve(Problem('DYN','inductance_energy',variables={'flux':-lc*I,'I':I,'N':1,'mutual':True},symbol_units=U|{lc:'H'}))
 eq(o.symbolic_result['M'],-lc)

@pytest.mark.variation(family='inductance_energy')
def test_inductance_invalid_zero_current_and_negative_self_rejected():
 with pytest.raises(InputError):solve(Problem('DYN','inductance_energy',variables={'flux':B*a*a,'I':0,'N':1}))
 with pytest.raises(InputError):solve(Problem('DYN','inductance_energy',variables={'flux':-B*a*a,'I':I,'N':1}))

@pytest.mark.variation(family='magnetic_material')
@pytest.mark.parametrize('power',[0,1,2])
def test_material_axial_M_free_current_and_bound_current(power):
 coeff=s.Symbol('M_coeff',positive=True)
 o=solve(Problem('BA','magnetic_material',variables={'kind':'magnetization','coordinates':[r,phi,z],'system':'cylindrical','M':[0,0,coeff*r**power],'normal':[1,0,0],'surface_substitutions':{r:a}},assumptions=['infinite_axial_symmetry','no_free_current','H_infinity_zero'],symbol_units=U|{coeff:f'A/m^{power+1}'}))
 eq(o.symbolic_result['H'],s.zeros(3,1));eq(o.symbolic_result['B'],s.Matrix([0,0,mu*coeff*r**power]));eq(o.symbolic_result['K_bound'],s.Matrix([0,coeff*a**power,0]))
 eq(o.symbolic_result['J_bound'],s.Matrix([0,-power*coeff*r**(power-1),0]))

@pytest.mark.variation(family='magnetic_material')
@pytest.mark.parametrize('mur',[1,4])
def test_material_gap_continuity_and_air_limit(mur):
 o=solve(Problem('BA','magnetic_material',variables={'kind':'magnetic_circuit','N':1,'I':I,'segments':[(a,mur*mu),(b,mu)]},assumptions=['negligible_leakage','uniform_cross_section'],symbol_units=U))
 eq(o.symbolic_result['B'],mu*I/(a/mur+b));eq(o.symbolic_result['H_1'],mur*o.symbolic_result['H_0'])

@pytest.mark.variation(family='magnetic_material')
def test_material_invalid_H_zero_assumption_rejected():
 with pytest.raises(InputError):solve(Problem('BA','magnetic_material',variables={'kind':'magnetization','coordinates':[r,phi,z],'system':'cylindrical','M':[0,0,q*r]}))
 with pytest.raises(InputError):solve(Problem('BA','magnetic_material',variables={'kind':'magnetization','coordinates':[r,phi,z],'system':'cylindrical','M':[q*r,0,0]},assumptions=['infinite_axial_symmetry','no_free_current','H_infinity_zero']))

@pytest.mark.variation(family='resistance')
@pytest.mark.parametrize('power',[0,1,2])
def test_resistance_series_integrals_and_voltage(power):
 rr=s.Symbol('resistivity_coefficient',positive=True)
 o=solve(Problem('DYN','resistance',variables={'coordinate':x,'bounds':[0,a],'area':b*b,'conductivity':1/(rr*x**power),'voltage':V},assumptions=['one_dimensional_steady_current'],symbol_units=U|{rr:f'ohm*m^{1-power}'}))
 eq(o.symbolic_result['R'],rr*a**(power+1)/((power+1)*b*b));assert all(c.passed for c in o.checks)

@pytest.mark.variation(family='resistance')
def test_resistance_invalid_geometry_and_assumption_rejected():
 with pytest.raises(InputError):solve(Problem('DYN','resistance',variables={'coordinate':x,'bounds':[0,a],'area':b*b,'conductivity':I/V/a}))

@pytest.mark.variation(family='circuit_power')
@pytest.mark.parametrize('sign',[-1,1])
def test_Joule_energy_independent_of_current_sign(sign):
 current,res,tau=s.symbols('current res tau',positive=True)
 o=solve(Problem('DYN','circuit_power',variables={'I':sign*current*s.exp(-t/tau),'R':res,'time':t,'time_bounds':[0,s.oo]},symbol_units={current:'A',res:'ohm',tau:'s',t:'s'}))
 eq(o.symbolic_result['W'],current*current*res*tau/2)

@pytest.mark.variation(family='circuit_power')
def test_Joule_invalid_negative_resistance_rejected():
 with pytest.raises(InputError):solve(Problem('DYN','circuit_power',variables={'I':I,'R':-a,'time':t}))

@pytest.mark.variation(family='multipole')
@pytest.mark.parametrize('sign',[-1,1])
def test_multipole_origin_and_dipole_sign(sign):
 o=solve(Problem('EV','multipole',variables={'charges':[(sign*q,[a,0,0]),(-sign*q,[-a,0,0])]},symbol_units=U))
 eq(o.symbolic_result['Q'],0);eq(o.symbolic_result['dipole'],s.Matrix([2*sign*q*a,0,0]))

@pytest.mark.variation(family='multipole')
def test_magnetic_dipole_axis_vs_equator_scaling():
 for point,factor in [([0,0,b],2),([b,0,0],-1)]:
  o=solve(Problem('BA','multipole',variables={'charges':[],'magnetic_current':I,'area':a*a,'normal':[0,0,1],'magnetic_field_point':point},assumptions=['far_field'],symbol_units=U))
  eq(o.symbolic_result['B_magnetic_far'],s.Matrix([0,0,factor*mu*I*a*a/(4*s.pi*b**3)]))

@pytest.mark.variation(family='multipole')
def test_multipole_invalid_far_field_assumption_rejected():
 with pytest.raises(InputError):solve(Problem('BA','multipole',variables={'charges':[],'magnetic_current':I,'area':a*a,'normal':[0,0,1],'magnetic_field_point':[0,0,b]}))
