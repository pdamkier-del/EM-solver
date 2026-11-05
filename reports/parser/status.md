# Parser-v2: recovery og målt status

Udviklingsbranch: `em1-domain-parser-2026-11-04`, baseret på `2f839c9696c12e7431b39fe431b693b8190049d1`. Den nævnte `parser-recovery-2026-11-04` fandtes ikke lokalt. Det eksisterende ucommittede arbejde blev videreført; der er ikke startet et nyt solverprojekt. Frosset tag og original Windows-ZIP er bevaret. Ingen ny branch/release er publiceret.

## Implementeret

- Deterministiske lag: Unicode/notation → sikre matematik-tokens → danske ord/fraser → kilder og symboler → SI-dimensioner → geometri/udstrækning → regioner/orientering → metodeforudsætninger → eksisterende engine.
- GREEN/YELLOW/RED med tekstlig evidens pr. felt og spørgsmål om konkrete mangler. Ingen sandsynlighedsbaseret confidence. Usikre felter blokerer beregning; svarmuligheder har intet fysisk standardvalg.
- Symbolsk støtte: radiale Gauss-problemer, aksiale Ampère-problemer, gradient/divergens/rotation, linjeintegraler efter Coulomb/Biot–Savart samt uniform orienteret flux/Faraday. Hule intervaller bruger ordnede interne hjælpesymboler, som gendannes til brugerens symboler i løsningen.
- Regionskilden udenfor det specificerede kildeområde er nul; glatte feltudtryk med begrænset gyldighed får en synlig domæneadvarsel. Slabs bevarer feltets fortegn på begge sider.
- Ukendt endelig/uendelig udstrækning, strømretning, grænser, tidsafhængige kilder under statiske regler, materialelove, randpotentialer, ukendte funktioner og beskadiget matematik giver afklaring/manual fallback.
- Ny opgave: indsæt → Analysér opgave → se/ret fortolkning → vælg Symbolsk eller Symbolsk og numerisk → Løs opgave. Kun mangler vises som formular; genkendte felter er sammenfoldet. Hele fortolkningen kan også rettes.
- Avanceret / Manuel bevarer original geometri-formular, specialiseret metode og den tidligere tekstformular med fuld bekræftelse. Historiske presets, eksamenstilstand, kopi/eksport og separat lokal parser-autosave er bevaret.
- Ingen nye fysiksolvere, ændringer i core/solvers, LLM, API eller netværksafhængigheder. Parseren læser ingen opgavebank/facit. Historiske opskrifter og orakler bruges kun af evalueringsværktøjet efter beregning.

## Målt autonomi

Den tidligere rapporterede baseline var 3/55 (5,5 %): to feltberegninger og én korrekt Gauss-afvisning. Den nye 55-score indeholder otte beregnede løsninger og to diagnostiske Maxwell-afvisninger. Datamangel/manglende løsningsmodel tælles som afståelse i den nye evaluator, selv om den gamle evaluator kunne kreditere en exception som korrekt afvisning. Den nye måling sender kun rå tekst til den offentlige analyse-/løsningskæde. IDs og facit er kun tilgængelige for den efterfølgende verifier. Strukturerede presets tælles aldrig som autonomi. Korrekte afvisninger af ikke-fysiske prøvefelter indgår som verificerede besvarelser og markeres i rårapporten.

| Datasæt | Fuld autonom parse | Autonomt verificeret | 0 rettelser | 1 feltrettelse | 2–3 feltrettelser | Manuel/uafklaret | Registrerede skjulte fejl |
|---|---:|---:|---:|---:|---:|---:|---:|
| 55-case regressionsbank | 10/55 | 10/55 (18.2 %) | 10 | 6 | 2 | 37 | 0 |
| Historisk holdout | 0/28 | 0/28 (0.0 %) | 0 | 0 | 0 | 28 | 0 |
| Alle historiske råtekster | 1/154 | 1/154 (0.6 %) | 1 | 0 | 0 | 153 | 0 |

Holdout er de komplette sæt 2022-02 og 2023-02 (28 delopgaver). De øvrige 9 sæt har 126 delopgaver. Alle 154 tekster er afprøvet. Felt-ground-truth er manuelt annoteret for alle 55 bankcases, alle 28 holdout-cases og én udviklingscase. Feltmål på alle historiske tekster dækker derfor kun de 29 annoterede cases, ikke 154.
Fuld parse kræver både klar struktur, de annoterede felter og et komplet manuelt review. Automatiske output verificeres desuden uafhængigt mod eksisterende fysiske orakler/facitchecks; numeriske referencechecks køres hvor de findes. Korrektionsgrupper er de faktisk afprøvede menneskelige feltrettelser, ikke et bevis på mindste mulige antal klik. Rettelser kan tilføre oplysninger, som mangler i teksten. De 28 holdout-cases fik ingen struktureret assisted-transskription i denne runde.
Nul registrerede skjulte fejl er en måling på disse testcases, ikke en garanti for alle fremtidige tekster. Falske/ikke-fysiske prøvefelter afvises med Maxwell-kontroller; manglende oplysninger giver afståelse.

## Feltkorrekthed

| Felt | 55-bank | Holdout |
|---|---:|---:|
| geometry | 43/55 (78.2 %) | 14/28 (50.0 %) |
| source | 30/55 (54.5 %) | 17/28 (60.7 %) |
| wanted | 43/55 (78.2 %) | 13/28 (46.4 %) |
| regions | 7/7 (100.0 %) | 3/3 (100.0 %) |
| orientation | 17/20 (85.0 %) | 7/12 (58.3 %) |

Region- og orienteringsmål har mindre nævnere: kun faktisk annoterbare oplysninger scores; null/ukendt udelades og tælles aldrig som korrekt. Høj regionsscore dokumenterer derfor ikke fuld dækning af alle 55/28 tekster. Sammensatte geometrier kræver en sammensat repræsentation; det er ikke nok at genkende et enkelt navneord.

## Hvad fejler fortsat?

De hyppigste uafklarede bankfelter er: source_formula (22), units (9), geometry (7), plane (6), boundary_model (6), method (6), wanted (5).
For historiske råtekster er det: source_formula (72), geometry (45), method (39), boundary_model (38), figure (35), source_conflict (32), wanted (29).
Figurafhængighed genkendes eksplicit i 35/154 tilfælde, heraf 3/28 i holdout. Det er en detekteret nedre grænse, ikke en komplet menneskelig figuraudit.
Automatisk kompilering af ledere/hulrum, dielektrika, spejlladninger, multipoler/Laplace, materialemagnetisme, kredsløbstransienter, Ampère–Maxwell, feedback og generelle flade-/volumenintegraler er endnu ikke færdig. Disse kan fortsat tilgås gennem de eksisterende manuelle solvere, hvor dækket.
Tab af eksponenter, græske tegn, brøker eller fortegn i PDF-tekst genskabes ikke fra facit. Foregående delopgavers information videreføres ikke automatisk, og figurer fortolkes ikke. 1/154 rå historiske løsninger viser, at parseren stadig har utilstrækkelig KU-eksamensdækning. Denne udviklingsversion er en parser-preview; den er ikke en ny exam-ready-certificering.

## Evalueringsprotokol og datalækage

9/2-opdelingen er gemt før udviklingen. `development_freeze.json` bevarer første kildefrysning før den nye holdout-inspektion. Alle historiske tekster og 55-banken havde været set i tidligere projektarbejde; de er ikke urørte blinddata.
Første kørsel (`evaluation_round1.json`) gav 8/55 verificerede og 0/28 holdout. En korrekt linjeintegralopsætning blev først registreret som uverificeret, fordi verifieren ikke omdøbte bundne integrationsvariable korrekt; kontrollen bruger nu xreplace/alpha-omdøbning. En kugleskal manglede desuden en eksplicit symmetry-antagelse i adapteren.
Efter første holdout-inspektion er der også tilføjet generelle sikkerhedskontroller for koordinatkort, tid, randdata og materialer samt bevaret en ekstra adgang til den gamle assisted-UI. Ændringerne står i `evaluation_manifest.json`. Den afsluttende måling er derfor regression efter evaluering; den er ikke en ny blind holdout-måling. Ingen opgavenumre, facit eller holdout-specifikke løsningsregler indgår i produktionsparseren.

## Regression og offline

Seneste fulde pytest-kørsel: 727 beståede, 0 fejlede; full_suite=True, exitstatus=0.
Fysik-, dimensions- og historiske tests er bevaret. Den gamle UI har kun fået opdateret testnavigation, fordi formularen nu ligger i Avanceret / Manuel. Nye tests dækker parserens struktur, sikker afståelse, SI, regioner, procesgrænse og faktiske Streamlit-widgets for EV/BA/DYN, rettelser, autosave og eksport.
Fysik-/parsertests og de nye UI-tests blokerer socket-forbindelser; worker-processen blokerer også netværk. certify_all udfører desuden den eksisterende offline-smoke og syv manuelle UI-smokes. Lokal launcher er afprøvet på 127.0.0.1:8519 med HTTP-health og startside. pip check fandt ingen dependency-konflikter.
Native Windows-installation, dobbeltklik på .bat og faktisk browser/clipboard på Windows kan ikke verificeres på denne Linux-maskine. Streamlit AppTest er widgettest, ikke en Windows-browsertest. Batchfiler og dependencies er uændrede; ny installationspakke kræver derfor stadig en lokal Windows-accepttest før eksamensbrug.

## Genskab målingen

```sh
/workspace/em1-venv/bin/python tools/certify_all.py
/workspace/em1-venv/bin/python tools/evaluate_text_parser.py
/workspace/em1-venv/bin/python tools/write_parser_report.py
```

Se `evaluation.json` for hver rå fortolkning, spørgsmål, rettelse, metode, output, dimensionskontrol, facitstatus og konkret fejl. Evaluatoren kontrollerer kildehash før og efter målingen.

## Næste udvikling

1. Gør manglende kontekst fra tidligere delspørgsmål eksplicit i brugerflowet.
2. Knyt danske materiale-/randbeskrivelser til eksisterende conductor-, dielectric- og Laplace-solvers med typed prerequisites.
3. Tilføj generel parameterisering af flade-/volumenkilder og ikke-uniform flux, med brugerbekræftet orientering.
4. Forbind kredsløbs-/Ampère–Maxwell-profilerne til den eksisterende dependency engine.
5. Indsaml et nyt, hidtil uset tekstsæt og gennemfør native Windows-accepttest.
