# Hvad der endnu ikke understøttes fuldt

## Input og metodevalg

Opgavetekst og figurer oversættes manuelt til `Problem`. Programmet vælger
ikke metode ud fra ord som “cylinder”. Gauss og Ampère kræver eksplicit
angivne symmetrier; orienteringer og randbetingelser er input. Det er
brugerens ansvar at de angivne symmetrier faktisk gælder. Solverne kan
afvise flere kendte modstridende input, men beviser ikke enhver symmetri
for en vilkårlig geometri.

Appen har redigerbare eksempelinput, regioner og et ekstra JSON-objekt til
at tilføje felter. Alle avancerede API-funktioner har ikke specialtegnede
formularer. Manglende data giver en fejl eller en eksplicit advarsel.

## Fysik og matematik

- Stykvist radiale Gauss-/Ampère-modeller, koncentriske sfæriske ledere og
  parallelle uendelige kilder understøttes; generelle 3D-randværdiproblemer
  gør ikke.
- Ingen automatisk feltlinjeskitse, geometrifortolkning fra en tegning,
  fuld stabilitetsanalyse af alle ladningers samlede bevægelse eller
  selvstændig udledning af enhver fysisk tilnærmelse.
- Dielektrika og magnetiske materialer er lineære i de implementerede
  geometrimodeller. Ingen hysterese, mætning eller dispersive materialer.
- Induktionsstrøm som EMF/R kræver negligerbar selvinduktans.
  Feedback-solveren har konstante koefficienter, fast elektromekanisk
  kobling og ingen friktion. Vilkårlig mekanik og kredsløbstopologi er ikke med.
- SymPy kan efterlade integraler og løsningsgrene. Ingen vilkårlig gren
  vælges. Numerisk evaluering kræver tilstrækkelige parametre; den er
  ikke en generel fejlkontrolleret singularitetskvadratur.
- Differentialkontroller gælder i glatte regioner. Delta-kilder,
  overfladespring og værdier præcis på singulariteter behandles særskilt.
- Resultaternes SI-enhedsetiketter er ikke en generel symbolsk
  dimensionsanalyse. Numeriske input med enheder kontrolleres mod
  eksplicit forventede enheder; rene SI-tal kan ikke dimensionskontrolleres.
- Betingelser på symbolske radier skal kunne afgøres med SymPys
  antagelser. Ellers skal de omparameteriseres eller gives numerisk.

## Historisk validering

`exam_coverage.md` skelner hele beregningsregressioner, delvise checks og
uvaliderede spørgsmål. Hele beregningsregressioner kan bruge flere
solver-kald med manuelt angivne geometriske reduktioner og retninger;
procenten betyder ikke at programmet selv kan læse eller fuldautomatisk
besvare samme procentdel af PDF-spørgsmålene. Ikke alle kvalitative
argumenter og figurskitser er dækket af test-oraklerne. Kun de dokumenterede certificerede familier kan give `stable=true`, og kun
med beståede runtime-kontroller.

Nogle regressioner tester en repræsentativ specialisering af en historisk
geometri (fx bestemte forhold mellem koncentriske radier). De generelle
udtryk og variations-/negativtests supplerer dette; der er ingen garanti
for alle parameterkombinationer. Den præcise testkode er reference for
hvad der er valideret, og alle testhenvisninger findes i
`data/historical_coverage.json`.

## Kilder og offlinebrug

Den aktuelle formelsamling og geometrinoter er vedhæftet og gennemgået;
se `formula_alignment.md`. Griffiths er ikke vedhæftet. Eksamenssæt og facitter
bruges fortsat som primært valideringsgrundlag, med visuelt kontrollerede rettelser
beskrevet i `reference_discrepancies.md`. Det oprindelige parameterinventar
er stadig kildeordlyd, og registry-sværhedsgrad 0 betyder “ikke vurderet”.

Ingen LLM, internetafhængig fortolkning, OCR, billedgenkendelse, FEM,
generel 3D-PDE, login eller cloud deployment er implementeret. Installation
kan kræve netadgang; beregning og lokal appdrift kræver kun installerede
afhængigheder. Offline installation kan forberedes med et wheel-arkiv.

## Migreringen frem mod eksamen

Alle 153 kvantitative delopgaver har nu en struktureret beregningsopskrift.
Kildeinput, fortegnsvalg, geometriske reduktioner og facitforventninger er
stadig menneskeligt gennemgået materiale; programmet fortolker ikke PDF'en.
Juni 2021 1b kræver fortsat en feltlinjeskitse/lokal argumentation.

En bestået opskrift er kun valideret for de resultater, retninger, tal og
specialgrænser, som dens uafhængige checks beskriver. Dansk LaTeX-rendering
testes for alle eksekverbare opskrifter, men ekstern TeX-kompilering indgår
ikke. Hjælpesolveren `algebra` sammensætter eksplicitte fysiske resultater
og geometriske ligninger; den opfinder ingen nye fysikregler.

## Ukendte opgaver og blindbanken

Den aktuelle måling står i `blind_unseen_summary.md`, med uændret baseline
og rå data. Autonom tekstfortolkning er langt svagere end motoren med
menneskeligt struktureret input. Assisted-succes kan kræve store JSON-
rettelser eller flere sammenkædede beregningsled. Disse tal er ikke et
løfte om hurtig automatisk besvarelse af nye PDF-opgaver.

BA14 (magnetisk dipolmoment og energi) har nu en generel offentlig
solvervej i vektor- og vinkelform, valideret med variationer og blindbank. Komplekse regioner, ukendte randbetingelser, konvergens ved
singulære kurver og fortegnsorientering kræver fysisk gennemgang.
Bevarede integraler er opsætninger; de er ikke i sig selv numeriske svar.
Numerisk kurveintegration kræver alle parametre og et feltpunkt uden for
kilden. To-præcisionskontrol er en sanity check, ikke et generelt fejlbevis.

Den nye begrænsede parser accepterer tildelinger og udvalgte danske
formuleringer. Uigenkendt tekst er fortsat synlig, og alle felter skal
bekræftes. GREEN betyder kun at de udførte kontroller bestod for den
bekræftede struktur; det beviser ikke tekstfortolkningen.

Den nye kurvevej opstiller Coulomb-/Biot–Savart-integraler for ring, bue,
ellipse, helix og andre eksplicitte regulære linjeparameteriseringer.
Ingen automatisk figurfortolkning, vilkårlig overflade-/volumenudledning,
FEM, OCR eller generativ AI er tilføjet. Den eksisterende manuelle
fysikmotor understøtter stadig sine tidligere eksplicitte flade-/volumen-
modeller. Korrekthed afhænger af, at deres geometri faktisk er angivet.
