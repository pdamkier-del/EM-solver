"""Public confirmation/runtime regression of the reviewed external blind bank.
BA14 remains an explicit missing capability, not a benchmark success.
"""
import json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from blind_inputs import assisted
from run_blind import attempt
BANK=json.loads((ROOT/'data/blind_unseen_bank_v2.json').read_text())['tests']

@pytest.mark.parametrize('row',BANK,ids=[r['id'] for r in BANK])
def test_external_bank_assisted_public_pipeline(row):
    result=attempt(row,assisted(row))
    assert result['outcome']=='PASS',result
