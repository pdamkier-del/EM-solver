"""Cross-platform one-click launcher; Windows opens a local app-style browser window."""
import argparse,os,shutil,subprocess,sys,time,urllib.request,webbrowser
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def healthy(port):
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/_stcore/health',timeout=1) as response:
            return response.status==200 and response.read()==b'ok'
    except (OSError,ValueError):
        return False

def _browser_candidates():
    env=os.environ
    candidates=[
        Path(env.get('PROGRAMFILES(X86)',''))/'Microsoft/Edge/Application/msedge.exe',
        Path(env.get('PROGRAMFILES',''))/'Microsoft/Edge/Application/msedge.exe',
        Path(env.get('LOCALAPPDATA',''))/'Microsoft/Edge/Application/msedge.exe',
        Path(env.get('PROGRAMFILES',''))/'Google/Chrome/Application/chrome.exe',
        Path(env.get('PROGRAMFILES(X86)',''))/'Google/Chrome/Application/chrome.exe',
        Path(env.get('LOCALAPPDATA',''))/'Google/Chrome/Application/chrome.exe',
    ]
    for name in ('msedge','chrome'):
        found=shutil.which(name)
        if found:
            candidates.insert(0,Path(found))
    seen=set()
    for candidate in candidates:
        try:
            key=str(candidate.resolve())
        except OSError:
            key=str(candidate)
        if key not in seen and candidate.is_file():
            seen.add(key)
            yield candidate

def open_local_app(url):
    """Open localhost as a standalone Edge/Chrome app window when possible."""
    if os.name=='nt':
        for browser in _browser_candidates():
            try:
                subprocess.Popen([
                    str(browser),
                    f'--app={url}',
                    '--start-maximized',
                    '--no-first-run',
                    '--disable-session-crashed-bubble',
                ])
                print('Aabnet som lokalt app-vindue: '+browser.name,flush=True)
                return True
            except OSError:
                continue
    return webbrowser.open(url)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--port',type=int,default=8501)
    args=parser.parse_args()

    from em1_solver.core.startup import check
    errors=check()
    if errors:
        print('Systemstatus: Ikke klar\n'+'\n'.join(errors),flush=True)
        return 1
    print('Systemstatus: Klar',flush=True)
    if args.check:
        return 0

    url=f'http://127.0.0.1:{args.port}'
    print('EM1 Solver lokal adresse: '+url,flush=True)
    if healthy(args.port):
        print('Porten er allerede optaget af en Streamlit-app.',flush=True)
        open_local_app(url)
        return 0

    command=[
        sys.executable,'-m','streamlit','run',str(ROOT/'app.py'),
        '--server.address','127.0.0.1',
        '--server.port',str(args.port),
        '--server.headless','true',
        '--browser.gatherUsageStats','false',
    ]
    child=subprocess.Popen(command,cwd=ROOT)
    try:
        end=time.monotonic()+45
        while time.monotonic()<end:
            if child.poll() is not None:
                return child.returncode or 1
            if healthy(args.port):
                break
            time.sleep(.2)
        else:
            print('Appen blev ikke klar inden 45 sekunder.',flush=True)
            return 1

        if args.self_test:
            client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with client.open(url,timeout=5) as response:
                assert response.status==200 and b'<html' in response.read()
            print('Launcher -> Streamlit -> health/startside: OK',flush=True)
            return 0

        if not args.no_browser:
            if not open_local_app(url):
                print('Kunne ikke aabne app-vinduet automatisk. Aabn '+url,flush=True)

        print('EM1 Solver koerer lokalt. Luk motorprocessen for at stoppe appen.',flush=True)
        return child.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        if child.poll() is None:
            child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    raise SystemExit(main())
