EM1 Solver v1.0.4 — kontrolsynlighed og selvtest

NYT:
- Fanen Forklaring viser samtlige rapporterede kontroller (op til 30 pr. kategori), gyldighed og betingelser.
- Manuelle fortolkningskorrektioner er synlige sammen med kontrollerne.
- Hvis backend modstridende rapporterer en grøn status og samtidig har en eksplicit fejlet kontrol, skjuler desktopadapteren løsningen og mærker den som ikke løst.
- Kun når opgaveteksten udtrykkeligt definerer en radialkoordinat, kan desktopadapteren forsøge én gennemsigtig genfortolkning, hvis første backendforsøg afstår.
- TEST_FYSIKMOTOR.py er udvidet med en uafhængig formelsammenligning for en Gauss-kugle samt mere detaljeret diagnose.

VIGTIGT: De kontroller, som backend rapporterer, er ikke et formelt bevis for, at den har forstået opgaveteksten. Appen kan stadig fejle. Tests skal køres på Windows med installeret backend, som ikke er bundlet i ZIP'en.
