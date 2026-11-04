"""Run the complete offline evidence and certification pipeline."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for args in [ ['-m','pytest','-q'], ['tools/certify_solvers.py'], ['tools/build_coverage.py'], ['tools/offline_smoke.py'], ['tools/ui_exam_smoke.py'] ]:
    subprocess.run([sys.executable,*args],cwd=ROOT,check=True)
