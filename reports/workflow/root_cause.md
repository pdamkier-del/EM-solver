# Gennemgang af de dokumenterede brugerproblemer

Udgangspunkt: Python 3.13-desktop, e5130b13732255f4581b862fd5f84447bb04b4f1.
Den oprindelige app og releases bevares på deres branches og som ZIP.

## Reproduceret i den faktiske app

Baseline: reports/workflow/baseline.json og *.before.png. Efter “Vælg fysisk model” står Faraday-fluxintegral stadig valgt til begge opgaver. Analyse viser kun forslag; den udfylder ikke V, J, radius, regioner, søgte størrelser eller symbolenheder. Tildelinger som a=4 cm kan ikke overføres til regionstabellen. J0 kræves som en tilsyneladende given konstant, selv når opgaven netop beder om at bestemme den fra I. Potentialets a,b får ingen automatisk enhed, og det er uklart at numeriske værdier ikke kræves til et symbolsk svar. Koordinater, system og flere betingelser skal gentages manuelt. Efterbehandlingstabellen viser 13 tekniske kolonner før de grundlæggende data er på plads.

Den konkrete LaTeX-tekst har gyldige én-tegnsargumenter i `\mathbf J` og `\mathrm A`. Den hidtidige strengnormalisering kræver klammer og stopper denne tekst. Gentagne s-tildelinger i del (c) skal behandles som evalueringspunkter, ikke modstridende fælles givne data.

Potentialet kunne beregnes korrekt efter en manuel opsætning. Baseline-opgørelsen tæller 18 semantiske formularhandlinger (inkl. indtastning/modelvalg/enheder/betingelser), ikke et observeret menneskes klik eller tid. Cylinderen havde ingen komplet normaliseringsvej i formularen; der angives derfor ikke et opdigtet baseline-antal til en løsning.

## Rettelser og afgrænsning

Forsidens nye “Analysér opgave” åbner en kort, redigerbar gennemgang for de to eksisterende modeltyper. Den eksisterende direkte solver, manuelle formular og øvrige modelkort bevares. Der er ingen nye fysikmodeller.

- Potentialets funktion, koordinater, søgte E/rho og entydigt bestemte dimensionsenheder overføres fra teksten. a,b holdes symbolske og får ingen positiv-antagelse alene på grund af navnet a.
- For cylinderen læses radius, totalstrøm, J(s), akse og evalueringspunkter. J0 markeres som ubekendt og bestemmes ved eksisterende integration og ligningsløsning. In-/out-regionerne dannes fra den eksplicitte massive cylinder.
- Kun relevante redigerbare felter vises. Entydige enheder og koordinater er læsbar information; de skal ikke genindtastes. Numeriske koefficienter kræves ikke til et symbolsk potentiale.
- Uafklarede enheder, modstridende tal, ukendt strømretning og en ødelagt PDF-formel får konkrete forklaringer og tilhørende felter. Et nyt symbol eller en manglende talværdi gættes ikke.
- Uendelig idealmodel, stationaritet og mu_0 bekræftes eksplicit for magnetfeltet. “Lang” er et forslag til idealisering, ikke dokumentation for uendelighed. Ved historisk længderetning vælges +z langs den oplyste strøm som synlig koordinatkonvention; ingen figurretning gættes.
- Gennemgangen og beregningen kører i afgrænsede, netværksblokerede processer. Ændret tekst under kørslen kasserer det gamle forslag; ændrede felter ugyldiggør det tidligere svar.

## To dokumenterede integrationstilpasninger

1. Det eksisterende potentialkort krævede vakuum. E=-grad(V) i elektrostatik og rho_total=epsilon_0 div(E) kræver ikke vakuum: rho_total er samlet ladning. Derfor er alene denne overflødige kortbetingelse fjernet. Der er ingen ændring af gradient/divergens-formlerne. Fri ladning i et materiale henvises til D/materialemodel, og rho vises udtrykkeligt som samlet ladning.
2. Eksisterende efterbehandling kunne løse normaliseringsligningen, men kunne ikke bruge dens resultat-ID som evalueringsværdi. Fire linjer tillader nu scalar-reference til en tidligere beregnet operation ved evaluate/limit. Numerisk givne parametre beholder deres betydning, enhedskontrollen beholdes, og der indsættes ingen cylinderformel. Den generelle Ampère-/integrationskerne og alle øvrige solvere er uændrede.

## Realistisk historisk kontrol

KU februar 2024, opgave 4(a,b), original opgave på PDF-side 27, J(s)=J0(1-s/S), S=3,1 mm og J0=96 A/mm². Det faktiske PDF-billede er læst fra eksamenssættet, ikke facit. Råteksten har mistet parenteser og brøkstruktur. Appen kræver én rettelse af J(s) fra billedet, og bevarer de givne tal. Del (b) og hele hovedopgave (a+b) afprøves i MainWindow med strøm, regionalt B og grænse-/punktværdier 0,S,2S. Det er en kendt regression og en realistisk tekstprøve, ikke en ny blindtest.
