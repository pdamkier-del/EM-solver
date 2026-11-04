# Blind unseen bank v2 — exam-priority plan

The full machine-readable bank is in:

`data/blind_unseen_bank_v2.json`

It contains **55 unseen problems**:

- EV: 19
- BA: 16
- DYN: 15
- General method-selection/rejection: 5

These problems were designed after the historical solver implementation and should be treated as a blind generalization benchmark.

## Run order

### Tier A — highest exam value

Run these first through the exact **Ny opgave** pipeline:

1. EV01 — sphere with new rho(r)
2. EV04 — cylinder with new rho(s)
3. EV05 — hollow multi-region cylinder
4. EV06 — nonuniform infinite slab
5. EV09 — finite line charge, general Coulomb integral
6. EV11 — nonuniform charged ring; Gauss must not be selected
7. EV16 — dielectric cylinder using D/E/P
8. EV19 — mixed Legendre boundary condition
9. BA01 — new J(s) in solid cylinder
10. BA02 — hollow cylindrical current distribution
11. BA05 — finite wire; Biot–Savart, not infinite-wire Ampere
12. BA10 — vector potential to B in Cartesian coordinates
13. BA15 — magnetic material plus air gap
14. DYN01 — B(s,t) requiring spatial flux integration
15. DYN02 — changing B and changing geometry simultaneously
16. DYN03 — Ampere–Maxwell inside/outside capacitor radius
17. DYN07 — motional EMF with mechanical feedback
18. DYN13 — induced E inside/outside time-varying B region
19. GEN02 — reject a nonconservative electrostatic field
20. GEN04 — reject direct Gauss extraction for finite cylinder

These 20 are the best first estimate of Friday robustness.

## Tier B — breadth

Run all remaining cases after Tier A.

This tests:
- capacitor variants
- polarization
- method of images
- multipoles
- loop/arc geometries
- magnetization
- inductance/mutual inductance
- RC/RL
- general parameterized ellipse
- missing-information handling
- Maxwell constraint rejection

## Scoring

Record two separate scores.

### Autonomous success

No manual corrections after pasting the problem.

A test passes only if:
- parser identifies a sufficient problem representation,
- method selection is physically valid,
- solver result/setup matches gold,
- sign/direction is correct where relevant,
- runtime checks do not report an unresolved contradiction.

### Assisted success

Manual correction of the parser/problem structure is allowed, but no solver code changes.

This separates parser quality from physics-engine quality.

## Failure classification

Every failed case must receive exactly one primary failure class:

- PARSER
- METHOD_SELECTION
- MISSING_SOLVER_CAPABILITY
- SYMBOLIC_ALGEBRA
- UNITS
- SIGN_DIRECTION
- REGION_HANDLING
- TIMEOUT
- RENDERING
- INPUT_VALIDATION

## Stop rule before fixing

Do **not** patch the solver after the first failure.

First run all Tier A cases and preserve the baseline.

Then group failures by root cause and fix the highest-yield general cause.

Never add test-ID-specific behavior.

## Desired targets

Before the exam, aim for:

- Tier A assisted success: >= 95%
- Tier A autonomous success: as high as practical
- Full-bank assisted success: >= 90%
- zero silent wrong answers on RED/insufficient-information cases

A visible refusal is safer than a confident wrong answer.
