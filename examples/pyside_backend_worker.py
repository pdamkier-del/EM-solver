"""Optional PySide6 integration, no window/layout; backend remains Qt-independent.

Run from repository: python -m examples.pyside_backend_worker
Requires PySide6 supplied by the separate frontend environment.
"""
import multiprocessing
from PySide6.QtCore import QObject,Signal,Slot,QRunnable,QThreadPool,QCoreApplication
from em1_solver.backend_client import run_text,choose_view

class BackendSignals(QObject):
    completed=Signal(dict)
    failed=Signal(str)

class BackendWorker(QRunnable):
    def __init__(self,text):
        super().__init__();self.text=text;self.signals=BackendSignals()
    @Slot()
    def run(self):
        try:self.signals.completed.emit(run_text(self.text))
        except Exception as exc:self.signals.failed.emit(str(exc))

class Receiver(QObject):
    @Slot(dict)
    def completed(self,response):
        # Real frontend: retain response; use choose_view for later tab changes.
        print(choose_view(response,'result'))
        print(choose_view(response,'derivation'))
        print(choose_view(response,'explanation'))
        QCoreApplication.quit()
    @Slot(str)
    def failed(self,message):
        print(message);QCoreApplication.quit()

def main():
    app=QCoreApplication([]);receiver=Receiver()
    worker=BackendWorker('En massiv kugle med radius R har rho(r)=k*r. Bestem den totale ladning Q.')
    worker.signals.completed.connect(receiver.completed);worker.signals.failed.connect(receiver.failed)
    QThreadPool.globalInstance().start(worker)
    return app.exec()

if __name__=='__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())
