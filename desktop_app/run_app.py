"""Diagnostic bootstrap: catches startup errors, saves traceback, shows a Windows message."""
from pathlib import Path
import traceback
import sys

try:
    import app
    app.main()
except Exception:
    trace = traceback.format_exc()
    log = Path(__file__).resolve().parent / 'EM1_ERROR_LOG.txt'
    try:
        log.write_text(trace, encoding='utf-8')
    except OSError:
        pass
    print(trace, file=sys.stderr)
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, 'EM1 Solver kunne ikke starte.\n\nSe EM1_ERROR_LOG.txt i programmets mappe.\n\n' + trace[-700:], 'EM1 Solver - fejl', 0x10)
        except Exception:
            pass
    raise SystemExit(1)
