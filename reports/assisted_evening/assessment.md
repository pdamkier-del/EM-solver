# Kritisk beslutning – 5. november 2026

## A. Hvad virker?

Den deterministiske kerne er genbrugelig: 28 registry-indgange, heraf også
hjælpemetoder, og eksisterende strukturerede modeller i EV/BA/DYN. Manuel
input og symbolske mellemtrin er væsentligt bredere end råtekstvejen. Den
eksisterende integration har stabile trinreferencer og tre visningsniveauer.
Det er ikke det samme som 28 generelle, autonome eksamensløsere.

Den nye brede genafprøvning omfatter alle 154 registrerede historiske dele:
153 kendte ekspertkodede beregningsveje matcher de eksisterende officielle
facitchecks; én har ikke en eksekverbar model og afstås. Ingen fejl eller
delvise svar i denne prøve. Gruppeoptællinger overlapper:

| Gruppe | Korrekte ekspertkodede dele |
|---|---:|
| Coulomb/superposition | 26 |
| Gauss/ikke-konstant tæthed | 6 |
| Potentiale/energi/multipoler | 29 |
| Laplace/Poisson-gruppen | 3 |
| Ledere/dielektrika/randbetingelser | 24 |
| Biot–Savart/Ampère og magnetiske kræfter | 28 |
| Magnetisering/bundne strømme | 5 |
| Induktion/kredsløb | 42 |

Laplace-gruppens tre kendte veje dokumenterer ikke en generel Poisson-solver.
Facitchecks dækker konkrete størrelser og punkter, ikke alle mulige input.
Disse tal kan **ikke** markedsføres som automatisk forståelse eller som en
students succesrate med en spørgeformular.

## B. Konkrete begrænsninger

Råtekstvejen nåede senest kun 2/154. Opgaver afvises, før den symbolske
motor aktiveres: tab af formler ved PDF-udtræk, figurafhængige oplysninger,
fælles data og manglende model-/metodekoblinger. Eksisterende heuristisk audit
fordeler disse som 86 repræsentationsproblemer, 16 metodevalg, 36 manglende
figur/kontekst, 14 mistænkt PDF-skade og 2 løste. Kategorierne er ikke en
uafhængig manuel gennemgang af alle originalfigurer; nul observerede
beregningsfejl blandt uafprøvede veje beviser ikke korrekthed.

Gauss kræver ikke blot ordet cylinder: uendelig udstrækning, symmetri,
tæthedskoordinat, gyldige regioner, medium og for potentiale også en gyldig
reference. “Lang” bekræfter hidtil ikke “uendelig”. Flere dielektriske
opgaver mangler konstitutiv model og ydre materiale i råtekstudtrækket.
Disse afvisninger er ofte forsigtige, men der mangler en praktisk
bekræftelsesvej. Brugerens kursusafklaring tillader nu forslag om uendelig
idealmodel, **aldrig** stiltiende anvendelse.

Flere a)/b)/c) blokerer den gamle tekstvej. Den har ikke en generel fælles
model eller en afhængighedsgraf for delspørgsmål. En regex-udvidelse løser
ikke dette fysisk. Den manuelle formulars eksempler, globale navneenheder
og retninger må heller ikke blive automatisk fortolkede fakta.

Grønne regressioner tester primært tidligere kendte strukturer. Metodevalg,
materiale-/geometrimodeller og fysisk kontrol er selvstændige problemer.
En dimensionscheck eller algebraisk identitet verificerer ikke fortolkningen.
Den gamle API's `verified`-betegnelse må ikke læses som et generelt bevis
for korrekt forstået opgavetekst.

Den gentagne råtekstevaluering giver 55-bank: **8 egentlige løsninger,
2 korrekte fysiske afvisninger, 45 øvrige afståelser, 0 forkerte**.
Den gamle optælling “10 korrekte” inkluderer de to diagnoser. Historiske
råtekster: **2 løsninger, 152 afståelser, 0 forkerte**. Tidligere holdout:
**1 løsning, 27 afståelser, 0 forkerte**. Der er ingen særskilt dokumenteret
delvis råtekstsucces i disse evaluatorudfald. Ingen af disse kendte banker
er nu en uafhængig blindprøve.

## C. Valg mellem A/B/C

| Mulighed | Vurdering til i aften |
|---|---|
| A: Udvide eksisterende råtekstparser | Smalle forbedringer mulige; ingen evidens for bred dækning inden deadline |
| B: Assisteret deterministisk model | Anbefalet: genbrug beregningsveje, kræv de afgørende fakta og bekræftelser |
| C: Ny arkitektur/lokal model | Fuld omskrivning er for risikabel. Deklarative modelkort er nyttige som et lille lag oven på motoren |

Der er ikke foretaget en kvalitets-/RAM-test af en lokal sprogmodel, og den
anbefales derfor ikke. Den tidligere offline-/ingen-LLM-begrænsning bevares.
12 GB RAM og højt eksisterende forbrug begrunder ikke en udokumenteret
modeldownload. Beregningsprocesser bør fortsat være afgrænsede og sekventielle.

## D. Leveret realistisk delmål

Separat `assisted-1.0` backend med 8 DYN-modelkort, eksplicitte fælles givne
data og delspørgsmål. Forslag fra prosa er markeret forslag, ikke udledte
fakta. Ingen nye fysikmoduler eller UI-ændringer. Eksplicit I(0), Q(0),
normal/lederorientering, N og idealmodelbetingelser; ingen skjulte eksempler.
Resultatstatus er betinget af en brugerbekræftet model. Fuld JSON-trace,
PySide6-proceseksempel og låste backendafhængigheder følger med.

Konkrete nye API-prøver: **7 korrekt assisterede, 0 delvise, 1 begrundet
afståelse, 0 forkerte**. Autonomt løste i denne prøve: **0**; alle syv har
eksplicit leverede fysiske modeller. Fejlårsag for afståelsen er manglende
bekræftet begyndelsesladning. Numeriske facitchecks og fortegn kontrolleres,
hvor de er tilgængelige. Dette er en lille kendt prøve, ikke bred validering
af alle otte modelkort eller alle parametre.

## E. Kan ikke kaldes færdigt

Ingen universel råtekstsolver, sikker figurforståelse, automatisk konstruktion
af alle delspørgsmålsafhængigheder eller generel kredsløbstopologifortolkning.
Den nye DYN-kontrakt håndterer ikke alle EV/BA-formularer. Den brede
ekspertkodede prøve giver ikke disse en ny brugergrænseflade.

Dette miljø er Linux uden PySide6/native Windows. Windows/Qt-oplevelsen er
derfor ikke end-to-end-verificeret. Der er en realistisk backendvej til i
aften, men **ikke dokumentation for en færdig eksamensklar Windows-app**.

## F. Forventet anvendelse

Autonomt: kun den gamle tekstvejs dokumenterede, snævre delmængde. Ingen
ny påstand om forbedret råtekstdækning. Assisteret DYN: flux/fluxintegral,
homogent B(t)/A(t), parameteriseret bevægelsesinduktion, konstant lineær
elektromekanisk kobling, RC-afladning, RL-spændingstrin og idealiseret
forskydningsstrøm. De sidste modeller er ikke vilkårlige RC/RL-netværk.
EV/BA kan fortsat løses gennem de eksisterende manuelle strukturer.

## G. Brugerens afklaringer og det, der mangler

Brugeren prioriterer elektrodynamik og indsætter hele hovedopgaver med
fælles givne data. “Lang” kan foreslå uendelig idealmodel til bekræftelse.
For den næste integrationstest hjælper et konkret DYN-hovedproblem med
korrekt transskriberede formler og disse oplysninger mest:

1. Forbindelser og kontaktstilling før/efter t=0; hvilke strømme deler grene?
2. Positiv strøm/omløb, B-retning, bevægelsesretning og polaritet.
3. Begyndelsesladning/-strøm/-hastighed og hvilke induktanser/modstande negligeres.
4. Præcise søgte størrelser i hvert delspørgsmål; hvilke tidligere resultater må anvendes?

Programmet må efterspørge dette, når det mangler, frem for at gætte.

## Prioritering og minimum for “brugbar”

1. Bekræft en rigtig DYN-model med brugeren; test fortegn, begyndelsesbetingelse og facit.
2. Kobl den isolerede JSON-kontrakt til desktopappens eksisterende felter.
3. Gennemfør en native Windows-offlineprøve med mindst én løst og én afstået opgave.
4. Først derefter udvid målrettet til flere modelkort eller fælles resultat-afhængigheder.

Minimum er en bruger, som uden kode kan bekræfte en fuldstændig model,
få sporbare mellemtrin/resultater, se præcist hvilke kontroller der er kørt,
og modtage konkret afvisning ved mangler. Ingen modelmålelig usikkerhed må
vises som verificeret fysik. Dette minimum er endnu ikke demonstreret i
den faktiske Windows-desktopapp.

## Afsluttende testgrundlag

Hele regressionen: **823 beståede, 0 fejlede**, inklusive 24 nye
assisteret-backendtests. `tools/certify_all.py` afsluttede også certificering,
dækningsrapport, historisk offline-smoke og de syv eksisterende app-smoke-cases.
Alle 8 nye JSON-fixtures blev desuden reproduceret under Python `-S` med
kun de 7 låste backenddistributioner og blokeret netværk. Ingen Qt-,
Streamlit-, NumPy- eller Pandas-import i denne isolerede backendprøve.
Dette er Linux-evidens; det ændrer ikke Windows/Qt-forbeholdet ovenfor.
