# Evaluering af 20 nye opgaver

Fuldt korrekte: 17/20 (85.0%). Delvise: 0; forkerte: 0; afstået: 3.

Automatisk fuldt: 0/20. Råtekstvejen gav én delvist korrekt symbolsk løsning (EV6), men indsatte ikke hele det angivne feltpunkt numerisk; de øvrige 19 var afståelser. Ingen automatiske fejlsvar. Assisteret: 17 fuldt korrekte. Disse tal gælder de konstruerede opgaver, ikke hele pensum eller et uafhængigt eksamenssæt.

Ingen fysisk model blev ændret under evalueringen. Referencesvar blev først genereret og anvendt efter alle appberegninger. De er afledt med separate analytiske formler uden engine-imports; samme forfatter valgte opgaverne, så evalueringen er ikke eksternt uafhængig.

| Opgave | Model | Resultat | Assisterede formularhandlinger |
|---|---|---|---|
| EV1 | image_plane | fully_correct | 26 |
| EV2 | image_sphere_grounded | fully_correct | 27 |
| EV3 | image_sphere_isolated | fully_correct | 30 |
| EV4 | point_superposition | fully_correct | 29 |
| EV5 | sphere_regions | fully_correct | 42 |
| EV6 | potential_field | fully_correct | 23 |
| EV7 | intet passende kort | abstained | 0 |
| BA1 | magnetization_currents | fully_correct | 26 |
| BA2 | magnetized_sphere | fully_correct | 23 |
| BA3 | ampere_regions | fully_correct | 24 |
| BA4 | magnetic_wires | fully_correct | 26 |
| BA5 | biot_savart_curve | fully_correct | 21 |
| BA6 | intet passende kort | abstained | 0 |
| DYN1 | RL_step | fully_correct | 25 |
| DYN2 | RL_driven | fully_correct | 25 |
| DYN3 | RC_driven | fully_correct | 24 |
| DYN4 | faraday_uniform | fully_correct | 33 |
| DYN5 | faraday_flux | fully_correct | 46 |
| DYN6 | motional_curve | fully_correct | 27 |
| DYN7 | intet passende kort | abstained | 0 |

## Brugerhjælp og begrænsninger

Alle løste opgaver krævede bekræftet model, givne felter, symbolenheder og betingelser. Handlingstal er semantiske formularhandlinger, ikke observerede menneskelige klik; se protocol.md. Den nye taloverførsel blev kontrolleret i regressionstesten, men denne evaluering anvendte eksplicit fuld indtastning for at logge alle data.

EV5 krævede desuden enhedsangivelse for de beregnede E- og V-referencer, fordi formularens symbolscanner medtager dem. Testværktøjet blev udvidet til at indtaste disse kendte enheder, efter evalueringen standsede på formulartrinnet; hverken fysikmotor, spørgsmål eller givne tal blev ændret, og de første fire registrerede svar blev ikke genberegnet. Dette er ekstra brugerhjælp og en kendt formularbegrænsning.

Manglende emner: generelle leder-randværdiproblemer (kuben), ikke-lineære/hysteretiske materialer uden tilstandsdata og serielle RLC-systemer med to begyndelsesbetingelser. Ingen numerisk løsning eller materialetilstand blev gættet.

Næste prioritering: mindre formulararbejde og sikker overførsel af beregnede resultatreferencer; bredere deterministisk forståelse af tekst og figuroplysninger; generaliseret lineær kredsløbs-ODE af anden orden; generelle randværdiproblemer kræver egen valideret numerisk metode.

Verificeret på Linux med faktisk PySide6 MainWindow, QProcess, beregningsworker og tre visningsfaner. Native Windows er ikke testet.
