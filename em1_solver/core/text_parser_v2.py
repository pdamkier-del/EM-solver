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
    "ρ": "rho", "Ρ": "rho", "ϱ": "rho", "⇢": "rho",
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
    "ω": "omega", "Ω": "ohm", "Ω": "ohm",
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
    s = re.sub(r"(\d+(?:[.,]\d+)?)\s*[×⋅·]\s*10\s*\^?\s*([+-]?\d+)", r"\1e\2", s)
    s = s.replace("·", "*").replace("×", "*").replace("⋅", "*")
    # Decimal comma only when it is between digits.
    s = re.sub(r"(?<=\d),(?=\d)", ".", s)
    # Micro-prefix in a numeric unit context. Keep standalone Greek mu as mu.
    s = re.sub(r"(?<=\d)\s*[µμ](?=[A-Za-z])", " u", s)
    # A Greek coefficient directly followed by a coordinate means multiplication
    # in the exam notation, e.g. alpha*s^2 or omega*t. Digits remain subscripts:
    # rho0 and mu0 must not become products.
    for greek, ascii_name in _GREEK.items():
        s = re.sub(re.escape(greek) + r"(?=[rsxyztu])", ascii_name + "*", s)
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
        ("bevægelig stang", GREEN, r"\b(?:(?:bevaegelig|bevægelig|glidende|roterende)\s+(?:ledende\s+)?stang|(?:metalstang|ledende\s+stang|metal\s+stang).{0,55}(?:frit\s+)?(?:bevaegelig|bevægelig|glider|roterer))\b"),
        ("toroid", GREEN, r"\b(toroid|toroide)"),
        ("spole", GREEN, r"\b(solenoide|solenoid|spole)\b"),
        ("kugleskal", GREEN, r"\b(kugleskal|sf[aæ]risk\s+skal|spherical\s+shell)\b"),
        ("cylinderskal", GREEN, r"\b(cylinderskal|hul\s+cylinder|hollow\s+cylinder|cylindrisk\s+skal)\b"),
        ("kugle", GREEN, r"\b(kugle|sphere|sf[aæ]re)\b"),
        ("cylinder", GREEN, r"\b(cylinder|cylinderformet|cylindrisk)\b"),
        ("ring", GREEN, r"\b(ring|cirkul[aæ]r\s+(?:str[oø]m)?loop|circular\s+(?:current\s+)?loop)\b"),
        ("bue", GREEN, r"\b(bue|cirkelbue|halvcirkel|arc|semicircle)\b"),
        ("disk", GREEN, r"\b(disk|skive)\b"),
        ("plan", GREEN, r"\b(plan|plade|slab|sheet|str[oø]mplan)\b"),
        ("punktladninger", GREEN, r"\bpunktladning(?:er)?\b|\bpoint\s+charge"),
        ("linje", GREEN, r"\b(linjeladning|line\s+charge|ladet\s+linje)\b"),
        ("strømloop", YELLOW, r"\b(str[oø]ml[oø]kke|l[oø]kke|sl[oø]jfe|loop)\b"),
        ("ledning", YELLOW, r"\b(ledning|wire|tr[aå]d)\b"),
        ("leder", YELLOW, r"\b(leder|conductor|kondensator|capacitor)\b"),
    ]
    hits = [(g, level, m.start()) for g, level, p in patterns for m in [re.search(p, lower)] if m]
    if not hits:
        return None, None
    distinct = []
    for g, level, pos in sorted(hits, key=lambda x: x[2]):
        if g not in distinct:
            distinct.append(g)

    # More specific geometry wins over generic conductor/wire/loop nouns.
    specific = [g for g in distinct if g not in ("ledning", "leder", "strømloop")]
    filtered = []
    for g in distinct:
        if g == "cylinder" and "cylinderskal" in distinct:
            continue
        if g == "kugle" and "kugleskal" in distinct:
            continue
        if g == "leder" and "ledning" in distinct:
            continue
        if g in ("ledning", "leder") and (specific or "bevægelig stang" in distinct):
            continue
        if g == "strømloop" and any(x in distinct for x in ("ring", "bue", "bevægelig stang")):
            continue
        filtered.append(g)
    if len(filtered) != 1:
        return ("AMBIGUOUS:" + ",".join(filtered)), YELLOW
    g = filtered[0]
    level = next(level for gg, level, _ in hits if gg == g)
    return g, level

def _extract_wanted(text: str):
    lower = text.lower()
    verbs = r"(?:find|bestem|beregn|udled|vis|angiv|opskriv|eftervis|fastlæg|fastlaeg|argument[eé]r|determine|calculate|derive|state|show)"
    parts = re.split(r"\b" + verbs + r"\b", lower, maxsplit=1)
    q = parts[1] if len(parts) > 1 else lower
    wanted = []
    patterns = [
        ("E", r"elektrisk(?:e)?\s+felt|\be\s*\("),
        ("V", r"potential(?:e|et)?|sp[aæ]ndingsforskel"),
        ("rho", r"ladningst[aæ]thed|\brho\b"),
        ("D", r"forskydningsfelt|electric\s+displacement"),
        ("P", r"polaris(?:ation|ering)"),
        ("B", r"magnet(?:isk|iske)?\s+felt|magnetfelt|\bb\s*\("),
        ("Phi", r"magnetisk\s+flux|\bflux(?:en)?\b"),
        ("EMF", r"elektromotorisk|\bemf\b|induceret\s+sp[aæ]nding"),
        ("I", r"\bstr[oø]m(?:men|styrken)?\b|\bcurrent\b"),
        ("F", r"\bkraft(?:en)?\b|\bforce\b"),
        ("U", r"\b(?:elektrostatisk\s+|magnetisk\s+|potentiel\s+)?energi(?:en)?\b|\benergy\b"),
        ("PWR", r"\beffekt(?:en)?\b|\bpower\b"),
        ("L", r"\b(?:selv|gensidig\s+)?induktans(?:en)?\b|\binductance\b"),
        ("C", r"\bkapacitans(?:en)?\b|\bcapacitance\b"),
        ("torque", r"\b(?:drejnings)?moment(?:et)?\b|\btorque\b"),
    ]
    for key, pat in patterns:
        if re.search(pat, q):
            wanted.append(key)
    mapping = {"I": "current", "F": "force", "U": "energy", "PWR": "power", "L": "inductance"}
    return list(dict.fromkeys(mapping.get(w, w) for w in wanted))

def _source_type(data: dict, text: str):
    resistivity_rho = bool(re.search(r"resistivit(?:et|y).{0,40}\brho\b|\brho\b.{0,40}resistivit", text, re.I))
    for key in ("rho", "sigma", "lambda", "J", "A", "V", "E", "B", "P", "M", "I", "q"):
        if key == "rho" and resistivity_rho:
            continue
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

def _quantities(out, text: str):
    """Extract explicit scalar numerical assignments from prose, never inferred values."""
    from .units import si
    # Units deliberately limited to common EM1 scalar inputs. Compound densities
    # normally appear in explicit source functions and are handled elsewhere.
    unit_pat = (
        r"(?:mm|cm|km|m|ns|us|ms|s|Hz|kHz|MHz|GHz|"
        r"uC|nC|pC|mC|C|uA|mA|kA|A|uV|mV|kV|V|"
        r"uT|mT|T|uohm|mohm|kohm|Mohm|ohm|"
        r"pF|nF|uF|mF|F|uH|mH|H|mW|kW|W|mJ|kJ|J)"
    )
    pattern = re.compile(
        rf"(?<![A-Za-z0-9_])([A-Za-z_]\w*)\s*=\s*"
        rf"([-+]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*({unit_pat})(?![A-Za-z])"
    )
    for m in pattern.finditer(text):
        name, number, unit = m.groups()
        raw = f"{number} {unit}"
        try:
            quantity = si(raw)
        except Exception:
            continue
        out.quantities[name] = raw
        out.units[name] = str(quantity.units)
        out.data.setdefault(name, name)
        _mark(out, "quantities", GREEN, "eksplicitte tal med enheder udtrukket")

    # Counts such as N=2180 vindinger are dimensionless.
    for m in re.finditer(r"(?<![A-Za-z0-9_])([A-Za-z_]\w*)\s*=\s*(\d+)\s+(?:vindinger|turns)\b", text, re.I):
        name, number = m.groups()
        out.quantities[name] = number
        out.units[name] = "1"
        out.data.setdefault(name, name)
        _mark(out, "quantities", GREEN, "eksplicit dimensionløst antal udtrukket")


def _named_symbols(out, text: str):
    """Extract explicitly named symbolic geometric/circuit parameters."""
    specs = [
        ("radius", r"radius(?:en)?", "m"),
        ("length", r"l[aæ]ngde(?:n)?|length", "m"),
        ("area", r"areal(?:et)?|area", "m^2"),
        ("distance", r"afstand(?:en)?|distance", "m"),
        ("R", r"modstand(?:en)?|resistance", "ohm"),
        ("epsilon", r"permittivitet(?:en)?|permittivity", "F/m"),
    ]
    for key, phrase, unit in specs:
        m=re.search(rf"\b(?:{phrase})\s*(?:er|=|på|of)?\s*([A-Za-z_]\w*)\b", text, re.I)
        if not m:
            continue
        symbol=m.group(1)
        # Do not treat prose words as symbols.
        if symbol.lower() in {"er","har","med","og","i","af","the","is"}:
            continue
        out.data.setdefault(key,symbol)
        out.units.setdefault(symbol,unit)
    m=re.search(r"\bvinkelhastighed(?:en)?\s*(?:er|=)?\s*([A-Za-z_]\w*)\b", text, re.I)
    if m:
        out.data.setdefault("speed",m.group(1));out.units.setdefault(m.group(1),"1/s")
    m=re.search(r"\b(?:N|([A-Za-z_]\w*))\s+vindinger\b", text, re.I)
    if m and m.group(1):
        out.data.setdefault("N",m.group(1));out.units.setdefault(m.group(1),"1")


def _symbolic_sources(out, text: str):
    """Fill only source symbols that are explicitly named in prose."""
    lower=text.lower()
    if "lambda" not in out.data and re.search(r"\b(?:lambda|linjet[aæ]thed)\b", lower):
        out.data["lambda"]="lambda";out.units.setdefault("lambda","C/m")
    if "I" not in out.data and re.search(r"\b(?:f[oø]rer|med|b[aæ]rer)\s+(?:str[oø]m(?:men)?\s*)?I\b|\bstr[oø]m(?:men)?\s*(?:er|=)?\s*I\b", text, re.I):
        out.data["I"]="I";out.units.setdefault("I","A")
    if "B" not in out.data and re.search(r"\b(?:uniformt|homogent)?\s*(?:magnetfelt(?:et)?\s*)?B\b", text, re.I):
        out.data["B"]="B";out.units.setdefault("B","T")
    if "E" not in out.data and re.search(r"\b(?:uniformt|homogent)?\s*(?:elektrisk\s+felt(?:et)?\s*)?E\b", text, re.I):
        out.data["E"]="E";out.units.setdefault("E","V/m")

def _special_field_forms(out, text: str):
    """Normalize a few common vector prose forms into the scalar preset inputs."""
    # Parallel-plate displacement-current problems use an axial E(t).
    m=re.search(r"\bE\s*\(\s*t\s*\)\s*=\s*(.+?)\s+([xyz])hat\b", text, re.I)
    if m:
        coefficient=m.group(1).strip().rstrip(".,;")
        out.data["E"]=coefficient
        out.data["time"]="t";out.units.setdefault("t","s")
        out.data.setdefault("orientation",{})["field_axis"]="+"+m.group(2).lower()
        _mark(out,"time_dependence",GREEN,"E(t) står eksplicit")

    # Current-sheet notation K=K0 xhat maps to the sheet preset's scalar input.
    m=re.search(r"\bK\s*=\s*([A-Za-z_]\w*)\s+([xyz])hat\b", text, re.I)
    if m:
        magnitude,axis=m.groups()
        out.data["I"]=magnitude
        out.units.setdefault(magnitude,"A/m")
        out.data.setdefault("orientation",{})["current_axis"]="+"+axis.lower()
        _mark(out,"source",GREEN,"overfladestrøm K står eksplicit")


def _standard_curve(out, text: str, source: str | None):
    """Construct canonical line/ring/arc parameterizations only from explicit geometry."""
    g=out.geometry;d=out.data
    if g in ("linje","ledning"):
        m=re.search(r"\blangs\s+([xyz])\s+fra\s+([^\s,;]+)\s+til\s+([^\s,;.]+)", text, re.I)
        if m:
            axis,lo,hi=m.groups();u="u"
            source_vec={"x":[u,0,0],"y":[0,u,0],"z":[0,0,u]}[axis.lower()]
            d.update(source=source_vec,parameter=u,bounds=[lo,hi])
            out.units.setdefault(u,"m")
            _mark(out,"curve",GREEN,"ret linjekilde med eksplicit akse og grænser")
        point=re.search(r"\bpunkt(?:et)?\s*\(\s*([^,]+),\s*([^,]+),\s*([^\)]+)\)", text, re.I)
        if point:
            d["point"]=[x.strip() for x in point.groups()]
            _mark(out,"field_point",GREEN,"feltpunkt står eksplicit")
    elif g in ("ring","bue"):
        radius=d.get("radius","R")
        parameter="phi"
        d.setdefault("parameter",parameter)
        d.setdefault("source",[f"{radius}*cos({parameter})",f"{radius}*sin({parameter})",0])
        out.units.setdefault(parameter,"1");out.units.setdefault(str(radius),"m")
        if g=="ring":
            d.setdefault("bounds",[0,"2*pi"])
        else:
            upper="pi" if re.search(r"halvcirkel|semicircle",text,re.I) else "theta"
            d.setdefault("bounds",[0,upper])
            if upper=="theta":out.units.setdefault("theta","1")
        if re.search(r"\bcentrum\b|\bcenter\b",text,re.I):
            d.setdefault("point",[0,0,0])
        elif re.search(r"\bz-aksen\b|\bz-axis\b",text,re.I):
            d.setdefault("point",[0,0,"z"]);out.units.setdefault("z","m")
        _mark(out,"curve",GREEN,"standard cirkulær kurve udledt fra eksplicit ring/bue")
        if not d.get("orientation",{}).get("plane"):
            _mark(out,"orientation",YELLOW,"ring/bue-plan eller positiv omløbsretning er ikke eksplicit")


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
    solid_radial = (
        (out.geometry == "kugle" and radius)
        or (out.geometry == "cylinder" and radius and out.data.get("extent") == "infinite")
    )
    if solid_radial:
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
    if re.search(r"faraday|induceret|forskydningsstr[oø]m|amp[eè]re-maxwell|rl-kredsl|rc-kredsl|selvindukt|mutual\s+induct|gensidig\s+indukt", lower) or any(w in wanted for w in ("EMF","Phi","inductance")):
        d = "DYN"
    elif re.search(r"lorentz|magnetisk\s+dipol|magnetisk\s+moment",lower):
        d = "BA"
    elif source == "B" and ("time" in out.data or re.search(r"tidsafh[aæ]ng|roter|bev[aæ]g|glid", lower)):
        d = "DYN"
    elif source in ("rho", "sigma", "lambda", "V", "E", "q", "P") or any(w in wanted for w in ("E", "V", "rho", "D", "P", "C")):
        d = "EV"
    elif source in ("J", "A", "M", "I") or re.search(r"biot|amp[eè]re|magnetostat", lower):
        d = "BA"
    elif any(w in wanted for w in ("B", "force", "torque")):
        d = "BA"
    else:
        return
    out.data["_domain_hint"] = d
    _mark(out, "domain", GREEN if source else YELLOW, f"domæne udledt fra kilde/søges: {d}")

def _preset_hint(out, source: str | None):
    g = out.geometry
    d = out.data
    lower=getattr(out,"normalized_text","").lower()
    hint = None
    if re.search(r"serie[- ]?rl|rl[- ]kredsl",lower):
        hint="dyn_rl"
        d.setdefault("time","t");out.units.setdefault("t","s")
    elif re.search(r"rc[- ]kredsl|aflades\s+gennem",lower):
        hint="dyn_rc"
        d.setdefault("time","t");out.units.setdefault("t","s")
    elif re.search(r"parallelplade",lower) and ("time" in d or re.search(r"e\s*\(\s*t\s*\)",lower)) and "B" in out.wanted:
        hint="dyn_capacitor"
        d.setdefault("time","t");out.units.setdefault("t","s")
    elif g=="spole" and "inductance" in out.wanted:
        hint="dyn_solenoid"
    elif re.search(r"magnetisk\s+dipol",lower):
        hint="ba_dipole"
    elif re.search(r"str[oø]mplan|overfladestr[oø]m",lower):
        hint="ba_sheet"
    elif re.search(r"parallelplade",lower) and not re.search(r"side\s+om\s+side|to\s+dielektriske|dielektriske\s+lag",lower):
        hint="ev_capacitor"
    elif source == "rho":
        hint = {
            "kugle": "ev_sphere", "kugleskal": "ev_shell",
            "cylinder": "ev_cylinder", "cylinderskal": "ev_hollow",
            "plan": "ev_slab",
        }.get(g)
    elif source == "sigma" and g == "plan":
        hint = "ev_plane"
    elif source == "lambda":
        hint = ("ev_infinite_line" if g=="linje" and d.get("extent")=="infinite" else {"linje":"ev_line","ring":"ev_ring","bue":"ev_arc"}.get(g))
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
        hint = (("ba_line" if d.get("extent")=="finite" else "ba_wire") if g=="ledning" else {"ring":"ba_ring","bue":"ba_arc","spole":"ba_solenoid","toroid":"ba_toroid"}.get(g))
    elif source == "B" and g == "bevægelig stang":
        hint = "dyn_rotating" if re.search(r"roter|vinkelhast|omega", getattr(out, "normalized_text", ""), re.I) else "dyn_sliding"
    elif source == "B" and "time" in d:
        hint = "dyn_moving" if re.search(r"bevaeg|bevæg|glid|areal.{0,20}t|area.{0,20}t", getattr(out, "normalized_text", ""), re.I) else "dyn_fixed"
    elif source == "E" and "time" in d and g in ("disk", "leder"):
        hint = "dyn_capacitor"
    if hint:
        out.data["_preset_hint"] = hint
        no_geometry={"ev_potential","ev_field","ba_vector_potential","ba_lorentz","ba_dipole","dyn_rl","dyn_rc"}
        no_source={"dyn_rl","dyn_rc","dyn_solenoid","ba_dipole","ev_capacitor"}
        if hint in no_geometry:
            _mark(out,"geometry",GREEN,"geometri er ikke nødvendig for den valgte model")
        if hint in no_source and not source:
            _mark(out,"source",GREEN,"ingen separat kildetype kræves for den valgte model")
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
    _quantities(out, text)
    _named_symbols(out, text)
    _symbolic_sources(out, text)
    _special_field_forms(out, text)

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

    _standard_curve(out, text, source)
    _regions(out, text, source)
    _orientation(out, text)
    _domain(out, source, out.wanted, text)
    _preset_hint(out, source)

    # Missing critical fields are explicit uncertainty, not an implicit pass.
    if out.geometry == "Ukendt" and getattr(out,"confidence",{}).get("geometry",{}).get("level")!="GREEN":
        _mark(out, "geometry", RED, "ingen sikker geometri fundet")
    if not source and getattr(out,"confidence",{}).get("source",{}).get("level")!="GREEN":
        _mark(out, "source", RED, "ingen sikker kildetype fundet")
    if not out.wanted:
        _mark(out, "wanted", RED, "ingen søgt størrelse fundet")
    if "_domain_hint" not in out.data:
        _mark(out, "domain", YELLOW, "domænet kræver fysisk kontrol")
    if "_preset_hint" not in out.data:
        _mark(out, "preset", YELLOW, "ingen entydig standardmodel valgt")

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
