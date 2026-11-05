# Assisteret DYN: indlejring i den eksisterende PySide6-app

Status: komponenten er testet med rigtige Qt-widgets og backendprocesser på
Linux/offscreen. Den eksisterende desktop-ZIP er endnu ikke modtaget i dette
workspace; integration i dens `app.py` er derfor **ikke** udført. Dette dokument
er udviklerintegration, ikke en påstand om en færdig Windows-opdatering.

## Bevar den hidtidige backend

`em1_solver.backend.respond`, JSON API 1.0 og de eksisterende Streamlit-flows
ændres ikke. Den assisterede side bruger alene `assisted-1.0` i en separat
proces. De to veje kan eksistere samtidigt i desktopappen.

Den indlejrbare komponent findes i `desktop_integration/dyn_panel.py`:

```python
from desktop_integration.dyn_panel import DynPanel

dyn_panel = DynPanel(
    python_exe=backend_python_exe,  # absolut sti til backendens python.exe
    repository=backend_repository, # mappe med em1_solver/
    parent=existing_window,
)
# Indsæt dyn_panel i den eksisterende apps tab/stack/layout.
# Eksisterende kontroller og backend_bridge forbliver på deres hidtidige vej.
dyn_panel.solutionReady.connect(existing_solution_handler)  # valgfrit
```

Hostmiljøet skal kunne importere `desktop_integration` og kataloget fra
`em1_solver.assisted_backend`. Backend-Python kan være en særskilt installation.
Qt skal ikke importeres i physics-workerprocessen. Den faktiske frontend skal
afprøves med dens fortolkning af backendplacering og med dens eksisterende
opstartsscripts; det kan ikke afgøres ud fra filnavne alene.

`solutionReady` udsender hele den assisterede JSON-response, også afvisninger.
Den gamle responseschema-validator må ikke bruges på denne nye kontrakt.
Hostens eksisterende matematikrenderer kan anvende `solution.steps[].latex`
og `solution.views`. Komponentens egen enkle visning viser LaTeX-kildetekst for
mellemtrin og tekstudtryk for resultater; den indeholder ingen webrenderer eller
CDN. Det er ikke en erstatning for hostens eksisterende LaTeX-renderer.

## Funktionelt flow

1. Indsæt den oprindelige opgavetekst. Analysér viser modelkortforslag; ingen
   modeldata eller tal udfyldes fra gæt eller facit.
2. Vælg et af de otte DYN-kort. Udfyld udtryk og søgte størrelser.
3. Find symboler i egne udtryk. Gennemgå enheder, tal med enheder og positive
   symbolantagelser i tabellen. Udtryksfelter indeholder matematik, ikke SI-tal
   med enheder; numeriske SI-værdier hører til i symboltabellen.
4. Bekræft relevante modelbetingelser og den viste præcise orientering.
5. Bekræft modellen og tryk Løs. UI'en forbliver responsiv under `QProcess`.
6. Se betinget resultat, faktisk udførte kontroller og eventuelle afvisninger.

Ændrede inputs ugyldiggør den tidligere løsning og brugerbekræftelse. Kopiér
løsning kopierer det synlige output, inklusive forbehold. Der foretages ingen
autonom fortolkning af figurer eller generelle kredsløbsnetværk.

Denne formular løser **ét delspørgsmål ad gangen**, eventuelt med flere søgte
størrelser. Den underliggende backend kan modtage flere eksplicitte delspørgsmål,
men formularen lover ikke automatisk løsning af hele hovedopgaver.

`dyn_panel.busy` og `activityChanged(bool)` gør det muligt at holde den
eksisterende apps lukning tilbage under beregning. Hostens `closeEvent` skal
afvise lukning, mens komponenten er busy; en lukning af hele hovedvinduet
behøver ikke kalde barnets `closeEvent`. Kill af kun forældreprocessen kan
efterlade en worker på Windows. Afvent dens tidsgrænse på 18 sekunder.

## Afprøvede konkrete eksamensdele

| Del | Model | Kontrolleret gennem Qt |
|---|---|---|
| 2026-01, 2c | RC-afladning | Startstrøm ≈250,55 A; tid til 1 % ≈0,105 s; symbolske outputs |
| 2025-01, 6a | Homogent normalfelt/Faraday | Samme symbolske resultater som den facitkontrollerede backendfixture |
| 2021-06, 6a | Bevægelsesinduktion | Strøm, ekstern kraft, mekanisk effekt og varme |
| 2023-02, 6a | Forskydningsstrøm | J_d, I_d og B med eksplicit vakuum-/idealmodel |
| 2023-11, 5c | Elektromekanisk tilbagekobling | Terminalhastighed |
| 2026-01, 3a | Fluxintegral | Flux, strøm og varme |
| 2023-02, 5b | Givet flux | EMF og effekt |

RL-kortet er desuden testet med en konstrueret opgave med ikke-nul I(0);
det er **ikke** en ottende historisk facitvalidering. RC med manglende Q0
giver spørgsmål og intet resultat. Manglende backendfortolker giver en synlig
opstartsfejl. Alle prøver bruger faktiske widgets, knapklik, QProcess, den
afgrænsede worker og resultatvisningen; ingen mock-solver.

## Installation og native Windows-kontrol

Backendkrav forbliver `requirements-backend-lock.txt`. Et separat testmiljø kan
installere `requirements-desktop-integration.txt` (PySide6 6.8.3 er testet).
Opgrader ikke blindt den eksisterende apps Qt-miljø. Brug dens aktuelle
afhængigheder eller et separat testmiljø, og bevar den tidligere app som backup.

Offline installation kræver på forhånd Windows-wheels til Python-versionen:

```text
python -m pip download --only-binary=:all: --dest wheelhouse -r requirements-desktop-integration.txt
python -m pip install --no-index --find-links=wheelhouse -r requirements-desktop-integration.txt
```

Download-trinnet kræver internet og skal køres på den relevante Windows/Python-
platform før eksamen. Runtime bruger ingen internetforbindelse, API-nøgle eller LLM.
Native Windows skal stadig verificere interpretersti, processtart, lukning,
unicode/enheder og hostens matematikvisning med Wi-Fi slået fra.

Linux-testkommando:

```text
QT_QPA_PLATFORM=offscreen python -m pytest -q tests/desktop/test_dyn_panel.py
```
