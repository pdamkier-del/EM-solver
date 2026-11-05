# EM1-Math-1

Backend mathematics is returned as LaTeX **math fragments**, without `$`, `$$`,
`\(...\)` or document preambles. Units are separate SI strings. A desktop renderer
may wrap fragments in its own display mode. Backend imports no Qt renderer.

The profile permits ordinary LaTeX/AMS mathematics: fractions, square roots,
subscripts/exponents, Greek letters, hats/vectors, derivatives, integrals, sums,
limits, relations, common functions and `operatorname`, fonts and spacing.
Matrix/cases/array/aligned/gathered/split environments are supported. Exact macro
and environment allowlists are in `em1_solver/rendering/math_profile.py`.

Validation checks bounded fragment length, macro allowlists, balanced braces,
paired left/right and matching allowed environments. Document/IO/macro-definition,
HTML, URL and external-resource commands are excluded. No TeX process runs.

This validates a documented structural profile, not mathematical truth or every
rule of the complete TeX language. Mathematical checking is separate. Rendering
in the actual desktop renderer still needs frontend integration testing.

The historical recipe tests validate every generated starting equation, step,
intermediate expression, symbolic result and check residual through the same
serializer. Unit tests cover fractions, vectors, integrals and piecewise output,
and rejection of unsafe/broken fragments. Symbolic expressions use SymPy's pinned
LaTeX printer; source input is never passed through as trusted executable TeX.

`solution.results[name]`: expression string, math LaTeX and separate unit.
`solution.numerical[name]`: numeric representation, math LaTeX and separate unit.
`solution.direction` preserves the actual solver's basis/sign convention. Scalar
radial/azimuthal field components must not be relabelled as Cartesian vectors.
