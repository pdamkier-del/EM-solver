"""A killable process boundary for new, untrusted symbolic workloads."""
import multiprocessing as mp
import queue
from .problem import InputError


def block_network():
    import socket
    def blocked(*args,**kwargs):raise InputError('Netværk er forbudt i beregningsprocessen.')
    socket.socket.connect=blocked;socket.socket.connect_ex=blocked;socket.create_connection=blocked


def _worker(output,parsed,evaluate):
    block_network()
    try:
        from .new_problem import execute
        if parsed.data.get('assisted_model_card'):
            from ..assisted_backend import validate_card
            validate_card(parsed)
        if 'composition' in parsed.data:
            from .composition import execute_plan
            answer=execute_plan(parsed,evaluate)
        else:answer=execute(parsed,evaluate_integrals=evaluate)
        output.put(('ok',answer))
    except Exception as exc:output.put(('error',str(exc)))


def _call(parsed,evaluate=False,timeout=18):
    context=mp.get_context('spawn');output=context.Queue();process=context.Process(target=_worker,args=(output,parsed,evaluate));process.start()
    try:
        try:kind,value=output.get(timeout=timeout)
        except queue.Empty:raise InputError('Tidsgrænsen er nået. Vælg integralopsætning uden analytisk evaluering eller forenklede input. Ingen løsning er opfundet.')
        if kind!='ok':raise InputError(value)
        return value
    finally:
        if process.is_alive():process.terminate()
        process.join(timeout=1);output.close()


def run_confirmed(parsed,evaluate=False,timeout=18):
    import time
    start=time.monotonic()
    curve='source' in parsed.data or parsed.data.get('solver_spec',{}).get('family')=='biot_savart'
    if not evaluate or not curve:return _call(parsed,evaluate,timeout)
    formal=_call(parsed,False,min(6,timeout/2))
    try:return _call(parsed,True,max(0.01,timeout-(time.monotonic()-start)))
    except InputError as exc:
        if 'Tidsgrænsen' not in str(exc):raise
        formal.warnings.append('TIMEOUT: analytisk beregning blev stoppet; den allerede opstillede korrekte integralbesvarelse bevares.')
        return formal
