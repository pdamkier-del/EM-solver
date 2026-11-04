"""Evaluate deterministic text parsing against the historical problem registry.

This is a parser benchmark, not a solver certification. The registry was already
used elsewhere in development, so the recent-exam split is an evaluation split,
not a pristine hold-out.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from em1_solver.core.new_problem import parse
from em1_solver.core.text_parser_v2 import critical_uncertainties
ROWS=json.loads((ROOT/"data/exam_problem_registry.json").read_text(encoding="utf-8"))
BLIND=json.loads((ROOT/"data/blind_unseen_bank_v2.json").read_text(encoding="utf-8"))["tests"]

RECENT_EVAL={"2025-11","2026-01"}

GEOMETRY_MAP={
    "solid_cylinder":"cylinder",
    "sliding_rod":"bevægelig stang",
    "driven_sliding_rod":"bevægelig stang",
    "circular_loop":"ring",
    "circular_coil":"ring",
    "falling_ring":"ring",
    "arc":"bue",
    "solenoid":"spole",
    "toroid_with_gap":"toroid",
    "magnetized_cylinder":"cylinder",
    "sphere":"kugle",
    "dielectric_sphere":"kugle",
    "annular_disk":"disk",
    "current_ribbon":"plan",
}

# Only cases whose current simple UI preset is genuinely equivalent.
PRESET_MAP={
    ("gauss_radial","solid_cylinder"):"ev_cylinder",
    ("gauss_radial","sphere"):"ev_sphere",
    ("gauss_radial","dielectric_sphere"):"ev_sphere",
    ("ampere","solid_cylinder"):"ba_cylinder",
    ("ampere","solenoid"):"ba_solenoid",
    ("motional_emf","sliding_rod"):"dyn_sliding",
    ("motional_emf","driven_sliding_rod"):"dyn_sliding",
    ("magnetic_material","magnetized_cylinder"):"ba_material",
}

def combined(row):
    return (row.get("source_context","").strip()+"\n"+row.get("source_question","").strip()).strip()

def metrics(rows):
    domain_total=domain_hit=domain_emitted=0
    geom_total=geom_hit=0
    preset_total=preset_hit=0
    uncertainty_bins=Counter()
    family=defaultdict(lambda:Counter(total=0,domain=0,ready=0))
    samples=[]
    errors=[]
    for row in rows:
        try:
            p=parse(combined(row))
        except Exception as exc:
            errors.append({"id":row["id"],"error":type(exc).__name__+": "+str(exc)})
            continue
        family[row["family"]]["total"]+=1
        domain_total+=1
        domain=p.data.get("_domain_hint")
        if domain:
            domain_emitted+=1
            if domain==row["domain"]:
                domain_hit+=1
                family[row["family"]]["domain"]+=1

        expected_geom=GEOMETRY_MAP.get(row["geometry"])
        if expected_geom:
            geom_total+=1
            if p.geometry==expected_geom:
                geom_hit+=1

        expected_preset=PRESET_MAP.get((row["family"],row["geometry"]))
        if expected_preset:
            preset_total+=1
            if p.data.get("_preset_hint")==expected_preset:
                preset_hit+=1

        u=critical_uncertainties(p)
        n=len(u)
        if n==0:
            uncertainty_bins["0"]+=1
            family[row["family"]]["ready"]+=1
        elif n==1:
            uncertainty_bins["1"]+=1
        elif n<=3:
            uncertainty_bins["2-3"]+=1
        else:
            uncertainty_bins["4+"]+=1
        if len(samples)<25 and (domain and domain!=row["domain"] or expected_geom and p.geometry!=expected_geom):
            samples.append({
                "id":row["id"],
                "truth_domain":row["domain"],
                "parsed_domain":domain,
                "truth_geometry":expected_geom,
                "parsed_geometry":p.geometry,
                "source":p.data.get("_source_hint"),
                "preset":p.data.get("_preset_hint"),
                "uncertain":sorted(u),
            })
    return {
        "n":len(rows),
        "domain":{"coverage":domain_emitted/domain_total if domain_total else 0,
                  "accuracy_when_emitted":domain_hit/domain_emitted if domain_emitted else 0,
                  "correct_overall":domain_hit/domain_total if domain_total else 0},
        "coarse_geometry":{"n":geom_total,"accuracy":geom_hit/geom_total if geom_total else 0},
        "direct_preset":{"n":preset_total,"accuracy":preset_hit/preset_total if preset_total else 0},
        "corrections":dict(uncertainty_bins),
        "families":{k:dict(v) for k,v in sorted(family.items())},
        "sample_misses":samples,
        "parse_errors":errors,
    }

def blind_metrics(rows):
    domain_hit=domain_emitted=0
    bins=Counter()
    by_domain=defaultdict(lambda:Counter(total=0,correct=0,ready=0))
    misses=[]
    errors=[]
    for row in rows:
        try:
            p=parse(row["problem"])
        except Exception as exc:
            errors.append({"id":row["id"],"error":type(exc).__name__+": "+str(exc)})
            continue
        truth=row["domain"]
        by_domain[truth]["total"]+=1
        got=p.data.get("_domain_hint")
        if got:
            domain_emitted+=1
            if got==truth:
                domain_hit+=1
                by_domain[truth]["correct"]+=1
        u=critical_uncertainties(p)
        n=len(u)
        if n==0:
            bins["0"]+=1
            by_domain[truth]["ready"]+=1
        elif n==1:bins["1"]+=1
        elif n<=3:bins["2-3"]+=1
        else:bins["4+"]+=1
        if len(misses)<20 and got!=truth:
            misses.append({"id":row["id"],"truth":truth,"parsed":got,
                           "geometry":p.geometry,"source":p.data.get("_source_hint"),
                           "preset":p.data.get("_preset_hint"),"uncertain":sorted(u)})
    return {
        "n":len(rows),
        "domain":{"coverage":domain_emitted/len(rows) if rows else 0,
                  "accuracy_when_emitted":domain_hit/domain_emitted if domain_emitted else 0,
                  "correct_overall":domain_hit/len(rows) if rows else 0},
        "corrections":dict(bins),
        "by_domain":{k:dict(v) for k,v in sorted(by_domain.items())},
        "sample_domain_misses":misses,
        "parse_errors":errors,
    }


def main():
    all_result=metrics(ROWS)
    eval_rows=[r for r in ROWS if r["exam"] in RECENT_EVAL]
    eval_result=metrics(eval_rows)
    report={"all_historical":all_result,"recent_evaluation_split":eval_result,
            "blind_55_text":blind_metrics(BLIND),
            "note":"Recent split is not pristine hold-out; historical material predated this benchmark."}
    out=ROOT/"reports/parser_text_benchmark.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
