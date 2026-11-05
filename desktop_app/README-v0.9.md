# EM1 Solver v0.9 – sammenhængende udledninger

Den samme offline Windows-app som v0.8, med en forbedret læsevenlig løsningsvisning:

- En sammenhængende, Markdown-lignende udledning med naturlige afsnit og overskrifter.
- Matematisk indsættelse og omskrivning står sammen med den ligning, de forklarer.
- Diskrete skillelinjer mellem trin og roligere typografi.
- Matematiske formler er fortsat genereret separat af Matplotlib MathText, ikke som PDF-tekst.
- De fem testcases og JSON-visningsformatet er bevaret.
- Codex-backenden er **ikke integreret**. Testcases må ikke forveksles med autonome beregninger.

Start på Windows med `START_WINDOWS.bat` og vælg en testbesvarelse.

## Næste trin

Når Codex-backendens faktiske kode og `docs/backend/API.md` er tilgængelige, skal der bygges en adapter til `em1.desktop.solution.v1`, og hele kæden skal testes på hidtil usete eksamensopgaver. Undlad at gætte API-felter.
