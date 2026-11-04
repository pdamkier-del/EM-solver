"""Deterministic EM1 language helpers.

This module deliberately does not solve physics. It extracts only explicit or
strongly implied structure from Danish/English exam prose and records confidence
per field. Ambiguity is surfaced instead of guessed.
"""
from __future__ import annotations

import re

GREEN = "GREEN"
YELLOW = "YELLOW"
RED = "RED"

_GREEK = {
    "ρ": "rho", "Ρ": "rho",
    "λ": "lambda", "Λ": "Lambda",
    "σ": "sigma", "Σ": "Sigma",
    "ε": "epsilon", "ϵ": "epsilon",
    "μ": "mu", "Μ": "mu",
    "α": "alpha", "Α": "alpha",
    "β": "beta", "Β": "beta",
    "γ": "gamma", "Γ": "Gamma",
    "δ": "delta", "Δ": "Delta",
    "θ": "theta", "Θ": "Theta",
    "φ": "phi", "ϕ": "phi", "Φ": "Phi",
    "ω": "omega", "Ω": "ohm",
}

def normalize_text(text: str) -> str:
    """Normalize common exam notation without executing or interpreting it."""
    if not text:
        return ""
    s = str(text)
    # Preserve exponent meaning before any broad unicode normalisation.
    s = (s.replace("⁰", "**0").replace("¹", "**1").replace("²", "**2")
           .replace("³", "**3").replace("⁴", "**4").replace("⁵", "**5")
           .replace("⁶", "**6").replace("⁷", "**7").replace("⁸", "**8")
           .replace("⁹", "**9"))
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("·", "*").replace("×", "*").replace("⋅", "*")
    # Decimal comma only when it is between digits.
    s = re.sub(r"(?<=\d),(?=\d)", ".", s)
    # Micro-prefix in a numeric unit context. Keep standalone Greek mu as mu.
    s = re.sub(r"(?<=\d)\s*[µμ](?=[A-Za-z])", " u", s)
    for greek, ascii_name in _GREEK.items():
        s = s.replace(greek, ascii_name)
    # Common vector hats used in copied PDF text.
    s = re.sub(r"\b([xyzrs])\s*\^?\s*hat\b", r"\1hat", s, flags=re.I)
    # Keep whitespace stable for regexes while preserving line boundaries.
    s = re.sub(r"[ \t]+", " ", s)
    return s

def _mark(out, field: str, level: str, reason: str = ""):
    confidence = getattr(out, "confidence", None)
    if confidence is None:
        out.confidence = {}
        confidence = out.confidence
    old = confidence.get(field)
    rank = {RED: 0, YELLOW: 1, GREEN: 2}
    if old and rank.get(old.get("level", YELLOW), 1) < rank.get(level, 1):
        return
    confidence[field] = {"level": level, "reason": reason}

def _warn_once(out, message: str):
    if message not in out.warnings:
        out.warnings.append(message)

def _geometry_candidate(text: str):
    lower = text.lower()
    patterns = [
        ("bevægelig stang", GREEN, r"\b(bevaegelig|bevægelig|glidende|roterende)\s+(ledende\s+)?stang\b"),
        ("toroid", GREEN, r"\btoroid"),
        ("spole", GREEN, r"\b(solenoide|solenoid|spole)\b"),
        ("kugleskal", GREEN, r"\b(kugleskal|sf[aæ]risk\s+skal|spherical\s+shell)\b"),
        ("cylinderskal", GREEN, r"\b(cylinderskal|hul\s+cylinder|hollow\s+cylinder|cylindrisk\s+skal)\b"),
        ("kugle", GREEN, r"\b(kugle|sphere|sf[aæ]re)\b"),
        ("cylinder", GREEN, r"\b(cylinder|cylindrisk)\b"),
        ("ring", GREEN, r"\b(ring|cirkul[aæ]r\s+loop|circular\s+loop)\b"),
        ("bue", GREEN, r"\b(bue|arc)\b"),
        ("disk", GREEN, r"\b(disk|skive)\b"),
        ("plan", GREEN, r"\b(plan|plade|slab|sheet)\b"),
        ("punktladninger", GREEN, r"\bpunktladning(?:er)?\b|\bpoint\s+charge"),
        ("ledning", YELLOW, r"\b(ledning|wire|tr[aå]d)\b"),
        ("leder", YELLOW, r"\b(leder|conductor|kondensator|capacitor)\b"),
    ]
    hits = [(g, level, m.start()) for g, level, p in patterns for m in [re.search(p, lower)] if m]
    if not hits:
        return None, None
    # Specific patterns appear before generic ones. If distinct geometries are
    # explicitly present, do not silently choose.
    distinct = []
    for g, level, pos in sorted(hits, key=lambda x: x[2]):
        if g not in distinct:
            distinct.append(g)
    # shell subsumes its base noun; moving rod subsumes generic conductor/wire.
    filtered = [g for g in distinct if not (
        (g == "cylinder" and "cylinderskal" in distinct)
        or (g == "kugle" and "kugleskal" in distinct)
        or (g in ("ledning", "leder") and "bevægelig stang" in distinct)
    )]
    if len(filtered) != 1:
        return ("AMBIGUOUS:" + ",".join(filtered)), YELLOW
    g = filtered[0]
    level = next(level for gg, level, _ in hits if gg == g)
    return g, level

def _extract_wanted(text: str):
    lower = text.lower()
    # Prefer the actual question clause, but fall back to the full text.
    parts = re.split(r"\b(?:find|bestem|beregn|udled|vis|determine|calculate|derive)\b", lower, maxsplit=1)
    q = parts[1] if len(parts) > 1 else lower
    wanted = []
    patterns = [
        ("E", r"elektrisk(?:e)?\s+felt|\be\s*\("),
        ("V", r"potential(?:e|et)?|sp[aæ]ndingsforskel"),
        ("rho", r"ladningst[aæ]thed|\brho\b"),
        ("D", r"forskydningsfelt|electric\s+displacement|\bd\b"),
        ("P", r"polaris(?:ation|ering)|\bp\b"),
        ("B", r"magnet(?:isk|iske)?\s+felt|magnetfelt|\bb\s*\("),
        ("Phi", r"magnetisk\s+flux|\bflux\b|\bphi\b"),
        ("EMF", r"elektromotorisk|\bemf\b|induceret\s+sp[aæ]nding"),
        ("I", r"\bstr[oø]m(?:men)?\b|\bcurrent\b"),
        ("F", r"\bkraft(?:en)?\b|\bforce\b"),
        ("U", r"\benergi(?:en)?\b|\benergy\b"),
        ("PWR", r"\beffekt(?:en)?\b|\bpower\b"),
        ("L", r"\binduktans(?:en)?\b|\binductance\b"),
        ("C", r"\bkapacitans(?:en)?\b|\bcapacitance\b"),
        ("torque", r"\bmoment(?:et)?\b|\btorque\b"),
    ]
    for key, pat in patterns:
        if re.search(pat, q):
            wanted.append(key)
    # Internal names used by the solver.
    mapping = {"I": "current", "F": "force", "U": "energy", "PWR": "power", "L": "inductance"}
    return list(dict.fromkeys(mapping.get(w, w) for w in wanted))

def _source_type(data: dict, text: str):
    for key in ("rho", "sigma", "lambda", "J", "A", "V", "E", "B", "P", "M", "I", "q"):
        if key in data:
            return key, GREEN
    lower = text.lower()
    phrases = [
        ("rho", r"ladningst[aæ]thed|volumenladning"),
        ("sigma", r"overfladeladning|surface\s+charge"),
        ("lambda", r"linjeladning|line\s+charge"),
        ("J", r"str[oø]mt[aæ]thed|current\s+density"),
        ("A", r"vektorpotential"),
        ("P", r"polaris(?:ation|ering)"),
        ("M", r"magnetisering|magnetization"),
        ("I", r"\bstr[oø]m(?:men)?\b|\bcurrent\b"),
    ]
    for source, pat in phrases:
        if re.search(pat, lower):
            return source, YELLOW
    return None, None

def _extent(out, text: str):
    lower = text.lower()
    if re.search(r"\b(uendelig|infinit(?:e|ely))\b", lower):
        out.data["extent"] = "infinite"
        _mark(out, "extent", GREEN, "uendelig/infinite står eksplicit")
    elif re.search(r"\b(endelig|finite)\b", lower):
        out.data["extent"] = "finite"
        _mark(out, "extent", GREEN, "endelig/finite står eksplicit")
    elif re.search(r"\b(meget\s+lang|lang\s+og\s+tynd|long\s+straight)\b", lower):
        _mark(out, "extent", YELLOW, "lang geometri ligner uendelig idealisering, men er ikke eksplicit")
        _warn_once(out, "Kilden beskrives som lang, men ikke eksplicit uendelig. Bekræft idealiseringen før Gauss/Ampère.")

def _regions(out, text: str, source: str | None):
    if not source or source not in out.data:
        return
    coord = out.data.get("coordinate")
    if not coord:
        m = re.search(r"\b(?:rho|J)\s*\(\s*([rsz])\s*\)", text)
        if m:
            coord = m.group(1)
            out.data["coordinate"] = coord
    if not coord:
        return
    # Explicit interval: a < s < b or a <= s <= b.
    interval = re.search(
        rf"\b([A-Za-z_]\w*|0)\s*<\s*=?\s*{re.escape(str(coord))}\s*<\s*=?\s*([A-Za-z_]\w*)\b",
        text,
    )
    if interval:
        lo, hi = interval.groups()
        out.data["regions"] = [dict(lower=lo, upper=hi, density=out.data[source], permittivity="epsilon_0")]
        _mark(out, "regions", GREEN, f"eksplicit interval {lo}<{coord}<{hi}")
        return
    # Radius phrasing: rho(s)=... for s<R / inside radius R.
    one_sided = re.search(rf"\b(?:for|hvor)\s+{re.escape(str(coord))}\s*<\s*=?\s*([A-Za-z_]\w*)\b", text, re.I)
    if one_sided:
        hi = one_sided.group(1)
        out.data["regions"] = [dict(lower="0", upper=hi, density=out.data[source], permittivity="epsilon_0")]
        out.data.setdefault("radius", hi)
        _mark(out, "regions", GREEN, f"eksplicit {coord}<{hi}")
        return
    radius = out.data.get("radius")
    if radius and out.geometry in ("kugle", "cylinder") and out.data.get("extent") == "infinite" if out.geometry == "cylinder" else radius:
        # Geometry + named radius strongly implies the material occupies the solid interior.
        out.data.setdefault("regions", [dict(lower="0", upper=str(radius), density=out.data[source], permittivity="epsilon_0")])
        _mark(out, "regions", YELLOW, "massiv geometri med navngivet radius; kontrollér at kilden fylder hele indersiden")

def _orientation(out, text: str):
    lower = text.lower()
    orient = out.data.setdefault("orientation", {})
    plane = re.search(r"\b(xy|yz|zx|xz)[ -]plan(?:et|e)?\b", lower)
    if plane:
        p = plane.group(1)
        if p == "xz":
            p = "zx"
        orient["plane"] = p
        _mark(out, "orientation_plane", GREEN, "planet står eksplicit")
    axis = None
    if re.search(r"\bud\s+af\s+(?:papiret|siden)|out\s+of\s+(?:the\s+)?page", lower):
        axis = "+z"
    elif re.search(r"\bind\s+i\s+(?:papiret|siden)|into\s+(?:the\s+)?page", lower):
        axis = "-z"
    else:
        m = re.search(r"(?<![A-Za-z0-9_])([+-])\s*([xyz])(?:-retning|\b)", lower)
        if m:
            axis = m.group(1) + m.group(2)
    if axis:
        orient["normal"] = axis if orient.get("plane") == "xy" or "page" in lower or "papir" in lower or "side" in lower else orient.get("normal", axis)
        _mark(out, "orientation", GREEN, f"retningen {axis} står eksplicit")

def _domain(out, source: str | None, wanted: list[str], text: str):
    lower = text.lower()
    if source in ("rho", "sigma", "lambda", "V", "E", "q", "P") or any(w in wanted for w in ("E", "V", "rho", "D", "P", "C")):
        d = "EV"
    elif source in ("J", "A", "M") or re.search(r"biot|amp[eè]re|magnetostat", lower):
        d = "BA"
    elif source == "B" and ("time" in out.data or re.search(r"tidsafh[aæ]ng|induc|faraday", lower)):
        d = "DYN"
    elif re.search(r"faraday|induceret|forskydningsstr[oø]m|amp[eè]re-maxwell|rl-kredsl|rc-kredsl", lower):
        d = "DYN"
    elif any(w in wanted for w in ("B", "force", "torque")):
        d = "BA"
    else:
        return
    out.data["_domain_hint"] = d
    _mark(out, "domain", GREEN if source else YELLOW, f"domæne udledt fra kilde/søges: {d}")

def _preset_hint(out, source: str | None):
    g = out.geometry
    d = out.data
    hint = None
    if source == "rho":
        hint = {
            "kugle": "ev_sphere", "kugleskal": "ev_shell",
            "cylinder": "ev_cylinder", "cylinderskal": "ev_hollow",
            "plan": "ev_slab",
        }.get(g)
    elif source == "sigma" and g == "plan":
        hint = "ev_plane"
    elif source == "lambda":
        hint = {"linje": "ev_line", "ring": "ev_ring", "bue": "ev_arc"}.get(g)
    elif source == "V":
        hint = "ev_potential"
    elif source == "E" and d.get("_domain_hint") == "EV":
        hint = "ev_field"
    elif source == "P":
        hint = "ev_polarization"
    elif source == "A":
        hint = "ba_vector_potential"
    elif source == "J" and g in ("cylinder", "cylinderskal"):
        hint = "ba_cylinder"
    elif source == "M":
        hint = "ba_material"
    elif source == "I":
        hint = {
            "ledning": "ba_wire", "ring": "ba_ring", "bue": "ba_arc",
            "spole": "ba_solenoid", "toroid": "ba_toroid",
        }.get(g)
    elif source == "B" and "time" in d:
        hint = "dyn_moving" if g == "bevægelig stang" or re.search(r"bevaeg|bevæeg|glid|area.*t", getattr(out, "normalized_text", ""), re.I) else "dyn_fixed"
    elif source == "E" and "time" in d and g in ("disk", "leder"):
        hint = "dyn_capacitor"
    if hint:
        out.data["_preset_hint"] = hint
        geo_level = getattr(out, "confidence", {}).get("geometry", {}).get("level", YELLOW)
        source_level = getattr(out, "confidence", {}).get("source", {}).get("level", YELLOW)
        _mark(out, "preset", GREEN if geo_level == GREEN and source_level == GREEN else YELLOW, hint)

def enrich_v2(out, extract_wanted: bool = True):
    """Add conservative high-value structure and confidence to an existing Parsed."""
    text = getattr(out, "normalized_text", "") or out.text
    candidate, level = _geometry_candidate(text)
    if candidate:
        if candidate.startswith("AMBIGUOUS:"):
            _mark(out, "geometry", YELLOW, candidate.split(":", 1)[1])
            _warn_once(out, "Flere mulige geometrier er nævnt. Vælg den geometri der faktisk bærer kilden.")
        elif out.geometry in ("Ukendt", candidate):
            out.geometry = candidate
            _mark(out, "geometry", level, "geometrien står i opgaveteksten")
        else:
            _mark(out, "geometry", YELLOW, f"eksisterende={out.geometry}, tekstforslag={candidate}")
            _warn_once(out, f"Geometri er tvetydig: parseren har både {out.geometry} og {candidate}.")

    _extent(out, text)

    if extract_wanted:
        wanted = _extract_wanted(text)
        if wanted:
            # Prefer explicitly extracted question targets over a weak earlier guess.
            out.wanted = wanted
            _mark(out, "wanted", GREEN, "udledt fra spørgsmålsleddet")
        elif out.wanted:
            _mark(out, "wanted", YELLOW, "beholdt tidligere parserforslag")
        else:
            _mark(out, "wanted", RED, "ingen søgt størrelse fundet")

    source, source_level = _source_type(out.data, text)
    if source:
        out.data["_source_hint"] = source
        _mark(out, "source", source_level, f"kildetype {source}")

    _regions(out, text, source)
    _orientation(out, text)
    _domain(out, source, out.wanted, text)
    _preset_hint(out, source)

    # Critical uncertainty policy: never silently bless a direct symmetry method.
    if out.geometry == "cylinder" and out.data.get("extent") not in ("infinite", "finite"):
        _mark(out, "extent", YELLOW, "cylinderens endelig/uendelig-status mangler")
    if source in ("rho", "J") and out.geometry in ("cylinder", "cylinderskal") and out.data.get("extent") != "infinite":
        _mark(out, "symmetry", YELLOW, "direkte Gauss/Ampère kræver eksplicit uendelig cylindersymmetri")
    elif source == "rho" and out.geometry in ("kugle", "kugleskal"):
        _mark(out, "symmetry", GREEN, "sfærisk geometri + radial kilde")
    elif source in ("rho", "J") and out.geometry == "cylinder" and out.data.get("extent") == "infinite":
        _mark(out, "symmetry", GREEN, "uendelig cylinder + radial kilde")

    return out

def critical_uncertainties(parsed):
    """Return only fields that should require user attention before auto-solve."""
    confidence = getattr(parsed, "confidence", {}) or {}
    critical = ("domain", "geometry", "source", "wanted", "extent", "regions", "orientation", "symmetry", "preset")
    return {k: v for k, v in confidence.items() if k in critical and v.get("level") != GREEN}
