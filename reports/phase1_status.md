# Migration og certificering frem mod eksamen

Arbejdet fortsætter fra det eksisterende HEAD og bruger den eksisterende
fysikmotor. 79 resterende beregningsopgaver er migreret; alle 153
kvantitative delopgaver har nu en eksekverbar struktureret opskrift.
Juni 2021 1b forbliver kvalitativ/manual.

Den autoritative testbaserede status findes i `exam_coverage.md` og
`coverage_summary.json`, inklusive særskilte method, executable, correct
executable og stable-mål samt en tabel pr. eksamen og konkrete blokeringer.

- Certificering bruger LOW/MEDIUM/HIGH med minimum 2/4/6 variationer,
  historiske facitchecks, faktisk familieanvendelse og dimensions-testsuite.
- Hver eksekverbar opskrift testes gennem Solution og dansk LaTeX-rendering.
- Preset-diagnostikken viser årsager til experimental/runtime-status.
- `python tools/certify_all.py` kører hele evidens- og rapportforløbet.
- Dimensionskontrol omfatter inputroller, koordinater og resultater.
- Mekanisk effekt integreres lokalt langs en bevægelig stav; dette dækker
  også varierende hastighed ved rotation. Tidsvarierende B plus en
  resistiv motional-kreds kræver total Faraday-flux og afvises ellers.
- Oprindelige eksamens-/facit-PDF'er, formelsamling og geometrinoter er
  bevaret; ingen runtime-AI, API, OCR eller netværksafhængighed er tilføjet.

Se `certification.md`, `formula_alignment.md`, `reference_discrepancies.md`
og `limitations.md` for evidenskrav og afgrænsninger.

## Verificeret slutstatus

11 eksamener, 154 delopgaver. Method 153/154 (99,4 %), executable
153/154 (99,4 %), correct executable 153/154 (99,4 %), stable 151/154
(98,1 %). 22/25 primærfamilier certificeret, 3 experimental, 0 failing;
begge hjælpeindgange er også certificeret. 476 beståede tests, 0 fejl,
153 historiske end-to-end, 143 variationer, 18 dimensions-tests.
Offline EV/BA/DYN AppTest samt lokal HTTP health/startside består.
De konkrete begrænsninger og forbedringsprioriteter står i dashboardet.

## Senere checkpoint: ukendte opgaver og blindvalidering

576 tests består, 0 fejl; alle 153 historiske end-to-end-tests består.
Historisk correct executable er fortsat 153/154, stable 151/154.
Den nye eksterne bank og adskilte autonome/assisterede målinger findes i
`blind_unseen_summary.md`, `blind_unseen_baseline.md`,
`blind_unseen_after_fixes.md` og `blind_unseen_full.md`.

Der er 30 selvkonstruerede positive strukturelle problemer (10 EV,
10 BA, 10 DYN) samt særskilte rejection-, integral-, timeout- og UI-tests.
De er intern udviklingsvalidering og må ikke blandes sammen med den
bevarede eksterne blindbaseline. En regressionstest af den kendte
BA14-afvisning består som sikkerhedskontrakt; BA14 er stadig et failure
på benchmarkets assisted-score.


## Feature-freeze-checkpoint

640 tests består, 0 fejl. Alle 153 historiske executable cases består;
historisk stable er 151/154. Tier A assisted 20/20 og full-bank assisted
55/55; autonomous 3/55, silent wrong 0, timeouts 0 i slutmålingen.
BA14 er implementeret generelt. 22 fysiske familier er certificeret
under den eksisterende politik; den nye dipolfamilie er testet, men har
ingen native historisk opskrift og forbliver experimental.

Den faktiske Streamlit-app har fire navigationspunkter, assisteret
bekræftelsespanel, region-builder, synlig orientering, autosave, eksport
og kopiering. Windows-installation og dobbeltklik-start følger med.
Se docs/FEATURE_FREEZE.md, docs/WINDOWS_INSTALLATION.md og
reports/final_validation.json for evidens og platformgrænse.
