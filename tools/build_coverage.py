"""Three independent coverage metrics, derived from a full test run and recipe evidence."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from em1_solver.core.historical import paths,load,run
from em1_solver.core.certification import certified,blockers,fingerprint
from em1_solver.core.registry import solvers

def build():
 rows=json.loads((ROOT/'data/exam_problem_registry.json').read_text());valid={r['id'] for r in rows}
 result=json.loads((ROOT/'reports/test-results.json').read_text())
 if result.get('fingerprint')!=fingerprint():raise RuntimeError('Testgrundlag er forældet.')
 if not result.get('full_suite') or len(result['results'])!=result['collected']:raise RuntimeError('Kør hele testsuiten først.')
 tests=result['results'];method=set();executable=set();partial=set();failed=set()
 for test in tests:
  if test.get('historical') and test['outcome']=='passed':method.update(test['historical']['ids'])
  if test.get('recipe'):
   rec=test['recipe']
   if test['outcome']!='passed':failed.add(rec['id'])
   elif rec['status']=='executable':executable.add(rec['id'])
   else:partial.add(rec['id'])
 recipes={r['id']:r for r in map(load,paths())};stable=set();reasons={}
 declared={id for id,r in recipes.items() if r['status']=='executable'}
 for id in executable:
  recipe=recipes[id];families={step['problem']['family'] for step in recipe['path']}
  if all(certified(f) for f in families):
   check=run(recipe)
   if check.passed and all(a.stable for a in check.solutions.values()):stable.add(id)
   else:reasons[id]=['Runtime: '+name+': '+', '.join(c.name for c in a.checks if c.passed is not True) for name,a in check.solutions.items() if not a.stable]
  else:reasons[id]=[f+': '+reason for f in families for reason in blockers(f)]
 manual={id for id,r in recipes.items() if r['status']=='qualitative/manual'}
 unmigrated=valid-executable-partial-manual-failed
 primary={r['family'] for r in rows};cert={f for f in primary if certified(f)}
 counts=Counter(t['outcome'] for t in tests)
 categories={'total':len(tests),'physics_core_and_historical':sum(t['test'].startswith(('tests/historical/','tests/variations/','tests/dimensions/')) or 'test_core.py' in t['test'] for t in tests),
  'historical_end_to_end':sum(bool(t.get('recipe')) for t in tests),'variations':sum(bool(t.get('variation')) for t in tests),'dimensions':sum(bool(t.get('dimensions')) for t in tests),'failures':counts.get('failed',0)}
 summary={'total_historical':154,'method_coverage':len(method&valid),'executable_historical_coverage':len(declared),'correct_executable_coverage':len(executable),'stable_historical_coverage':len(stable),'stable_families':sorted(cert),'experimental_families':sorted(primary-cert),'failing_recipes':sorted(failed),'qualitative_manual':sorted(manual),'not_migrated':sorted(unmigrated),'partial':sorted(partial),'tests':categories}
 physical=set(solvers())-{'algebra','potential_from_field'}
 summary['implemented_physical_families']=len(physical)
 summary['stable_implemented_families']=sorted(f for f in physical if certified(f))
 summary['experimental_implemented_families']=sorted(f for f in physical if not certified(f))
 summary['non_stable_reasons']=reasons
 summary['per_exam']={exam:{'total':len(ids),'executable':len(ids&declared),'correct':len(ids&executable),'stable':len(ids&stable),'manual':len(ids&manual)} for exam in sorted({r['exam'] for r in rows}) for ids in [{r['id'] for r in rows if r['exam']==exam}]}
 (ROOT/'reports/coverage_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 lines=['# EM1: metode, eksekverbar historik og stabil dækning','',
 'Dækning må ikke forveksles med autonom løsning af opgavetekst. Al indlæsning er struktureret; ingen OCR, AI eller automatisk figurtolkning.', '',
 '| Mål | Antal / 154 | Procent | Betydning |','|---|---:|---:|---|',
 f'| Method coverage | {len(method&valid)} | {100*len(method&valid)/154:.1f}% | Bibliotekets beregninger repræsenteres i beståede tidligere regressionschecks; ikke et selvstændigt historisk inputforløb. |',
 f'| Executable historical coverage | {len(declared)} | {100*len(declared)/154:.1f}% | Struktureret beregningsopskrift findes. |',
 f'| Correct executable coverage | {len(executable)} | {100*len(executable)/154:.1f}% | Maskinlæsbar gennemgået opskrift → solver-path → Solution → uafhængige facitchecks. |',
 f'| Stable historical coverage | {len(stable)} | {100*len(stable)/154:.1f}% | Eksekverbar opskrift, kun certificerede familier, og bestået symbolsk dimensionskontrol på hvert beregningsled. |', '',
 'Det tidligere 153/154-tal er alene method coverage. Ingen af tallene betyder automatisk forståelse eller fuldstændig kvalitativ PDF-besvarelse.', '',
 'Opskrifterne i `data/historical_problems/` har kildehenvisning, oprindelig given/søges-tekst, symboler/enheder, geometri, regioner, antagelser, beregningsvej og forventede resultater. Facitforventninger er håndkodet fra kilden, ikke frosset solver-output. Se testkode og opskrift for konkret orakelomfang. Opskrifter med ikke-migreret status har bevidst ingen opdigtede input.', '',
 '## Solver-status','',f'{len(primary)} konsoliderede primærfamilier; {len(cert)} stable, {len(primary-cert)} experimental. Failing familier: '+str(len({r['family'] for r in rows if r['id'] in failed}))+'. Hjælpeindgangene potential_from_field og algebra rapporteres særskilt.', '',
 'Stable: '+(', '.join(sorted(cert)) or 'ingen')+'. Certifikatgrundlag findes i `data/solver_certificates.json` og `reports/certification.md`. Runtime stable kræver kendte symbolenheder og beståede dimensions-/fysikchecks; certifikater ugyldiggøres ved ændret kildetekst/test/opskrifter.', '',
 '## Tests','', '| Kategori | Antal |','|---|---:|']
 lines += [f'| {k} | {v} |' for k,v in categories.items()]
 lines+=['',f'Outcomes: {dict(counts)}. Kategorier overlapper; fysik er en overkategori. Historiske end-to-end er kun opskriftstests, ikke de gamle isolerede regressionsfunktioner.', '',
 '## Dækning pr. eksamen','', '| Eksamen | Delopgaver | Executable | Correct | Stable | Manual |','|---|---:|---:|---:|---:|---:|', *[f"| {e} | {v['total']} | {v['executable']} | {v['correct']} | {v['stable']} | {v['manual']} |" for e,v in summary['per_exam'].items()], '', '## Historiske problemstatusser','',f'- Fuldt eksekverbare beregningsopskrifter: {len(executable)}.',f'- Delvist understøttede opskrifter: {len(partial)}.',f'- Kvalitative/manual: {len(manual)} (Juni 2021 1b).',f'- Ikke migreret til opskrift: {len(unmigrated)}; dette betyder ikke nødvendigvis manglende fysisk metode.',f'- Fejlede end-to-end-opskrifter: {len(failed)}.', '',
 '| ID | Metodefamilie | Opskriftstatus | Stable path |','|---|---|---|']
 for row in rows:
  id=row['id'];state='executable' if id in executable else 'partial' if id in partial else 'qualitative/manual' if id in manual else 'failing' if id in failed else 'not_migrated'
  lines.append(f'| {id} | {row["family"]} | {state} | {id in stable} |')
 lines+=['','## Konkrete stable-blokeringer','']
 for id,why in sorted(reasons.items()):lines.append('- '+id+': '+'; '.join(why))
 gaps=Counter(r['family'] for r in rows if r['id'] not in stable and r['id'] not in manual)
 lines+=['','## Top remaining gaps','', '| Familie | Potentiel stabil historisk gevinst (primærklassifikation) |','|---|---:|']
 lines += [f'| {f} | {n} |' for f,n in gaps.most_common()]
 lines+=['','## Top remaining risks','',
 '- Et ukontrolleret symmetriudsagn kan stadig være fysisk forkert: metodevælgeren kræver eksplicit bekræftelse og fortolker ingen figur.',
 '- Den kvalitative feltlinjeskitse Juni 2021 1b kræver fortsat menneskelig argumentation.',
 '- En runtime-beregning uden komplette symbolenheder er ikke stable, selv om familien har et certifikat.',
 '- Krumme koordinater, randflader og integralers konvergens kræver egne antagelser. Eksperimentelle familier er ikke certificeret af et enkelt korrekt facit.',
 '- RC-strømfortegn afhænger af orientering: I er positiv afladningsstrøm; I_charge følger formelsamlingens ladeorientering.',
 '- Symbolsk dimensionskontrol beviser ikke en logaritmes fysiske domæne eller vælger løsningsgren. RL-mål kræver nåelighed.',
 '- Generel LaTeX-kompilering på en ekstern TeX-installation er ikke verificeret; eksportens indhold er testet.', '',
 'Kildekontrol mod formelsamlingen: `formula_alignment.md`. Kilde-/facitafvigelser: `reference_discrepancies.md`.','']
 (ROOT/'reports/exam_coverage.md').write_text('\n'.join(lines))
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':build()
