# Stable-kriterier og evidens

`stable` certificerer de dokumenterede implementerede inputmodeller.
Det er ikke en garanti for vilkårlig fysik eller autonom opgavefortolkning.

## Familiecertifikat

1. En fuld testkørsel uden fejl, skips eller xfails; fingerprintet skal
   svare til den aktuelle fysikkode, tests, opskrifter, registry, policy
   og certifier. Ændringer ugyldiggør certifikaterne.
2. Alle relevante primære og sekundære kvantitative historiske ID'er
   samt alle opskrifter, der faktisk kalder familien, skal bestå facitchecks.
   Juni 2021 1b undtages eksplicit som kvalitativ/manual.
3. Mindst én bestået historisk opskrift skal faktisk kalde familien.
   En metodeetiket eller en anden solvers svar certificerer ikke familien.
4. Risikobaserede variationer: LOW mindst 2, MEDIUM 4, HIGH 6. Policy og
   kort risikobegrundelse findes i `data/certification_policy.json`.
   HIGH omfatter regioner, koordinater og geometriske randbetingelser.
   Variationerne efterprøver selvstændige grænser, fortegn og ugyldige
   antagelser. Antal alene er ikke et fysisk korrekthedsbevis.
5. Bestået uafhængig dimensions-testsuite (mindst ti tests), inklusive
   bevidst forkerte enheder, manglende længde og forkert tidspotens.
6. Faglig relation til formelsamlingen og konventionsforskelle er
   gennemgået i `formula_alignment.md`.

Alle familier evalueres automatisk; ingen stable-flag sættes manuelt.
Præcise historiske ID'er, variations-tests og konkrete blokeringer gemmes
pr. familie i `data/solver_certificates.json`.

## Runtime-krav

`Solution.stable=true` kræver desuden gyldigt familiecertifikat,
eksplicitte enheder for de anvendte symboler, beståede input-/resultat-
dimensionskontroller og alle udførte fysiske checks bestået.
Ukendte dimensioner tæller ikke som bestået. Nulvektorer er kompatible
med den deklarerede dimension. SI-etiketter alene er ikke en kontrol.

Manglende krævede symmetrier, randbetingelser og kendt ugyldige parametre
afvises i de relevante inputmodeller. Symbolske domæner skal stadig
fremgå af antagelserne. En forkert dimensionskontrol udelukker stable.

Preset-diagnostikken viser familie- og runtime-blokeringer. Dashboardet
viser method, executable, correct executable og stable separat, pr.
eksamen og pr. historisk ID. En bestået opskrift dækker kun dens eksplicitte
facitorakler; dette betyder ikke automatisk kvalitativ PDF-besvarelse.

## Reproducer hele forløbet

```sh
python tools/certify_all.py
```

Kører hele pytest-suiten inklusive historik, dansk LaTeX-rendering,
variationer og dimensioner; genererer certifikater og dashboard; kører
EV/BA/DYN-app-presets med socket-forbindelser blokeret. En fejl stopper
batchen. Rapporter er i `reports/test-results.json`,
`reports/coverage_summary.json` og `reports/exam_coverage.md`.
