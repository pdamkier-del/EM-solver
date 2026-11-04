"""Readiness checks include a real spawn worker, also on Windows."""
import multiprocessing as mp
import tempfile,json
from pathlib import Path

def probe_worker(output):
    from .task_runtime import block_network
    block_network()
    import sympy as sp
    output.put(str(sp.diff(sp.Symbol('x')**2,sp.Symbol('x'))))

def check():
    errors=[]
    try:
        import sympy
        from .registry import solvers
        assert solvers()
    except Exception as exc:errors.append('SymPy/solverimport: '+str(exc))
    root=Path(__file__).resolve().parents[2]
    try:
        rows=json.loads((root/'data/exam_problem_registry.json').read_text())
        if len(rows)!=154:raise ValueError('Forventede 154 historiske delopgaver.')
        if len(list((root/'data/historical_problems').glob('*.json')))!=154:raise ValueError('Historiske opskrifter mangler.')
    except Exception as exc:errors.append('Historiske data: '+str(exc))
    try:
        with tempfile.TemporaryDirectory(prefix='em1-start-') as folder:
            file=Path(folder)/'write.txt';file.write_text('ok');assert file.read_text()=='ok'
    except Exception as exc:errors.append('Temp-directory: '+str(exc))
    process=None;output=None
    try:
        context=mp.get_context('spawn');output=context.Queue();process=context.Process(target=probe_worker,args=(output,));process.start()
        if output.get(timeout=8)!='2*x':raise ValueError('Uventet symbolsk worker-resultat.')
    except Exception as exc:errors.append('Symbolsk worker kunne ikke startes: '+str(exc))
    finally:
        if process is not None and process.pid is not None:
            if process.is_alive():process.terminate()
            process.join(timeout=1)
        if output:output.close()
    return errors
