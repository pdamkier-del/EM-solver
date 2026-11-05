"""Local paths only. Preserve an existing legacy vendor backend if installed."""
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent


def location(assisted=False):
    project=ROOT.parent
    assisted_root=ROOT/'vendor'/'EM-solver-assisted'
    legacy=ROOT/'vendor'/'EM-solver'
    if assisted:
        root=assisted_root if (assisted_root/'em1_solver').is_dir() else project
    else:
        root=legacy if (legacy/'em1_solver').is_dir() else assisted_root if (assisted_root/'em1_solver').is_dir() else project
    current=Path(sys.executable)
    base=Path(os.getenv('LOCALAPPDATA',str(Path.home())))/'EM1'
    candidates=[Path(os.environ['EM1_BACKEND_PYTHON'])] if os.environ.get('EM1_BACKEND_PYTHON') else []
    if not assisted and root==legacy:candidates += [base/'backend312'/'Scripts'/'python.exe',base/'backend313'/'Scripts'/'python.exe']
    candidates.append(current)
    return root,next((p for p in candidates if p.is_file()),current)
