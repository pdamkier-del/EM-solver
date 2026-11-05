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

The current model describes one recognized body plus its sources and support
relations. Multiple independently identified bodies, arbitrary initial conditions,
previous-subquestion context and many material boundary problems remain unsupported;
the API exposes missing data instead of inventing objects or conditions.

Expression strings and LaTeX are output formats. Do not eval them. To change input,
resubmit raw mathematical text or explicit correction strings. No UI/layout changes
are required by this API. The current Streamlit UI continues using its existing
public text/solver functions.
