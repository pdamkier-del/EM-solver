# EM1 Solver Desktop v0.7 – Test af løsningsvisningen

Dette er en **Windows-desktopapp**, ikke en autonom solver. Den er bygget på v0.6 med uændret lokal notedatabase.

## Brug

1. Pak ZIP'en ud, helst til `C:\EM1`.
2. Åbn `EM1-Desktop-Prototype` og start `START_WINDOWS.bat`.
3. Vælg en af de fem testbesvarelser øverst og tryk **Vis testbesvarelse**.
4. Skift mellem **Resultat**, **Udledning** og **Forklaring**.
5. Vælg **Importér solver-JSON** for at afprøve visningsformatet med egne eksportfiler.

Testbesvarelserne er illustrative, lokalt gemte data og **er ikke output fra Codex**. Du kan ikke skrive en vilkårlig ny opgave og få den autonomt løst endnu. Der er ikke ændret noget i Codex-repository.

## Integration

Se `docs/VIEWER_EXCHANGE.md` for den lokale visningskontrakt. Når Codex' faktiske `docs/backend/API.md` og kode er til rådighed, skal en adapter mappe de rigtige felter til dette visningsformat. Intet felt må gættes, og desktopappen må ikke tildele `verified` selv.

## Installation

Bruger fortsat `PySide6-Essentials`, Matplotlib og PyMuPDF. Startloggen gemmes i `EM1_START_LOG.txt`. Noter ligger under `%APPDATA%\EM1SolverDesktop` og overskrives ikke af opdatering.
