# Feature freeze: exam-ready-2026-11-05

Når checkpointet er oprettet, tilføjes ingen nye store features før eksamen.
Kun nødvendige fejlrettelser må ændre den frosne version, og de kræver
fornyet regression, blindbank og relevant UI-smoke.

Checkpointets commit findes med:

```sh
git rev-parse exam-ready-2026-11-05^{commit}
```

Den lokale `reports/feature_freeze.json` og den leverede pakkes
`BUILD_INFO.json` registrerer den konkrete SHA. Dette undgår at ændre den
commit, hvis SHA dokumenteres i dens egen tekst.

## Valideringsgrundlag

- Fuld pytest-suite inklusive alle 153 historiske beregningsopskrifter.
- Tier A og hele den eksterne 55-bank gennem offentlig problem-/workervej.
- Faktisk Streamlit-widget-flow for Gauss, Biot–Savart, Ampère, Faraday,
  bevægelsesinduktion, materiale og fysisk afvisning.
- Ny opgave-flow for EV/BA/DYN samt frisk sessions autosave-gendannelse.
- Launcher starter en rigtig lokal server, og HTTP health/startside testes.
- Socket-forbindelser er blokeret under de relevante offline-beregninger
  og AppTest-forløb. Streamlit bruger kun lokal browserkommunikation.

## BA14 og familiecertificering

Den generelle magnetiske dipolrelation er implementeret i vektor- og
vinkelform. Parallel, antiparallel og vinkelret orientering samt
fortegnsvariationer testes. Ny solverfamilie er experimental under den
hidtidige certifikatpolitik, fordi den ikke har native historiske
opskrifter. Den må ikke mærkes stable blot fordi blindtesten består.
De historisk certificerede familier og deres runtime-krav bevares.

## Platformgrænse

Windows-batchfiler, installationsinstruktioner, offline-wheel-forberedelse
og ét-klik-start er leveret. Linux-miljøet kan ikke udføre en native
Windows-dobbeltklik/browser-test. Tagget dokumenterer den verificerede
kode og den Linux-testede app/launcher; det er ikke en påstand om, at en
bestemt Windows-computer er afprøvet. Følg Windows-installationsguiden og
udfør EV/BA/DYN-smoke på eksamenscomputeren før fredag.

## Kendte risici

- Fri tekst alene er svag; brug den bekræftede, assisterede formular.
- Gennemgå symmetri, materialer, randbetingelser og retningsvalg fysisk.
- Ikke alle specialiserede modeller kan beskrives i den hurtige formular;
  den oprindelige solveradgang er bevaret som Specialiseret metode.
- Symbolske standardparametre er ikke tal fra opgaven. Tal og enheder
  skal indsættes eksplicit; komplekse enheder kan kræve avanceret kontrol.
- Et korrekt integral er ikke nødvendigvis et numerisk facit. Singulariteter
  og numerisk konvergens kræver særskilt vurdering.
- Autosave er lokal. Brug separate lokale mapper ved samtidige sessioner.

Portabilitetsrettelsen normaliserer certifikatstier på tværs af Windows/Unix.
Batchfilerne aktiverer Python UTF-8-mode. Inputvalidering adskiller desuden
uafhængige variabelnavne fra numeriske evalueringsværdier. Slutvalidering:
640 beståede tests og uændret grøn historisk/ekstern regression.
