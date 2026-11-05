"""Optional frontend adapter; backend stays independent of PySide6.

Keep this QObject alive until finished. Pass the application's absolute venv
python.exe path and repository directory. No shell, network or API credentials.
Native Windows/Qt behaviour requires a separate integration test.
"""
import json
from PySide6.QtCore import QObject, QProcess, Signal, QProcessEnvironment


class AssistedProcess(QObject):
    completed=Signal(dict)
    failed=Signal(str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.process=QProcess(self)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(lambda error:self.failed.emit(self.process.errorString()))

    def start(self,python_exe,repository,request):
        if self.process.state()!=QProcess.NotRunning:
            raise RuntimeError('En beregning kører allerede.')
        environment=QProcessEnvironment.systemEnvironment()
        environment.insert('PYTHONUTF8','1')
        self.process.setProcessEnvironment(environment)
        self.process.setWorkingDirectory(str(repository))
        self.process.start(str(python_exe),['-m','em1_solver.assisted_backend'])
        self.process.write(json.dumps(request,ensure_ascii=False,allow_nan=False).encode('utf-8'))
        self.process.closeWriteChannel()

    def _finished(self,code,status):
        if code!=0:
            self.failed.emit(bytes(self.process.readAllStandardError()).decode('utf-8',errors='replace'));return
        try:self.completed.emit(json.loads(bytes(self.process.readAllStandardOutput()).decode('utf-8')))
        except (ValueError,UnicodeError) as exc:self.failed.emit(str(exc))

    def cancel(self):
        # Normal cancellation should be between requests. Killing the parent
        # alone cannot guarantee termination of its spawned worker on Windows.
        self.failed.emit('Afbryd ikke med kill; afvent den afgrænsede worker (18 s pr. delspørgsmål).')
