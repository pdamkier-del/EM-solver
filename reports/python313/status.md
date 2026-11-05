# Python 3.13 x64-migration

Branch em1-python313-2026-11-05 fra a7126412be66c50c54f46e897a11e16f983e2ba9. Ingen ændringer af fysikmotor, modelkort eller parser. Python 3.12-versionen, main og frosne releases bevares.

## Faktisk kontrolleret

- Standard CPython 3.13.5 x64 på Linux, PySide6 Essentials/shiboken6 6.8.3, SymPy 1.14.0, matplotlib 3.10.8 og PyMuPDF 1.26.7 importeret og brugt.
- Alle 21 eksisterende runtimeversioner understøtter Python 3.13 og er fortsat låst eksakt. Ingen versionsopgradering var nødvendig. Desktopkrav peger nu på hele samme transitive lås frem for åbne versionsintervaller eller en delmængde af GUI-dependencies.
- Faktiske Windows CPython 3.13/x64-wheels hentet: 21/21. Wheel-tags og Requires-Python passer; alle aktive Windows Requires-Dist er opfyldt af låsen. CRC/SHA256 registreret. 262 PE-binaries er AMD64. Qt-platformplugin qwindows.dll og de nødvendige Qt-DLL'er/extensions findes i Windows-wheelen. Lokal pip-resolution med --no-index --platform win_amd64 --python-version 3.13 --abi cp313 lykkes.
- 873/873 regressionstests bestået under Python 3.13.5. Certificering, historisk dækningsopgørelse og offline Streamlit-smokes afsluttede med kode 0. 446 warnings er primært eksisterende Python 3.13-deprecations og test-/biblioteksadvarsler; de er ikke nye fysikfejl og er ikke skjult som beståede fejlsvar.
- De 20 tidligere desktopkontrolopgaver er genafspillet i den faktiske MainWindow, QProcess og worker: 17 fuldt korrekte med brugerhjælp, 3 afståelser, ingen forkerte. Dette er regression, ikke ny blindtest eller en pensumprocent. Automatisk vej: 1 delvis og 19 afståelser.
- Ren separat Python 3.13-venv installeret helt fra lokale Linux-wheels med --no-index, kun de 21 runtimepakker. EV, BA og DYN løst korrekt i den faktiske app med Python-netværk blokeret. PDF rasteriseret, noter gemt og fundet igen ved en senere MainWindow. Backend isoleret under -S med kun de syv backenddependencies; ingen Qt/Streamlit-import nødvendig for backend alene.
- Fire migrationskontroller og 31 målrettede desktop/fysiktests bestået (indgår i de 873); migrationskontrollerne gentaget efter sidste startfiljustering. Den separate lokale fysikdiagnostik består 5/5 efter rettet lokal backendsti.

## Installation

Installér standard Python 3.13 x64 med py-launcher, ikke 3.13t/free-threaded, ARM64 eller 32-bit. Udpak den nye ZIP i en ny mappe og kør INSTALL_WINDOWS.bat. Nyt miljø: %LOCALAPPDATA%\EM1\desktop-python313-20261105. Installer/start kontrollerer interpreterversion, arkitektur og GIL-variant; startfilen binder også backend til samme interpreter, selv hvis en gammel EM1_BACKEND_PYTHON er sat i brugerens miljø. START_WINDOWS.bat downloader og installerer intet. Ældre setup- og startgenveje er omdirigeret til den samlede installation frem for at hente en gammel backend eller genbruge Python 3.12.

Offlineinstallation kan forberedes med PREPARE_OFFLINE_WINDOWS.bat på en Windows/Python 3.13-maskine. Brug den nye wheelhouse, ikke en gammel cp312-wheelhouse. Første installation er ellers online. Runtime kræver intet netværk.

Noterne har uændret format og samme APPDATA/EM1SolverDesktop-mappe. Tag sikkerhedskopi før afprøvning, og kør ikke gammel og ny version samtidigt. PDF-ressourcer og eksisterende opgavefunktioner er bevaret.

## Ikke verificeret native

Ingen native Windows-installation eller -kørsel er gennemført. Windows-wheels og batchfiler er kontrolleret, men det erstatter ikke en test af Win32/Qt-platformplugin, DLL-loading, filrettigheder, py-launcher og DPI på brugerens computer. Kontrollér INSTALL_WINDOWS.bat, START_WINDOWS.bat, en prøvenote efter genstart, PDF'er og de tre kontrolopgaver fra START_HER_DANSK.md, først online ved installation og derefter med Wi-Fi fra. Gem EM1_START_LOG.txt og EM1_ERROR_LOG.txt ved fejl.
