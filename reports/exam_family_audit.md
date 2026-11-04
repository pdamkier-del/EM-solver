# Konsolideret EM1-familieaudit

11 eksamenssæt, 154 bogstaverede delopgaver, 25 primære metodefamilier (tidligere 58). Alle kildeposter og oprindelige klassifikationer bevares. Sekundære metoder registreres separat.

Kilde: `data/sources/exams.pdf` (43 sider) og `answers.pdf` (5 sider), SHA256 i `data/source_manifest.json`. Registry henviser til eksamens-PDF-side og facitspørgsmål. Januar 2025/2026 betegnes Februar i facit. i/ii er underpunkter af samme bogstaverede delopgave.

**Afgrænsning:** Dette er en metodeaudit af det leverede materiale, ikke en påstand om alle KU-sæt nogensinde. Geometrier er registreret; parameterinventar bevares som kildeordlyd. Sværhedsgrad er ikke vurderet. Den aktuelle formelsamling og Griffiths er ikke leveret. Notation følger derfor de leverede eksamenssæt. Figurorientering indlæses manuelt og antages aldrig af programmet.

Brugerens opdaterede bestilling prioriterer direkte implementering efter hurtig konsolidering; fuld redaktionel annotering af registry er udskudt. Ingen solver får historisk dækning alene ud fra denne klassifikation.

| Familie | Antal delopgaver | Eksamener | Seneste | Prioritet |
|---|---:|---|---|---|
| field_calculus | 23 | 2021-06, 2021-11, 2022-02, 2022-11, 2023-02, 2023-11, 2024-11, 2025-01, 2025-11, 2026-01 | 2026-01 | høj |
| point_charges | 17 | 2021-06, 2022-02, 2022-11, 2023-02, 2023-11, 2024-02, 2024-11, 2025-11, 2026-01 | 2026-01 | høj |
| ampere | 10 | 2021-06, 2021-11, 2022-02, 2022-11, 2023-02, 2023-11, 2024-02, 2025-01, 2025-11 | 2025-11 | høj |
| polarization | 9 | 2021-11, 2022-02, 2023-02, 2023-11, 2024-02, 2025-11 | 2025-11 | høj |
| faraday | 9 | 2022-02, 2022-11, 2023-02, 2024-02, 2024-11, 2025-01, 2026-01 | 2026-01 | høj |
| conductors | 7 | 2021-06, 2021-11, 2022-02, 2023-11, 2025-01 | 2025-01 | høj |
| wire_force | 7 | 2021-06, 2022-02, 2024-02, 2026-01 | 2026-01 | høj |
| circuit_power | 7 | 2021-06, 2023-02, 2023-11, 2024-02, 2025-01, 2026-01 | 2026-01 | høj |
| gauss_radial | 7 | 2022-02, 2022-11, 2023-02, 2024-11, 2025-01, 2025-11 | 2025-11 | høj |
| coulomb_integral | 6 | 2021-11, 2024-02, 2025-01, 2026-01 | 2026-01 | høj |
| feedback | 6 | 2023-11, 2025-11 | 2025-11 | normal |
| capacitance | 5 | 2021-11, 2026-01 | 2026-01 | normal |
| multipole | 5 | 2022-02, 2022-11, 2023-02, 2026-01 | 2026-01 | normal |
| magnetic_superposition | 5 | 2022-02, 2025-01, 2025-11 | 2025-11 | normal |
| inductance_energy | 5 | 2022-11, 2023-02, 2023-11, 2024-11 | 2024-11 | normal |
| magnetic_material | 5 | 2022-11, 2024-11 | 2024-11 | normal |
| resistance | 4 | 2022-11, 2024-02, 2024-11, 2025-01 | 2025-01 | normal |
| lorentz_force | 3 | 2021-06, 2021-11, 2025-01 | 2025-01 | normal |
| ampere_maxwell | 3 | 2021-11, 2023-02 | 2023-02 | normal |
| motional_emf | 2 | 2021-06, 2023-11 | 2023-11 | normal |
| rc_transient | 2 | 2022-11, 2026-01 | 2026-01 | normal |
| images | 2 | 2024-11, 2025-11 | 2025-11 | normal |
| biot_savart | 2 | 2024-11 | 2024-11 | normal |
| laplace_legendre | 2 | 2026-01 | 2026-01 | normal |
| units | 1 | 2021-06 | 2021-06 | normal |

## Ti hyppigste primærfamilier

field_calculus: 23, point_charges: 17, ampere: 10, polarization: 9, faraday: 9, conductors: 7, wire_force: 7, circuit_power: 7, gauss_radial: 7, coulomb_integral: 6

Tilsammen 102/154 (66.2%) primærklassifikationer. Det er en prioriteringsindikator, ikke en løselighedsprocent. Se `exam_coverage.md` for testet dækning.

## Kombinationer i samme delopgave

| Metodekæde | Antal |
|---|---:|
| circuit_power + faraday | 4 |
| circuit_power + motional_emf | 3 |
| ampere + magnetic_superposition | 3 |
| conductors + polarization | 2 |
| ampere + inductance_energy | 2 |
| motional_emf + resistance | 1 |
| motional_emf + wire_force | 1 |
| multipole + point_charges | 1 |
| field_calculus + gauss_radial + polarization | 1 |
| inductance_energy + rc_transient | 1 |
| circuit_power + resistance | 1 |
| gauss_radial + polarization | 1 |
| ampere + field_calculus | 1 |
| conductors + gauss_radial + polarization | 1 |
| coulomb_integral + point_charges | 1 |
| ampere + wire_force | 1 |
| faraday + resistance | 1 |
| faraday + wire_force | 1 |
| circuit_power + faraday + resistance | 1 |
| images + point_charges | 1 |
| field_calculus + resistance | 1 |
| faraday + inductance_energy | 1 |
| coulomb_integral + field_calculus | 1 |
| field_calculus + gauss_radial | 1 |
| conductors + field_calculus | 1 |
| coulomb_integral + multipole | 1 |
| ampere + rc_transient + wire_force | 1 |
| field_calculus + laplace_legendre | 1 |

## Implementeringsprioritet

Først Coulomb/superposition, differentialoperatorer, radial Gauss/Ampère og Faraday-kredsløb. Derefter ledere/materialer, energier, kapacitans, geometriske integraler og mekanisk feedback. De oprindelige ti solvere bliver funktioner i bredere metodefamilier frem for isolerede specialsolvere.

## Facitkontrol

- November 2025 5d: original-PDF er kontrolleret visuelt. Facit har korrekt V²; tekstudtrækket mistede eksponenten.
- November 2021 2c kræver skelnen mellem fri, bunden og samlet overfladeladning.
- Januar 2026 4a har to tilfælde; facit mærker dem a/b.
- November 2025 2c: teksten viser 74 5 nC; direkte beregning giver 74,55 nC. Det symbolske udtryk og feltets talværdi stemmer.
- Februar 2024 4a: originalfacit angiver 70 kA; integration med de opgivne data giver cirka 966 A. Se reference_discrepancies.md.
- November 2021 1: original-PDF har Q=0,75 µC, selv om tekstudtrækket fejlagtigt viser mC.
