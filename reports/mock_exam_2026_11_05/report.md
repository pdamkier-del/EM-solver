# EM1 Solver – mock-eksamen, 5. november 2026

**Resultat: 11 fuldt korrekte, 1 delvist korrekt, 0 forkerte og 2 afståelser ud af 14 delopgaver.**

App: den faktisk leverede Windows-kildepakke fra commit `59b4decefd119b12c44230f8b18b0b6db6889a8e`, kørt på Linux med Python 3.13.5, PySide6 MainWindow, produktionsstylesheet og QProcess-worker. Ingen solver-/parser-/UI-ændringer under testen. Den oprindelige ZIP er uændret. Native Windows er ikke testet.

[Læs mock-eksamen](exam.md) · [Alle appkald](execution.json) · [Referenceberegninger](reference_and_grade.py) · [Bedømmelse med residualer](grading.json)

## Bedømmelse for hele sættet

| Kategori | Antal |
|---|---:|
| Fuldt korrekte med brugerhjælp | 11/14 (78,6 %) |
| Delvist korrekte | 1/14 |
| Forkerte | 0/14 |
| Afstået | 2/14 |
| Fuldt automatisk fra tekst | 0/14 |

Der er seks hovedopgaver. Tre hovedopgaver blev løst fuldt; tre har en manglende eller delvis delopgave. EV: 4 fulde og 1 afståelse. BA: 4 fulde og 1 afståelse. DYN: 3 fulde og 1 delvis. Tallene er delopgavetælling, ikke en vægtet eksamenskarakter og ikke en procentdel af hele pensum.

## Delopgaver

| Del | Fysik | Resultat | Appvej og brugerarbejde |
|---|---|---|---|
| 1a | Integreret ladning i kugle | Fuldt korrekt | Manuel modelopsætning: 23 semantiske handlinger |
| 1b | Gauss-felt inde/ude | Fuldt korrekt | Manuel modelopsætning: 23 semantiske handlinger |
| 1c | Potentiale i centrum og udenfor | Fuldt korrekt | Manuel modelopsætning: 34 semantiske handlinger |
| 2a | Billedladning: kraft og induceret ladning | Fuldt korrekt | Manuel modelopsætning: 22 semantiske handlinger |
| 2b | Kvasistatisk arbejde ved flytning | Afstået | Manuel modelopsætning: 22 semantiske handlinger |
| 3a | Normalisering af J0 fra total I | Fuldt korrekt | Kort gennemgang: 4 handlinger for hele opgave 3 tilsammen |
| 3b | Ampère-felt i begge regioner | Fuldt korrekt | Kort gennemgang: 4 handlinger for hele opgave 3 tilsammen |
| 3c | To numeriske feltværdier | Fuldt korrekt | Kort gennemgang: 4 handlinger for hele opgave 3 tilsammen |
| 4a | Bundne volumen-/overfladestrømme | Fuldt korrekt | Manuel modelopsætning: 24 semantiske handlinger |
| 4b | H/B fra magnetisering og randbetingelser | Afstået | Manuel modelopsætning: 24 semantiske handlinger |
| 5a | Flux og emf, både B(t) og areal ændres | Fuldt korrekt | Manuel modelopsætning: 27 semantiske handlinger |
| 5b | Induktiv strøm, varme og strømretning | Delvist korrekt | Manuel modelopsætning: 47 semantiske handlinger |
| 6a | Stangens hastighed, tidskonstant og terminalhastighed | Fuldt korrekt | Manuel modelopsætning: 33 semantiske handlinger |
| 6b | Strøm og Joule-varme med tilbagekobling | Fuldt korrekt | Manuel modelopsætning: 37 semantiske handlinger |

## Hvad krævede hjælp?

Tre delopgaver (hele opgave 3) blev løst via den korte gennemgang: indsæt hovedopgaven, analysér, bekræft model og beregn. Fire handlinger dækker alle tre delopgaver; de må ikke summeres til 12. Ingen formel eller enhed skulle skrives igen.

Otte fuldt korrekte delopgaver og den ene delvise krævede den manuelle formular. Alle manuelle forsøg, også afståelserne, krævede 22–47 semantiske indtastninger/valg/bekræftelser i den anvendte forsøgsprocedure. Det omfatter valg af model, funktioner, symbolenheder, tal, betingelser og eventuelle efterbehandlinger. Det er ikke målt læsetid eller et minimum af menneskelige museklik; testværktøjet gentog fælles felter ved separate delopgaver, som en erfaren bruger kan genbruge.

Ved 5b blev alene appens faktiske beregnede emf fra 5a overført til den drevne RL-model. Brugeren skulle kende forbindelsen mellem emf og kredsløbsligning samt indtaste Joules lov og tidsintegralet. Ingen referenceværdi for I eller varme blev indtastet. Ved 6a/b blev koblingen k=B*ell identificeret fra geometri og fortegn. Det er betydelig faglig brugerhjælp, ikke automatisk opgaveforståelse.

## Mangler og afståelser

- **2b:** Kortet for jordet plan kan finde kraften, men tilbyder ikke en komplet arbejdskæde for at flytte den virkelige ladning. Appen afstod. Reference: W_ext=q²/(32*pi*epsilon_0*d)>0. Ingen fiktiv parenergi blev indsat som en fysisk energi.
- **4b:** Det generelle M-kort kræver H som input for at give B. Det udleder ikke selv H fra de frie strømme og fjernbetingelsen. Appen afstod frem for at få H=0 indtastet som et facitsvar. Reference: H=0; B=mu_0*M inde og nul ude.
- **5b:** De eksakte strømfunktioner, I(T) og varmen er korrekte. Den efterspurgte rumlige forklaring af strømretningen mangler: svaret har tomt direction-felt og kobler ikke den negative strøm eksplicit til med-uret set fra +z. Derfor delvist korrekt, selv om matematikken er korrekt.

## Direkte tekstvej

Den eksisterende direkte backend afstod fra alle 14 delopgaver. Eksempelvis udløste kugleopgaven en besked om flere delopgaver, selv om hvert kald kun indeholdt én delopgave med fælles givne data. Cylinderteksten med både total I og J(s) blev opfattet som flere uafhængige kilder, og ord fra strømretningen endte blandt de efterspurgte symbolenheder. Dette er læse-/arbejdsgangsproblemer, ikke dokumentation for at integrationen af rho eller J er umulig. Den korte cylindergennemgang håndterede samme hovedopgave korrekt.

De direkte forsøg og assisterede forsøg er alternative ruter. Hvert direkte forsøg bestod af tekstindsættelse og beregningsknap; disse to handlinger ligger ud over manuelle forsøg, hvis man som bruger først prøver den direkte vej.

## Referencekontrol og testens begrænsning

Spørgsmål og indtastningsplaner blev skrevet og SHA256-låst før første beregning. Alle 14 delopgaver tæller, også dem uden et passende komplet kort. Det faktiske pakkede appvindue blev brugt med Python-netværksforbindelser blokeret; alle tre svarfaner blev gennemgået for renderingsfejl. Der var ingen registrerede LaTeX-visningsfejl.

Referencesvar blev beregnet efter alle appkald i et separat script uden imports af EM1-motoren. Kontrollen kombinerer eksakte symbolske sammenligninger, numeriske værdier og en separat kvadratur af Joule-varmen. Et testværktøjsproblem i den første referencekontrol blev rettet: evalueringspunkternes nye symbolnavne skulle knyttes til de allerede givne 3 cm og 18 cm. Appen blev ikke ændret eller genkørt for at tilpasse et svar. En efterfølgende kvalitativ kontrol nedgraderede 5b fra korrekt matematik til delvis eksamensbesvarelse.

**Dette er et selvkonstrueret mock-sæt, ikke en eksternt uafhængig blindtest.** Samme udvikler valgte spørgsmål og assisterede modeller. Bedømmelsen gælder de konkret afprøvede forløb og beviser ikke, at enhver anden avanceret kombination af inputfelter er umulig. Sættet omfatter kendte EM1-familier og nye funktioner/parameterkombinationer, men resultatet kan ikke ekstrapoleres til en vilkårlig KU-eksamen.

## Prioritering efter testen

1. Gør korte gennemgange til Gauss og kredsløb lige så brugbare som cylinderforløbet. Ret tekstvejens falske delopgave-/kildekonflikter.
2. Bevar orientering og ønskede fysiske forklaringer, når et beregnet emf-resultat overføres til et kredsløb. Matematiske resultatfelter alene er ikke en fuld besvarelse.
3. Gør eksisterende kraft→arbejde og magnetisering→randbetingelser→H/B tilgængelige i appens sammensætning. Afklar manglende modelkapacitet tidligt, før mange manuelle felter udfyldes.

Ingen af disse ændringer er implementeret under mock-testen.
