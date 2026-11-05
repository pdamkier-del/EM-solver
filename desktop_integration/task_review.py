"""Small task review for existing potential/cylindrical-current solvers."""
import json,sys,html
from PySide6.QtCore import QProcess,QProcessEnvironment,QTimer,Signal,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QLabel,QLineEdit,QCheckBox,QPushButton,QScrollArea,QGroupBox,QComboBox

class TaskReview(QWidget):
    solutionReady=Signal(dict)
    activityChanged=Signal(bool)
    modelInvalidated=Signal()
    def __init__(self,python_exe,repository,parent=None):
        super().__init__(parent);self.python_exe=str(python_exe);self.repository=str(repository)
        self.text='';self.proposal=None;self.last_reply=None;self.last_request=None;self.fields={};self.quantities={};self.unit_fields={};self.wanted={};self._loading=False
        self.process=QProcess(self);self.process.finished.connect(self._finished);self.process.errorOccurred.connect(self._error)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self._timeout)
        layout=QVBoxLayout(self);self.summary=QLabel('Indsæt opgaven på forsiden og tryk Analysér opgave.');self.summary.setWordWrap(True);layout.addWidget(self.summary)
        self.editor=QWidget();self.form=QFormLayout(self.editor);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(self.editor);layout.addWidget(scroll)
        self.missing=QLabel();self.missing.setWordWrap(True);layout.addWidget(self.missing)
        self.confirm=QCheckBox('Jeg bekræfter de viste data og modelbetingelser');layout.addWidget(self.confirm)
        self.confirm.toggled.connect(lambda checked:self.invalidate() if not checked and not self._loading else None)
        self.solve=QPushButton('Beregn opgaven');layout.addWidget(self.solve);self.solve.clicked.connect(self._solve)
        self.status=QLabel('Ingen beregning kørt.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.solve.setEnabled(False)
    @property
    def busy(self):return self.process.state()!=QProcess.NotRunning
    def invalidate(self,*args):
        if self._loading:return
        self.confirm.setChecked(False);self.last_reply=None;self.last_request=None;self.modelInvalidated.emit();self.status.setText('Data ændret. Gennemgå og bekræft modellen igen.')
    def invalidate_text(self,text):
        if text!=self.text:
            self.text=text;self.invalidate();self.proposal=None;self.solve.setEnabled(False);self.summary.setText('Opgaveteksten er ændret. Tryk Analysér opgave igen.')
    def analyze(self,text):
        if self.busy:return
        self.text=text;self.proposal=None;self.confirm.setChecked(False);self.last_reply=None;self.last_request=None;self.modelInvalidated.emit()
        self._start(dict(mode='analyze',text=text))
    def _start(self,data):
        self.mode=data['mode'];environment=QProcessEnvironment.systemEnvironment();environment.insert('PYTHONUTF8','1');environment.remove('PYTHONPATH')
        self.process.setProcessEnvironment(environment);self.process.setWorkingDirectory(self.repository)
        self.editor.setEnabled(False);self.solve.setEnabled(False);self.confirm.setEnabled(False);self.activityChanged.emit(True)
        self.status.setText('Læser opgaven offline …' if self.mode=='analyze' else 'Beregner med den eksisterende fysikmotor …')
        self.process.start(self.python_exe,['-m','desktop_integration.workflow_worker'])
        self.process.write(json.dumps(data,ensure_ascii=False).encode('utf8'));self.process.closeWriteChannel();self.timer.start(45000 if self.mode=='solve' else 10000)
    def _error(self,error):
        if error==QProcess.FailedToStart:
            self.timer.stop();self.editor.setEnabled(True);self.confirm.setEnabled(True);self.activityChanged.emit(False);self.status.setText('Backend kunne ikke startes: '+self.process.errorString())
    def _timeout(self):
        self.process.kill();self.status.setText('Tidsgrænsen blev nået. Ingen løsning er godkendt.')
    def _render(self,p):
        self._loading=True
        while self.form.count():
            item=self.form.takeAt(0)
            if item.widget():item.widget().deleteLater()
        self.fields={};self.quantities={};self.unit_fields={};self.wanted={}
        notes=' '.join(p.get('notes',[]));self.summary.setText('Forslag: '+p['title']+'\n'+p['reasoning']+'\n\nBetingelser, som du skal bekræfte: '+p['physical_conditions']+('\n'+notes if notes else ''))
        source=QLineEdit(p['source']);source.textChanged.connect(self.invalidate);self.fields['source']=source
        self.form.addRow('Potentiale V(x,y,z)' if p['kind']=='potential' else 'Strømtæthed J('+p['coordinate']+')',source)
        if p['kind']=='cylinder':
            if not p.get('radius_symbol'):
                field=QLineEdit();self.fields['radius_symbol']=field;field.textChanged.connect(self.invalidate);self.form.addRow('Radiussymbol fra opgaven',field)
            if p.get('total_current') is not None or any(i['field']=='total_current' for i in p['issues']):
                field=QLineEdit(p.get('total_current',''));field.setPlaceholderText('Samlet strøm med enhed, fx 8 A');field.textChanged.connect(self.invalidate);self.fields['total_current']=field;self.form.addRow('Samlet strøm – bruges til at finde '+p.get('normalization_symbol','amplituden'),field)
            if any(i['field']=='normalization_symbol' for i in p['issues']):
                field=QLineEdit();self.fields['normalization_symbol']=field;field.textChanged.connect(self.invalidate);self.form.addRow('Konstant der skal findes',field)
            if any(i['field']=='direction' for i in p['issues']):
                field=QComboBox();field.addItems(['Vælg strømretning','+z','-z']);self.fields['direction']=field;field.currentIndexChanged.connect(self.invalidate);self.form.addRow('Strømretning',field)
            else:self.form.addRow('Strømretning fra teksten',QLabel(p['direction']))
            if p.get('points'):
                field=QLineEdit('; '.join(p['points']));self.fields['points']=field;field.textChanged.connect(self.invalidate);self.form.addRow('Feltet beregnes ved disse afstande',field)
        for name,value in p['quantities'].items():
            field=QLineEdit(value);field.textChanged.connect(self.invalidate);self.quantities[name]=field
            self.form.addRow(('Radius '+name if name==p.get('radius_symbol') else name)+' (med enhed)',field)
        unit_text=', '.join(name+': '+unit for name,unit in sorted(p['units'].items()))
        unit_label=QLabel(unit_text);unit_label.setWordWrap(True);self.form.addRow('Enheder fra koordinater og dimensionskrav',unit_label)
        for issue in p['issues']:
            if issue['field'].startswith('unit:'):
                name=issue['field'].split(':',1)[1];field=QLineEdit();field.setPlaceholderText('Enhed fra opgaven');field.textChanged.connect(self.invalidate);self.unit_fields[name]=field;self.form.addRow(issue['label'],field)
        if p['wanted']:
            labels={'E':'Elektrisk felt E','rho':'Samlet volumenladning rho','B':'Magnetfelt inde og ude','I':'Samlet strøm','I_enc':'Omsluttet strøm I(s)','density_amplitude':'Ukendt amplitude i strømtætheden'}
            targets=QLabel(', '.join(labels.get(k,k) for k in p['wanted']));targets.setWordWrap(True);self.form.addRow('Søges ifølge teksten',targets)
        else:
            for name in ('E','rho') if p['kind']=='potential' else ('B','I'):
                box=QCheckBox(name);box.toggled.connect(self.invalidate);self.wanted[name]=box;self.form.addRow('Søges',box)
        self.missing.setText('Oplysninger der mangler:\n'+'\n'.join(i['label']+': '+i['reason'] for i in p['issues']) if p['issues'] else 'De givne størrelser er læst. Der er ikke indsat gættede tal. Medie- og modelbetingelser skal stadig bekræftes ovenfor.')
        self.confirm.setChecked(False);self.solve.setEnabled(True);self._loading=False
    def _solve(self):
        if self.busy or not self.proposal:return
        if not self.confirm.isChecked():self.status.setText('Bekræft først data og de viste modelbetingelser.');return
        edits={k:(v.currentText() if isinstance(v,QComboBox) else v.text().strip()) for k,v in self.fields.items()}
        if 'points' in edits:edits['points']=[v.strip() for v in edits['points'].split(';') if v.strip()]
        edits['quantities']={k:v.text().strip() for k,v in self.quantities.items()}
        edits['units']={k:v.text().strip() for k,v in self.unit_fields.items() if v.text().strip()}
        if self.wanted:edits['wanted']=[k for k,v in self.wanted.items() if v.isChecked()]
        self._start(dict(mode='solve',text=self.text,edits=edits))
    def _finished(self,code,status):
        self.timer.stop();self.editor.setEnabled(True);self.confirm.setEnabled(True);self.activityChanged.emit(False);self.solve.setEnabled(self.proposal is not None)
        try:
            if code or status!=QProcess.NormalExit:raise ValueError('Processen blev stoppet; ingen løsning. '+bytes(self.process.readAllStandardError()).decode('utf8',errors='replace')[-500:])
            data=json.loads(bytes(self.process.readAllStandardOutput()).decode('utf8'))
            if data.get('error'):raise ValueError(data['error'])
            if data['proposal']['text']!=self.text:raise ValueError('Opgaveteksten blev ændret under kørslen. Analysér den nye tekst igen.')
            self.proposal=data['proposal']
            if self.mode=='analyze':self._render(self.proposal);self.status.setText('Forslaget er klar til din gennemgang. Intet er beregnet endnu.')
            else:
                self.last_request=data['request'];self.last_reply=data['reply'];self.solutionReady.emit(data['reply']);state=data['reply']['status']
                messages=list(data['reply'].get('errors',[]))+[q['message'] for q in data['reply'].get('questions',[])]
                for part in data['reply'].get('subproblems',[]):messages.extend(part.get('errors',[]))
                self.status.setText('Beregnet under din bekræftede model.' if state=='calculated_under_confirmed_model' else 'Ikke fuldt løst: '+'; '.join(messages or [state]))
                self.missing.setText('Løsningen vises i Resultat, Udledning og Forklaring. Fortolkningen er bekræftet af dig.' if state=='calculated_under_confirmed_model' else '; '.join(messages))
        except (ValueError,KeyError,TypeError) as exc:
            self.last_reply=None;self.modelInvalidated.emit();self.status.setText('Ret følgende: '+str(exc))
