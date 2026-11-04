"""Physical-method consolidation of the existing 154-row audit."""
import json
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
 'point_charges': 'point_charge_superposition electrostatic_energy',
 'coulomb_integral': 'continuous_line_charge continuous_surface_charge continuous_volume_charge',
 'gauss_radial': 'gauss_sphere gauss_cylinder gauss_plane piecewise_gauss_regions charge_integration',
 'conductors': 'conductors_surfaces conductor_cavity',
 'field_calculus': 'potential_from_field field_from_potential charge_from_divergence field_consistency vector_potential_to_B current_from_curl vector_potential_poisson faraday_differential',
 'capacitance': 'capacitance capacitor_field',
 'polarization': 'polarization_bound_charge dielectric_D_field',
 'ampere': 'ampere_wire ampere_cylinder ampere_regions ampere_solenoid ampere_sheet current_integration',
 'magnetic_superposition': 'magnetic_superposition magnetic_cavity',
 'lorentz_force': 'lorentz_force charged_particle_motion',
 'wire_force': 'force_on_wire force_between_currents magnetic_work',
 'magnetic_material': 'magnetic_material_H magnetization_bound_current',
 'faraday': 'faraday_changing_B faraday_changing_area magnetic_flux inverse_induction',
 'circuit_power': 'joule_energy',
 'feedback': 'motional_emf_feedback',
 'resistance': 'conductivity_resistance',
 'inductance_energy': 'self_inductance mutual_inductance magnetic_energy',
 'ampere_maxwell': 'displacement_current ampere_maxwell induced_E_field',
 'rc_transient': 'RC_discharge RL_transient',
 'biot_savart': 'biot_savart_wire biot_savart_arc_loop',
 'motional_emf': 'motional_emf',
 'multipole': 'multipole magnetic_dipole',
 'images': 'method_of_images',
 'laplace_legendre': 'laplace_legendre',
 'units': 'dimensional_analysis',
}
GEOMETRY = {
 '2021-06':'sphere_with_cavity tetrahedron coaxial_cylinders circular_orbit cartesian_polynomial sliding_rod',
 '2021-11':'hemispherical_shell concentric_spheres cartesian_or_spherical azimuthal_B rotating_cylinder parallel_plates',
 '2022-02':'four_point_charges coaxial_cylinders wire_and_semicircle cylinder_with_cavity cartesian_polynomial circular_loop solid_cylinder',
 '2022-11':'two_point_charges sphere solenoid rotating_ring_and_disk magnetized_cylinder square_loop',
 '2023-02':'equilateral_triangle dielectric_sphere axial_quadrupole cartesian_polynomial wire_and_rectangular_loop parallel_plates',
 '2023-11':'line_and_square parallel_sheets cartesian_polynomial sphere_two_dielectrics falling_ring',
 '2024-02':'arc cube wire_and_rectangular_loop solid_cylinder expanding_triangle',
 '2024-11':'corner_planes solid_cylinder current_ribbon graded_resistor coupled_loops toroid_with_gap',
 '2025-01':'cartesian_linear concentric_spheres annular_disk cartesian_vectors parallel_wires circular_coil',
 '2025-11':'plane_images spherical_log_potential concentric_spheres lens_shaped_cavity driven_sliding_rod',
 '2026-01':'dipoles parallel_plate_RC circular_loop cartesian_vector_potential spherical_legendre',
}
# Explicit method chains; adding a secondary family does not claim solver coverage.
SECONDARY = {
 '2021-06:6a':['resistance'], '2021-06:6b':['motional_emf'], '2021-06:6c':['motional_emf'], '2021-06:6d':['motional_emf'],
 '2021-11:1a':['coulomb_integral'], '2021-11:2c':['conductors'],
 '2022-02:1c':['point_charges'], '2022-02:2c':['gauss_radial','field_calculus'],
 '2022-02:4b':['ampere'], '2022-02:5a':['field_calculus'],
 '2022-11:3b':['ampere'], '2022-11:3c':['inductance_energy'], '2022-11:3d':['circuit_power'],
 '2023-02:2b':['gauss_radial'], '2023-02:4b':['field_calculus'],
 '2023-02:5c':['faraday'], '2023-02:5d':['circuit_power'],
 '2023-11:1a':['point_charges'], '2023-11:2b':['ampere'], '2023-11:3b':['field_calculus'],
 '2023-11:4c':['gauss_radial','conductors'], '2023-11:5b':['motional_emf'],
 '2024-02:1d':['point_charges'], '2024-02:3a':['ampere'], '2024-02:3b':['wire_force'],
 '2024-02:5b':['faraday'], '2024-02:5c':['faraday'], '2024-02:5d':['faraday','resistance'],
 '2024-11:1b':['point_charges'], '2024-11:4b':['resistance'], '2024-11:5c':['inductance_energy'],
 '2025-01:2c':['conductors'], '2025-01:3b':['coulomb_integral'], '2025-01:6b':['faraday'],
 '2025-11:1a':['point_charges'], '2025-11:2c':['field_calculus'], '2025-11:3a':['conductors'],
 '2025-11:3b':['conductors'], '2025-11:4b':['ampere'], '2025-11:4c':['ampere'],
 '2026-01:1a':['point_charges'], '2026-01:1c':['coulomb_integral'],
 '2026-01:2b':['capacitance'], '2026-01:2d':['rc_transient','ampere'],
 '2026-01:3c':['faraday'], '2026-01:5c':['laplace_legendre'],
}

def consolidate():
 path=ROOT/'data/exam_problem_registry.json'
 rows=json.loads(path.read_text())
 translation={old:new for new,olds in GROUPS.items() for old in olds.split()}
 for row in rows:
  old=row.get('original_family',row['family'])
  row['original_family']=old
  row['family']=translation[old]
  key=f"{row['exam']}:{row['problem']}{row['subproblem']}"
  row['id']=key
  row['family']={'2021-11:1a':'coulomb_integral','2025-01:2c':'conductors','2026-01:2b':'capacitance'}.get(key,row['family'])
  row['geometry']=GEOMETRY[row['exam']].split()[row['problem']-1]
  row['secondary_families']=sorted(set(SECONDARY.get(key,[]))-{row['family']})
  row['methods']=[row['family']]+row['secondary_families']
  row['notes']='Metodeklassifikation konsolideret; given/wanted bevarer kildeordlyden. Sværhedsgrad 0 = ikke vurderet. Figurretninger skal angives eksplicit i solverinput.'
 counts=Counter(r['family'] for r in rows)
 occurrences=defaultdict(set)
 for r in rows: occurrences[r['family']].add(r['exam'])
 chains=Counter(tuple(sorted({r['family'],*r['secondary_families']})) for r in rows if r['secondary_families'])
 top=counts.most_common(10)
 lines=['# Konsolideret EM1-familieaudit','',
 f'11 eksamenssæt, 154 bogstaverede delopgaver, {len(counts)} primære metodefamilier (tidligere 58). Alle kildeposter og oprindelige klassifikationer bevares. Sekundære metoder registreres separat.', '',
 'Kilde: `data/sources/exams.pdf` (43 sider) og `answers.pdf` (5 sider), SHA256 i `data/source_manifest.json`. Registry henviser til eksamens-PDF-side og facitspørgsmål. Januar 2025/2026 betegnes Februar i facit. i/ii er underpunkter af samme bogstaverede delopgave.', '',
 '**Afgrænsning:** Dette er en metodeaudit af det leverede materiale, ikke en påstand om alle KU-sæt nogensinde. Geometrier er registreret; parameterinventar bevares som kildeordlyd. Sværhedsgrad er ikke vurderet. Den aktuelle formelsamling og Griffiths er ikke leveret. Notation følger derfor de leverede eksamenssæt. Figurorientering indlæses manuelt og antages aldrig af programmet.', '',
 'Brugerens opdaterede bestilling prioriterer direkte implementering efter hurtig konsolidering; fuld redaktionel annotering af registry er udskudt. Ingen solver får historisk dækning alene ud fra denne klassifikation.', '',
 '| Familie | Antal delopgaver | Eksamener | Seneste | Prioritet |','|---|---:|---|---|---|']
 for i,(f,n) in enumerate(counts.most_common()):
  lines.append(f'| {f} | {n} | {", ".join(sorted(occurrences[f]))} | {max(occurrences[f])} | {"høj" if i<10 else "normal"} |')
 lines+=['','## Ti hyppigste primærfamilier','',', '.join(f'{f}: {n}' for f,n in top),'',
 f'Tilsammen {sum(n for _,n in top)}/154 ({100*sum(n for _,n in top)/154:.1f}%) primærklassifikationer. Det er en prioriteringsindikator, ikke en løselighedsprocent. Se `exam_coverage.md` for testet dækning.', '',
 '## Kombinationer i samme delopgave','', '| Metodekæde | Antal |','|---|---:|']
 lines += [f'| {" + ".join(fs)} | {n} |' for fs,n in chains.most_common()]
 lines+=['','## Implementeringsprioritet','',
 'Først Coulomb/superposition, differentialoperatorer, radial Gauss/Ampère og Faraday-kredsløb. Derefter ledere/materialer, energier, kapacitans, geometriske integraler og mekanisk feedback. De oprindelige ti solvere bliver funktioner i bredere metodefamilier frem for isolerede specialsolvere.', '',
 '## Facitkontrol','',
      '- November 2025 5d: original-PDF er kontrolleret visuelt. Facit har korrekt V²; tekstudtrækket mistede eksponenten.',
 '- November 2021 2c kræver skelnen mellem fri, bunden og samlet overfladeladning.',
 '- Januar 2026 4a har to tilfælde; facit mærker dem a/b.',
      '- November 2025 2c: teksten viser 74 5 nC; direkte beregning giver 74,55 nC. Det symbolske udtryk og feltets talværdi stemmer.',
      '- Februar 2024 4a: originalfacit angiver 70 kA; integration med de opgivne data giver cirka 966 A. Se reference_discrepancies.md.',
      '- November 2021 1: original-PDF har Q=0,75 µC, selv om tekstudtrækket fejlagtigt viser mC.', '']
 path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'reports/exam_family_audit.md').write_text('\n'.join(lines))
 print(f'Konsolideret: {len(counts)} familier, {len(rows)} delopgaver')

if __name__=='__main__': consolidate()
