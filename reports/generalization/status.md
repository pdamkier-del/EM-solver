# Testet desktop-udvikling

Branch: em1-generalization-2026-11-05, fra den uændrede integration 706e2711.

- 869/869 regressionstests bestået. tools/certify_all.py afsluttede med kode 0, inklusive historisk dækning og offline Streamlit-smoke. Der er ingen nye ændringer i den manuelle solver eller Streamlit-frontend.
- 26 nye målrettede tests: uafhængige analytiske referenceudtryk, geometri-/domæneafvisning, generel drevet RC/RL, stationære tider, sammensætning og faktisk MainWindow-visning. De er med i de 869, ikke ekstra historisk dækning.
- 20 nye spørgsmål gennem den faktiske PySide6-app: 17 fuldt korrekte med bekræftede modeller og input, 0 delvise, 0 forkerte, 3 afståelser. Automatisk særskilt: 0 fulde, 1 delvis, 0 forkerte, 19 afståelser. Ingen pensumprocent udledes af dette lille selvkonstruerede sæt.
- Originale noter, PDF-visning og opgavefunktioner er bevaret; en ny assisteret formular og fælles efterbehandling bruges uden at erstatte den gamle backendvej.
- Dependencies genafspillet offline under Python -S med kun de syv låste backenddistributioner, uden frontendimports. Ingen netværk tilladt i beregningsworker eller evaluerings-GUI.
- Ingen native Windows-test er udført. Installation/batchstart, DPI, filstier og noter på brugerens Windows skal kontrolleres. 21 fastlåste Windows x64/Python 3.12 wheels var allerede hentet og hashkontrolleret for den uændrede dependency-fil; det er ikke en Windows-installationstest.

## Vigtige praktiske grænser

Formulararbejdet er fortsat betydeligt. De løste evalueringsopgaver krævede 21–46 semantiske input-/bekræftelseshandlinger; dette er ikke målte menneskelige klik. Taloverførsel kan reducere arbejdet, men erstatter ikke en sikker fortolkning af figurer, geometri og forudsætninger.

Ved sammensatte formler kan symbolscanneren også bede om enheder for beregnede resultatreferencer (fx E:V/m og V:V). Disse enheder blev indtastet eksplicit i EV5. Motoren og spørgsmålene blev ikke rettet under evalueringen. Flere rødder og ukendte domæner mærkes betingede; identiteter eller ingen endelig rod giver ikke en opfundet tid.

Kubiske ledere/generelle randværdi-PDE'er, hysterese uden materialedata og RLC-kredse er ikke dækket af de nye kort. Generelle vektorfladeintegraler kræver eksplicit parameterisering. Magnetisering uden yderligere geometri bestemmer ikke H/B alene. Lokale ekstrema er ikke automatisk globale ekstrema.

## Pakning

Ny ZIP: distribution/EM1-Solver-Desktop-Development-2026-11-05.zip. BUILD_MANIFEST.json angiver det præcise kildecommit og SHA256 for hver medfølgende fil. INSTALL_WINDOWS.bat bruger et nyt miljø desktop-development-20261105; den gamle integrationsinstallation ændres ikke. Notedatabasen deles fortsat, så tag backup og undgå samtidige versioner. Pakken indeholder kildekode og en installationsprocedure, ikke en selvstændig Windows .exe.
