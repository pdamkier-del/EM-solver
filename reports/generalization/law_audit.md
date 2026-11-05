# Fysiklove, sammensætning og grænser

Udviklingsbranch fra 706e2711. Den leverede integrationsbranch, main og frosne releases er uændrede. Ingen eksamens-ID'er eller facit i de nye kerner.

| Eksisterende modelgruppe | Generel lov og variationer | Bevidst afgrænsning |
|---|---|---|
| EV kugle/cylinder/plan-regioner | Integrér vilkårlig rho over hver region; D fra Gauss, E fra eksplicit epsilon; fladekilder særskilt | Kræver deklareret symmetri. Plan kræver spejlsymmetri. Endelige cylindre er ikke uendelige |
| EV koncentriske ledere/hulrum | Gauss og elektrostatisk ligevægt; inducerede nettoladninger, regionale felter og potentialer | Hulrumskortet giver ikke lokal fordeling i asymmetrisk hulrum |
| EV potentiale/felt/potentialforskel | Gradient, divergens, curl og orienteret integral med korrekt koordinatmetrik | Glatte områder; singularitetens delta-led kræver særskilt behandling |
| EV punktkilder | Vektorsuperposition, potentiale, testkraft | Ingen selvfelter eller sammenfaldende kilder |
| EV billeder | Entydighed og randpotentiale; vilkårligt orienteret forskudt plan, jordet/ladet isoleret kugle, op til otte eksterne ladninger | Ikke vilkårlige lederformer eller indre kuglehulrum; ingen fysisk energi fra fiktiv parenergi |
| BA Ampère-ledning/regioner | Integrér vilkårlig aksial J(s) over regioner, evt. overfladestrøm | Kræver uendelig cylindrisk symmetri og stationære strømme |
| BA Biot–Savart | Parameteriseret orienteret kurve med eksplicitte endelige/uendelige grænser | Symbolsk budget; uafsluttet integral er delvist, ikke et tal |
| BA superposition | Summer vektorfelter fra parallelle ledninger/uniforme cylindre, også negative kilder for hulrum | Ikke vilkårlige finite volumenkilder |
| BA vektorpotentiale | Curl(A), div(B), Ampère-residual | Glatte stationære felter, ingen materiale-PDE-løser |
| BA magnetisering | Jb=curl(M), Kb=M×n i tre koordinatsystemer; B kun med eksplicit H | M bestemmer ikke generelt H alene |
| BA uniform magnetiseret kugle | Indre H og ydre dipol bestemt ved normal B/tangentiel H kontinuitet | Foreskrevet uniform M, ingen frie strømme eller påtrykt felt |
| DYN flux/homogent felt/fluxintegral | -N dPhi/dt. B og geometri må begge variere | Fortegn kræver orientering; rent resistiv strøm kræver negligerbar selvinduktans |
| DYN bevægelsesinduktion | Integral af (v×B)·dl med orienteret kurve og eksplicitte grænser | Returvejen skal være oplyst stationær; ikke dobbeltregning af flux og bevægelse |
| DYN stang-feedback | Samtidige kraft- og kredsløbsligninger med generel initialhastighed/drivning | Lineære konstante mekaniske koefficienter, ingen friktion |
| DYN RC/RL | dsolve med eksplicit begyndelsesbetingelse, konstant R,C,L og givet V(t) | Ikke generelt RLC-netværk, ikke ikke-lineære komponenter |
| DYN forskydningsstrøm | Ampère–Maxwell, cirkulær pladegeometri | Homogent aksialt E, vakuumgab, randeffekter negligeres eksplicit |

## Fælles resultatoperationer

Op til otte sekventielle operationer i samme netværksblokerede, tidsbegrænsede worker: differentiation (evt. i et punkt), evaluering, grænse, reel ligningsløsning, bestemt integration, enhedskontrolleret algebraisk forbindelse og lineær førsteordens ODE a·dy/dt+b·y=kilde, y(0)=y0. Operationer vælger resultater og refererer til tidligere resultater. a,b,y0 skal være tidsuafhængige. Fysisk betydning bekræftes; dimensionsrigtighed beviser ikke en lovs relevans.

Eksempler testet separat: rho → Gauss E → regionalt V → testkraft qE og potentiel energi qV; flux → emf → induktiv kredsstrøm → Joule-effekt → varmeintegral. Magnetisk B kan føres til flux via en eksplicit bekræftet formel (fx B*A for homogent normalfelt) og derefter differentieres. Vektorprojektioner/generelle fladeintegraler skal stadig parameteriseres; ingen geometrisk flade gættes.

RL: initial_slope, zero_time og extremum_times bruger de fælles operationer. Stationære tider klassificeres med andenafledte-test; det er ikke automatisk en global maksimumsbestemmelse. Ingen reel endelig rod eller identitet giver delvis status og bevarede basisresultater. Symbolske betingelser og flere grene mærkes betingede. Periodiske ligningers fundne rødder er ikke garanteret en komplet periodefamilie.

## Lokal fortolkning

Regulære udtryk foreslår kort med synligt tekstevidens, udtrækker eksplicitte numeriske tildelinger/enheder og mulige søgte størrelser. Konflikter vises og overføres ikke. Funktionsudtryk vises som ufortolkede forslag; ingen matematisk kode evalueres i GUI-tråden. Brugeren kan overføre sikre skalare tildelinger til valgt kort, men geometri, enheder, positive symboler og antagelser forbliver ubekræftede. Ingen generativ AI eller netværk bruges. Råtekstvejen og manuel solver bevares.
