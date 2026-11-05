"""Seven-stage baseline diagnosis, explicitly separate from human PDF review."""
import json,re
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def main():
 data=json.loads((ROOT/'reports/autonomy/evaluation.json').read_text());source=json.loads((ROOT/'data/exam_problem_registry.json').read_text());by_id={f"{r['exam']}:{r['problem']}{r['subproblem']}":r for r in source};out=[]
 for item in data['historical']:
  result=item['result'];q=result.get('questions',{});row=by_id[item['id']];text=row['source_context']+'\n'+row['source_question'];damaged=bool(re.search(r'[⇢⇥⇤⎧⎨]|\)\s*\d|[#]0',text))
  if result['status']=='verified':category='verified'
  elif damaged:category='1_pdf_damage_suspected'
  elif 'figure' in q or re.search(r'fra (?:delopgave|spørgsmål)|givet i a\)|som i a\)|samme .* som',text,re.I):category='2_missing_figure_or_context'
  elif any(k in q for k in ('source_formula','source_conflict','geometry','units','regions','coordinate','radius')):category='3_problem_representation'
  elif any(k in q for k in ('method','boundary_model','validation')):category='4_method_selection'
  elif result['status']=='error':category='5_mathematical_operations'
  elif result['status']=='wrong_or_unverified':category='7_verification_or_unverified_result'
  else:category='3_problem_representation'
  out.append(dict(id=item['id'],first_diagnostic_category=category,first_true_error='not established without full independent source/figure/model review',text_extraction='suspected_damage' if damaged else 'unverified',figure_information='detected_missing' if 'figure' in q else 'unverified',problem_fields=result.get('fields',{}),method=result.get('method'),equation_setup='compiled' if result.get('ready') else 'not_reached',symbolic_verification=result.get('verification'),uncertainties=q))
 counts=Counter(r['first_diagnostic_category'] for r in out)
 for k in ['verified','1_pdf_damage_suspected','2_missing_figure_or_context','3_problem_representation','4_method_selection','5_mathematical_operations','6_symbolic_derivation','7_verification_or_unverified_result']:counts.setdefault(k,0)
 payload=dict(baseline='64520a0',total=len(out),counts=counts,limitation='All 154 diagnosed. PDF damage is heuristic, not verified against every original PDF/figure. Zero confirmed symbolic errors is not proof the unattempted solvers are correct.',records=out)
 (ROOT/'reports/desktop/failure_audit.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(counts,ensure_ascii=False))
if __name__=='__main__':main()
