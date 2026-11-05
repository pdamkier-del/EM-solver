# Assisteret DYN-backend – særskilt integrationsforslag

Aktuel desktopintegration findes nu i `desktop_app/`; se
[Windows-guide](../../desktop_app/WINDOWS_INTEGRATED.md).
Kataloget indeholder desuden EV/BA-kort fra `em1_solver/assisted_models.py`.
Samme `assisted-1.0`-kontrakt og bekræftelsesregler gælder. Regioner angives
eksplicit som objekter med lower/upper/density og for EV permittivity;
den faktiske desktopapp tilbyder tabelfelter til disse data.
Den tidligere beskrevne DYN-grænseflade bevares.

Denne kontrakt er `assisted-1.0`. Den erstatter **ikke** desktopintegrationens
frosne JSON API 1.0. Der er ingen ændringer i frontend eller nye fysikmoduler.

## Python og proces-entrypoint

```python
from em1_solver.assisted_backend import catalog, plan, respond
suggestions = plan(opgavetekst)  # forslag og evidens, aldrig fysiske givne data
questions = respond(request)   # strukturel kontrol og bekræftelsesspørgsmål
answer = respond(request, solve=True)
```

`respond(..., solve=True)` starter en offline `spawn`-worker pr. delspørgsmål
med 18 sekunders grænse. Brug `if __name__ == '__main__':` og
`multiprocessing.freeze_support()` i et Python-program. Kald ikke direkte fra
Qt's UI-tråd. Alternativet nedenfor kræver ikke multiprocessing i GUI-processen.

CLI modtager ét UTF-8 JSON-objekt på stdin og skriver ét på stdout:

```text
<venv-python> -m em1_solver.assisted_backend
<venv-python> -m em1_solver.assisted_backend --plan
```

`--plan` accepterer kun `{"text":"..."}`. Andre kald kræver kontrakten nedenfor.
Prosa bruges som provenance og til modelkortforslag, **ikke** som en verificeret
fortolkning. Forslag udfylder ingen tal, funktioner eller begyndelsesbetingelser.

## Input

```json
{
  "schema_version": "assisted-1.0",
  "text": "Den oprindelige hovedopgave",
  "confirmed": true,
  "variables": {"time":"t", "R":"Z", "C":"Cap", "Q0":"Q0"},
  "units": {"t":"s", "Z":"ohm", "Cap":"F", "Q0":"C"},
  "positive": ["Z", "Cap"],
  "assumptions": ["constant_coefficients"],
  "subproblems": [
    {"id":"a", "model":"RC_discharge", "wanted":["Q","I"], "orientation_confirmed":true},
    {"id":"b", "model":"RC_discharge", "wanted":["tau"], "orientation_confirmed":true}
  ]
}
```

`variables` er fælles givne data; delspørgsmålets valgfrie `variables` kan
overstyre dem eksplicit. `numbers` angiver eventuelle tal med enheder, fx
`{"Z":"250 mOhm", "Cap":"91 mF"}`; symbolske udtryk og numeriske
indsættelser holdes adskilt. `units` er de faktiske symbolers enheder, ikke
automatisk navnegæt. `positive` er brugerbekræftede symbolantagelser.
`assumptions` kan også stå på det enkelte delspørgsmål. Højst 8 delspørgsmål;
samlet input højst 24000 tegn / CLI højst 96000 UTF-8 bytes.

`catalog()` beskriver alle obligatoriske og valgfrie variable, deres
enhedsroller, modelbetingelser og præcise fortegnskonventioner. Modeller:

| Model | Anvendelse |
|---|---|
| `faraday_flux` | Eksplicit signeret flux pr. vinding |
| `faraday_uniform` | Homogent normalfelt og positivt areal |
| `faraday_integral` | Fuldt fluxintegrand inkl. Jacobian og integrationsgrænser |
| `motional_curve` | Orienteret parameteriseret leder, v og B som vektorer |
| `feedback` | Konstant elektromekanisk kobling, drivkraft og begyndelseshastighed |
| `RC_discharge` | Kildeafbrudt RC-afladning med eksplicit Q(0) |
| `RL_step` | Konstant påtrykt spænding med eksplicit I(0) |
| `displacement_disk` | Ideelle cirkulære plader, homogent aksialt E(t) |

Én vinding skal angives som `N: "1"`; I(0)=0 skal angives eksplicit. Intet
af dette gætttes. Strøm fra Faraday/bevægelses-EMF og R kræver bekræftet
negligerbar selvinduktans; bevægelsesmodellen kræver stationær returvej.
`feedback` kræver den præcise katalogkonvention for koblingens fortegn.
Disse idealmodeller gælder ikke generelle kredsløbsnetværk. RC/RL kræver
konstante koefficienter, og forskydningsstrømsmodellen kræver `vacuum_gap`.
Et tidsafhængigt areal kræver `positive_area_on_interval`; brugeren bekræfter
det fysiske anvendelsesinterval. Positive konstante geometri-/kredsløbsdata,
intervallernes orden og numeriske modstrid kontrolleres også i workeren.

## Output og status

- `needs_confirmation`: `questions` angiver manglende givne/betingelser/retning;
  der foretages ingen beregning.
- `ready`: strukturen er bekræftet; **ikke** en beregnings- eller fysikgodkendelse.
- `not_solved`: fejl/afvisning; ingen successtatus eller opfundet svar.
- `partial`: nogle delspørgsmål afvises, eller kontroller/integraler er uafklarede.
- `calculated_under_confirmed_model`: søgte resultater findes og de tilgængelige
  kontroller er bestået. **Ikke** en påstand om autonomt verificeret fortolkning.

`confirmed_model` bevarer brugerens input. `interpretation_status` er
`user_confirmed` efter bekræftelse; det betyder ikke maskinverificeret fysik.
Hvert `subproblems[]` indeholder eget `status`, `errors`, `verification` og
`solution`. Mislykkede dele skjuler ikke vellykkede dele.

`solution` bruger den eksisterende strukturerede renderer: `results`,
`numerical`, `steps` med stabile ID'er, `checks` og alle tre `views`:
`result`, `derivation`, `explanation`. LaTeX valideres mod `EM1-Math-1`.
Vis altid modellens betingelser og afvisninger sammen med resultatet.

Kontrolresidualer er konkrete, familieafhængige checks. Fx er Faradays
fortegnsrelation en intern konsistenskontrol, **ikke** en uafhængig bekræftelse
af den valgte normal, magnetfeltets homogenitet eller brugerens model.
RC/RL-ODE-residualer og feedback-effektbalance er heller ikke bevis for,
at kredsløbet i figuren svarer til ligningen. Dimensionskontrol alene er
utilstrækkelig. Der loves ikke fuldstændig Maxwell-/randbetingelsesverifikation.

## PySide6 og offline Windows

Eksemplet [pyside_assisted_process.py](../../examples/pyside_assisted_process.py)
bruger `QProcess`: giv den absolutte sti til det eksisterende lokale
`venv\Scripts\python.exe`, repository-mappen og request-objektet. Hold objektet
i live; forbind `completed` og `failed` til GUI'en. `start` er asynkron og
blokerer ikke GUI'en. Arbejdsmappen skal indeholde `em1_solver`.

Backendkrav er uændrede og låst i `requirements-backend-lock.txt`; Python 3.12
er testmiljøet. PySide6 tilhører desktopappen og importeres ikke af backend.
Offline installation kræver allerede installerede pakker eller et lokalt
wheelhouse med wheels til den aktuelle Windows/Python-arkitektur:

```text
venv\Scripts\python.exe -m pip install --no-index --find-links=wheelhouse -r requirements-backend-lock.txt
```

Der downloades ingen model, bruges ingen nøgler og startes ingen webserver.
Workerens udgående socketforbindelser er blokeret. Afvent en kørende request;
at dræbe alene forældreprocessen garanterer ikke worker-oprydning på Windows.
Individuelle delspørgsmål er begrænsede, en batch kan tage op til ca. 8×18 s.

**Windows/Qt er ikke kørt her.** QProcess-eksemplet er et integrationsforslag,
ikke en færdig Windows-app. Den eksisterende frontend er ikke ændret.

## Reproducerbar afprøvning

`data/integration/assisted_v1/` indeholder 8 komplette requests/responses:
7 kendte eksamensmodeller og 1 manglende begyndelsesbetingelse. Kør:

```text
python tools/evaluate_assisted_evening.py
python tools/evaluate_structured_breadth.py
python tools/evaluate_autonomy.py --output-directory reports/assisted_evening/autonomy
python tools/check_assisted_dependencies.py
python tools/certify_all.py
```

Første evaluering gemmer svaret **før** den åbner facitcheckene. Den brede
evaluering løser ekspertkodede modeller uden `expected`, og sammenligner
derefter de cachede resultater. Historiske opgaver er tidligere kendte;
ingen af prøverne er nye, uafhængige blindprøver.
