# EM1 exam runbook

Use this as the operational fallback sequence during the exam.

## Normal path

1. Open **Ny opgave**.
2. Paste the full problem text.
3. Run **Analysér opgave**.
4. Check:
   - geometry
   - source/known quantities
   - regions
   - wanted quantity
   - proposed method
5. Correct any misunderstanding.
6. Run **Løs opgave** in **Eksamen** mode.
7. Copy only after checking warnings and final units.

## If parser is wrong

Do not keep retrying the same free text.

Switch immediately to manual structuring:
- choose EV / BA / DYN,
- choose geometry,
- enter source function(s),
- enter regions,
- enter wanted quantity.

Then solve through the same physics engine.

## If method selection looks wrong

Use this decision order.

### Electric field
- strong symmetry -> Gauss
- otherwise potential/Coulomb integral

### Magnetic field
- strong symmetry -> Ampere
- otherwise Biot-Savart/superposition

### Induction
- first establish magnetic flux
- then Faraday
- then resistance/current/power/energy as needed

Never force Gauss/Ampere just because the geometry contains a sphere/cylinder/wire.

## If symbolic solver times out

Accept a correct symbolic setup as the first safe fallback.

The app should show:
- correct governing equation,
- correct bounds/parameterization,
- remaining symbolic integral/equation,
- timeout warning.

If all numerical values are known, use numerical evaluation.

## If app says RED / insufficient information

Do not let the solver invent an assumption.

Re-read the exam statement/figure and supply the missing datum manually.

## Sanity check before using an answer

Check at least:
- units,
- sign/direction,
- region,
- relevant boundary value,
- expected limiting behavior.

Typical checks:
- outside finite line/sphere/cylinder scaling,
- continuity where no surface source exists,
- div(B)=0,
- curl(E)=0 for electrostatics,
- Lenz sign for induction.

## Emergency fallback

If the app cannot solve the problem:
1. use the formula collection,
2. use the geometry/regneteknik sheet,
3. use the app only for algebra/integration/curl/divergence where safe.

The solver is an aid, not a reason to commit to an interpretation flagged as uncertain.
