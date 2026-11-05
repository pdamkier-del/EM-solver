from pathlib import Path
p=Path(__file__).parent/'app.py'
s=p.read_text(encoding='utf8')
s=s.replace('"""EM1 Solver – standalone Qt desktop design prototype.\n\nRequires PySide6. Does not import or claim to operate the Codex solver.\nLocal files and editable notes function offline.\n"""', '"""EM1 Solver Windows desktop frontend and optional pinned offline Codex backend."""')
s=s.replace('from PySide6.QtCore import Qt, QTimer, QUrl','from PySide6.QtCore import Qt, QTimer, QUrl, QProcess, QProcessEnvironment')
s=s.replace('from pathlib import Path','from pathlib import Path\nfrom backend_bridge import translate_backend')
s=s.replace("if eq:derivation.append('\\\\['+str(eq)+'\\\\]')", "if eq:derivation.append(str(eq) if str(eq).lstrip().startswith('\\\\[') else '\\\\['+str(eq)+'\\\\]')")
# confirm variant
s=s.replace("if eq:derivation.append('\\['+str(eq)+'\\]')", "if eq:derivation.append(str(eq) if str(eq).lstrip().startswith('\\[') else '\\['+str(eq)+'\\]')")
s=s.replace("'Fysisk metode → indsættelse → omskrivning → resultat. Testdata vises som importerede løsninger.'", "'Indsæt opgave → løs offline → se metode og udledning.'")
s=s.replace("self.prompt=QPlainTextEdit();self.prompt.setPlaceholderText('Indsæt din opgave her. Uden tilkoblet backend bliver fri tekst ikke løst.')", "self.prompt=QPlainTextEdit();self.prompt.setPlaceholderText('Indsæt din EM1-opgavetekst her, og tryk Løs opgave med backend.')")
s=s.replace("self.import_button=QPushButton('Åbn opgavetekst');actions.addWidget(self.import_button)", "self.solve_button=QPushButton('Løs opgave med backend');self.solve_button.setObjectName('primary');actions.addWidget(self.solve_button)\n        self.import_button=QPushButton('Åbn opgavetekst');actions.addWidget(self.import_button)")
s=s.replace('self.import_button.clicked.connect(self.import_txt)', 'self.import_button.clicked.connect(self.import_txt)\n        self.solve_button.clicked.connect(self.solve_live)')
s=s.replace("self.interpret.setHtml('<b>Tilstand:</b> Visnings- og integrationstest. Ingen autonom løsning.')", "self.interpret.setHtml('<b>Tilstand:</b> Klar til en installeret, låst offline-backend. Demoerne er stadig tilgængelige.')\n        self._backend_process=None\n        self._backend_task_path=None\n        self._backend_reply_path=None\n        self._backend_requested_text=''\n        self._backend_errors=[]")
needle='    def load_selected_test(self):'
addition='''    def solve_live(self):
        text=self.prompt.toPlainText().strip()
        if not text:
            QMessageBox.information(self, 'Manglende opgave', 'Indsæt først opgaveteksten.')
            return
        backend_root=ROOT/'vendor'/'EM-solver'
        backend_python=Path(os.getenv('LOCALAPPDATA',str(Path.home()))) / 'EM1' / 'backend312' / 'Scripts' / 'python.exe'
        if not (backend_root/'em1_solver'/'backend_client.py').is_file() or not backend_python.is_file():
            QMessageBox.warning(self,'Installer backend først',
                'Fysikmotoren mangler. Kør SETUP_BACKEND_WINDOWS.bat fra programmappen én gang.\\n'
                'Backend er testet på Python 3.12. Dine fem demoopgaver virker uden installation.')
            return
        if self._backend_process and self._backend_process.state()!=QProcess.ProcessState.NotRunning:
            QMessageBox.information(self,'Beregning i gang','Der kører allerede en beregning.')
            return
        import tempfile, uuid
        run_dir=DATA_DIR/'backend_runs';run_dir.mkdir(parents=True,exist_ok=True)
        run_id=uuid.uuid4().hex
        self._backend_task_path=run_dir/('task_'+run_id+'.txt')
        self._backend_reply_path=run_dir/('reply_'+run_id+'.json')
        self._backend_task_path.write_text(text,encoding='utf-8')
        self._backend_requested_text=text
        self._backend_errors=[]
        self.solve_button.setEnabled(False)
        self.solve_button.setText('Beregner …')
        self.warning.setText('BEREGNER · Arbejder offline med låst Codex-backend. Ingen resultatstatus endnu.')
        self._backend_process=QProcess(self)
        self._backend_process.setWorkingDirectory(str(backend_root))
        env=QProcessEnvironment.systemEnvironment()
        env.insert('PYTHONIOENCODING','utf-8')
        env.insert('PYTHONUTF8','1')
        self._backend_process.setProcessEnvironment(env)
        self._backend_process.readyReadStandardError.connect(self._collect_backend_error)
        self._backend_process.errorOccurred.connect(self._backend_failed)
        self._backend_process.finished.connect(self._backend_finished)
        self._backend_process.start(str(backend_python), ['-m','em1_solver.backend_client','--input',str(self._backend_task_path),'--output',str(self._backend_reply_path)])
        QTimer.singleShot(120000,lambda proc=self._backend_process: self._backend_timeout(proc))

    def _collect_backend_error(self):
        if self._backend_process:
            message=bytes(self._backend_process.readAllStandardError()).decode('utf-8',errors='replace')
            if message:self._backend_errors.append(message[:2000])

    def _backend_timeout(self,proc):
        if proc is self._backend_process and proc.state()!=QProcess.ProcessState.NotRunning:
            self._backend_errors.append('Beregningen blev afbrudt efter 120 sekunder.')
            proc.kill()

    def _backend_failed(self,error):
        if self._backend_process:
            self._backend_errors.append('Procesfejl: '+str(error))

    def _backend_finished(self,exit_code,exit_status):
        self.solve_button.setEnabled(True)
        self.solve_button.setText('Løs opgave med backend')
        try:
            if not self._backend_reply_path or not self._backend_reply_path.is_file():
                raise ValueError('Backend producerede ikke en JSON-fil. '+(' '.join(self._backend_errors))[-1600:])
            data=json.loads(self._backend_reply_path.read_text(encoding='utf-8'))
            payload=translate_backend(data,self._backend_requested_text)
            self.show_solution(payload,origin='BACKEND')
            # An exit code 2 is expected for not_solved; still show the genuine missing-data response.
            if exit_code not in (0,2):
                self.warning.setText('BACKEND FEJL · Afsluttede med kode '+str(exit_code)+'. Resultatet er ikke godkendt.')
        except Exception as exc:
            self.warning.setText('BACKEND FEJL · Ingen godkendt besvarelse. '+str(exc)[:400])
            self.interpret.setHtml('<b>Backend kunne ikke levere et læsbart svar.</b>')
        finally:
            for filename in (self._backend_task_path,self._backend_reply_path):
                try:
                    if filename and filename.is_file():filename.unlink()
                except OSError:pass

'''
s=s.replace(needle,addition+needle)
s=s.replace("self.prompt.setPlainText(_as_text(payload.get('prompt','')))","self.prompt.setPlainText(_as_text(payload.get('prompt','')))")
s=s.replace("if origin=='TESTDATA':\n            note='TESTDATA · Illustrativt eksempel. Ikke beregnet eller verificeret af den autonome EM1-motor.'\n        else:\n            note='IMPORTERET · Status oplyst af afsender: '+status+'. Desktopappen kontrollerer ikke fysikkens korrekthed.'", "if origin=='TESTDATA':\n            note='TESTDATA · Illustrativt eksempel. Ikke beregnet eller verificeret af den autonome EM1-motor.'\n        elif origin=='BACKEND':\n            note='LIVE BACKEND · '+_as_text(payload.get('backend_status',status))+'. Kun backendens faktisk gennemførte kontroller ligger bag status. Læs antagelser og advarsler.'\n        else:\n            note='IMPORTERET · Status oplyst af afsender: '+status+'. Desktopappen kontrollerer ikke fysikkens korrekthed.'")
s=s.replace("self.warning.setText('OPGAVETEKST INDLÆST · Ingen autonom solver er tilkoblet. Vælg testbesvarelse eller importér resultat-JSON.')", "self.warning.setText('OPGAVETEKST INDLÆST · Klik Løs opgave med backend for at forsøge en offline løsning.')")
s=s.replace("payload=json.loads(path.read_text(encoding='utf-8'))\n            self.show_solution(payload,origin='IMPORT')", "payload=json.loads(path.read_text(encoding='utf-8'))\n            if isinstance(payload,dict) and payload.get('schema_version')=='1.0':\n                payload=translate_backend(payload,self.prompt.toPlainText())\n            self.show_solution(payload,origin='IMPORT')")
p.write_text(s,encoding='utf-8')
