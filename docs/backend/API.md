# Offline backend JSON API 1.0

Python entry point (no server or network required):

```python
from em1_solver.backend import respond
import json
request = {
    'schema_version': '1.0',
    'text': 'En massiv kugle med radius R har rho(r)=k*r. Bestem den totale ladning Q.',
    'corrections': {},
    'evaluate_integrals': False,
}
interpretation = respond(request)
answer = respond(request, solve=True)
print(json.dumps(answer, ensure_ascii=False, allow_nan=False))
```

`respond` returns native JSON values only. The frontend must preserve unknown
values; null/empty is not a physical zero. It must not render an unsuccessful
response as an approved answer. No task identifier, historical preset or gold
value is accepted or used to select a method.

Response fields:

- `schema_version`: `1.0`.
- `status`: `not_solved`, `ready`, `partial`, `verified_with_assumptions`, `verified`.
- `interpretation.model`: objects, source distributions, object/support relations,
  coordinates, orientation, boundary and initial conditions, units, numeric givens,
  wanted quantities, explicit assumptions and planned dependencies.
- `interpretation.fields`: per-field status, evidence, missing-data explanation and
  options. GREEN is a deterministic extraction/compilation state, not probability.
- `missing`: only unresolved root questions; dependent questions remain in fields.
- `solution`: method/reason, starting equations and steps as LaTeX, result expressions
  plus SI units, numerical values, directions, warnings and individual checks.
- `errors`: concrete input, computation or physical consistency failures.

Status semantics:

- `ready`: analysis complete enough to attempt calculation, no result yet.
- `not_solved`: incomplete input, unsupported model, worker error or failed physical
  checks. A retained result is diagnostic only and must not be approved.
- `partial`: formal unevaluated integrals or unresolved verification/dimensions.
- `verified_with_assumptions`: produced outputs pass available checks, conditional
  on the listed physical assumptions. This is not a complete proof of text fidelity.
- `verified`: produced outputs pass available checks without additional recorded
  physical assumptions, e.g. differentiation of a fully given scalar function.
- `solution.physical_model_rejected`: diagnostic curl/divergence correctly rejects
  a proposed nonphysical field; false physical-model checks are expected here.

Verification status is distinct from historical solver certification. Newly composed
plans are not labelled stable just because a component has a historical certificate.
No single matching numerical answer establishes full verification.

The model supports one radial/curve body or an explicit multi-point-source scene.
General mixtures of independently identified bodies, arbitrary initial conditions,
previous-subquestion context and many material boundary problems remain unsupported;
the API exposes missing data instead of inventing objects or conditions.

Expression strings and LaTeX are output formats. Do not eval them. To change input,
resubmit raw mathematical text or explicit correction strings. No UI/layout changes
are required by this API. The current Streamlit UI continues using its existing
public text/solver functions.


## Additive desktop presentation extension (API remains 1.0)

Existing top-level fields, `steps[].text/latex`, result `expression/latex/unit`,
and numerical `value/unit` are preserved. The existing response schema already
allowed additional solution/step fields, so the extension is backwards compatible
for readers of the original fields. No new request option is necessary.

Fresh replies add `solution.presentation_version = "1.0"`,
`latex_profile = "EM1-Math-1"`, `method_contexts` and `views`.
Steps add deterministic `id`, `title`, `physical_reasoning` (nullable),
`reasoning_scope`, `law`, `method_context_id`, `intermediate_latex`, `assumptions`,
`validity` and `check_ids`. Checks add `id` and `step_ids`. Numerical values also
have math LaTeX. IDs are stable for the same execution structure with the pinned
SymPy version. They are not promised unchanged after editing equations or changing
library versions. Identical repeated steps receive deterministic occurrence IDs.

Context is captured by `Solution.add` AT EXECUTION. A nested potential solver's
steps retain its own method/reason after merging with Gauss steps. Serialization
never guesses a law from wording or invents a missing local explanation. With
`reasoning_scope="method"`, use the referenced method context's physical reason;
with `"step"`, the explicit local physical reason was supplied by that operation.
Unlinked checks are global checks, not fabricated local evidence.

Three views reference the same computed payload:

- `views.result`: requested final symbolic/numeric results and direction.
- `views.derivation`: starting equations and ordered step IDs.
- `views.explanation`: steps, executed-method contexts and global check IDs.

`em1_solver.backend_client.choose_view(reply, level)` resolves references without
parsing or solving. It retains status, assumptions, validity, warnings and the
`physical_model_rejected` flag at every level. A failed/unsolved response is never
exposed as an approved result. Cached legacy replies without structured views
need one recalculation with this backend; the client does not silently recalculate
on view changes.

The model now represents multiple explicit point sources, their pair interactions,
the observation point and force target. Every source position and the Cartesian
frame must be given. This bounded profile supports at most 16 point sources;
excess sources are rejected rather than omitted. Groups/figures, time-dependent sources and unparsed source
bindings cause abstention. Energy-only requests require no observation point;
force on a source excludes self-field. Model conditions explicitly scope the
stationary vacuum Coulomb calculation and source separation.

A complete scalar material model is also supported for one filled radial body:
free volume charge, linear isotropic positive permittivity, and explicit vacuum
outside. D/E/P and spherical potential chains use the supplied constitutive law.
Unknown exterior media, anisotropy, missing material parameters and extra free
surface charges are not replaced by vacuum assumptions.

See [desktop handoff](../desktop/INTEGRATION.md) and
[LaTeX profile](../desktop/LATEX_PROFILE.md).
