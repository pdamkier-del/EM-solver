"""Cross-platform one-click launcher; Windows uses START_EM1_SOLVER.bat."""
import argparse,json,os,subprocess,sys,time,urllib.request,webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def healthy(port):
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/_stcore/health',timeout=1) as response:return response.status==200 and response.read()==b'ok'
    except (OSError,ValueError):return False

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--self-test',action='store_true');parser.add_argument('--no-browser',action='store_true');parser.add_argument('--port',type=int,default=8501);args=parser.parse_args()
    from em1_solver.core.startup import check
    errors=check()
    if errors:
        print('Systemstatus: Ikke klar\n'+'\n'.join(errors),flush=True);return 1
    print('Systemstatus: Klar',flush=True)
    if args.check:return 0
    url=f'http://127.0.0.1:{args.port}';print('EM1 Solver: '+url,flush=True)
    if healthy(args.port):
        print('Porten er allerede optaget af en Streamlit-app. Brug den aabne EM1-fane, eller luk den anden app.',flush=True)
        return 1
    command=[sys.executable,'-m','streamlit','run',str(ROOT/'app.py'),'--server.address','127.0.0.1','--server.port',str(args.port),'--server.headless','true','--browser.gatherUsageStats','false']
    child=subprocess.Popen(command,cwd=ROOT)
    try:
        end=time.monotonic()+45
        while time.monotonic()<end:
            if child.poll() is not None:return child.returncode or 1
            if healthy(args.port):break
            time.sleep(.2)
        else:print('Appen blev ikke klar inden 45 sekunder.',flush=True);return 1
        if args.self_test:
            client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with client.open(url,timeout=5) as response:assert response.status==200 and b'<html' in response.read()
            print('Launcher -> Streamlit -> health/startside: OK',flush=True);return 0
        if not args.no_browser:
            if not webbrowser.open(url):print('Aabn adressen ovenfor i din browser.',flush=True)
        print('Lad dette vindue vaere aabent under eksamen. Ctrl+C stopper appen.',flush=True)
        return child.wait()
    except KeyboardInterrupt:return 0
    finally:
        if child.poll() is None:child.terminate()
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill();child.wait()
if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    raise SystemExit(main())
