# Kildekontrol og afvigelser

Original-PDF er reference ved fejl i `pdftotext`. Der er ikke ændret i de
leverede PDF-filer eller i facitter for at få tests til at bestå.

## Februar 2024, 4a: numerisk facitfejl

Originalt facit, side 3, er kontrolleret visuelt og angiver **70 kA**.
Det symbolske facit er derimod

\[
I(S)=2\pi J_0(S^2/2-S^2/3)=\pi J_0 S^2/3.
\]

Med opgavens `J0=96 A/mm²=96·10⁶ A/m²` og `S=3,1 mm` fås
`I≈966,1 A`, ikke 70 kA. Det afledte `B(S)≈62,33 mT` stemmer med
facits feltværdi. Regressionen kontrollerer den korrekte integration og
SI-konvertering. Afvigelsen er dokumenteret, ikke skjult som et match med
det numeriske strømfacit.

## November 2021, 1: udtræksfejl i µC

Opgavens originalside 5 har `Q=0,75 µC`. Tekstudtrækket viser fejlagtigt
`0,75 mC`. Det giver en faktor 1000 i energi og kraft, hvis det bruges
ukritisk. Testen anvender den visuelt kontrollerede størrelse og får
`U≈4,286 J` og `Fz≈9,741 N`, i overensstemmelse med afrundet facit.

## November 2025, 5d: korrekt facit, mistet eksponent

Tekstudtrækket så først ud til at have `mV/(B²d²)`. Originalfacit på side 4
er kontrolleret visuelt og har korrekt `mV²/(B²d²)`. Det samme fås fra
`∫ V I(t) dt`, og Joule-varmen er halvdelen. Dette er en udtræksfejl,
ikke en fejl i det originale facit.

## November 2021, 2c: skeln fri, bunden og samlet ladning

Facits symboler er tvetydige i dielektriktilfældet og gengiver ikke alle
frie og bundne tætheder særskilt. Programmet bruger springbetingelserne:

- `sigma_free = n·(D_out-D_in)`.
- `sigma_total = epsilon_0 n·(E_out-E_in)`.
- `sigma_bound = sigma_total-sigma_free`.

De frie lederladninger ændres ikke ved at fylde mellemrummet med et
lineært dielektrikum. Samlet lokal tæthed ved grænsefladen reduceres med
faktoren `epsilon_r`; forskellen er den bundne ladning. Regressionen
tester disse størrelser hver for sig.

## Datoer og typografi

- Januar 2025 og januar 2026 betegnes Februar i facit. Registry bruger
  de faktiske eksamensdatoers måned, så ID'erne er entydige.
- November 2025, 2c viser `74 5 nC`; direkte beregning giver `74,55 nC`.
  Det symbolske udtryk `4π epsilon_0 aR` er korrekt.
- Januar 2026, 4a indeholder to tilfælde i samme bogstaverede delopgave;
  facit betegner dem a/b. Audit tæller dem samlet som én af de 14 delopgaver.
