# Separat fysikudvikling efter desktop-snapshot

Branch: em1-autonomous-physics-2026-11-05.
Worktree: /workspace/EM-solver-physics.
Basis: desktop-integration-2026-11-05, commit 22c78ffdc545736ddb81c042f83a94b71613b3eb.

Integrationsbranchen og /workspace/EM-solver forbliver uændrede. Denne
fysikbranch er lokal og er ikke pushet. Ingen integration-fixtures genopbygges.

Første udviklingscyklus forbedrer den eksisterende field_calculus-solver:

- Magnetostatisk afledt J kontrolleres med div(J)=0 som statisk kontinuitetslov.
- Et samtidigt givet J må ikke længere ignoreres eller overskrives uden bevis
  for konsistens med curl(B)/mu_0. Uafklaret/modstridende input afvises.
- En eksplicit tidssymbolrolle og tidsafhængigt B kan ikke erklæres magnetostatisk.
- Ingen stationær antagelse udledes alene af symbolnavne. Uden magnetostatisk
  forudsætning fremkommer ingen automatisk J fra denne statiske relation.
- Den lokale kontrol er knyttet til det faktisk udførte strømtrin i sporet.

Seks nye tests dækker analytisk J, konsistent/modstridende givet J, eksplicit tid,
fravær af den statiske antagelse og cylindriske metriske faktorer.

Fuld regression: 799 beståede, 0 fejlede. Certifikater/dækning er genkørt kun i
denne worktree. Native historiske og offline/UI-smokes består. Der hævdes ingen
ny råtekst-autonomiscore eller uafhængig blindtest på baggrund af disse kontroller.

Desktopversionens dokumenterede resultat forbliver 793 tests og dens publicerede
SHA. Nye fysikændringer må først indgå i en senere integrationsrevision efter
aftale; den publicerede integrationsreference flyttes ikke.
