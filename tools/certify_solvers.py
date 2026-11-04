"""Generate risk-based certificates from a complete current green test run."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from em1_solver.core.certification import fingerprint
from em1_solver.core.historical import paths,load

def certify():
    run=json.loads((ROOT/'reports/test-results.json').read_text())
    if run.get('fingerprint')!=fingerprint():raise RuntimeError('Kildekode, tests, policy eller opskrifter er ændret siden testkørslen.')
    if not run.get('full_suite') or run['exitstatus']!=0 or len(run['results'])!=run['collected'] or any(t['outcome']!='passed' for t in run['results']):
        raise RuntimeError('Certificering kræver en frisk, fuld grøn testkørsel uden skips.')
    rows=json.loads((ROOT/'data/exam_problem_registry.json').read_text())
    policy=json.loads((ROOT/'data/certification_policy.json').read_text())
    recipes={r['id']:r for r in map(load,paths())}
    executable={t['recipe']['id'] for t in run['results'] if t.get('recipe') and t['recipe']['status']=='executable'}
    dimensions=[t['test'] for t in run['results'] if t.get('dimensions')]
    evidence={};stable=[]
    for family,criteria in policy.items():
        native={id for id,r in recipes.items() if any(s['problem']['family']==family for s in r.get('path',[]))}
        relevant={r['id'] for r in rows if r['family']==family or family in r.get('secondary_families',[])}|native
        manual={id for id in relevant if recipes.get(id,{}).get('status')=='qualitative/manual'}
        variants=[t['test'] for t in run['results'] if t.get('variation') and t['variation'].get('family')==family]
        missing=sorted(relevant-executable-manual);reasons=[]
        if missing:reasons.append('Mangler beståede historiske opskrifter: '+', '.join(missing))
        if not native&executable:reasons.append('Ingen historisk opskrift kalder denne familie direkte.')
        if len(variants)<criteria['minimum_variations']:reasons.append(f"Variationer: {len(variants)}/{criteria['minimum_variations']} ({criteria['risk']}).")
        if len(dimensions)<10:reasons.append('Dimensions-testsuite utilstrækkelig.')
        ok=not reasons
        evidence[family]=dict(criteria,historical_ids=sorted(relevant),native_historical_ids=sorted(native),manual_excluded=sorted(manual),missing_recipes=missing,variation_tests=variants,dimension_tests=dimensions,stable=ok,blockers=reasons)
        if ok:stable.append(family)
    result={'schema_version':2,'fingerprint':fingerprint(),'stable_families':stable,'evidence':evidence,'scope':'Kun dokumenterede implementerede inputmodeller; runtime kræver beståede dimensions- og fysikchecks. Manual-opgaver undtages eksplicit fra kvantitativ certificering.'}
    (ROOT/'data/solver_certificates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Stable:',', '.join(stable))
if __name__=='__main__':certify()
