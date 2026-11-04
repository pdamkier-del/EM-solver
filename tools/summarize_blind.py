"""Summarize retained baseline and current repeat measurements without altering evidence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 baseline=json.loads((ROOT/'reports/blind_unseen_baseline.json').read_text())
 after=json.loads((ROOT/'reports/blind_unseen_after_fixes.json').read_text())
 full=json.loads((ROOT/'reports/blind_unseen_full.json').read_text())
 lines=['# Blind generalisering: målegrundlag og eksamensstatus','',
 '| Mål | Tier A baseline | Tier A efter fixes | Hele banken efter fixes |','|---|---:|---:|---:|']
 for key,label in [('autonomous','Autonomous'),('assisted','Assisted')]:
  vals=[r['summary'][key] for r in (baseline,after,full)]
  lines.append('| '+label+' | '+' | '.join(f"{v['passed']}/{v['total']} ({v['percent']} %)" for v in vals)+' |')
 lines+=['','## Hvad tallene betyder','',
 'Autonomous modtager kun bankens originale opgavetekst. Ingen skjult feltudfyldning, solvervalg, enheder eller positivitet tilføjes fra test-ID. Assisted-input er eksplicit menneskelig transskription i `tools/blind_inputs.py`, inklusive geometri, enheder, betingelser og eventuelle flere beregningsled. Nogle paths er betydeligt mere arbejde end én lille rettelse. Et assisted pass må derfor ikke markedsføres som paste-and-solve.', '',
 'Der er ikke anvendt benchmark-ID eller gold-svar i produktionskode. ID-opslag findes kun i evalueringsdata, orakler og regressionstests. Algoritmerne læser ikke blindbanken under normal appdrift. Kompositte paths genbruger den eksisterende dependency/opskriftsmotor; aritmetiske led anvender navngivne fysiske relationer på beregnede delresultater.', '',
 'Baseline blev kørt før rettelser efter modtagelsen af blindtesten. Kodefiler og branch-commit er fastholdt i `blind_baseline_source_manifest.json`. Den aktuelle slutkørsel indeholder også filhashes, bankhash, fortolkninger, løsninger, warnings, checks og tider. Efter-fix-banken er nu set og anvendt som regression; den er ikke en ny uafhængig blindvalidering.', '',
 '## Orakelomfang og scorekorrektion','',
 'Checks sammenligner eksplicitte symbolske referencer, regionpunkter, komponenter/fortegn og enheder samt dansk rendering. Ikke alle parameterrum er formelt bevist. Et korrekt opstillet integral kan bestå, også uden elementær evaluering; dette er ikke det samme som et numerisk facit. Ikke-elektrostatiske/ikke-solenoidale felter skal afvises fysisk, og utilstrækkelig geometri skal give en konkret mangelbesked.', '',
 'Første fuldbankkørsel er bevaret som `blind_unseen_full_first_run.*`. Evaluatoren krævede dér en særskilt fritekstretning også for skalare kapacitanser/energier og allerede entydige vektorkomponenter. Det gav fejlagtige failures og silent-wrong-flag. Slutevalueringen kræver korrekte komponenter/fortegn, hvor relevant; skalarer kræver ingen retning. Denne ændring vedrørte evalueringen, ikke facit eller fysikmotoren. Tier A-baselinens score er uændret.', '',
 '## Generelle rettelser','',
 '- Inline-funktioner og eksplicit multiplikation i begrænset dansk prosa; symbolsk wanted-genkendelse og forsigtigt synlige dimensionsslutninger.',
 '- Adgang til eksisterende solver-familier gennem bekræftede strukturer samt sammensatte paths gennem den eksisterende motor.',
 '- Dimensionsregler for bevarede nul-integraler og Min/Max; eksplicit energi/induktans pr. længde.',
 '- Signed slab-felter og lineært dielektrisk D/E/P; cirkulær Faraday-relation med indre/ydre feltregion.',
 '- Eksplicit potentiale-fjernfelt i den eksisterende punktladningssolver.',
 '- Bekræftelse, synlige mangler, afvisning af direkte Gauss for endelig cylinder og ingen tavs antagelse om uendelig ledning.',
 '- Separat beregningsproces med netværk blokeret; analytisk timeout bevarer en allerede opstillet kurveintegralbesvarelse.', '',
 'Autonome mangler, som opstår ved ufuldstændig build-struktur eller parserens manglende enheder, klassificeres i slutmålingen primært som PARSER; den tekniske INPUT_VALIDATION/UNITS-fase beholdes sekundært. Den oprindelige baseline bevarer sin oprindelige klassifikation. Raterne ændres ikke af denne præcisering.', '', '## Afgrænsninger i banken','',
 '- BA14 er implementeret som generel m kryds B / minus m dot B-relation, med vektor- og vinkelform, fortegns-/ligevægtsvariationer og dimensionskontrol. Den oprindelige baseline er bevaret.',
 '- DYN12: bankens negative strøm bruger ladeorientering. Solveren viser `I_charge=dQ/dt`; den positive afladningsstrøm hedder `I=-dQ/dt`. Begge retninger er eksplicitte, og fysikken er ikke fortegnsændret for at matche banken.',
 '- BA12: nul Lorentzkraft bestemmer den tværgående drifthastighed; en parallel hastighedskomponent er fri. Den assisterede model beholder denne frihed.',
 '- EV11 indfører radiusnavnet R som en fri geometrisk parameter; opgaven angiver ingen radiusværdi. DYN07 beholder stangens masse som fri parameter m. Der er ikke gættet numeriske værdier.', '',
 '## Tre prioriteringer før eksamen','',
 '1. Øv den bekræftede strukturerede arbejdsgang på de forventede geometrier. Den lave autonome score gør blind tillid til parseren uforsvarlig.',
 '2. Gør de hyppige manuelle korrektioner til hurtige, validerede formularer: regioner, symbolenheder, orientering og materiale-/randbetingelser. Bevar synlig usikkerhed.',
 '3. Stop featureudvikling ved exam-ready-checkpointet. Verificér den konkrete Windows-computer og øv de testede UI-forløb offline.', '',
 'Start lokalt fra `/workspace/EM-solver`: `/workspace/em1-venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501`. Ingen generativ AI eller internet anvendes under løsning.']
 (ROOT/'reports/blind_unseen_summary.md').write_text('\n'.join(lines)+'\n')
 p=ROOT/'reports/blind_unseen_after_fixes.md'
 comparison=['','## Sammenligning med baseline','','| Metric | Baseline | Efter fixes |','|---|---:|---:|']
 for key,label in [('autonomous','Autonomous'),('assisted','Assisted')]:
  b=baseline['summary'][key];a=after['summary'][key];comparison.append(f"| {label} | {b['passed']}/{b['total']} ({b['percent']} %) | {a['passed']}/{a['total']} ({a['percent']} %) |")
 for key,label in [('silent_wrong','Silent wrong'),('timeouts','Timeout')]:
  comparison.append(f"| {label} (assisted) | {baseline['summary']['assisted'][key]} | {after['summary']['assisted'][key]} |")
 comparison+=['','Måleforbehold og rettelser: [blind_unseen_summary.md](blind_unseen_summary.md).','']
 p.write_text(p.read_text().split('## Sammenligning med baseline')[0]+'\n'.join(comparison))
if __name__=='__main__':main()
