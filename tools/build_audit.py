"""Rebuild the audit from the supplied, locally extracted PDFs. No networking."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# One classification per printed lettered question, in source order.
MAP = {
 '2021-06': ['conductor_cavity conductor_cavity potential_from_field', 'electrostatic_energy', 'ampere_regions force_between_currents', 'charged_particle_motion', 'field_consistency dimensional_analysis charge_from_divergence', 'motional_emf force_on_wire joule_energy joule_energy'],
 '2021-11': ['electrostatic_energy continuous_surface_charge', 'conductors_surfaces capacitance polarization_bound_charge capacitance', 'field_consistency field_consistency', 'lorentz_force current_from_curl', 'ampere_solenoid', 'capacitor_field ampere_maxwell induced_E_field'],
 '2022-02': ['electrostatic_energy point_charge_superposition multipole', 'gauss_cylinder conductors_surfaces dielectric_D_field', 'force_on_wire', 'current_integration magnetic_cavity', 'charge_from_divergence potential_from_field', 'faraday_changing_B', 'vector_potential_poisson vector_potential_to_B'],
 '2022-11': ['point_charge_superposition point_charge_superposition electrostatic_energy', 'gauss_sphere charge_from_divergence', 'ampere_solenoid self_inductance RL_transient conductivity_resistance', 'magnetic_dipole magnetic_dipole', 'magnetization_bound_current magnetic_material_H', 'faraday_changing_B'],
 '2023-02': ['point_charge_superposition point_charge_superposition electrostatic_energy', 'charge_integration dielectric_D_field polarization_bound_charge', 'multipole', 'vector_potential_to_B current_integration', 'mutual_inductance faraday_changing_B joule_energy inverse_induction', 'ampere_maxwell'],
 '2023-11': ['point_charge_superposition point_charge_superposition electrostatic_energy', 'ampere_sheet magnetic_energy', 'charge_from_divergence faraday_differential', 'dielectric_D_field conductors_surfaces dielectric_D_field', 'motional_emf joule_energy motional_emf_feedback motional_emf_feedback'],
 '2024-02': ['point_charge_superposition point_charge_superposition continuous_line_charge continuous_line_charge', 'polarization_bound_charge polarization_bound_charge', 'force_on_wire magnetic_work', 'current_integration ampere_cylinder', 'faraday_changing_area conductivity_resistance force_on_wire joule_energy'],
 '2024-11': ['point_charge_superposition method_of_images', 'charge_integration gauss_cylinder', 'biot_savart_wire biot_savart_wire', 'conductivity_resistance charge_from_divergence', 'mutual_inductance mutual_inductance faraday_changing_B', 'magnetic_material_H magnetic_material_H magnetic_material_H'],
 '2025-01': ['potential_from_field charge_from_divergence', 'piecewise_gauss_regions conductors_surfaces electrostatic_energy', 'continuous_surface_charge field_from_potential', 'lorentz_force', 'ampere_wire magnetic_superposition magnetic_superposition', 'faraday_changing_B joule_energy conductivity_resistance'],
 '2025-11': ['point_charge_superposition method_of_images', 'field_from_potential charge_from_divergence charge_integration', 'potential_from_field dielectric_D_field', 'ampere_cylinder magnetic_cavity magnetic_cavity', 'motional_emf_feedback motional_emf_feedback motional_emf_feedback motional_emf_feedback'],
 '2026-01': ['point_charge_superposition continuous_line_charge multipole', 'capacitance electrostatic_energy RC_discharge force_between_currents', 'magnetic_flux faraday_changing_B joule_energy', 'vector_potential_to_B', 'laplace_legendre laplace_legendre field_from_potential'],
}
BA = set('ampere_regions force_between_currents charged_particle_motion lorentz_force current_from_curl ampere_solenoid force_on_wire current_integration magnetic_cavity vector_potential_poisson vector_potential_to_B magnetic_dipole magnetization_bound_current magnetic_material_H ampere_sheet magnetic_work ampere_cylinder biot_savart_wire ampere_wire magnetic_superposition'.split())
DYN = set('motional_emf joule_energy ampere_maxwell induced_E_field faraday_changing_B self_inductance RL_transient conductivity_resistance mutual_inductance inverse_induction magnetic_energy faraday_differential motional_emf_feedback faraday_changing_area RC_discharge magnetic_flux'.split())
METHODS = {
 'point_charge_superposition':['Coulombs lov','superposition'], 'gauss_sphere':['Gauss’ lov'], 'gauss_cylinder':['Gauss’ lov'],
 'charge_from_divergence':['Gauss’ differentiallov'], 'field_from_potential':['E = -grad(V)'],
 'ampere_wire':['Ampères lov'], 'ampere_cylinder':['Ampères lov'], 'lorentz_force':['Lorentzkraft'],
 'faraday_changing_B':['Faradays lov','Lenz’ lov'], 'motional_emf':['bevægelsesinduktion','Lenz’ lov'],
}

def build():
 text = (ROOT/'data/exams_extracted.txt').read_text()
 chunks = re.split(r'Skriftlig prøve i EM1[^\n]*\n', text)[1:]
 assert len(chunks) == len(MAP) == 11
 records=[]
 for (exam, groups), chunk in zip(MAP.items(), chunks):
  problems = re.split(r'\nOpgave (\d+)\s*\n',chunk)
  assert len(problems[1::2]) == len(groups), exam
  for number, body, families in zip(problems[1::2],problems[2::2],groups):
   # Figure panel labels are not question labels: require prose after the letter.
   matches=list(re.finditer(r'^\s{0,4}([a-d])\) (?=[A-ZÆØÅEiV])',body,re.M))
   expected=families.split()
   assert len(matches)==len(expected),(exam,number,len(matches),expected)
   context=body[:matches[0].start()].strip()
   for index,(m,family) in enumerate(zip(matches,expected)):
    question=body[m.end():matches[index+1].start() if index+1<len(matches) else len(body)].strip()
    question=question.split('Opgavesættet slut')[0].strip()
    domain='BA' if family in BA else 'DYN' if family in DYN else 'EV'
    records.append(dict(exam=exam,problem=int(number),subproblem=m[1],domain=domain,family=family,
      geometry='se source_context',given=[context],wanted=[question],methods=METHODS.get(family,[family]),
      dependencies=[],answer_reference=f'answers_extracted.txt: {exam}, Opgave {number}, {m[1]})',
      difficulty=0,notes='Foreløbig tekstbaseret klassifikation. Sværhedsgrad ikke vurderet (0). Figurer og matematiske tegn kræver kontrol mod PDF.',
      source_context=context,source_question=question,review_status='text_classified',
      source_pdf='data/sources/exams.pdf',source_page=text[:text.index(body)+m.start()].count('\f')+1))
  assert sum(r['exam']==exam for r in records)==14,exam
 (ROOT/'data/exam_problem_registry.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 counts=Counter(r['family'] for r in records)
 years=defaultdict(set)
 combinations=defaultdict(set)
 for r in records:
  years[r['family']].add(r['exam'])
  combinations[(r['exam'],r['problem'])].add(r['family'])
 pairs=Counter()
 from itertools import combinations as comb
 for fs in combinations.values():
  pairs.update(comb(sorted(fs),2))
 lines=['# EM1: tekstbaseret familieaudit', '',
 'Kilde: brugerens eksamen_alle (5).pdf og eksamen_facits (4).pdf. 11 eksamener, 154 bogstaverede delopgaver (14 per eksamen). Januar 2025 og januar 2026 kaldes Februar i facit; registry følger eksamensdatoen. Underpunkter i)/ii) bevares i samme bogstaverede delopgave.', '',
 '**Status: foreløbig.** Alle bogstaverede spørgsmål har en primær familie, men figurkontrol, eksplicit parameterinventar, afhængigheder, sværhedsgrader og formelsamlingskontrol er endnu ikke afsluttet. Dette er ikke en komplet faglig audit, og solverudvikling er derfor ikke startet.', '',
 'En primær familie tælles pr. delopgave. Delopgaver kan kræve flere metoder; frekvens er derfor ikke automatisk fuld solverdækning. PDF-tekst mister bl.a. minus-tegn, græske tegn og brøker. Se kilde-PDF ved tvivl.', '',
 '| Family | Antal | Eksamener | Seneste | Prioritet |','|---|---:|---|---|---|']
 for i,(f,n) in enumerate(counts.most_common()):
  lines.append(f'| {f} | {n} | {", ".join(sorted(years[f]))} | {max(years[f])} | {"høj" if i<10 else "normal"} |')
 top=counts.most_common(10)
 lines+=['','## Ti hyppigste primærfamilier','',', '.join(f'{f} ({n})' for f,n in top), '',
 f'De ti familier er primærklassifikation for {sum(n for _,n in top)}/154 = {100*sum(n for _,n in top)/154:.1f}% af delopgaverne. Dette er en prioriteringsindikator, ikke implementeret eller historisk valideret dækning.', '',
 '## Kombinationer inden for samme hovedopgave','', '| Familier | Hovedopgaver |','|---|---:|']
 lines += [f'| {a} + {b} | {n} |' for (a,b),n in pairs.most_common()]
 lines += ['', '## Kildeafvigelser og næste skridt','',
 '- November 2025 5d: facits batterienergi skal efterprøves selvstændigt. Energien fås fra integralet af V I(t); tekstudtrækket viser et udtryk, som ser dimensionsmæssigt forkert ud.',
 '- November 2021 2c: facit skelner ikke tydeligt mellem fri, bunden og samlet overfladeladning; kræver faglig kontrol.',
 '- Januar 2026 4 har to tilfælde i samme bogstaverede spørgsmål; facit kalder dem a og b.',
 '- Aktuel formelsamling og Griffiths er ikke leveret. Ingen udgave eller notation antages.',
 '- Fase 2-prioritering kan først fastlægges endeligt efter verificeret audit og fase 1-regressioner. Frekvenstabellen er det foreløbige grundlag.', '']
 (ROOT/'reports/exam_family_audit.md').write_text('\n'.join(lines))
 print(f'{len(chunks)} eksamener; {len(records)} delopgaver; {len(counts)} primærfamilier')

if __name__=='__main__':
 build()
 from consolidate_audit import consolidate
 consolidate()
