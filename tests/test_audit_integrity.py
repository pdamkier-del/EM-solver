"""Corpus integrity checks; these do not validate classifications or physics."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROWS = json.loads((ROOT/'data/exam_problem_registry.json').read_text())

def test_all_eleven_sets_have_fourteen_lettered_questions():
    counts = Counter(r['exam'] for r in ROWS)
    assert len(counts) == 11
    assert set(counts.values()) == {14}

def test_question_identifiers_are_unique():
    assert len({(r['exam'],r['problem'],r['subproblem']) for r in ROWS}) == len(ROWS)

def test_every_question_has_source_and_answer_locator():
    for row in ROWS:
        assert row['source_context']
        assert row['source_question']
        assert row['answer_reference']
        assert row['source_page'] >= 1
        assert (ROOT/row['source_pdf']).is_file()

def test_required_registry_fields():
    required = set('exam problem subproblem domain family geometry given wanted methods dependencies answer_reference difficulty notes'.split())
    for row in ROWS:
        assert required <= row.keys()
        assert row['domain'] in {'EV','BA','DYN'}
        assert row['review_status'] == 'text_classified'

def test_all_extracted_lettered_questions_match_registry():
    # Compare independent count from the PDF text, excluding figure panel labels.
    import re
    source = (ROOT/'data/exams_extracted.txt').read_text()
    questions = re.findall(r'^\s{0,4}([a-d])\) (?=[A-ZÆØÅEiV])', source, re.M)
    assert len(questions) == len(ROWS) == 154
