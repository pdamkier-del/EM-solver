import pytest
from em1_solver.core.historical import paths,load,run
from em1_solver.rendering.latex import document
from em1_solver.rendering.structured import serialize

RECIPES=[p for p in paths() if load(p)['status'] in ('executable','partial')]

@pytest.mark.recipe
@pytest.mark.parametrize('path',RECIPES,ids=lambda p:load(p)['id'])
def test_historical_recipe_end_to_end(path):
    recipe=load(path)
    result=run(recipe)
    assert result.passed,result.checks
    assert result.solutions
    for solution in result.solutions.values():
        assert solution.steps and solution.reasoning
        assert not any('WARNING: dimensional inconsistency' in w for w in solution.warnings),solution.warnings
        fragments=serialize(solution)
        assert len(fragments['steps'])==len(solution.steps)
        text=document(solution)
        assert r'\section*{Mellemregninger}' in text and r'\section*{Resultat}' in text
