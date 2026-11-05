"""Desktop-only offline runner: send explicit corrections to the pinned backend. No physics inference."""
import argparse
import json
from pathlib import Path
import sys
from backend_paths import location
sys.path.insert(0,str(location()[0]))
from em1_solver.backend_client import run_text
from interpretation_aid import text_corrections


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--corrections',default='{}')
    a=p.parse_args()
    corrections=json.loads(a.corrections)
    if not isinstance(corrections,dict) or len(corrections)>15:
        raise ValueError('Corrections must be a small JSON object')
    allowed={'geometry','coordinate','extent','radius','inner_radius','outer_radius',
             'source','source_formula','regions','wanted'}
    if set(corrections)-allowed:
        raise ValueError('Unsupported correction field')
    text=Path(a.input).read_text(encoding='utf-8')
    response=run_text(text,corrections=corrections)
    # Retry only if a literal textual declaration of the radial coordinate was missed.
    # This is not a physics fallback: the authoritative backend still owns the model.
    auto, evidence=text_corrections(text,corrections)
    if response.get('status')=='not_solved' and auto:
        retried=run_text(text,corrections={**auto,**corrections})
        # Prefer the second reply only when it makes actual progress.
        if retried.get('status')!='not_solved':
            response=retried
            response['desktop_text_corrections']={'values':auto,'evidence':evidence}
    # Keep backend status unchanged. Preserve disclosed user choices.
    response['desktop_user_corrections']=corrections
    Path(a.output).write_text(json.dumps(response,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    return 0 if response.get('status') not in ('not_solved',) else 2

if __name__=='__main__':
    raise SystemExit(main())
