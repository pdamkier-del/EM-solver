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
    assert "rho(s)=alpha*s**2" in text.replace(" ","")
    assert "2.5 uC" in text


def test_explicit_numeric_quantities_from_exam_prose():
    p=parse("En solenoide har N = 2180 vindinger, radius r = 3,00 m og strøm I = 18,2 kA. Bestem B.")
    assert p.quantities["N"]=="2180"
    assert p.quantities["r"]=="3.00 m"
    assert p.quantities["I"]=="18.2 kA"
    assert p.wanted==["B"]


def test_micro_ohm_and_scientific_notation_normalization():
    text=normalize_text("R = 75 µΩ og rho = 2,8 × 10−8 Ω*m")
    assert "75 uohm" in text
    assert "2.8e-8 ohm*m" in text.replace(" ","")


def test_historical_wording_infinite_cylinderformet_is_understood():
    p=parse("En uendelig lang cylinderformet leder med radius R bærer en konstant strømtæthed J(s)=J0. Bestem magnetfeltets størrelse og retning.")
    assert p.geometry=="cylinder"
    assert p.data["extent"]=="infinite"
    assert p.data["_source_hint"]=="J"
    assert p.data["_preset_hint"]=="ba_cylinder"
    assert p.wanted==["B"]


def test_historical_moving_rod_word_order_is_understood():
    p=parse("En metalstang er frit bevægelig langs skinnerne i et homogent magnetfelt B. Bestem den inducerede strøm.")
    assert p.geometry=="bevægelig stang"
    assert p.confidence["geometry"]["level"]=="GREEN"


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


def test_finite_line_charge_builds_canonical_curve_fields():
    p=parse("En endelig linjeladning ligger langs x fra -L til +L med konstant lambda. Find V og E i punktet (0,a,0).")
    assert p.geometry=="linje"
    assert p.data["extent"]=="finite"
    assert p.data["_preset_hint"]=="ev_line"
    assert p.data["source"]==["u",0,0]
    assert p.data["bounds"]==["-L","+L"]
    assert p.data["point"]==["0","a","0"]


def test_finite_current_wire_uses_biot_savart_preset():
    p=parse("En ret endelig leder langs z fra -L til +L fører I. Find B i punktet (a,0,0).")
    assert p.geometry=="ledning"
    assert p.data["extent"]=="finite"
    assert p.data["_preset_hint"]=="ba_line"
    assert p.data["source"]==[0,0,"u"]


def test_circular_current_loop_maps_to_ring_geometry():
    p=parse("En cirkulær strømloop med radius R fører I. Find B i centrum.")
    assert p.geometry=="ring"
    assert p.data["_preset_hint"]=="ba_ring"
    assert p.data["bounds"]==[0,"2*pi"]


def test_rl_and_rc_get_direct_circuit_presets_without_fake_geometry():
    rl=parse("Et serie-RL-kredsløb med spænding V kobles til ved t=0 med I(0)=0. Find I(t), tidskonstant og slutenergi i spolen.")
    rc=parse("En kondensator C med initial ladning Q0 aflades gennem R fra t=0. Find Q(t), I(t) og lagret energi.")
    assert rl.data["_preset_hint"]=="dyn_rl"
    assert rc.data["_preset_hint"]=="dyn_rc"
    assert rl.confidence["geometry"]["level"]=="GREEN"
    assert rc.confidence["source"]["level"]=="GREEN"


def test_parallel_plate_time_dependent_E_selects_ampere_maxwell():
    p=parse("En parallelpladekondensator har cirkulære plader radius R og uniform E(t)=E0*t^2 zhat mellem pladerne. Find B(s,t).")
    assert p.data["_preset_hint"]=="dyn_capacitor"
    assert p.data["E"]=="E0*t**2"
    assert p.data["time"]=="t"


def test_current_sheet_vector_is_reduced_to_scalar_sheet_input():
    p=parse("Et uendeligt strømplan z=0 fører overfladestrøm K=K0 xhat. Find B over og under planet.")
    assert p.data["_preset_hint"]=="ba_sheet"
    assert p.data["I"]=="K0"
    assert p.data["orientation"]["current_axis"]=="+x"


def test_spherical_potential_does_not_use_cartesian_preset_silently():
    p=parse("I et sfærisk område er potentialet V(r)=-a*log(r/R). Bestem E(r).")
    assert p.data.get("_preset_hint")!="ev_potential"
    assert p.confidence.get("coordinate_system",{}).get("level")=="YELLOW"


def test_cylindrical_vector_potential_does_not_use_cartesian_preset_silently():
    p=parse("I cylindriske koordinater er A(s)=A0*s**2 phihat. Bestem B.")
    assert p.data.get("_preset_hint")!="ba_vector_potential"
