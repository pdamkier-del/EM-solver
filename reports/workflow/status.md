# Praktisk desktopgennemgang

Branch em1-desktop-workflow-2026-11-05 fra e5130b1. Ingen nye fysikmodeller eller kernel-omskrivning. Den gamle Python 3.13-pakke, øvrige branches og frosne releases bevares.

| Opgave | Resultat fra faktisk app | Semantiske brugerhandlinger | Manuelle data |
|---|---|---:|---|
| Brugerens præcise LaTeX-cylinder, alle a/b/c | J0=2I/(pi*a²)≈3183,10 A/m²; B inde=mu0*I*s³/(2pi*a⁴), B ude=mu0*I/(2pi*s); 5 µT og 20 µT | 4 | Ingen genindtastning; bekræft stationær, uendelig, ikke-magnetisk model |
| V(x,y,z)=a*x²+b*y², E og rho | E=(-2ax,-2by,0), rho_total=-2eps0(a+b) | 4 | Ingen tal for a,b; bekræft elektrostatik og samlet rho |
| KU februar 2024 opg. 4b, uændret råtekst | Korrekt regionalt B og 0, ca. 62 mT, ca. 31 mT | 5 | Ret én ødelagt J-formel fra originalbilledet; bekræft idealmodel/mu0 |
| Samme historiske hovedopgave 4a+b med fælles data | Korrekt strømintegral og B; numerisk I≈966 A, dokumenteret uenighed med trykt 70 kA | 5 | Samme ene formelrettelse; ingen tal fra facit bruges som input |

Handlingerne er indsæt tekst, analysér, bekræft, beregn. Historisk råtekst tilføjer én formelrettelse. Dette er reproducerede semantiske widgethandlinger, ikke en måling af menneskers læsetid, musebevægelser eller tastetryk. Den afprøvede gamle manuelle potentialvej krævede 18 sådanne handlinger. Der foreligger ikke et komplet før-antal for cylinderen, fordi normaliseringen ikke var tilgængelig som et forståeligt formularforløb. Den gamle direkte backendvej kunne stadig bruges separat; der hævdes ikke, at 18 var den teoretisk korteste gamle vej.

## Hvad er faktisk testet?

884 regressionstests bestået på CPython 3.13.5/Linux, kode 0 i hele certificerings-/offline-smokepipelinen. 11 nye gennemgangstests indgår i de 884 og er gentaget efter den sidste præsentationsrettelse; de skal ikke tælles dobbelt. Derudover er de fire forløb genafspillet med netværk blokeret i samme MainWindow, med QProcess, eksisterende fysikworker og alle tre løsningsfaner. Ingen registrerede LaTeX-visningsfejl. Testene omfatter uklare enheder, modstridende tal, endelig geometri, manglende retning, kildeformel fra beskadiget PDF og forældet analyse efter tekstændring.

Kernefysikken er uændret. De to dokumenterede integrationstilpasninger er fjernelse af en overflødig vakuumbetingelse for samlet rho fra V og binding af et tidligere beregnet scalarresultat som evalueringsværdi. Se root_cause.md for præcis begrundelse og før-billeder.

## Facitafvigelse

Facit er åbnet efter beregningerne. Opgave 4b stemmer med det trykte facit. For 4a står det korrekte symbolske integral, men tallet 70 kA stemmer ikke med S=3,1 mm og J0=96 A/mm². Integral og Ampère-kontrol fra det angivne 62 mT giver begge cirka 966 A. Dette registreres som en facitafvigelse, ikke som fuld numerisk facitoverensstemmelse og ikke som grund til at hardkode et andet svar.

## Praktiske grænser og Windows

Den korte gennemgang gælder potentialer V(x,y,z) og massive aksiale cylinderfordelinger. Andre modeller bruger fortsat den bevarede manuelle eller direkte vej. Der læses ikke figurer eller OCR. Usikker eller beskadiget formel kræver rettelse fra opgaven; flere delproblemer med forskellige fysiske kilder skal opdeles. Der gættes ikke enheder ved underbestemte dimensionskrav, og rho_total må ikke forveksles med fri ladning i et dielektrikum. Magnetfeltmodellen kræver en begrundet mu0-/symmetribekræftelse, når teksten ikke fastlægger dem.

Native Windows er ikke testet. Python 3.13 x64 og de 21 låste afhængigheder er uændrede fra den senest verificerede Windows-wheel-kontrol. Udpak i en ny mappe og brug START_WINDOWS.bat; hvis Python 3.13-miljøet ikke allerede findes, køres INSTALL_WINDOWS.bat én gang. Første installation kan kræve internet; runtime er offline. Noter og PDF-visning er bevaret, og notedatabaseformatet ændres ikke. Tag backup af APPDATA/EM1SolverDesktop og undgå at køre to versioner samtidig.
