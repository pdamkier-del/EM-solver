> **Python 3.13 x64-desktop:** På branchen `em1-python313-2026-11-05` ligger den nye pakke `distribution/EM1-Solver-Desktop-Python313-2026-11-05.zip`. Installér i en ny mappe med `INSTALL_WINDOWS.bat` og start med `START_WINDOWS.bat`. [Startvejledning](desktop_app/START_HER_DANSK.md) · [Python 3.13-kompatibilitet](reports/python313/status.md). Python 3.12-pakken nedenfor bevares som backup. Native Windows kræver brugerafprøvning.

> **Ny desktop-udviklingsversion:** På branchen `em1-generalization-2026-11-05` findes en samlet PySide6-pakke under `distribution/EM1-Solver-Desktop-Development-2026-11-05.zip`. Udpak i en ny mappe, kør `INSTALL_WINDOWS.bat` online og derefter `START_WINDOWS.bat`. Læs [den danske startvejledning](desktop_app/START_HER_DANSK.md). Den tidligere integrationspakke og frosne releases er bevaret.
>
> [Fysiklove og afgrænsninger](reports/generalization/law_audit.md) · [Evaluering af 20 nye opgaver](reports/generalization/evaluation20/report.md). 17/20 fuldt korrekte **med brugerhjælp**, 3 afståelser; 0 fuldt automatiske. Ikke en ekstern blindtest. Native Windows kræver brugerafprøvning.

# EM1 Solver – samlet desktopintegration

Den eksisterende uploadede PySide6-app ligger i [desktop_app](desktop_app).
Start med [Windows-installation og eksamens-runbook](desktop_app/WINDOWS_INTEGRATED.md).
Branchen `em1-assisted-evening-2026-11-05` indeholder otte DYN-modelkort og
assisterede EV/BA-former over de eksisterende fysiksolvere. Den almindelige
tekstbaserede backendvej, noter, PDF'er og de tre løsningsfaner er bevaret.

[Samlet app-evaluering](reports/desktop_integrated/evaluation.json) indeholder
35 historiske delopgaver kørt gennem det faktiske hovedvindue med eksplicitte,
brugerbekræftede modeller. Dette er ikke autonom råtekstdækning eller en ny
blindprøve. Native Windows skal testes på brugerens computer; Linux/offscreen
og Windows-wheel-tilgængelighed er testgrundlaget her.

Frosne releases, `main` og `desktop-integration-2026-11-05` er ikke ændret.
De oprindelige Streamlit-instruktioner nedenfor er fortsat tilgængelige.

# EM1 Solver – lokal eksamensapp

Desktopintegration: [entrypoints og Windows-setup](docs/desktop/INTEGRATION.md),
[låste backendkrav](requirements-backend-lock.txt),
[seks komplette JSON-fixtures](data/integration/desktop_v1/index.json) og
[afsluttende integrationsrapport](reports/desktop/status.md). Integrationskoden
holdes fast; senere fysikudvikling foregår separat.

Nyeste backend-udvikling: [fejlanalyse og målinger](reports/autonomy/status.md)
og [frontend-kontrakt 1.0](docs/backend/API.md). Den nye backend-branch
ændrer ikke appens layout. Ældre parsermålinger nedenfor er bevaret som baseline.

På Windows: udpak hele projektet, installér Python 3.12, dobbeltklik
**install_windows.bat**, og start derefter med **START_EM1_SOLVER.bat**.
Appen åbner i standardbrowseren på 127.0.0.1. Ingen terminalkommandoer
kræves under eksamen. Installationen kan kræve internet; appen gør ikke.

Se [Windows-installation og offline-forberedelse](docs/WINDOWS_INSTALLATION.md)
og [den korte eksamens-runbook](docs/EXAM_UI_RUNBOOK.md).

Denne branch er **Parser Preview**. Den frosne eksamensversion er stadig tagget
`exam-ready-2026-11-05` på commit `2f839c9`; dens ZIP ændres ikke.
Se [måling, begrænsninger og reproducerbare tests](reports/parser/status.md).

Forsiden **Ny opgave** bruger nu rå dansk tekst: **Analysér opgave** →
kontrollér kun uafklarede oplysninger → vælg symbolsk/numerisk visning →
**Løs opgave**. Sammenfoldet fortolkning kan gennemgås og rettes.
**Avanceret / Manuel** indeholder den oprindelige geometri-formular,
specialiserede metoder og **Tekst med fuld bekræftelse** som fallback.
**Historiske opgaver** og **Hjælp** er de øvrige navigationspunkter.
Eksamenstilstand, separat lokal tekst-autosave og tekst-/LaTeX-eksport er bevaret.

Parseren afstår, når den ikke sikkert kan bestemme model og data.
Den er stadig under udvikling; historiske presets og manuelt metodevalg
dokumenterer ikke autonom forståelse af nye tekster.

Windows-batchfilerne kræver lokal validering på eksamenscomputeren;
udviklingsmiljøet her er Linux. Se dokumentationen for den præcise grænse.

---

# EM1 Offline Exam Solver

Deterministisk Python/SymPy-værktøj til manuelt strukturerede EM1-opgaver.
Det eksisterende auditmateriale er genbrugt: 11 eksamenssæt, 154 bogstaverede
delopgaver og 25 konsoliderede primære metodefamilier. Se den aktuelle,
testbaserede [dækningsrapport](reports/exam_coverage.md).

## Start i dette cloudmiljø

```sh
cd /workspace/EM-solver
/workspace/em1-venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Åbn den lokale app på port 8501 i browseren på samme maskine.
Der er ingen cloud-hosting eller brugerlogin.

## Installation på egen maskine

Python 3.12 er testet. Fra projektmappen:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

På Windows bruges `.venv\Scripts\python.exe` i stedet for `.venv/bin/python`.
Installation af afhængigheder kan kræve internet. Selve beregningerne og den
lokale app kræver det ikke. Hvis installationen også skal være offline,
forbered et wheel-arkiv på en maskine med samme Python-version, OS og arkitektur:

```sh
python -m pip download -r requirements-lock.txt -d wheelhouse
python -m pip install --no-index --find-links wheelhouse -r requirements-lock.txt
```

Streamlit-telemetri er slået fra i `.streamlit/config.toml`. Appen bruger
lokalt pakket matematikvisning. Fysikmotoren indeholder ingen HTTP-klient,
API-kald, LLM eller generativ tekstfortolkning. Enhedstestene for fysikmotoren
blokerer socket-forbindelser under kørsel. Streamlit bruger kun den lokale
browserforbindelse; brug ikke eksterne komponenter eller internetressourcer.

## Brug

1. Vælg EV, BA eller DYN og en fysisk metodefamilie.
2. Tilpas de viste strukturerede inputfelter. Lister og objekter skrives som JSON.
   Matematiske udtryk kan bruge `sin`, `cos`, `exp`, `log`, `sqrt`, `pi`,
   `^` eller `**`. Multiplikation skrives med `*`.
3. Angiv symmetri, randbetingelser og orientering eksplicit. Programmet stopper,
   hvis nødvendige data eller antagelser mangler. Positiv ladnings-/strømretning
   må ikke forveksles med størrelsen af en vektor.
4. Numeriske værdier holdes adskilt fra det symbolske input. Eksempel:
   `{"a":"2 cm","q":"3 nC"}` med forventede enheder `{"a":"m","q":"C"}`.
   Uforenelige enheder afvises. Rene tal betyder SI; deres dimension er ikke
   automatisk verificeret. Alle symboler er positive undtagen de i appen
   angivne koordinater. Brug `-q` eller `-I` til negative værdier.
5. Tryk **Løs**. Løsningen viser genkendelse, metode, begrundelse, givne data,
   startligninger, integrations-/differentieringstrin, resultat, retning og
   de kontroller, som faktisk er udført. Besvarelsen kan gemmes som LaTeX.

Eksemplerne er bevidst simple og kan ændres. Et symbol betegner én størrelse
ad gangen: radius og modstand skal eksempelvis have forskellige symboler i
samme induktionsproblem. En uafklaret SymPy-integral beholdes som integral;
programmet opfinder ikke en lukket løsning.

Dependency engine kan kæde blandt andet `V → E → rho`,
`A → B → orienteret flux → EMF → I → P → W` og
`rho + radiale regioner → Q_enc → E_radial → delta_V`.
Alle geometriske data og nødvendige antagelser skal stadig være angivet.

## Python-API

```python
import sympy as sp
from em1_solver import Problem, Region, solve
from em1_solver.core.validation import EPS0

s, R, alpha = sp.symbols('s R alpha', positive=True)
problem = Problem(
    domain='EV', family='gauss_radial',
    geometry='infinite_cylinder',
    variables={'coordinate': s, 'symmetry': 'cylinder'},
    regions=[Region(0, R, alpha*s**2, EPS0)],
    assumptions=['infinite_cylindrical_symmetry'], wanted=['E'],
)
answer = solve(problem)
print(answer.symbolic_result['E'])
```

Resultatet er et stykkevist felt indenfor og udenfor cylinderen. Hule og flere
ladede områder angives med flere ikke-overlappende `Region`-objekter.
Regionernes orden skal kunne fastslås af SymPy, fx radier `a`, `a+b`, `a+b+d`
med positive `a,b,d`. En ukendt ordning gættes ikke.

`solve_for` og `target_values` kan bruges i Python-API'et til at løse eksplicitte
resultatbetingelser for ubekendte. Flere løsningsgrene returneres som grene;
der vælges ikke en vilkårlig rod. Se historiske tests for komplette eksempler.

## Tests og rapporter

```sh
cd /workspace/EM-solver
/workspace/em1-venv/bin/python -m pytest -q
/workspace/em1-venv/bin/python tools/build_coverage.py
```

Brug `.venv/bin/python` lokalt. Tests er opdelt i dataintegritet,
fysik/kerne, historiske regressioner og Streamlit-funktionstest.
Dækningsrapporten nægter at blive bygget efter en delvis testkørsel.

Auditten kan reproduceres lokalt med Popplers `pdftotext`:

```sh
pdftotext -layout data/sources/exams.pdf data/exams_extracted.txt
pdftotext -layout data/sources/answers.pdf data/answers_extracted.txt
python tools/build_audit.py
```

`build_audit.py` genbruger den oprindelige klassifikation og konsoliderer den.
Den udfører ikke automatisk fysikforståelse af fri tekst. PDF-tekst kan miste
fortegn og græske tegn; rettelser dokumenteres mod original-PDF.

## Begrænsninger

Ingen automatisk opgavetekstforståelse, figurlæsning, OCR, LLM, generel PDE/FEM
eller automatisk fysik fra en vilkårlig geometri. Se
[afgrænsninger](reports/limitations.md),
[facitafvigelser](reports/reference_discrepancies.md) og den præcise restliste
i [dækningsrapporten](reports/exam_coverage.md).
Certificering er betinget af den konkrete inputmodel og gennemførte kontroller; historisk
testdækning er ikke en garanti for alle variationer. Formelsamlingen er nu leveret
og gennemgået. Griffiths er ikke leveret.

## Eksamensworkflow og historiske presets

Vælg **Hurtigt metodevalg** for EV/BA/DYN/**Ved ikke**, givne størrelser og
søgt størrelse. Forslagene bruger eksplicit symmetri; geometriens navn er
ikke nok. Vælg **Historiske opgaver** for at indlæse og køre en gennemgået
JSON-opskrift, se facitkontroller og eksportere løsningen. **Eksamen** viser
kun de efterspurgte resultater; **Forklaring** viser også hjælperesultater.

Opskriftsformat og kildehenvisninger findes i `data/historical_problems/`.
`executable` betyder en faktisk kørt, struktureret historisk beregningsvej;
`not_migrated` er ikke et eksekverbart preset. Juni 2021 1b er
`qualitative/manual`. Det oprindelige 153/154-tal er **method coverage**,
ikke autonom eller eksekverbar historisk dækning.

Den aktuelle formelsamling og geometrinoter er nu inkluderet i
`data/sources/`. Se [notation og forskelle](reports/formula_alignment.md),
især RC-fortegnet: `I` er positiv afladningsstrøm, `I_charge` er den
ladeorienterede strøm som i formelsamlingen.

Symbolsk dimensionskontrol kræver enheder for alle anvendte symboler i
feltet **Symbolernes SI-enheder** eller `Problem.symbol_units`. Eksempel:
`{"q":"C","a":"m","b":"m"}`. Forkerte dimensioner giver
`WARNING: dimensional inconsistency`; ukendte dimensioner tæller ikke som
bestået. SI-enhedsetiketter alene er ikke dokumentation for en kontrol.

Certificering og de tre dækningstal reproduceres med:

```sh
python -m pytest -q
python tools/certify_solvers.py
python tools/build_coverage.py
```

Certificerede familier fremgår af `data/solver_certificates.json`.
Et individuelt `stable=true` kræver også beståede dimensions- og
fysikkontroller. Kode-, test- og opskriftsændringer ugyldiggør certifikatet.
Læs [certificeringskriterierne](reports/certification.md) før fortolkning
som en generel garanti.

Offline-funktionstest efter installation:

```sh
python tools/offline_smoke.py
```

Denne test kører EV-, BA- og DYN-presets gennem appen med alle
socket-forbindelser blokeret. En egentlig Streamlit-server kræver kun
loopback-forbindelsen til browseren, ikke internetadgang.

## Samlet test og certificering

```sh
/workspace/em1-venv/bin/python tools/certify_all.py
```

Kommandoen opdaterer automatisk certifikater og det historiske dashboard,
hvis hele den aktuelle testsuite består. LOW/MEDIUM/HIGH-kriterier og
konkrete blokeringer vises i certifikatdata og preset-diagnostikken.
Executable, correct executable og stable er adskilte mål i
[dashboardet](reports/exam_coverage.md); Juni 2021 1b forbliver manual.

## Ny opgave og ekstern blindtest

Appen åbner nu på **Ny opgave**: indsæt tekst og eventuelle tildelinger,
tryk **Analysér opgave**, kontrollér/ret strukturen og bekræft de fysiske
antagelser før **Løs opgave**. Manuel strukturering bevarer teksten.
LaTeX og tekst kan gemmes lokalt; tekstvisningen kan kopieres.

Parseren er begrænset. Brug den assisterede strukturering ved mangler;
en vellykket beregning beviser ikke, at opgaveteksten er fortolket korrekt.
Kurver angives med `source`, `parameter`, `bounds`, `point` og linjetæthed
eller strøm. Linjeelementet beregnes automatisk. Analytisk integration er
valgfri og tidsbegrænset; korrekte integraler bevares. Numerisk integration
kræver alle værdier og en eksplicit nonsingularitetsbekræftelse (`off_source`).

Den eksterne 55-problem-bank, baseline, efter-fix-måling og begrænsninger
beskrives i [blindtestoversigten](reports/blind_unseen_summary.md).
Autonomous og assisted må ikke sammenblandes. Den assisterede måling bruger
menneskeligt gennemgåede input, undertiden med flere beregningsled.

```sh
/workspace/em1-venv/bin/python tools/run_blind.py after
/workspace/em1-venv/bin/python tools/run_blind.py full
/workspace/em1-venv/bin/python tools/summarize_blind.py
```

Den oprindelige baseline er bevaret med kodehashes. Baselinekommandoen
nægter at genmåle under ændret produktionskode.
