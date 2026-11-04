# Kort eksamens-runbook

## Hurtigste vej

1. Dobbeltklik START_EM1_SOLVER.bat og kontrollér **Systemstatus: Klar**.
2. Indsæt opgaven i **Ny opgave**, vælg **Analysér opgave**.
3. Ret område/preset, kildefunktion og søges. Feltværdier er symbolske,
   indtil der indsættes tal; symbolske standardnavne er synlige modeller,
   ikke gættede tal fra opgaveteksten.
4. Kontrollér regioner og orientering. En uendelig model er ikke gyldig
   for en endelig kilde. Brug `a+h` med positiv h til ordnede radier, eller
   indtast numeriske radier med enheder som `1 cm` og `3 cm`.
5. Bekræft de synlige vilkår og tryk **Løs opgave**.
6. Læs resultat, retning og kontrol. Gem LaTeX/tekst, eller brug
   kopi-ikonet i felterne **Kopiér løsning / Kopiér slutresultat**.

Hvis parseren fejler: gå til **Manuel solver**. Teksten bevares. Vælg
geometri-formularen; de sjældnere oprindelige solvermodeller findes under
**Specialiseret metode**. Denne avancerede vej kan kræve strukturerede
liste-/vektorinput, men ingen kildekode eller terminal skal åbnes.

## Retning

- Punktladninger: koordinater er kartesiske; ladningens fortegn bruges.
- Ring/bue: kurveparameter og strømretning bestemmer højrehåndsreglen.
- Gauss: feltet er radial-/normalkomponenten, ikke en fast x-komponent.
- Ampère-cylinder: aksial strøm +z giver felt +phi; negativ J vender det.
- Faraday: kontrollér plan, normal og B. Alle tidsafhængige faktorer skal
  differentieres; et ikke-uniformt B kræver fladeintegration.
- Glidende stang: den viste model har stang langs +y og en eksplicit v/B.
- Roterende stang: langs +x, rotation om +z; lokal hastighed afhænger af u.
- Dipol: torque er m kryds B. Parallel er stabil, antiparallel labil.

## Confidence

GREEN: krævede felter og de udførte forhåndskontroller består for den
bekræftede model. YELLOW: kontrollér uafklarede felter/enheder. RED:
modellen kan ikke løses via den valgte vej; ret input før beregning.
En korrekt fysisk afvisning er et nyttigt svar, ikke noget der skal omgås.

GREEN garanterer ikke, at den oprindelige tekst er fortolket korrekt.
De højeste dokumenterede success-rater er assisterede rater på en nu
kendt testbank. Fri tekst alene er ikke den anbefalede eksamensvej.

## Fejl og genstart

Analytisk timeout må bevare et allerede opstillet kurveintegral. Ved
manglende værdier indsættes ingen gættede tal. Hvis appen genstartes,
brug autosave-gendannelse og kontrollér modellen igen. Ændret input
skjuler gamle resultater; den gemte løsningskopi vises særskilt.
