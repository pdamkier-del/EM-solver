# Prospektiv evaluering af 20 nye tekster

Spørgsmål og planlagte input er fastlagt i questions_and_inputs.json og SHA256 i seal.json før første beregning. Ingen produktionskode må ændres mellem første opgave og sidste registrerede svar. Hvis et svar fejler, registreres fejlen frem for at justere motoren. Referencer beregnes først efter alle appkald i en separat beregningsfil uden imports af EM1-motoren.

Dette er selvkonstruerede opgaver og ikke en uafhængig ekstern blindtest: samme udvikler har valgt spørgsmål og modeller. Nye geometrier, funktioner, koefficienter og sammensætninger er testvariationer, ikke et mål for hele pensum eller et helt eksamenssæt. Der er 7 EV, 6 BA og 7 DYN; 3 er bevidst uden passende kort eller nødvendige materialedata.

Den faktiske MainWindow bruges først med “Løs opgave med backend”, uden rettelser. Derefter åbnes “Vælg fysisk model”, og de låste, brugerbekræftede fysiske oplysninger indtastes i de samme widgets som i appen. Beregning sker via QProcess og en begrænset offlineworker. Alle tre visningsfaner kontrolleres for matematikfejl. Ingen PDF-facit eller historiske opskrifter læses af evaluatoren. Råtekst-backenden har dog fortsat sit eksisterende historiske bibliotek, derfor er dette heller ikke en påstand om en træningsfri motor.

Kategorier pr. opgave: fuldt korrekt (alle efterspurgte resultater, retninger og nødvendige betingelser), delvist korrekt (korrekt delmængde eller uafsluttet matematisk svar), forkert (forkert fysik eller resultat), afstået (intet brugbart beregnet svar). Automatisk/assisteret registreres separat. Betinget korrekt svar under en gyldig brugerbekræftet model kan være fuldt korrekt ved denne sammenligning uden at være universelt fysikcertificeret.

Brugerhjælp tælles som semantiske kontrolhandlinger: tekstindsættelse, modelåbning/-valg, felt-/tabelindhold, symbolenheder, tal, positive markeringer, bekræftelser, efterbehandling og beregningsknap. Dette er reproducerbare programmerede widgethandlinger, ikke observation af et menneskes klik eller tidsforbrug. Modelkortets tomme valgfrie felter tælles konservativt som formularfelter, hvorfor tallet er et overslag over formulararbejde, ikke en præcis minimal interaktionslængde. Ingen oplysninger kommer fra referencesvar.

Alle opgaver tæller i nævneren 20, også de tre uden kort. Automatisk forkerte forsøg registreres særskilt, selv hvis den assisterede vej senere løser opgaven. Det samlede forløb rubriceres efter bedste faktisk opnåede, fysisk gyldige løsning uden at skjule tidligere fejlsvar.
