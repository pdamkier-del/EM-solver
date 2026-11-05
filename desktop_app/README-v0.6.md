# EM1 Solver v0.6 – Windows desktop

## Start
1. Udpak hele ZIP-filen (fx til `C:\\EM1`).
2. Kør `START_WINDOWS.bat` (Python 3.13 er understøttet af de valgte afhængigheder).
3. Første start installerer `PySide6-Essentials`, `matplotlib` og `PyMuPDF` i `%LOCALAPPDATA%\\EM1\\v`. Internet kræves kun til pakkeinstallation.
4. Ved fejl: send `EM1_START_LOG.txt`.

## Hvad er nyt?
- **Originale PDF-sider i appen** under *Mine noter > Kilder · søg* og *Formler*. Tidligere blev kun udtrukket, matematisk ødelagt PDF-tekst vist.
- PDFsider kan bladres igennem og zoomes; sidetal i notesøgningen går direkte til den korrekte originalside.
- `Opgaveløser > Vis backend-JSON` importerer strukturerede løsningsdata. Test med `examples/cylinder_solution_demo.json`.
- Tre faner – resultat, udledning, forklaring – med *udledning* som standard.
- Originale PDF'er og LaTeX-kilden er bevaret.
- Noter lagres fortsat i `%APPDATA%\\EM1SolverDesktop\\notes.db`.

## Vigtige begrænsninger
- **Den faktiske Codex-fysikmotor er endnu ikke tilkoblet.** JSON-import er en skærmvisningstest, ikke autonom løsning.
- Codex-backendens faktiske `docs/backend/API.md` er ikke tilgængelig i denne pakke. Se `docs/VIEWER_EXCHANGE.md` om adapterformat.
- Matplotlib MathText er *ikke* fuld LaTeX; avancerede `cases`, `aligned`, `\\begin{...}` kan kræve en rendererudvidelse. Originale PDFsider har intet af dette tab.
- UI-start er ikke verificeret på en native Windows-maskine i denne byggeproces.
