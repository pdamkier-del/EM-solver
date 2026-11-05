# EM1 Desktop v0.6 – viewer exchange format

This is a **desktop display import schema** (`em1.desktop.solution.v1`), NOT a claim that the existing Codex `docs/backend/API.md` uses these exact fields. The Codex repository is not attached here. Write a minimal adapter from its actual API to this structure after verifying that schema.

```json
{
  "viewer_schema": "em1.desktop.solution.v1",
  "title": "Cylindrisk Gauss-problem",
  "prompt": "...",
  "status": "verified",
  "interpretation": {"method": "Gauss", "geometry": "uendelig cylinder"},
  "result": {"symbolic_latex": "E(s)=\\frac{\\rho s}{2\\varepsilon_0}", "numeric_text": null, "units": "N/C"},
  "steps": [{"id": "gauss-1", "title": "Metodevalg", "reason": "...", "latex": "...", "check": "..."}],
  "warnings": []
}
```

`status`: verified, assumptions, partial, unsolved or unverified. Frontend displays status exactly as supplied, never certifies it itself. `steps` order is preserved and each step is shown both as mathematical derivation with reasons and as pure explanatory view. A malformed/unrecognized JSON file is rejected. `symbolic_latex` and each `latex` field are display math expressions *without* `\\[...\\]` delimiters. Matplotlib MathText is used offline and supports only part of LaTeX. Some expressions may be shown as an explicit fallback rather than beautifully typeset.

**Integration contract:** Keep Codex solver physically separate. Build a verified adapter for its real output, import dynamically through that adapter, do not pre-fill missing physics, and never label absent verification as verified. A CSV/text/JSON display import is not equivalent to live solver integration.

## v0.8 optional explanatory fields

Each `steps[]` object may also include `substitution` (text explaining which quantities or expressions were inserted) and `operation` (algebraic action performed). Both are optional and backward compatible. They are presented as text accompanying `latex`, not inferred by the UI.

`result.extra_latex` is an optional list of additional result equations shown after the primary `symbolic_latex`; useful for piecewise solutions without relying on MathText `cases`.
