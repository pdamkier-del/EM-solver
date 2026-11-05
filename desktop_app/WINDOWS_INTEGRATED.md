# Samlet EM1 Solver-desktopapp

Den uploadede PySide6-app er bevaret med noter, PDF'er, testbesvarelser og
almindelig opgaveindtastning. “Vælg fysisk model” tilføjer den assisterede vej.
Ingen LLM, webserver eller API-nøgle.

## Installation

1. Bevar din gamle app. Udpak hele den nye ZIP i en ny mappe.
2. Installér Python **3.12 x64** med `py`-launcher, hvis det mangler.
3. Dobbeltklik `INSTALL_WINDOWS.bat` én gang online. Et separat miljø oprettes
   i `%LOCALAPPDATA%\EM1\desktop-integrated-20261105`; dit gamle miljø ændres ikke.
4. Dobbeltklik `START_WINDOWS.bat`. Startfilen downloader og installerer intet.
   Fejl skrives i `EM1_START_LOG.txt`.

Backend følger med under `vendor/EM-solver-assisted`. Den gamle backendsetupfil
skal ikke køres for denne pakke. En eksisterende `vendor/EM-solver` bevares til
den almindelige backendvej, hvis den findes.

For installation på en anden computer uden internet: kør først
`PREPARE_OFFLINE_WINDOWS.bat` online på Windows/Python 3.12 x64. Kopiér hele
mappen inklusive wheelhouse. Installeren bruger `--no-index`, når wheels findes.
Python skal stadig være installeret. Runtime kræver ingen forbindelse.

## Assisteret løsning

Indsæt opgaven i det eksisterende opgavefelt og vælg “Vælg fysisk model”.
Vælg kort, givne udtryk og søgte størrelser. Find symboler og angiv deres
enheder og tal i tabellen. Bekræft relevante positive symboler, betingelser
og orientering. Bekræft modellen og tryk “Løs opgave”.

Svar vises i de eksisterende Resultat/Udledning/Forklaring-faner. Forklaring
viser dine bekræftede data og faktisk udførte kontroller. Fortolkningen er
ikke automatisk fysikverificeret. Ét delspørgsmål behandles ad gangen.
Manglende data giver spørgsmål, ikke opfundne værdier. Ændrede modeldata
ugyldiggør det tidligere assisterede svar. Afvent beregning før lukning.

## Native Windows-test før eksamen

Windows kan ikke køres her. Afprøv på din computer:

1. Start med dobbeltklik; åbn noter, PDF og eksisterende testbesvarelse.
2. Slå Wi-Fi fra og genstart. Vælg RC-afladning med `time=t, R=R, C=C,
   Q0=Q0, fraction=1/100`; søg `I_initial, decay_time`.
   Symbolenheder: t=s, R=ohm, C=F, Q0=C; R og C positive.
   Tal: R=`0.25 ohm`, C=`91 mF`, Q0=`5.7 C`.
   Bekræft konstante koefficienter, orientering og model.
   Resultat: ca. **250,55 A** og **0,10477 s**.
3. Fjern Q0: der skal vises spørgsmål og intet resultat.
4. Brug den oprindelige backendknap på `V(x,y,z)=k*x**2. Bestem E.`
5. Kontrollér µ-enheder, formler i alle tre faner og hukommelse i Jobliste.
   Luk og genstart; noter skal stadig findes som hidtil i APPDATA.

Gem logfilen ved fejl og brug din bevarede gamle app. Native Windows,
batchfiler og hukommelse på din konkrete maskine er ikke verificeret af Linux-prøver.

## EV og BA

Modelkortene har EV/BA i navnet. Gauss- og Ampère-regioner indtastes i en
tabel med nedre/øvre grænse, tæthed og (for EV) permittivitet. Brug fx øvre
radius `a+h` med a,h positive, når en regions bredde skal være positiv;
to uafhængige positive radier beviser ikke deres rækkefølge.

For Gauss-kugle kan V og samlet Q findes fra regionerne. V kræver eksplicit
`V(infinity)=0`; udeladte regioner skal bekræftes som vakuum. Denne
potentialkæde understøtter ikke ekstra fladeladninger. Gauss-plan bruger
spejlsymmetri: koordinaten er positiv afstand fra midterplanet; retningen
på den modsatte side skal vendes.

Lederkortet har en tabel med koncentriske lederes indre/ydre radius og
nettoladning. Central ladning, permittiviteter og potentialreference angives
eksplicit. Hulrumskortet bestemmer kun totale overfladeladninger og potentiale
ved sfærisk ydre flade, ikke lokalt felt i et asymmetrisk hulrum.

Biot–Savart kræver orienteret kildekurve, parameter, grænser, strøm og
feltpunkt. Hvis analytisk beregning ikke afsluttes i tidsbudgettet, bevares
integralet som delvis løsning. Det skal ikke læses som et færdigt feltresultat.

Appen løser ikke automatisk hele hovedopgaver, figurer, generelle
Poisson-/Laplace-randværdiproblemer eller vilkårlige kredsløbsnetværk.
Ingen model må vælges alene fordi den giver et ønsket facitsvar.
