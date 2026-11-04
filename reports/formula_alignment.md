# Kontrol mod de leverede EM1-noter

Kilder: `data/sources/formulas.pdf` (01_EM_formelsamling_AKTUEL.pdf) og
`geometry.pdf` (02_EM_geometri_og_regneteknik.pdf). Originalerne bevares;
lokale tekstudtræk ligger ved siden af auditmaterialet. Dokumenternes
metodeanvisninger behandles som fagligt indhold, ikke programinstruktioner.

| Implementering | Formelsamling | Kontrol |
|---|---|---|
| point_charges, coulomb_integral | EV2, s. 3–5 | Kilde→felt-separationsvektor, dq og vektorsummering |
| gauss_radial | EV2–EV3, s. 5–6 | Variabel r/s, faste radier, inde/ude, korrekt Qenc-integral |
| conductors | EV4, s. 7 | E=0 i metal, total hulrumsladning kontra lokal sigma |
| capacitance | EV0/EV4 | C=Q/ΔV og positive geometriske mellemrum |
| field_calculus, potential_from_field | EV0–EV1, BA1/BA6 | E=-grad V, rho=epsilon0 div E, B=curl A |
| images, laplace_legendre | EV5, s. 8 | Randbetingelser, entydighed og sfæriske Legendre-led |
| multipole | EV6, BA5 | Afhængighed af origo og fjernfeltsbetingelse vises |
| polarization | EV7, s. 9–10 | Fri, bunden og samlet ladning holdes adskilt |
| ampere, biot_savart, magnetic_superposition | BA2–BA3, s. 11–13 | Ampère kræver symmetri; endelige kurver bruger Biot–Savart |
| lorentz_force, wire_force | BA4, s. 14 | Krydsproduktets rækkefølge og q-fortegn |
| magnetic_material | BA7, s. 15–16 | H bruger fri strøm; Jb=curl M og Kb=M×n |
| resistance, rc_transient | DYN2, s. 18 | Lokal Ohm, serieintegral og RC-fortegn |
| motional_emf, feedback | DYN3–DYN4, s. 19 | Mod-EMF, Newton, terminalhastighed og effektbalance |
| faraday, circuit_power | DYN5–DYN7, s. 20–21 | Differentier hele fluxen inkl. geometri; Lenz separat |
| inductance_energy | DYN8–DYN10, s. 21–22 | Flux pr. vinding kontra fluxkobling; 1/2 LI² |
| ampere_maxwell | DYN11, s. 22 | Indesluttet elektrisk flux og s/a-regioner |

Geometriarket anvendes til ortonormale koordinater, parameterretning,
volumen-/arealelementer og integration. Den vektorielle Laplace-operator
beregnes som grad(div A)-curl(curl A), ikke ukritisk komponentvist i
krumme koordinater, i overensstemmelse med BA6.

## Væsentlige fortegns- og navneforskelle

- DYN2 har afladningsstrømmen negativ i en ladeorienteret konvention.
  Eksamensfacit bruger ofte positiv afladningsstørrelse. Den eksisterende
  `I=-dQ/dt` er derfor bevaret; `I_charge=dQ/dt` viser formelsamlingens
  konvention eksplicit. Retningsteksten angiver begge. Ingen fysik ændres.
- `EMF` er API-navnet for elektromotorisk kraft, vist som E-kalligrafisk
  i startformler; det må ikke forveksles med vektorfeltet E.
- Formelsamlingen bruger `sigma_c` om ledningsevne. API-feltet hedder
  `conductivity`; `sigma` i ladningsproblemer er overfladeladning.
- Cylinderens Q_enc kan være pr. længdeenhed, hvis ingen L er angivet.
  Med `length` returneres total Q_enc og separat Q_enc_per_length. Det
  svarer til, at L forkortes i Gauss' lov; enheder fremgår af resultatet.
- Magnetiske springbetingelser kontrolleres ud fra den valgte normal:
  n×(H_out-H_in)=K_free. Tekst/typografiske tvetydigheder i BA7 bruges
  ikke til at ændre krydsproduktets fysiske retning.

Gennemgangen erstatter ikke en korrekturlæsning af hver figur eller en
certificering af alle familier. Certifikaterne bygger på eksekverbare
opskrifter, variations-/negativtests og dimensionskontrol. Juni 2021 1b
er fortsat `qualitative/manual` som tilladt i bestillingen.
