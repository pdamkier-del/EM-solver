"""Ten-stage audit of every raw historical record; unknowns are never passed."""
import json,re
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def main():
    source=json.loads((ROOT/'reports/parser/evaluation.json').read_text());rows=json.loads((ROOT/'data/exam_problem_registry.json').read_text())
    results={r['id']:r['autonomous'] for r in source['historical_records']};records=[]
    stages=['text_extraction','figure_information','geometry','variables_units','boundary_conditions','method','equation_setup','symbolic_operations','final_result']
    for row in rows:
        id=f"{row['exam']}:{row['problem']}{row['subproblem']}";r=results[id];text=row['source_context']+'\n'+row['source_question'];fields=r.get('interpretation',{}).get('fields',{});questions=r.get('questions',{})
        suspicious=bool(re.search(r'[⇢⇥⇤⎧⎨]|\)\s*\d|[#]0',text))
        audit={k:dict(status='unverified',evidence='Not independently reviewed against PDF/figure or not reached.') for k in stages}
        audit['text_extraction']=dict(status='suspected_damage' if suspicious else 'unverified',evidence='Glyph/layout heuristic only; no OCR reconstruction or claim of complete text fidelity.')
        audit['figure_information']=dict(status='required_missing' if 'figure' in questions else 'unverified',evidence=questions.get('figure','Figure mention alone cannot establish sufficiency.'))
        for key,stage in [('geometry','geometry'),('units','variables_units'),('boundary_model','boundary_conditions'),('method','method')]:
            audit[stage]=dict(status='blocked' if key in questions else 'field_recognized_unverified' if fields.get(key,{}).get('status')=='GREEN' else 'unverified',evidence=questions.get(key,fields.get(key,{}).get('evidence',[])))
        if r.get('ready'):audit['equation_setup']=dict(status='compiled',evidence='Typed model compiled without gold; does not establish text correctness.')
        if r['status']=='verified':
            audit['symbolic_operations']=dict(status='verified',evidence=r.get('verification',{}));audit['final_result']=dict(status='verified',evidence=r.get('verification',{}))
        if r['status']=='error':audit['symbolic_operations']=dict(status='failed',evidence=r.get('reason'))
        first='text_damage_suspected' if suspicious else 'figure_information' if 'figure' in questions else 'context_or_source_extraction' if 'source_formula' in questions else 'geometry' if 'geometry' in questions else 'boundary_model' if 'boundary_model' in questions else 'dimensional_constraints' if 'units' in questions else 'method_or_composition' if any(k in questions for k in ('method','validation')) else 'other_missing_information' if questions else 'none'
        records.append(dict(id=id,stages=audit,first_detected_blocker=first,independent_first_true_error='unverified unless a final oracle check identifies it',questions=questions))
    counts=Counter(r['first_detected_blocker'] for r in records)
    (ROOT/'reports/autonomy/failure_audit.json').write_text(json.dumps(dict(baseline='f1bd7eb',total=len(records),limitations='Machine diagnostic, not a completed human PDF/figure audit. First detected blocker is not asserted to be first true physical error.',root_cause_counts=counts,records=records),ensure_ascii=False,indent=2)+'\n')
    (ROOT/'reports/autonomy/failure_audit.md').write_text('# Råtekst-fejlanalyse\n\nAlle 154 delopgaver har ni fasestatusser og en særskilt registrering af første diagnosticerede blokering. Ukontrolleret PDF-/figurtroskab er markeret unverified, aldrig passed. Den første egentlige fejl kan ikke fastslås automatisk for alle tekster.\n\n'+ '\n'.join(f'- {k}: {v}' for k,v in counts.most_common())+'\n\nPrioritering: typed kilder/randdata og generelle afhængighedskæder; derefter kontekst fra delspørgsmål og materialer. PDF-tab må ikke repareres fra facit.\n')
if __name__=='__main__':main()
