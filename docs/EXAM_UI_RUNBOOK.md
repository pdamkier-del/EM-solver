# Kort eksamens-runbook

## Hurtigste vej

1. Dobbeltklik START_EM1_SOLVER.bat og kontrollér **Systemstatus: Klar**.
2. Indsæt opgaven i **Ny opgave**, vælg **Analysér opgave**.
3. Se fortolkningen i det sammenfoldede panel. Besvar kun viste spørgsmål;
   intet fysisk valg er forhåndsvalgt. Brug **Ret fortolkningen**, hvis et
   genkendt felt skal ændres.
4. Kontrollér geometri, udstrækning, regioner, retning og givne værdier.
   GREEN er en regelbaseret status, ikke en sandsynlighed eller fuld validering
   af alle oplysninger i teksten.
5. Vælg **Symbolsk** eller **Symbolsk og numerisk**, og tryk **Løs opgave**.
6. Læs resultat, retning og kontrol. Gem LaTeX/tekst, eller brug kopi-ikonet
   ved **Kopiér løsning / Kopiér slutresultat**.

Hvis parseren afstår: gå til **Avanceret / Manuel**. Her ligger den oprindelige
geometri-formular, **Specialiseret metode** og **Tekst med fuld bekræftelse**.
De oprindelige formularer er bevaret. Den nye råtekst gemmes separat og findes
fortsat, når du vender tilbage til Ny opgave. Ingen kildekode behøver åbnes.

Parser-preview er ikke en ny exam-ready-godkendelse. Den frosne eksamensversion
findes stadig på tagget exam-ready-2026-11-05. Se reports/parser/status.md for
målt autonomi og aktuelle begrænsninger.

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
