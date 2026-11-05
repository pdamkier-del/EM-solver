# Samlet desktopversion – 5. november 2026

**Aktuelle instruktioner: [WINDOWS_INTEGRATED.md](WINDOWS_INTEGRATED.md).**
Brug Python 3.12 x64, kør `INSTALL_WINDOWS.bat` én gang og derefter
`START_WINDOWS.bat`. Backend følger med. Startfilen installerer intet.
De ældre prototypeinstruktioner nedenfor er bevaret som historik og beskriver
ikke den nye installationsprocedure.

---

# EM1 Solver – Windows desktopprototype

Dette er en **selvstaendig Qt/PySide6-desktopapp**, ikke en browserapp. Designet er lavet som et separat frontend-spor, saa den eksisterende Codex-backend ikke aendres.

## Start paa Windows

1. Installer Python 3.10 eller nyere fra python.org (inkluder Python i PATH).
2. Udpak ZIP-filen til en almindelig mappe.
3. Dobbeltklik `START_WINDOWS.bat`.
4. Foerste start installerer PySide6 i en lokal `.venv` og kræver internet. Herefter er brugen offline.

Manuel start: `pip install -r requirements.txt` og `python app.py`.

## Det fungerer allerede i koden

- Fem hovedsider: Opgaveloeser, Mine noter, Formler, Eksamen, Historik.
- Notesidepanel ved siden af opgaveløseren, som kan skjules (Ctrl+Shift+N).
- Lokal SQLite-lagring, automatisk notesave, opret/slet/søg i noter.
- Tre præsentationsniveauer: Resultat, Udledning og Forklaring.
- Tre gennemregnede, **foruddefinerede** eksempler med markering af demonstrationsstatus.
- Lokal adgang til din originale LaTeX-formelsamling, dens PDF, en PDF med geometri/regneteknik samt historiske eksamenssæt og facit.
- Gem aktuel opgavetekst og viste resultater som en redigerbar note.

## Ikke implementeret endnu

- Den virkelige EM1-solver fra Codex er ikke tilsluttet, da dens repository ikke var tilgængeligt i dette arbejdsrum. Fri dansk tekst giver derfor korrekt **Ikke løst** i stedet for et opdigtet svar.
- Import af figurer og direkte indlejret PDF-visning.
- Desktop-appens native Windows-afprøvning; denne kode er statisk kontrolleret i et miljø uden installeret PySide6. Startscriptets PySide6-installation er derfor ikke testet på Windows.
- Søgning i original-PDF-tekst, visuelt matematik-rendering, produktionshistorik.
- En kompileret `.exe`: det er en Python-desktopapp, der startes med et `.bat`-script.

## Data

Redigerbare noter lagres i `%APPDATA%\EM1SolverDesktop\notes.db` på Windows. De originale noter under `resources/` er pakket med som **read-only referencefiler**. Del aldrig notebook-databasen uden at vide, hvad den indeholder.

## Backend-integration

Udskift kun `SolverPage.solve()` med adapteren til Codex-backendens strukturerede resultat (opgavefortolkning, trin, svar, status). Backend bør ikke importere Qt. Bevar tydelig status for uverificerede svar.

## Fejl ved opstart (rettet launcher)

Brug `START_WINDOWS.bat`. Den opretter `EM1_START_LOG.txt` i appmappen, og `run_app.py` opretter `EM1_ERROR_LOG.txt` ved en Python-fejl. Hvis appen ikke aabner, kan du dobbeltklikke `START_DEBUG.bat`, eller sende indholdet af logfilen. Python 3.13 er understøttet, men PySide6 skal installeres foerste gang.

Hvis installationen af .venv er afbrudt: luk appen, slet **kun** `.venv`-mappen inde i den udpakkede appmappe, og start igen. Slet ikke dine noter: de ligger i `%APPDATA%\EM1SolverDesktop`.

## v0.2 – matematisk visning
- Rigtige formelglyffer og brøker via Matplotlib MathText, der tegner inde i Qt-vinduet (ingen browser).
- Alle tre solverfaner understøtter formelblokke.
- Noter har fanerne Redigér og Matematikvisning. Skriv formler som `\[\frac{Q}{\varepsilon_0}\]` eller `$$\frac{Q}{\varepsilon_0}$$` på separate linjer.
- MathText understøtter en delmængde af LaTeX; fulde LaTeX-dokumenter og `cases`-miljøer understøttes endnu ikke. Ved visningsfejl vises kildeformlen og fejlen i stedet for et forkert resultat.
- Appen er stadig en frontendprototype; den egentlige Codex-solver er ikke koblet på.
- Eksisterende lokale noter i %%APPDATA%%/EM1SolverDesktop/notes.db bevares ved opgradering.

## v0.3 – begrundelser som del af løsningsmotorens outputstruktur
- Fanen **Udledning** viser nu hvert trin med fysisk **Hvorfor**, matematisk ligning og **Kontrol**, ikke blot en efterfølgende forklarende tekst.
- Knappen **Vis fysiske begrundelser i udledningen** skifter mellem forklarende eksamensgennemgang og ren udledning.
- Fanen **Forklaring** viser det samlede pædagogiske forløb.
- Tre indbyggede eksempler er udvidet til i alt 12 begrundede trin med 15 testede matematikblokke.
- `EXPLANATION_STEPS` er et integrationsforlæg til Codex: hvert trin skal have `title`, `why`, `math` og `check`. Disse begrundelser skal komme fra den faktiske fysiske opgavemodel, ikke fra generiske tekstskabeloner.
- **Bemærk**: Indtil Codex-motoren kobles på, er kun de tre uændrede demoopgaver aktive. Appen opfinder ikke selv en begrundelse til fritekst.


## v0.4 – Integreret notesamling
- Åbn **Mine noter** eller sidepanelet ved Opgaveløser.
- Vælg **Kilder · søg** for at søge i 54 sider fra dine to EM-noter PDF'er.
- Et opslag viser tekst fra den tilsvarende side. Åbn original PDF-side for korrekt matematisk layout og figurer.
- Klik **Lav redigerbar kopi** for at oprette et selvstændigt opslag i dine egne noter.
- Dine tidligere redigerbare noter ligger fortsat i `%APPDATA%\EM1SolverDesktop\notes.db`.
- Installerede tredjepartsafhængigheder ændres ikke. Appen bruger samme opstartsfiler som før.
- PDF-kilder opdateres ikke, når du redigerer en kopi. Søgning i kilder er ikke den automatiske Codex-fysikmotor.


## v0.5 – automatisk noterelation

Når opgaveteksten ændres, søger appen lokalt i de 54 indekserede PDF-sider og viser op til fire relaterede opslag i solvervinduet. Klik på et opslag for at åbne det præcise kildeopslag i højre sidepanel; derfra kan PDF-originalen åbnes. Søgeresultatet er en heuristisk tekstmatch, **ikke** et bevis for at Gauss eller en anden løsningsmetode er fysisk rigtig. Ingen internetforbindelse eller backend påkrævet. Den eksisterende Codex-solver er stadig ikke forbundet.

## v0.5.1 – Windows installationsfix
- Erstattet `PySide6` meta-pakken med `PySide6-Essentials`, fordi appen kun bruger QtCore/QtGui/QtWidgets. Dette undgaar download og installation af QtWebEngine, som gav Windows `WinError 2` / lange sti-navne.
- Hvis installationen tidligere stoppede under pip: luk appen, slet kun `.venv` i appmappen, og start `START_WINDOWS.bat` igen. Dine redigerbare noter i `%APPDATA%\EM1SolverDesktop` beroeres ikke.
- Undgaa at udpakke appen i flere indlejrede mapper under Downloads, hvis Windows har deaktiveret lange filstier.
