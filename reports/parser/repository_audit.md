# Repository-audit ved genoptagelse, 2026-11-05

- Workspace: `/workspace/EM-solver`.
- Aktiv branch: `em1-domain-parser-2026-11-04`; HEAD ved overtagelse: `2f839c9696c12e7431b39fe431b693b8190049d1`.
- Andre lokale branches: `work` på samme commit og `exam-ready-download-2026-11-05` på `6ed34ee2d864ab6b298f1202455792693f4e02f0`.
- Den omtalte `parser-recovery-2026-11-04` fandtes ikke lokalt. Ingen ny kloning eller omskrivning blev foretaget.
- Der fandtes ucommittet parserarbejde i `em1_solver/text_parser/`, `data/parser/`, `tests/parser/`, `em1_solver/ui_text_parser.py`, samt ændringer i app/navigation. Dette blev videreført.
- Første genoptagede parserkørsel: 47 beståede og 10 fejlede tests. Fejl omfattede adapterens manglende symmetry-antagelser, ufuldstændig enheds-tokenisering og nye tests, som fejlagtigt forventede prefiks-enheder efter en SI-konvertering. De oprindelige fysiksolvere blev ikke ændret.
- Det frosne tags commit er kontrolleret med `exam-ready-2026-11-05^{commit}` og er fortsat `2f839c9696c12e7431b39fe431b693b8190049d1`.
- `EM1-Solver-Windows.zip`: 5.088.198 bytes, SHA-256 `b1f1d47fd28a12c545b5a8b3ba425826ed42cf552958af95fd158b8ab04d7af6`, uændret.
- 11 eksamener, 154 delopgaver og 25 konsoliderede primære familier er i eksisterende auditdata. Registreringslaget har desuden hjælpe-/alternative beregningsveje; antal registry-entries er derfor ikke det samme som antal primære eksamensfamilier.
- Genkørt fuld dækning: 153/154 eksekverbare og korrekte historiske opskrifter; 151/154 stabile. Dette er strukturerede historiske tests, ikke autonom tekstforståelse.
- Den oprindelige 55-bankrapport har 3 autonome successes: to feltberegninger og en korrekt metodeafvisning; den assisterede score er 55/55. Denne bank er allerede kendt i projektet.
- `core/`, `solvers/`, den oprindelige assisted-UI og specialiserede UI, dependencies og Windows-batchfiler er byte-identiske med den frosne commit. Nye parser-/UI-lag ligger separat. Certifikater/dækningsrapporter er regenereret efter nye tests.
- Ingen push, ændring af release-tag, main-ændring eller udgivelse er udført i denne opgave. Den nye versionspakke gemmes lokalt med et andet navn.
