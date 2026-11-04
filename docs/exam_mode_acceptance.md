# EM1 exam-mode acceptance specification

Purpose: make the offline solver fast and safe enough to use under exam conditions without generative AI or internet.

## Primary workflow

The default page should be **Ny opgave**.

1. Paste problem text.
2. Click **Analysér opgave**.
3. Show an editable interpretation before solving:
   - domain: EV / BA / DYN
   - geometry
   - known quantities/functions
   - regions
   - wanted quantities
   - proposed method
   - assumptions
4. Highlight uncertainty and missing information.
5. User confirms/corrects interpretation.
6. Click **Løs opgave**.
7. Render a compact exam-ready solution.

The parser must never silently invent missing assumptions.

## Result layout

In Exam mode, show only:

1. Genkendelse / metode
2. Givet og søges
3. Startformler
4. Necessary intermediate calculations
5. Boxed final result
6. Direction/sign
7. Relevant checks
8. Warnings

A separate **Forklaring** mode may add pedagogical prose.

## Confidence state

Every new problem should show one of:

- GREEN: method and inputs sufficiently determined.
- YELLOW: solvable, but one or more interpretation choices should be checked.
- RED: not uniquely determined; do not solve until corrected.

Confidence must be based on deterministic parser/validation state, not a probabilistic LLM score.

## Method-selection safety

Do not choose Gauss merely because a sphere/cylinder/plane is mentioned.
Do not choose Ampere merely because a wire/cylinder is mentioned.

The required symmetry assumptions must be verified.

Fallback examples:

- electric field: Gauss -> potential/Coulomb integral
- magnetic field: Ampere -> Biot-Savart
- line source: parameterized line integral
- unsolved analytic integral: display correct symbolic integral, optionally numerical evaluation

## Speed requirements

The normal path should require no more than:
- paste text
- inspect/correct interpretation
- solve

No required navigation through multiple pages.

If symbolic work times out, return a useful partial result instead of hanging:
- selected method
- correctly set up integral/equation
- timeout warning
- numerical option if possible

## Copy/export

Provide:
- Copy solution
- Copy final result
- LaTeX export
- Plain-text export

All must work offline.

## Historical fallback

Keep historical presets as a separate training/smoke-test path. They must not dominate the default exam interface.

## Acceptance tests before Friday

At minimum verify:
- new Gauss sphere/cylinder with unseen rho functions
- new Ampere cylinder with unseen J(s)
- finite wire -> Biot-Savart, not infinite-wire Ampere
- nonuniform line charge -> Coulomb integral
- B(s,t) flux integral -> Faraday
- moving/changing loop -> product rule
- vector potential -> curl
- nonconservative proposed electrostatic E -> correct physical rejection
- parameterized ellipse -> correct symbolic line integral fallback
- missing information -> explicit rejection, no guessed assumption

## Non-goals before the exam

Do not spend significant time on:
- cloud deployment
- accounts/login
- generative AI
- OCR/image recognition
- FEM/general PDE solver
- visual polish that does not improve exam speed or correctness

Priority: correctness > safe interpretation > speed > polish.
