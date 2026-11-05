# EM1 Solver v1.0 – integration med Codex backend

Denne pakke bevarer desktopappens layout fra v0.9 og tilføjer live offline-kald til en separat fysikmotor.

1. Udpak ZIP til f.eks. `C:\EM1`.
2. Python **3.12 anbefales**, fordi Codex har testet backend dér. Har du kun 3.13, prøver installationen den i et separat miljø og advarer om, at den ikke er backend-valideret.
3. Dobbeltklik `SETUP_BACKEND_WINDOWS.bat` i `EM1-Desktop-Prototype` (kræver internet **én gang** for at hente GitHub-kode og Pythonpakker).
4. Dobbeltklik `START_WINDOWS.bat`, indsæt opgave, og klik **Løs opgave med backend**.
5. Detaljer om eventuelle installationsfejl står i `EM1_BACKEND_SETUP_LOG.txt`; opstart i `EM1_START_LOG.txt`.

Integrationskilde: public GitHub repo `pdamkier-del/EM-solver`, branch `desktop-integration-2026-11-05`. Setup læser branchens commit SHA, downloader ZIP med **præcis dette commit** og gemmer SHA i `vendor/EM-solver/EM1_DESKTOP_PINNED_COMMIT.txt`. Ved efterfølgende starter ændres den IKKE. Codex kan fortsætte på en anden branch. Backend-venv: `%LOCALAPPDATA%\EM1\backend312` eller `backend313`; frontend-venv: `%LOCALAPPDATA%\EM1\v`.

Backend er en deterministisk fysikmotor med begrænset autonom opgavedækning. `verified` betyder kun, at dens konkrete kontroller bestod, ikke at enhver opgavetekst fortolkes korrekt. `partial` og `not_solved` skal respekteres. Appen gemmer ikke backendteksten i skyen og ændrer ikke GitHub.

### Begrænsninger
- Selve backendkoden er ikke bundlet i desktop-ZIP; hent den med setup-scriptet. Førstegangsinstallationen kræver internet og Python 3.12 eller 3.13 (kun 3.12 er backend-valideret).
- Native Windows-integration er ikke afprøvet i udviklingsmiljøet; installeret app skal afprøves.
- Figur- og billedopgaver kræver manuel læsning eller udtrykkelig tekstbeskrivelse.
- I `Udledning` vises kun mellemregninger og metodebegrundelser, som backend faktisk leverer. Ingen forklaringer opfindes af UI.
- De fem oprindelige testbesvarelser forbliver tydeligt mærkede som demo.
