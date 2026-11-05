# Autonom backend: udviklingsrapport 2026-11-05

Branch: `em1-autonomous-engine-2026-11-05`, fortsat fra `f1bd7eb`. Ingen push eller udgivelse. Frosset tag/ZIP, manuel solver og frontend-layout er bevaret.

## Audit og første fejlklasse

Alle 154 historiske delopgaver har maskinelle fasestatusser i failure_audit.json: tekst, figur, geometri, variable/enheder, randbetingelser, metode, ligningsopsætning, symbolsk matematik, slutresultat og første diagnosticerede blokering.
Dette er ikke en fuldført manuel kontrol af alle PDF-sider og figurer. Troskab mod PDF/figur og den første egentlige fejl står som unverified, når det ikke kan fastslås. Kendt manuelt struktureret ground truth bruges til feltkontrol, hvor det allerede findes. Der opfindes ingen manglende figuroplysninger.

| Første diagnosticerede blokering på baseline | Antal |
|---|---:|
| context_or_source_extraction | 50 |
| method_or_composition | 13 |
| figure_information | 35 |
| text_damage_suspected | 14 |
| dimensional_constraints | 14 |
| boundary_model | 17 |
| other_missing_information | 3 |
| geometry | 7 |
| none | 1 |

Sprog/kontekst og PDF-/figurmangler dominerer. Udviklingen har derfor ikke forsøgt at rekonstruere tabte tegn fra facit. Den valgte forbedring gør kendte, eksplicit givne fysiske størrelser mere anvendelige gennem typed løsningskæder og et dokumenteret interface.

## Implementerede generelle forbedringer

1. `core/composition.py` genbruger eksisterende solvere i den tidsbegrænsede, netværksblokerede worker. Kuglesymmetrisk tæthed kan nu give total ladning og stykvist potentiale med eksplicit fjernreference. Hule regioners vakuumgab indgår; potentialets konstanter matches fra ydersiden indad.
2. Ren integration af en given fri volumenladning kræver ingen dielektrisk feltlov. Ved kun Q-beregning produceres ingen uberettigede vakuumfelter. Det samme materialedata er fortsat utilstrækkeligt til E uden korrekt materialemodel.
3. Aksial strømtæthed kan give total eller omsluttet strøm sammen med B. Integrationsområdet skal fremgå af spørgsmålet; uklar I udløser afklaring.
4. Ampère–Maxwell kobles til den eksisterende solver ved cirkulære plader, eksplicit aksialt homogent E(t), angivet radial observationskoordinat, radius og negligerede randeffekter. Manglende forudsætninger gættes ikke.
5. Eksplicitte V(infinity)=0-randdata adskilles fra rumligt givne kildefunktioner. Navngivning af den efterspurgte ukendte, fx B=B(t,s), behandles ikke som en ekstra uafhængig kilde.
6. En sammensat radius R/2 må ikke blive til R. Relativ permittivitet behandles som dimensionsløs. Positive radiusforhold anvendes til en dimensionsbevarende logaritmeform; der antages ikke vilkårlige komplekse logaritmeidentiteter.
7. Et afgrænset LaTeX-inputlag understøtter eksplicitte brøker, grupperede eksponenter/indeks, græske symboler, simple vektor-/basis-markeringer og funktionsnavne. Det er ikke OCR eller TeX-eksekvering. Beskadiget eller uunderstøttet notation giver fejl.
8. `em1_solver.backend.respond` eksponerer et serialiserbart schema 1.0 med objekter/kilder/supportrelationer, variable/enheder, antagelser, randdata, metoder, usikkerheder, LaTeX-trin, SI-resultater, checks og fejl. Requesten accepterer ikke IDs, presets eller facit. Ingen Streamlit-import eller netværksserver er nødvendig.

## Fysisk validering

Nye sammensatte løsninger kontrollerer Gauss differentiallov i åbne regioner, D-kontinuitet uden fri fladeladning, potentialkontinuitet, -grad(V)=E og fjernreference, samt Ampère cirkulation/differentiallov, hvor relevant. Symbolske dimensionskontroller følger de nye output. Nye planer får ikke automatisk et stable-certifikat fra komponenternes historiske certifikater.
Backend skelner ready, verified, verified_with_assumptions, partial og not_solved. Formelle integraler/uafklarede checks er partial; mislykkede fysiske checks kan ikke godkendes som en løsning. Diagnostisk afvisning af et foreslået ikke-fysisk felt er eksplicit markeret. Status beskriver udførte checks og antagelser, ikke et universelt bevis på tekstforståelse.
Eksisterende kontinuitets-, Maxwell-, energi- og fortegnskontroller er bevaret. Generel tidsafhængig ladnings-/strømtransport med en fuld kontinuitetsligning er ikke færdigimplementeret i tekstplanlæggeren.

## Før/efter og svarpræcision

| Datasæt | Før | Forsøgt | Korrekte svar | Afstået | Forkerte | Præcision blandt afgivne svar |
|---|---:|---:|---:|---:|---:|---:|
| Kendt 55-bank | 10/55 | 55 | 10 | 45 | 0 | 100.0 % |
| Historiske råtekster | 1/154 | 154 | 2 | 152 | 0 | 100.0 % |
| Tidligere historisk holdout | 0/28 | 28 | 1 | 27 | 0 | 100.0 % |
| Nyt internt genereret sæt | — | 24 | 20 | 4 | 0 | 100.0 % |

55-scoren inkluderer to korrekte diagnostiske Maxwell-afvisninger som svar. Afståelser i tabellen betyder manglende oplysninger/understøttelse, ikke en verificeret fysisk afvisning. Gamle preset-/assisted-successes tælles ikke som autonomi. Ingen fejl/timeouts forekom i den afsluttende måling.
Registrerede skjulte forkerte svar: bank 0, historiske 0, interne 0. Nul i disse forsøg garanterer ikke nul på fremtidige tekster.
25 %-målet er ikke nået på den kendte bank (18,2 %) eller historiske råtekster (1,3 %). Et højt tal på det afgrænsede interne sæt ændrer ikke denne konklusion.
I første diagnostiske måling blev en korrekt total fri ladning markeret wrong_or_unverified, fordi den historiske oracle benævner størrelsen Q_enc ved den faktiske ydergrænse. Verifieren accepterer nu denne generelle semantiske ækvivalens efter kontrol af både evalueringspunkt og enhed. Dette ændrer ingen fysik, runtime-input eller historisk opskrift. Første råkørsel er bevaret i evaluation_round1.json.

## Generalisering og testniveauer

- A: komponenttests for datatypekontrakt, LaTeX, SI-roller, manglende forudsætninger og sikker afståelse.
- B: alle eksisterende fysik-/historiske regressioner samt råtekst-måling af 154 delopgaver. Holdout 2022-02/2023-02 er tidligere set og kaldes kun regression.
- C/E: sammensatte problemer med forskellige tæthedsprofiler, hule/solide geometrier, fortegn, tidsfunktioner og formuleringer; uafhængige symbolske volumen-/potential-/strømintegraler og Maxwell-relationer er referencer.
- D: et seed blev gemt før de nye 24 cases blev instansieret til slutmålingen. 20 komplette cases består; fire målrettet ufuldstændige cases afvises korrekt. Der er ikke tilføjet casespecifikke parserregler efter første kørsel. Kun metodevisning og seed-outputmetadata blev præciseret bagefter; resultatet før disse ændringer er bevaret i evaluation_before_metadata.json.
- Det interne sæt er konstrueret af samme udvikler og dækker kun få udvalgte fysikfamilier. Det er ikke en ekstern uafhængig blindtest og dokumenterer ikke 83 % autonomi på nye eksamener. Et eksternt, hidtil uset evalueringssæt mangler fortsat.

## Tests og offline

Fuld suite: 753 beståede, 0 fejlede; fuld-kørselsflag og kildefingerprint matcher. Før denne udvikling: 727 tests. Alle eksisterende tests er bevaret.
certify_all har også kørt historiske offline-smokes og syv faktiske Streamlit-widgetforløb. Socket-forbindelser blokeres i fysik-/nye tests og workers. Numerisk SI-smoke: R=2 cm, rho=k*r, k=3 nC/m^4 giver Q=1,5079644737231e-15 C; det serialiserede svar validerer mod JSON-schemaet.
Den strukturerede historiske dækning er fortsat 153/154 eksekverbare korrekte og 151/154 stabile. Det er et andet mål end autonom råtekstforståelse. Ingen frontend-redesign, nye API-afhængigheder, push, release eller Windows-rebuild er udført.

## Resterende begrænsninger og prioritering

1. Manuel kontrol af PDF-/figurtroskab for samtlige 154 opgaver er ikke afsluttet. Første egentlige fejl kan derfor ikke fastslås på alle cases; audit bevarer denne usikkerhed.
2. Flere objekter, positionsrelationer, kontekst fra tidligere delspørgsmål og eksplicitte begyndelsesbetingelser er de vigtigste næste modeludvidelser. Den nuværende serialiserbare model omfatter hovedsageligt én genkendt krop og dens kilder.
3. Materiale-/randbetingelser skal kobles generelt til de eksisterende D/P-, leder-, spejl- og Laplace-solvers. Total fri ladning er understøttet uafhængigt af materialelov; generelle materialefelter er det ikke.
4. Planlægning af vilkårlige kæder på tværs af alle metodefamilier, generelle flade-/volumenintegraler, kredsløb/feedback og dynamisk kontinuitet mangler stadig. Brug manuel solver, hvor en understøttet vej allerede findes.
5. Et nyt eksternt evalueringssæt er nødvendigt, før præstation på ukendte eksamener kan vurderes. Flere regex-patches på de kendte IDs er ikke en løsning på denne blokering.

## Frontend-handoff og genskabelse

Se docs/backend/API.md og docs/backend/schema-v1.json. Backend importerer ikke præsentationslaget; frontend kan bygge direkte på kontrakten. Kommandoerne nedenfor kræver ingen netværksadgang under løsningen.

```sh
/workspace/em1-venv/bin/python tools/audit_raw_failures.py
/workspace/em1-venv/bin/python tools/certify_all.py
/workspace/em1-venv/bin/python tools/evaluate_autonomy.py
/workspace/em1-venv/bin/python tools/write_autonomy_report.py
```

Rå fortolkninger, konkrete fejl, metode, symbolsk kontrol, afståelser, kildehash og evaluatorhash findes i evaluation.json. Den gamle parserrapport bevares som baseline; den ændres ikke til nye tal.
