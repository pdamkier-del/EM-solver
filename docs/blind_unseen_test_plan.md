# Blind unseen stress-test plan

These cases were designed **after** the historical solver work. They should be run through the same public "Ny opgave" path. Do not add ID-specific special cases before measuring baseline performance.

## Pass criteria

A case passes only if:
- the method is physically appropriate,
- the setup is correct,
- the result is correct or the symbolic fallback is correct,
- direction/sign is correct when relevant,
- runtime validation does not silently accept invalid assumptions.

## Cases

### EV
1. **Sphere with rho(r)=k r^2** — Gauss + piecewise E + V with V(infinity)=0.
2. **Hollow cylinder with rho(s)=k/s for a<s<b** — three-region Gauss solution.
3. **V(x,z)=V0 exp(-kz) cos(kx)** — compute E and verify rho=0.
4. **Ring with lambda(phi)=lambda0 cos(phi)** — Coulomb integral; must not select Gauss.
5. **Sphere with P=alpha r rhat** — bound volume/surface charge; total bound charge zero.
6. **Parallel-plate capacitor half-filled side-by-side with eps1/eps2** — recognize parallel capacitances.

### BA
7. **Cylinder with J(s)=J0(1-s^2/R^2)** — Ampere inside/outside.
8. **A=A0(-y xhat + x yhat)** — curl to obtain uniform B.
9. **Finite straight wire from -L to +L** — Biot-Savart; must not use infinite-wire Ampere formula.
10. **Circular arc plus radial leads** — arc contributes, radial leads give zero at center.
11. **Toroid with permeability mu and air gap g** — H/B piecewise with Ampere's law.

### DYN
12. **Circular loop in B(s,t)=beta t s zhat** — spatial flux integral then Faraday.
13. **Expanding square in decaying B(t)** — product rule in d(BA)/dt.
14. **Circular capacitor plates with E(t)=E0 t^2** — Ampere-Maxwell inside/outside plate radius.
15. **Coaxial cable inductance and magnetic energy per length** — consistency with U=1/2 LI^2.
16. **1D conductor with sigma(x)=sigma0(1+x/L)** — R, E(x), rho(x).

### Generalization / rejection
17. **Uniformly charged ellipse** — parameterized line geometry; correct symbolic Coulomb integral is sufficient.
18. **Proposed electrostatic E=(alpha y)xhat+(beta z)yhat+(gamma x)zhat** — compute curl and reject unless alpha=beta=gamma=0.

## Required reporting

For each case record:
- parser interpretation,
- proposed method,
- whether manual correction was needed,
- solver result,
- runtime checks,
- pass/fail,
- failure class: parser / method selection / solver / rendering / timeout.

Report:
- total blind success rate,
- success rate before manual correction,
- success rate after manual correction,
- top three failure modes.

Do not modify solver behavior until the baseline run has been recorded.
