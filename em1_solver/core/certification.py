"""Certificates are evidence tied to source, recipes, variation tests and a full test run."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/'data/solver_certificates.json'

def fingerprint():
    digest=hashlib.sha256()
    files=sorted((ROOT/'em1_solver').rglob('*.py'))+sorted((ROOT/'tests').rglob('*.py'))+sorted((ROOT/'data/historical_problems').glob('*.json'))
    files += [ROOT/'data/certification_policy.json', ROOT/'data/exam_problem_registry.json', ROOT/'tools/certify_solvers.py']
    for path in files:
        digest.update(str(path.relative_to(ROOT)).encode());digest.update(path.read_bytes())
    return digest.hexdigest()

def certified(family):
    if not PATH.exists():return False
    evidence=json.loads(PATH.read_text())
    return evidence.get('fingerprint')==fingerprint() and family in evidence.get('stable_families',[])


def blockers(family):
    if not PATH.exists():return ['Intet certifikat; kør tools/certify_all.py.']
    evidence=json.loads(PATH.read_text())
    if evidence.get('fingerprint')!=fingerprint():return ['Certifikatet er forældet efter en kilde-, test- eller opskriftsændring.']
    return evidence.get('evidence',{}).get(family,{}).get('blockers',['Ingen familieevidens.'])
