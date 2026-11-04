"""Safe autonomous text -> structured solver benchmark on the 55-case bank.

Only zero-critical-uncertainty parses are allowed to enter the solver. All other
cases are NEEDS_CONFIRMATION, not failures and never guessed.
"""
from __future__ import annotations
import json,sys,time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"tools"))

from em1_solver.core.new_problem import parse
from em1_solver.core.assisted import auto_compile
from em1_solver.core.task_runtime import run_confirmed
from em1_solver.core.text_parser_v2 import critical_uncertainties
from blind_oracles import verify

BANK=json.loads((ROOT/"data/blind_unseen_bank_v2.json").read_text(encoding="utf-8"))["tests"]

def main():
    records=[]
    for row in BANK:
        start=time.monotonic()
        parsed=parse(row["problem"])
        uncertain=critical_uncertainties(parsed)
        record={"id":row["id"],"domain":row["domain"],"uncertain":sorted(uncertain),
                "status":None,"silent_wrong":False,"method":None}
        if uncertain:
            record["status"]="NEEDS_CONFIRMATION"
            records.append(record);continue
        try:
            structured=auto_compile(parsed)
            answer=run_confirmed(structured,False,timeout=20)
            record["method"]=answer.method
            try:
                verify(row["id"],structured,answer)
                record["status"]="PASS"
            except Exception as exc:
                record["status"]="WRONG"
                record["silent_wrong"]=not answer.warnings and not any(c.passed is False for c in answer.checks)
                record["error"]=type(exc).__name__+": "+str(exc)
        except Exception as exc:
            message=str(exc)
            if row["id"]=="GEN02" and ("Fysisk afvisning" in message or "curl" in message):
                record["status"]="PASS"
                record["correct_refusal"]=True
            else:
                record["status"]="STRUCTURE_FAIL"
                record["error"]=type(exc).__name__+": "+message
        record["elapsed_seconds"]=round(time.monotonic()-start,3)
        records.append(record)

    counts=Counter(r["status"] for r in records)
    autonomous=[r for r in records if r["status"]!="NEEDS_CONFIRMATION"]
    summary={
        "total":len(records),
        "zero_uncertainty":len(autonomous),
        "correct_autonomous":counts["PASS"],
        "wrong_autonomous":counts["WRONG"],
        "structure_fail":counts["STRUCTURE_FAIL"],
        "needs_confirmation":counts["NEEDS_CONFIRMATION"],
        "silent_wrong":sum(bool(r.get("silent_wrong")) for r in records),
        "safe_autonomous_percent":round(100*counts["PASS"]/len(records),1),
        "accuracy_when_attempted":round(100*counts["PASS"]/len(autonomous),1) if autonomous else 0,
    }
    payload={"summary":summary,"records":records}
    (ROOT/"reports/parser_autonomy.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(payload,ensure_ascii=False,indent=2))
    if summary["wrong_autonomous"] or summary["silent_wrong"]:
        raise SystemExit("Unsafe autonomous result detected")
    print("SAFE_AUTONOMY",json.dumps(summary,ensure_ascii=False))

if __name__=="__main__":
    main()
