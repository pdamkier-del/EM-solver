# EM1: metode, eksekverbar historik og stabil dækning

Dækning må ikke forveksles med autonom løsning af opgavetekst. Al indlæsning er struktureret; ingen OCR, AI eller automatisk figurtolkning.

| Mål | Antal / 154 | Procent | Betydning |
|---|---:|---:|---|
| Method coverage | 153 | 99.4% | Bibliotekets beregninger repræsenteres i beståede tidligere regressionschecks; ikke et selvstændigt historisk inputforløb. |
| Executable historical coverage | 153 | 99.4% | Struktureret beregningsopskrift findes. |
| Correct executable coverage | 153 | 99.4% | Maskinlæsbar gennemgået opskrift → solver-path → Solution → uafhængige facitchecks. |
| Stable historical coverage | 151 | 98.1% | Eksekverbar opskrift, kun certificerede familier, og bestået symbolsk dimensionskontrol på hvert beregningsled. |

Det tidligere 153/154-tal er alene method coverage. Ingen af tallene betyder automatisk forståelse eller fuldstændig kvalitativ PDF-besvarelse.

Opskrifterne i `data/historical_problems/` har kildehenvisning, oprindelig given/søges-tekst, symboler/enheder, geometri, regioner, antagelser, beregningsvej og forventede resultater. Facitforventninger er håndkodet fra kilden, ikke frosset solver-output. Se testkode og opskrift for konkret orakelomfang. Opskrifter med ikke-migreret status har bevidst ingen opdigtede input.

## Solver-status

25 konsoliderede primærfamilier; 22 stable, 3 experimental. Failing familier: 0. Hjælpeindgangene potential_from_field og algebra rapporteres særskilt.

Stable: ampere, ampere_maxwell, capacitance, conductors, coulomb_integral, faraday, feedback, field_calculus, gauss_radial, images, inductance_energy, laplace_legendre, lorentz_force, magnetic_material, magnetic_superposition, motional_emf, multipole, point_charges, polarization, rc_transient, resistance, wire_force. Certifikatgrundlag findes i `data/solver_certificates.json` og `reports/certification.md`. Runtime stable kræver kendte symbolenheder og beståede dimensions-/fysikchecks; certifikater ugyldiggøres ved ændret kildetekst/test/opskrifter.

## Tests

| Kategori | Antal |
|---|---:|
| total | 799 |
| physics_core_and_historical | 470 |
| historical_end_to_end | 153 |
| variations | 149 |
| dimensions | 18 |
| failures | 0 |

Outcomes: {'passed': 799}. Kategorier overlapper; fysik er en overkategori. Historiske end-to-end er kun opskriftstests, ikke de gamle isolerede regressionsfunktioner.

## Dækning pr. eksamen

| Eksamen | Delopgaver | Executable | Correct | Stable | Manual |
|---|---:|---:|---:|---:|---:|
| 2021-06 | 14 | 13 | 13 | 12 | 1 |
| 2021-11 | 14 | 14 | 14 | 13 | 0 |
| 2022-02 | 14 | 14 | 14 | 14 | 0 |
| 2022-11 | 14 | 14 | 14 | 14 | 0 |
| 2023-02 | 14 | 14 | 14 | 14 | 0 |
| 2023-11 | 14 | 14 | 14 | 14 | 0 |
| 2024-02 | 14 | 14 | 14 | 14 | 0 |
| 2024-11 | 14 | 14 | 14 | 14 | 0 |
| 2025-01 | 14 | 14 | 14 | 14 | 0 |
| 2025-11 | 14 | 14 | 14 | 14 | 0 |
| 2026-01 | 14 | 14 | 14 | 14 | 0 |

## Historiske problemstatusser

- Fuldt eksekverbare beregningsopskrifter: 153.
- Delvist understøttede opskrifter: 0.
- Kvalitative/manual: 1 (Juni 2021 1b).
- Ikke migreret til opskrift: 0; dette betyder ikke nødvendigvis manglende fysisk metode.
- Fejlede end-to-end-opskrifter: 0.

| ID | Metodefamilie | Opskriftstatus | Stable path |
|---|---|---|
| 2021-06:1a | conductors | executable | True |
| 2021-06:1b | conductors | qualitative/manual | False |
| 2021-06:1c | field_calculus | executable | True |
| 2021-06:2a | point_charges | executable | True |
| 2021-06:3a | ampere | executable | True |
| 2021-06:3b | wire_force | executable | True |
| 2021-06:4a | lorentz_force | executable | True |
| 2021-06:5a | field_calculus | executable | True |
| 2021-06:5b | units | executable | False |
| 2021-06:5c | field_calculus | executable | True |
| 2021-06:6a | motional_emf | executable | True |
| 2021-06:6b | wire_force | executable | True |
| 2021-06:6c | circuit_power | executable | True |
| 2021-06:6d | circuit_power | executable | True |
| 2021-11:1a | coulomb_integral | executable | True |
| 2021-11:1b | coulomb_integral | executable | True |
| 2021-11:2a | conductors | executable | True |
| 2021-11:2b | capacitance | executable | True |
| 2021-11:2c | polarization | executable | True |
| 2021-11:2d | capacitance | executable | True |
| 2021-11:3a | field_calculus | executable | False |
| 2021-11:3b | field_calculus | executable | True |
| 2021-11:4a | lorentz_force | executable | True |
| 2021-11:4b | field_calculus | executable | True |
| 2021-11:5a | ampere | executable | True |
| 2021-11:6a | capacitance | executable | True |
| 2021-11:6b | ampere_maxwell | executable | True |
| 2021-11:6c | ampere_maxwell | executable | True |
| 2022-02:1a | point_charges | executable | True |
| 2022-02:1b | point_charges | executable | True |
| 2022-02:1c | multipole | executable | True |
| 2022-02:2a | gauss_radial | executable | True |
| 2022-02:2b | conductors | executable | True |
| 2022-02:2c | polarization | executable | True |
| 2022-02:3a | wire_force | executable | True |
| 2022-02:4a | ampere | executable | True |
| 2022-02:4b | magnetic_superposition | executable | True |
| 2022-02:5a | field_calculus | executable | True |
| 2022-02:5b | field_calculus | executable | True |
| 2022-02:6a | faraday | executable | True |
| 2022-02:7a | field_calculus | executable | True |
| 2022-02:7b | field_calculus | executable | True |
| 2022-11:1a | point_charges | executable | True |
| 2022-11:1b | point_charges | executable | True |
| 2022-11:1c | point_charges | executable | True |
| 2022-11:2a | gauss_radial | executable | True |
| 2022-11:2b | field_calculus | executable | True |
| 2022-11:3a | ampere | executable | True |
| 2022-11:3b | inductance_energy | executable | True |
| 2022-11:3c | rc_transient | executable | True |
| 2022-11:3d | resistance | executable | True |
| 2022-11:4a | multipole | executable | True |
| 2022-11:4b | multipole | executable | True |
| 2022-11:5a | magnetic_material | executable | True |
| 2022-11:5b | magnetic_material | executable | True |
| 2022-11:6a | faraday | executable | True |
| 2023-02:1a | point_charges | executable | True |
| 2023-02:1b | point_charges | executable | True |
| 2023-02:1c | point_charges | executable | True |
| 2023-02:2a | gauss_radial | executable | True |
| 2023-02:2b | polarization | executable | True |
| 2023-02:2c | polarization | executable | True |
| 2023-02:3a | multipole | executable | True |
| 2023-02:4a | field_calculus | executable | True |
| 2023-02:4b | ampere | executable | True |
| 2023-02:5a | inductance_energy | executable | True |
| 2023-02:5b | faraday | executable | True |
| 2023-02:5c | circuit_power | executable | True |
| 2023-02:5d | faraday | executable | True |
| 2023-02:6a | ampere_maxwell | executable | True |
| 2023-11:1a | point_charges | executable | True |
| 2023-11:1b | point_charges | executable | True |
| 2023-11:1c | point_charges | executable | True |
| 2023-11:2a | ampere | executable | True |
| 2023-11:2b | inductance_energy | executable | True |
| 2023-11:3a | field_calculus | executable | True |
| 2023-11:3b | field_calculus | executable | True |
| 2023-11:4a | polarization | executable | True |
| 2023-11:4b | conductors | executable | True |
| 2023-11:4c | polarization | executable | True |
| 2023-11:5a | motional_emf | executable | True |
| 2023-11:5b | circuit_power | executable | True |
| 2023-11:5c | feedback | executable | True |
| 2023-11:5d | feedback | executable | True |
| 2024-02:1a | point_charges | executable | True |
| 2024-02:1b | point_charges | executable | True |
| 2024-02:1c | coulomb_integral | executable | True |
| 2024-02:1d | coulomb_integral | executable | True |
| 2024-02:2a | polarization | executable | True |
| 2024-02:2b | polarization | executable | True |
| 2024-02:3a | wire_force | executable | True |
| 2024-02:3b | wire_force | executable | True |
| 2024-02:4a | ampere | executable | True |
| 2024-02:4b | ampere | executable | True |
| 2024-02:5a | faraday | executable | True |
| 2024-02:5b | resistance | executable | True |
| 2024-02:5c | wire_force | executable | True |
| 2024-02:5d | circuit_power | executable | True |
| 2024-11:1a | point_charges | executable | True |
| 2024-11:1b | images | executable | True |
| 2024-11:2a | gauss_radial | executable | True |
| 2024-11:2b | gauss_radial | executable | True |
| 2024-11:3a | biot_savart | executable | True |
| 2024-11:3b | biot_savart | executable | True |
| 2024-11:4a | resistance | executable | True |
| 2024-11:4b | field_calculus | executable | True |
| 2024-11:5a | inductance_energy | executable | True |
| 2024-11:5b | inductance_energy | executable | True |
| 2024-11:5c | faraday | executable | True |
| 2024-11:6a | magnetic_material | executable | True |
| 2024-11:6b | magnetic_material | executable | True |
| 2024-11:6c | magnetic_material | executable | True |
| 2025-01:1a | field_calculus | executable | True |
| 2025-01:1b | field_calculus | executable | True |
| 2025-01:2a | gauss_radial | executable | True |
| 2025-01:2b | conductors | executable | True |
| 2025-01:2c | conductors | executable | True |
| 2025-01:3a | coulomb_integral | executable | True |
| 2025-01:3b | field_calculus | executable | True |
| 2025-01:4a | lorentz_force | executable | True |
| 2025-01:5a | ampere | executable | True |
| 2025-01:5b | magnetic_superposition | executable | True |
| 2025-01:5c | magnetic_superposition | executable | True |
| 2025-01:6a | faraday | executable | True |
| 2025-01:6b | circuit_power | executable | True |
| 2025-01:6c | resistance | executable | True |
| 2025-11:1a | point_charges | executable | True |
| 2025-11:1b | images | executable | True |
| 2025-11:2a | field_calculus | executable | True |
| 2025-11:2b | field_calculus | executable | True |
| 2025-11:2c | gauss_radial | executable | True |
| 2025-11:3a | field_calculus | executable | True |
| 2025-11:3b | polarization | executable | True |
| 2025-11:4a | ampere | executable | True |
| 2025-11:4b | magnetic_superposition | executable | True |
| 2025-11:4c | magnetic_superposition | executable | True |
| 2025-11:5a | feedback | executable | True |
| 2025-11:5b | feedback | executable | True |
| 2025-11:5c | feedback | executable | True |
| 2025-11:5d | feedback | executable | True |
| 2026-01:1a | point_charges | executable | True |
| 2026-01:1b | coulomb_integral | executable | True |
| 2026-01:1c | multipole | executable | True |
| 2026-01:2a | capacitance | executable | True |
| 2026-01:2b | capacitance | executable | True |
| 2026-01:2c | rc_transient | executable | True |
| 2026-01:2d | wire_force | executable | True |
| 2026-01:3a | faraday | executable | True |
| 2026-01:3b | faraday | executable | True |
| 2026-01:3c | circuit_power | executable | True |
| 2026-01:4a | field_calculus | executable | True |
| 2026-01:5a | laplace_legendre | executable | True |
| 2026-01:5b | laplace_legendre | executable | True |
| 2026-01:5c | field_calculus | executable | True |

## Konkrete stable-blokeringer

- 2021-06:5b: units: Variationer: 0/2 (LOW).
- 2021-11:3a: Runtime: solve: Elektrostatisk rotation

## Top remaining gaps

| Familie | Potentiel stabil historisk gevinst (primærklassifikation) |
|---|---:|
| units | 1 |
| field_calculus | 1 |

## Top remaining risks

- Et ukontrolleret symmetriudsagn kan stadig være fysisk forkert: metodevælgeren kræver eksplicit bekræftelse og fortolker ingen figur.
- Den kvalitative feltlinjeskitse Juni 2021 1b kræver fortsat menneskelig argumentation.
- En runtime-beregning uden komplette symbolenheder er ikke stable, selv om familien har et certifikat.
- Krumme koordinater, randflader og integralers konvergens kræver egne antagelser. Eksperimentelle familier er ikke certificeret af et enkelt korrekt facit.
- RC-strømfortegn afhænger af orientering: I er positiv afladningsstrøm; I_charge følger formelsamlingens ladeorientering.
- Symbolsk dimensionskontrol beviser ikke en logaritmes fysiske domæne eller vælger løsningsgren. RL-mål kræver nåelighed.
- Generel LaTeX-kompilering på en ekstern TeX-installation er ikke verificeret; eksportens indhold er testet.

Kildekontrol mod formelsamlingen: `formula_alignment.md`. Kilde-/facitafvigelser: `reference_discrepancies.md`.
