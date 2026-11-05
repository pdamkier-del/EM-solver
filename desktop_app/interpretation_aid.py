"""Only recover explicitly stated coordinates from plain Danish task texts.

No inferred physics, no guessed geometry, and no use of historical solutions.
All auto corrections must carry literal-text evidence for disclosure.
"""
from __future__ import annotations
import re


def explicit_radial_coordinate(text:str) -> dict:
    if not isinstance(text,str):return {}
    # We require a sentence declaring which variable is the radial distance.
    # Do not infer from E(s) alone: E(s) might denote another variable.
    patterns=(
        r'\b(?:hvor|idet)\s+([rs])\s+er\s+(?:den\s+)?radial(?:e)?\s+(?:afstand|koordinat)',
        r'\b(?:den\s+)?radial(?:e)?\s+(?:afstand|koordinat)\s+er\s+([rs])\b',
        r'\b([rs])\s+er\s+afstanden\s+fra\s+(?:cylinderens|kuglens|lederens)\s+(?:akse|centrum)',
        r'\b(?:med\s+)?radial(?:e)?\s+koordinat\s+([rs])\b',
    )
    options=[]
    for pat in patterns:
        for m in re.finditer(pat,text,flags=re.I):
            options.append((m.group(1).lower(),m.group(0)))
    names={v for v,_ in options}
    if len(names)!=1:return {}
    symbol=next(iter(names))
    return {'coordinate':symbol,'evidence':[ev for v,ev in options if v==symbol]}


def text_corrections(raw_text:str,existing:dict|None=None) -> tuple[dict,dict]:
    existing=existing or {}
    evidence=explicit_radial_coordinate(raw_text)
    if not evidence or 'coordinate' in existing:return {},{}
    # A radial coordinate is relevant to radial electric/current source models, but
    # the backend still decides whether it can physically solve the problem.
    return {'coordinate':evidence['coordinate']},{'coordinate':evidence['evidence']}
