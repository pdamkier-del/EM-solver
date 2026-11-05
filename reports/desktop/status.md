# Desktop-backend: integrationssnapshot

Planlagt integrationsbranch: `desktop-integration-2026-11-05`. Udviklet fra `64520a0` på `em1-desktop-backend-2026-11-05`. Det publicerede commit-SHA er den entydige versionsreference. Dette snapshot må ikke ændres under efterfølgende fysikudvikling.

## Implementeret og kontrolleret

- Flere eksplicit placerede punktkilder, parinteraktioner, observationspunkt og kraftmål. Kilder eller grupper med ufuldstændige positioner/bindinger gættes ikke; højst 16 kilder i denne afgrænsede profil.
- Parenergi kræver intet opdigtet feltpunkt. Kraft på en kilde udelader selvfelt. Konkrete SI-tal kontrolleres for sammenfaldende kilder/feltpunkter og komplekse/ikke-endelige koordinater, før et svar kan godkendes. Ukendte symbolske domæner forbliver eksplicitte gyldighedsbetingelser.
- En udfyldt radial krop med given fri volumenladning, positiv skalar permittivitet, lineært isotropt medium og eksplicit vakuum udenfor kan bruge D → E → P samt kuglesymmetrisk potentialintegration. Manglende materialeforudsætninger giver afståelse.
- Alle trin optager den faktisk udførte metodekontekst ved execution. Indlejrede potentialtrin beholder deres egen kontekst. Lokale begrundelser tilføjes ved den konkrete operation, ikke ved efterfølgende gæt ud fra teksten. Hvor kun metodebegrundelsen findes, markeres reasoning_scope=method.
- Stabile, deterministiske trin-ID’er, LaTeX-mellemregninger, antagelser/gyldighed, lokale kontrolreferencer og globale checks er serialiseret. Feltregning deklarerer kun de love, som den konkrete kørsel anvender.
- API 1.0 er udvidet additivt med presentation_version, method_contexts og views. Resultat, udledning og forklaring skiftes via cache uden solver eller SymPy-beregning. Status, advarsler og negative fysiske diagnoser bevares i alle niveauer.
- EM1-Math-1 validerer begrænset matematisk LaTeX uden TeX-eksekvering, IO-kommandoer eller rendererafhængighed. Alle genererede math-fragmenter i de 153 eksekverbare historiske opskrifter kontrolleres under deres eksisterende tests.
- Offline CLI, responsvalidator, PySide6 QRunnable/Signal-eksempel og seks fulde request/response-fixtures er leveret. App-layout, navigation, manuelle formularer og Windows-batchfiler er ikke ændret.

## Regression og installation

Før: 753 tests. Nu: **793 beståede, 0 fejlede**. Fuld-kørselsflag og kildefingerprint matcher. Native historiske data er fortsat 153/154 eksekverbare korrekte og 151/154 stabile; dette er ikke autonom råtekstforståelse.
certify_all omfatter historiske offline-smokes og syv faktiske Streamlit-widgetforløb. Backendens symbolske worker og integrations-smoke kører med udgående sockets blokeret.
De seks integrationseksempler har formal JSON-schema-validering=True; alle tre niveauer blev åbnet fra samme respons. Det mangelfulde eksempel returnerer not_solved og solution=null, ikke en opfundet besvarelse.
En isoleret Python -S-proces med kun de syv låste runtime-distributioner har løst tre backendcases og åbnet alle tre niveauer. Ingen Qt, Streamlit, NumPy eller pandas blev importeret. Den oprindelige fulde requirements-lock er bevaret; requirements-backend-lock.txt er separat.
PySide6 findes ikke i dette Linux-miljø. Worker-eksemplet er syntakskontrolleret, men native Windows-/Qt- og faktisk math-renderer-integration er ikke udført. Frontend skal levere sin Qt-installation og afprøve processtart, signaler og lokal renderer på Windows. Desktopintegration kan begynde; dette er ikke en ny exam-ready-erklæring.

## Råtekstevaluering

| Sæt | Forsøgt | Korrekte | Afstået | Forkerte | Præcision blandt afgivne svar |
|---|---:|---:|---:|---:|---:|
| Kendt 55-bank | 55 | 10 | 45 | 0 | 100.0 % |
| Historiske råtekster | 154 | 2 | 152 | 0 | 100.0 % |
| Tidligere 28-holdout | 28 | 1 | 27 | 0 | 100.0 % |
| Tidligere internt 24-sæt | 24 | 20 | 4 | 0 | 100.0 % |

Scorerne er uændrede fra 64520a0. 55-scoren inkluderer to korrekte diagnostiske afvisninger af ikke-fysiske prøvefelter. Afståelser er manglende oplysninger/understøttelse og tælles ikke som løste. Ingen fejl/timeouts eller registrerede skjulte forkerte svar forekom i den afsluttende måling.
Alle disse materialer, også det interne sæt, har været set før. Dette er regression, ikke en ny uafhængig blindtest. 25 %-målet er fortsat ikke nået på bank/historiske råtekster. Ingen generel præstation på ukendte eksamener kan udledes af 100 % præcision blandt de få afgivne svar.

## Første diagnosticerede begrænsning på baseline

| Kategori | Antal |
|---|---:|
| 3_problem_representation | 86 |
| 4_method_selection | 16 |
| 2_missing_figure_or_context | 36 |
| 1_pdf_damage_suspected | 14 |
| verified | 2 |
| 5_mathematical_operations | 0 |
| 6_symbolic_derivation | 0 |
| 7_verification_or_unverified_result | 0 |

Alle 154 har en registrering. PDF-skade er en heuristisk mistanke; PDF-/figurtroskab og den første egentlige fejl er ikke fastslået manuelt for alle opgaver. Null/unverified må ikke læses som korrekt. Nul kendte symbolske fejl siger intet om de mange opgaver, som aldrig nåede solveren.
Problemrepræsentation og manglende figur/kontekst dominerer. De nye scene-/materialeveje reducerer disse fejlklasser på komplette udviklingseksempler, men giver ingen målbar ekstra råtekstdækning på de kendte sæt i denne runde.

## Integrationsleverance

- Python: em1_solver.backend.respond(request, solve=True). Praktisk wrapper: em1_solver.backend_client.run_text(text).
- Niveauvalg uden genberegning: em1_solver.backend_client.choose_view(reply, result/derivation/explanation).
- Kontrakt: docs/backend/API.md og docs/backend/schema-v1.json.
- Installation, modulsti og Qt-kald: docs/desktop/INTEGRATION.md.
- Matematikprofil: docs/desktop/LATEX_PROFILE.md.
- PySide6 eksempel: examples/pyside_backend_worker.py. Ingen vindues-/layoutkode.
- Komplette fixtures: data/integration/desktop_v1/*.request.json og *.response.json; hashes i index.json.
- Præcise runtime-pins: requirements-backend-lock.txt. Python/wheels/Qt er ikke bundlet; offline installation kræver forberedt wheelhouse.
- Lokal kildepakke: /workspace/EM1-Backend-Desktop-Integration-2026-11-05.zip, bygget fra det rene integrationscommit. BUILD_INFO.json indeholder commit og checkpoint. Arkivets checksum ligger ved siden af pakken.
- Det frosne exam-ready-2026-11-05-tag og begge eksisterende Windows-ZIP-filer bevares.

## Resterende begrænsninger

Generelle blandede objektgeometrier, gruppetekst/figurer, symbolske kildebindingsligninger, vilkårlige materialer/grænseflader, tidligere delopgavers kontekst, generel dynamik og initialbetingelser er ikke fuldt understøttet. Den manuelle solver bevares til dækkede fysiske familier. Uafhængige nye opgaver og native Windows-/Qt-test mangler fortsat.
Efter dette snapshot skal yderligere fysikudvikling ske på en anden branch og helst i en separat worktree, så frontendens integrationskode ligger stille. Der publiceres ingen ændringer til main eller den frosne eksamensversion.

## Genskab

```sh
python tools/certify_all.py
python tools/evaluate_autonomy.py --output-directory reports/desktop
python tools/desktop_backend_smoke.py
python tools/check_backend_dependencies.py
python tools/write_desktop_report.py
```
