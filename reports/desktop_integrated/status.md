# Samlet desktopleverance – 5. november 2026

Den faktiske frontend fra EM1_Desktop_Source.zip er integreret i `desktop_app/`. Det er dens eksisterende MainWindow, opgavefelt, noter, PDF-visning og tre løsningsfaner, der bruges. Modelformularen er tilføjet som en fane; den oprindelige råtekstvej er også afprøvet.

## Resultater

**35 kendte historiske delopgaver: 35 korrekt assisterede, 0 delvise, 0 afståelser og 0 forkerte i den afsluttende prøve.** Fordeling: DYN 18, EV 13, BA 4. Ingen autonom løsningsrate udledes heraf. Alle prøver krævede eksplicit modelvalg, indtastede givne/enheder og bekræftede betingelser og orientering. Nogle delopgaver deler samme fysiske opstilling. Dette er ikke 35 uafhængige nye problemfamilier eller en blindprøve.

Facitchecks åbnes af evaluatoren efter beregningen og efter at fuld JSON er gemt. Backend får ikke opgave-ID eller facit som løsningsinput. Egne valgtaster/fields og QProcess/worker indgår i prøven. For talresultater kontrolleres også, at appen faktisk udsender dem.

| Delopgave | Fysisk model | Udfald | Brugerhjælp |
|---|---|---|---|
| 2021-06, 1a | `conductor_cavity_totals` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-06, 1c | `conductor_cavity_totals` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-06, 3a | `ampere_regions` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-06, 5a | `electric_field_charge` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-06, 6a | `motional_curve` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-06, 6b | `motional_curve` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-06, 6c | `motional_curve` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-06, 6d | `motional_curve` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-11, 2a | `concentric_conductors` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-11, 3b | `potential_field` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2021-11, 6b | `displacement_disk` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2022-02, 2a | `cylinder_regions` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2022-02, 5a | `electric_field_charge` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2023-02, 2a | `sphere_regions` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2023-02, 2b | `sphere_regions` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2023-02, 5b | `faraday_flux` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2023-02, 5c | `faraday_flux` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2023-02, 6a | `displacement_disk` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2023-11, 5a | `faraday_uniform` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2023-11, 5b | `faraday_uniform` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2023-11, 5c | `feedback` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2023-11, 5d | `feedback` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2024-02, 4a | `ampere_regions` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2024-02, 4b | `ampere_regions` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2024-11, 2a | `cylinder_regions` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2024-11, 2b | `cylinder_regions` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2025-01, 1a | `potential_difference` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2025-01, 2a | `concentric_conductors` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2025-01, 6a | `faraday_uniform` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2025-01, 6b | `faraday_uniform` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2025-11, 4a | `ampere_regions` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2026-01, 2c | `RC_discharge` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2026-01, 3a | `faraday_integral` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2026-01, 3b | `faraday_integral` | korrekt assisteret | model, givne, enheder, betingelser og retning |
| 2026-01, 3c | `faraday_integral` | korrekt assisteret | model, givne, enheder, betingelser og retning |

## Rettelser fundet under afprøvning

- Rendererens manglende understøttelse af matrixvektorer, ubundtet mathcal og integralernes limits blev rettet uden at ændre matematikken. Før rettelsen blev disse svar talt som delvise. Matricer/vektorer vises med alle komponenter; integralgrænser bevares.
- 2025-01, 6a/b krævede at den negative konstant B_offset ikke var erklæret positiv. Den modstridende indtastning blev korrekt afvist, hvorefter modelinput blev korrigeret; solverens geometri-/fortegnskontrol blev ikke omgået.
- Ved 2025-01, 1a blev de givne tal L=20 m, a=500 V/m og b=50 V/m² føjet til symboltabellen, så det numeriske svar faktisk vises. Den første EV/BA-evaluators ene incorrect-markering var manglende numerisk output, ikke en forkert symbolsk formel; klassifikationen er korrigeret til partial ved denne type mangel.
- Den gamle manuelle forhåndskontrol kendte ikke Q og laplacian_V som tilgængelige mål, selv om feltkernen beregner dem. Den nye adapter validerer samme fulde input med et basismål og håndhæver derefter alle faktisk ønskede resultater. Den gamle manuelle solver er ikke ændret.

## Afståelser og grænser

Manglende Q0, manglende potentialreference, ufuldstændigt materialeinput, eksplicit endelig cylinder valgt som uendelig og ikke-nul curl i et påstået elektrostatisk felt giver spørgsmål eller afvisning. De er særskilte kontrolprøver, ikke inkluderet i de 35 komplette historiske modeller.
Biot–Savart, plan-Gauss, Gauss→V, flerregions-Ampère, en uendelig ledning og vektorpotentiale er også kontrolleret i den faktiske app på konstruerede opgaver. Disse tælles ikke som yderligere historiske facitsucceser.
Ingen generel figur-/OCR-fortolkning, automatisk løsning af hele hovedopgaver, generelle Poisson/Laplace-randværdiproblemer eller vilkårlige kredsløbsnetværk. Asymmetriske lederhulrum giver kun de deklarerede totale overfladeladninger/potentiale. Tidsbegrænset Biot–Savart kan give et eksplicit delvist integralresultat.

## Kontroller og drift

843 tests bestod; 0 fejlede. Hele certificering/offline/app-smoke-forløbet afsluttede med exitkode 0. De oprindelige frontendprøver bestod særskilt: 8 adapterprøver, 8 fortolkningsprøver og 3 process-retry-prøver. Runtime bruger ingen API, LLM eller internet. En backend-only prøve med kun syv låste pakker består fortsat uden Qt eller Streamlit.

Linux/offscreen måling: {"main_window_seconds": 0.68, "rss_after_main_window_mb": 204.9, "peak_parent_rss_mb": 248.2, "peak_parent_and_children_rss_mb": 388.7, "limitation": "RSS sum sampled every 30 ms while Qt event loop runs; can double-count shared pages or miss brief spikes; Linux not Windows"}. Oprettelsestiden er MainWindow-tid, ikke fuld Windows-koldstart. RSS-summen kan dobbeltregne delte sider eller overse korte toppe.

Windows er ikke kørt. Alle 21 låste afhængigheder kunne hentes som Windows/Python 3.12 x64-wheels, men dette er ikke en native installationsprøve. Følg [installations- og native testproceduren](../../desktop_app/WINDOWS_INTEGRATED.md). Installér før eksamen; START_WINDOWS.bat downloader intet.

[Fuld evaluering og indtastet brugerhjælp pr. opgave](evaluation.json) · [Kilde-/testvalidering](validation.json)

## Downloadklar kilde-/installationspakke

[EM1-Solver-Desktop-Integrated-2026-11-05.zip](../../distribution/EM1-Solver-Desktop-Integrated-2026-11-05.zip) indeholder frontend og medfølgende backend. Størrelse: 14128027 bytes. SHA256: `dd350d2f7ce942c89fe466db845ce4b9515e9345f3556deef26a007a83c36f87`. Kildecommit: `80ed036045a211bd4f9b5fada8756bcac883c50b`.

Den endelige pakke er udpakket og startet via dens faktiske run_app.py-bootstrap på Linux/offscreen. Alle 394 manifest-hashes og ZIP-CRC er kontrolleret; RC-resultatet og en afvisning ved manglende Q0 består fra pakkens egen backendsti. Målt proces-til-vindue: 1.188 s. Det er fortsat ikke native Windows-validering.
