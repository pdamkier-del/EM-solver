# EM1 Solver på Windows

1. Installer **64-bit Python 3.12** fra Python.org med Python Launcher (`py`).
2. Hent projektet eller udpak `EM1-Solver-Windows.zip` til en skrivbar mappe.
   Pak hele ZIP-filen ud; start ikke direkte inde i ZIP-visningen.
3. Dobbeltklik **install_windows.bat**. Vent på `Systemstatus: Klar`.
4. Dobbeltklik **START_EM1_SOLVER.bat**. Appen starter på `127.0.0.1`
   og åbner standardbrowseren. Adressen står også i vinduet, hvis browseren
   ikke åbner. Lad startvinduet være åbent under eksamen.
5. Vælg Ny opgave eller Manuel solver. Ingen terminalkommandoer kræves.

Installationen behøver normalt internet; selve appdriften gør ikke.
Ingen API-nøgler, lokale sprogmodeller eller cloud-konti bruges.

## Installation uden netforbindelse

Før eksamen: kør **prepare_windows_offline.bat** på en Windows-computer
med internet og Python 3.12. Det henter Windows-kompatible wheels til
`wheelhouse/`. Kopier hele projektet inklusive denne mappe til en
Windows-computer med samme arkitektur og Python 3.12 allerede installeret.
`install_windows.bat` bruger automatisk `--no-index` og dette lokale arkiv.
Hvis wheel-download fejler, er offline-installationspakken ikke komplet.
Den leverede kilde-ZIP indeholder ikke et downloadet Windows-wheelarkiv
eller selve Python-installationen.

Geninstallér ikke om morgenen før eksamen. Afprøv appen og de nødvendige
opgavetyper, mens der stadig er tid til at rette maskinopsætningen.

## Eksamen med Wi-Fi slået fra

- Åbn appen via START_EM1_SOLVER.bat og slå derefter Wi-Fi fra.
- Gennemfør en EV-, BA- og DYN-opgave med formularerne.
- Kontrollér fortegn, enheder, regioner og eksport.
- Lokal browserforbindelse til 127.0.0.1 skal tillades i en eventuel firewall.
- Port 8501 må ikke allerede bruges af et andet program. Luk en tidligere
  Streamlit-instans, hvis launcher melder portkonflikt.

## Autosave

Seneste ændrede opgave og løsningskopi gemmes atomisk i
`%LOCALAPPDATA%\EM1Solver\latest.json`. Brug **Gendan seneste lokale arbejde**
og **Gendan opgave** efter genstart. Bekræft modellen igen før genberegning.
Den gemte tekstkopi er tydeligt markeret som en historisk kopi.

`EM1_STATE_DIR` kan sættes til en anden lokal mappe ved behov. Ingen
historik uploades. Undlad at køre to eksamenssessioner samtidigt i samme
autosave-mappe; den sidst gemte session bliver den nyeste.

## Valideringens platformgrænse

Udviklingsmiljøet er Linux. Den fælles Python-launcher, en rigtig lokal
Streamlit-server, spawn-workers, autosave og UI-forløb er testet dér.
Windows-batchfilerne er leveret med CRLF og passende stier/anførselstegn,
men en native Windows-dobbeltklik/browser-test kan ikke udføres i dette
miljø. Afprøv derfor ovenstående trin på den konkrete eksamenscomputer.

Specialiseret metode har en separat lokal autosave-fil
`%LOCALAPPDATA%\EM1Solver\specialized.json`, som gendannes fra den samme
specialiserede formular. Eksportér gerne løsningen som ekstra sikkerhed.
