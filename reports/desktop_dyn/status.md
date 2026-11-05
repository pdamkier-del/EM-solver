# DYN-desktopintegration – status 5. november 2026

Backendcommit `cc06f5ab620d3469ddef4c714d77e659e1e80c25` blev pushet og
verificeret på `em1-assisted-evening-2026-11-05`.

Der er nu en indlejrbar Qt-komponent med alle otte DYN-kort. Den første
fulde prøve var 2026-01, 2c: tekst, analyseforslag, modelvalg, eksplicitte
givne/enheder/tal, bekræftelse, QProcess, physics-worker og synligt resultat.
Startstrømmen blev 250,549450549451 A og tiden til 1 % 0,104767621731229 s,
som matcher de officielle facitchecks inden for deres tolerancer.

Efter denne prøve blev de øvrige modeller afprøvet. Resultat: syv kendte
historiske dele matcher de facitkontrollerede backendfixtures gennem Qt;
RL-kortet består en separat konstrueret begyndelsesbetingelsesprøve.
RC med manglende Q0 afstås med spørgsmål og uden resultat. Manglende
backendfortolker rapporteres som teknisk opstartsfejl, ikke et fysiksvar.
Tilbagekaldt modelbekræftelse og ændrede inputs fjerner det viste svar.

Hele testsuiten: **834 beståede, 0 fejlede**, heraf **11 faktiske
Qt-integrationstests**. Hele certificerings-/offline-/app-smoke-forløbet
afsluttede med exitkode 0. De otte backendfixtures består desuden med kun
de syv låste runtimepakker under Python `-S`, uden Qt/Streamlit-importer.
Se [maskinlæsbar validering](validation.json) og [fuldt RC-output](rc_qt_response.json).

## Det, der stadig blokerer den ønskede leverance

Den eksisterende frontend er angivet som
`EM1-Solver-Desktop-v1.0.4-Kontrol-2026-11-05.zip`, med kode i
`EM1-Desktop-Prototype/`. Det angivne `sandbox:/mnt/data/...`-link refererer
ikke til en fil, som er tilgængelig i dette workspace. ZIP-filen skal
vedhæftes i denne chat eller lægges på et tilgængeligt repository/link.

Derfor er komponenten **ikke endnu indsat i den eksisterende apps app.py,
backend_bridge.py eller opstartsscripts**. Der leveres ikke en angiveligt
færdig Windows-opdatering på baggrund af gættet frontendkode. Native Windows
er ikke testet. Komponentens grundvisning har tekstresultater og LaTeX-kilde
for mellemtrin; hostens eksisterende matematikrenderer mangler at blive tilkoblet.

Næste konkrete skridt er at modtage ZIP, bevare dens eksisterende flows,
indlejre DYN-komponenten, gentage prøverne i dens faktiske hovedvindue og
pakke den samlede app med en præcis Windows-opdateringsprocedure.
Der tilføjes ingen nye fysikmoduler i dette integrationsarbejde.

[Integrationsvejledning og præcis opgaveliste](../../docs/desktop/ASSISTED_DYN_UPDATE.md).
