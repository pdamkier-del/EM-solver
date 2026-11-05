# Start her – EM1 Solver, udviklingsversion

## Installér uden at ændre din gamle app

1. Installér Python 3.12 x64 med Python Launcher (`py`).
2. Udpak hele ZIP-filen i en NY mappe. Kør ikke direkte inde fra ZIP'en.
3. Dobbeltklik INSTALL_WINDOWS.bat én gang med internet. Vent på “Installation OK”.
4. Dobbeltklik START_WINDOWS.bat. Denne fil downloader intet.
5. Slå Wi-Fi fra, luk og genstart, og gennemfør en kontrolopgave.

Programmet kræver Python og de installerede dependencies; ZIP'en er en samlet
kilde-/installationspakke, ikke en selvstændig .exe. Denne udviklingsversion
har et separat Python-miljø. Noter ligger fortsat under APPDATA/EM1SolverDesktop;
begge appversioner bruger samme notedatabase. Tag kopi af denne mappe før
første afprøvning, og undgå at have begge appversioner åbne samtidig.

Native Windows er ikke testet i udviklingsmiljøet. Test derfor selv opstart,
PDF-visning og at en prøvenote bevares efter genstart. Ved fejl: gem
EM1_START_LOG.txt og eventuelt EM1_ERROR_LOG.txt fra programmappen.

## Den mest pålidelige arbejdsgang

1. Indsæt ét delspørgsmål sammen med de fælles data, som det afhænger af.
   Hele hovedopgaven kan bruges som kontekst, men løs ét delmål ad gangen.
2. Klik “Vælg fysisk model” og derefter “Analysér opgave”. Forslag er hjælp,
   ikke et bevist modelvalg. En lang ledning er ikke automatisk uendelig.
3. Vælg det korrekte EV-, BA- eller DYN-kort. Kontroller navn, orientering og
   betingelser. Hvis intet kort passer, brug ikke et tilnærmet kort uden
   en fysisk begrundet, udtrykkelig idealisering.
4. “Overfør eksplicitte tal” kan kopiere sikre skalare tildelinger som
   R=12 ohm og L=85 mH til det valgte kort. Det udfylder ikke geometri,
   vektorer eller implicitte oplysninger og markerer ingen antagelser.
5. Skriv symbolske udtryk i formularen, fx R, L, I0 og v0*exp(-R*t/L).
   Brug ** til potenser, * til multiplikation, pi og lister som [0,0,B0].
   Skriv tal med enheder i symboltabellen, fx 85 mH. Enhedsnavne: ohm,
   uF, uC, mT, cm. Brug 1 som enhed for dimensionsløse symboler.
6. Klik “Find symboler i mine udtryk”; udfyld enheder og eventuelle tal.
   Markér kun symboler positive, når opgaven faktisk tillader det.
7. Angiv søgte resultatnavne fra kortets hjælp. Bekræft hver nødvendig
   betingelse, retning og hele modellen. Klik “Løs opgave”.
8. Læs Resultat, Udledning og Forklaring. Kontroller især fortegn,
   komponentbasis, område og om kontroller er bestået, uafklarede eller
   fejlet. “Brugerbekræftet” er ikke automatisk fysikverifikation.
9. Skifter du data eller model, skal du beregne igen. Gem den nye besvarelse
   som note. Brug aldrig et gammelt svar efter en ændring.

Den almindelige “Løs opgave med backend” er stadig tilgængelig som et hurtigt
første forsøg. Den assisterede vej er det sikrere valg ved nye geometrier,
figurer, flere regioner eller mangelfuld råtekstgenkendelse.

## Tre korte installationskontroller

### EV: elektrisk felt fra potentiale

Opgave: V(x,y,z)=k*x**2 i vakuum, k=100 V/m^2. Find E ved x=2 cm.
Kort: EV – felt og ladning fra potentiale.
Felter: V=k*x**2; coordinates=[x,y,z]; system=cartesian; søges E.
Symboler: k:V/m^2, tal 100 V/m^2; x,y,z:m, tal 2 cm,0 m,0 m.
Bekræft elektrostatik og vakuum. Forvent E=(-4,0,0) V/m.

### BA: uendelig ret ledning

Opgave: I=2 A langs +z, afstand s=5 cm, vakuum. Find B.
Kort: BA – Ampère, uendelig ledning. Felter I=I og distance=s; søges B.
Symboler I:A, tal 2 A; s:m, tal 5 cm, positiv.
Bekræft uendelig ledning, magnetostatik og ikke-magnetisk medium.
Forvent B=8 mikrotesla i positiv phi-retning.

### DYN: RL med nulpassage

Opgave: R=12 ohm,L=85 mH, konstant voltage=-6 V,I0=0.32 A.
Kort: RL – spændingstrin. Felter time=t,R=R,L=L,voltage=V,I0=I0.
Søges I, initial_slope, zero_time.
Symboler t:s; R:ohm (12 ohm), L:H (85 mH), V:V (-6 V), I0:A (0.32 A).
Markér R,L positive, bekræft konstante koefficienter og orientering.
Forvent I(t)=-0.5+0.82*exp(-t/(0.085/12)) A,
startafledt ca. -115.765 A/s og nulpassage ca. 3.50410 ms.

## Hvornår skal du være særlig forsigtig?

- Figurer/OCR aflæses ikke. Indtast selv mål, retninger og koordinater.
- Alle kort dækker bestemte geometrier; programmet løser ikke hele pensum.
- Symbolsk tidsgrænse, formelle integraler eller betingede rødder er ikke
  automatisk en komplet løsning. “Delvis” skal læses bogstaveligt.
- Billedladningskortet gælder det erklærede fysiske område, ikke inde i
  hjælpekildernes område. Brug ikke fiktiv parenergi som fysisk energi.
- Magnetisering alene bestemmer ikke generelt H eller B. Kuglekortet
  kræver uniform M og ingen frie strømme eller påtrykt felt.
- RC-afladningskortets positive I er afladningsretningen. Det generelt
  drevne RC-kort bruger positiv opladningsstrøm dQ/dt.
- Ekstremumstider er stationære punkter med lokal andenafledte-test;
  globale ekstrema kræver også endepunkter og interval.
- Efterbehandling kræver en eksplicit fysisk sammenhæng. Fx B*A er kun
  fluxen for et homogent normalfelt med det angivne areal.
- Indbygget formelsamling er fortsat mærket GAMMEL_2026-10-30.
  Kontrollér den mod kursets aktuelle materiale.

## Registrér en fejl, så den kan reproduceres

Gem opgavetekst/figur, valgt kort, alle felter, symbolenheder/tal,
antagelser/orientering, det viste resultat og fejlbeskeden. Notér branch
og commit fra downloadlinket. Angiv separat hvad facit siger, og hvad du
forventede. Brug kun facit til kontrol efter beregningen.
