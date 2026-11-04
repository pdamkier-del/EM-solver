import pytest

from em1_solver.core.new_problem import parse
from em1_solver.core.text_parser_v2 import normalize_text,critical_uncertainties


def test_unicode_math_and_danish_cylinder_are_normalized_and_structured():
    p=parse(
        "En uendelig massiv cylinder med radius R har ρ(s)=ρ0(1-s/R). "
        "Bestem det elektriske felt E(s)."
    )
    assert p.geometry=="cylinder"
    assert p.data["extent"]=="infinite"
    assert p.data["_source_hint"]=="rho"
    assert p.data["_preset_hint"]=="ev_cylinder"
    assert p.wanted==["E"]
    assert "rho(s)" in p.normalized_text
    assert p.confidence["geometry"]["level"]=="GREEN"
    assert p.confidence["extent"]["level"]=="GREEN"


def test_superscript_and_decimal_comma_normalization():
    text=normalize_text("ρ(s)=αs², q=2,5 µC")
    assert "rho(s)=alphas**2" in text.replace(" ","")
    assert "2.5 uC" in text


def test_hollow_cylinder_interval_becomes_source_region():
    p=parse(
        "En uendelig hul cylinder har ladningstætheden rho(s)=k*s for a<s<b. "
        "Bestem E."
    )
    assert p.geometry=="cylinderskal"
    assert p.data["extent"]=="infinite"
    assert p.data["regions"][0]["lower"]=="a"
    assert p.data["regions"][0]["upper"]=="b"
    assert p.data["_preset_hint"]=="ev_hollow"


def test_potential_selects_field_calculus_preset():
    p=parse("Potentialet er V = V0*x*y/L**2. Bestem det elektriske felt E.")
    assert p.data["_source_hint"]=="V"
    assert p.data["_preset_hint"]=="ev_potential"
    assert "E" in p.wanted


def test_finite_cylinder_is_not_silently_approved_for_symmetry():
    p=parse(
        "En endelig cylinder med radius R har rho(s)=rho0. "
        "Bestem det elektriske felt."
    )
    assert p.data["extent"]=="finite"
    assert p.confidence["extent"]["level"]=="GREEN"
    assert p.confidence["symmetry"]["level"]=="YELLOW"
    assert "symmetry" in critical_uncertainties(p)


def test_orientation_out_of_page_is_extracted():
    p=parse(
        "En strømloop ligger i xy-plan og magnetfeltet peger ud af papiret. "
        "B(t)=B0*cos(omega*t). Beregn flux og emf."
    )
    assert p.data["orientation"]["plane"]=="xy"
    assert p.data["orientation"]["normal"]=="+z"
    assert set(p.wanted)>={"Phi","EMF"}


@pytest.mark.parametrize(
    "text,expected",
    [
        ("En kugle med radius R og rho(r)=rho0. Bestem E.", "kugle"),
        ("En sfærisk skal med radius R og rho(r)=rho0. Bestem E.", "kugleskal"),
        ("En toroid med N vindinger fører strømmen I. Bestem magnetfeltet.", "toroid"),
        ("En glidende ledende stang bevæger sig i et magnetfelt. Bestem emf.", "bevægelig stang"),
    ],
)
def test_high_value_geometry_phrases(text,expected):
    assert parse(text).geometry==expected
