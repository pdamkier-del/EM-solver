# Desktop integration handoff

The frontend can start against `em1_solver.backend.respond` and the additive API
1.0 presentation extension. Backend has no PySide6/Qt import and no renderer or
network dependency. Existing Streamlit navigation/layout is unchanged.

```python
from em1_solver.backend_client import run_text, choose_view
reply = run_text(raw_danish_task)   # run in a background task, not the GUI thread
result = choose_view(reply, 'result')
derivation = choose_view(reply, 'derivation')
explanation = choose_view(reply, 'explanation')
```

Keep `reply` in frontend state. Switching levels does not invoke SymPy, parsing or
a worker. Missing inputs are in `reply['missing']`, with full per-field confidence
and evidence in `reply['interpretation']['fields']`. Amend the original text or
explicit correction strings, then calculate again. Do not turn null into zero.

Respect `not_solved`, `partial`, `verified_with_assumptions` and `verified`.
`ready` means analysis is ready to attempt computation. A mathematically verified
negative diagnosis may set `physical_model_rejected=True`; never present that as
a physical field being accepted. Display assumptions/validity/warnings at every
level. A passed check proves only its own stated property, not all physics.

`validate_response` validates structure, status consistency, references and the
LaTeX profile. It does not redo physics or authenticate a manually modified cache.
Use trusted backend replies; never eval expression strings or LaTeX.

## Offline CLI

With the project's existing Python environment:

```sh
python -m em1_solver.backend_client --input task.txt --output reply.json --view result
python -m em1_solver.backend_client --response reply.json --view derivation
python -m em1_solver.backend_client --response reply.json --view explanation
python -m em1_solver.backend_client --input task.txt --analyse-only
```

Input/output files and CLI streams use UTF-8. A cached response requires no source
text and no computation. Exit 0 indicates a valid ready/solved/partial response;
exit 2 indicates unresolved input, invalid contract or an IO/computation failure.
Partial must still be presented as partial. The client has no Qt dependency.

`python tools/desktop_backend_smoke.py` exercises EV/BA/DYN, multiple sources,
material/potential chains and missing-data abstention, validates JSON/LaTeX and
opens all three cached levels with outbound sockets blocked.

## PySide6 bridge

`examples/pyside_backend_worker.py` supplies a QRunnable with completed/failed
signals and a headless QCoreApplication example. Use it from the separate frontend:

```sh
python -m examples.pyside_backend_worker
```

It requires PySide6 in the frontend environment; no Qt dependency was added to the
backend requirements. Call `multiprocessing.freeze_support()` inside the desktop
entry point's `if __name__ == '__main__'` guard. The sample does this. Importing a
module in a spawned worker must not open a window or start another event loop.

The example keeps the Qt event loop responsive while the existing bounded symbolic
worker calculates. Deliver returned dictionaries through signals to the UI thread;
keep rendering outside backend. Native Windows/PySide6 execution and the actual
math renderer still require frontend acceptance tests. Linux backend/widget tests
are not substitutes for those tests. No installer or desktop layout is delivered
by this backend handoff, and no frozen ZIP is rebuilt.

## Exact entry point and Windows setup

Supported runtime: CPython 3.12. The backend-only pinned dependencies are in
`requirements-backend-lock.txt` (SymPy, mpmath, Pint and Pint's four dependencies).
The complete existing app's requirements are unchanged. Backend imports no Qt,
Streamlit, NumPy or pandas; the dependency-isolation smoke tests this in a `-S`
interpreter containing only those seven installed distributions.

From the extracted integration root on a Windows computer:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-backend-lock.txt
.venv\Scripts\python.exe -m em1_solver.backend_client --input task.txt --output reply.json
```

Installation can require internet once. For an offline installation, prepare a
wheelhouse for the pinned requirements first, then use:

```bat
.venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r requirements-backend-lock.txt
```

No wheelhouse, Python executable or PySide6 installer is bundled in the source
integration ZIP. Runtime solving and cached-view selection are fully local. The
frontend must supply its own compatible PySide6 environment; no untested Qt
version is silently added to the backend lock.

The exact function entry points are:

- `em1_solver.backend.respond(request: dict, *, solve: bool = False) -> dict`
- `em1_solver.backend_client.run_text(text: str, *, solve=True, corrections=None, evaluate_integrals=False) -> dict`
- `em1_solver.backend_client.choose_view(response: dict, level: str) -> dict`

A request is JSON with `schema_version: "1.0"`, `text`, optional `corrections`, and
optional boolean `evaluate_integrals`. See `docs/backend/schema-v1.json` for the
response and `docs/backend/API.md` for status/field semantics. Text/LaTeX are not
executable code. No task ID, answer or preset is part of an accepted request.

If the desktop app lives in a separate directory, keep the integration folder
intact (including its `data` directory) and add its root to Python's module path
BEFORE importing `em1_solver`. For example, in the desktop entry point:

```python
from pathlib import Path
import sys
backend_root = Path(__file__).resolve().parent / 'vendor' / 'EM1-Solver'
sys.path.insert(0, str(backend_root))
from em1_solver.backend_client import run_text, choose_view
```

Do not point the frontend at the evolving physics worktree. Use the published
integration commit or the extracted version-fixed integration package.

## Integration fixtures

`data/integration/desktop_v1/` contains six full request/response pairs: multi-point
EV, regional potential, dielectric D/E/P, Ampère/current, Ampère–Maxwell and an
unsolvable/missing-extent request. `index.json` records fixture hashes, source
hashes, Python version and the dependency-lock hash. All solved replies include
all three presentation levels, stable step IDs and validated EM1-Math-1 fragments.
The missing-input reply intentionally has `solution: null`; it must not invent
three levels of solution content. It remains valid input to `choose_view`, which
returns the missing information instead of an approved result.

Replay any fixture WITHOUT solving:

```bat
.venv\Scripts\python.exe -m em1_solver.backend_client --response data\integration\desktop_v1\EV_point.response.json --view explanation
```

`tools/desktop_backend_smoke.py` regenerates fixtures only when deliberately
validating a NEW integration snapshot. Do not regenerate them on the frozen
integration branch during later physics development.
