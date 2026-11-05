"""Embeddable assisted DYN form. No replacement of the host's old backend.

The host supplies its backend Python interpreter and repository path. Prose
suggestions do not populate physical givens. All calculations use QProcess.
"""
import ast
import html
import json
import re
import sys
from pathlib import Path
from PySide6.QtCore import QProcess, QProcessEnvironment, Signal, Qt
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,
    QPlainTextEdit,QPushButton,QComboBox,QLabel,QLineEdit,QCheckBox,QTableWidget,
    QTableWidgetItem,QTextBrowser,QScrollArea,QApplication)
from em1_solver.assisted_backend import catalog,plan,VERSION

LABELS={'faraday_flux':'Faraday – givet flux','faraday_uniform':'Faraday – homogent normalfelt',
    'faraday_integral':'Faraday – fluxintegral','motional_curve':'Bevægelsesinduktion',
    'feedback':'Stang med elektromekanisk tilbagekobling','RC_discharge':'RC – afladning',
    'RL_step':'RL – spændingstrin','displacement_disk':'Forskydningsstrøm – cirkulære plader'}
FIELDS={'time':'Tidsvariabel','flux':'Flux pr. vinding','N':'Vindingstal',
    'B_normal':'Signeret normalfelt','area':'Positivt areal','R':'Samlet modstand',
    'source':'Orienteret kildekurve [x,y,z]','parameter':'Kurveparameter',
    'bounds':'Integrationsgrænser','v':'Hastighedsvektor [vx,vy,vz]',
    'B':'Magnetfelt [Bx,By,Bz]','mass':'Masse','coupling':'Signeret kobling k',
    'voltage':'Påtrykt spænding','drive_force':'Signeret drivkraft',
    'initial_velocity':'Hastighed ved t=0','C':'Kapacitans','Q0':'Ladning ved t=0',
    'L':'Selvinduktans','I0':'Strøm ved t=0','fraction':'Søgt tilbageværende brøk',
    'E':'Signeret aksialt E(t)','coordinate':'Positiv radialkoordinat',
    'plate_radius':'Pladeradius','time_bounds':'Tidsinterval [fra,til]'}
WANTED={'faraday_flux':'Phi, EMF, I, P, W','faraday_uniform':'Phi, EMF, I, P, W',
    'faraday_integral':'Phi, EMF, I, P, W','motional_curve':'EMF, I, P, W, F_external, F_magnetic',
    'feedback':'v, I, tau, v_infinity, acceleration_initial, P, W',
    'RC_discharge':'Q, I, tau, I_initial, decay_time',
    'RL_step':'I, tau, I_initial, I_infinity',
    'displacement_disk':'B, J_displacement, I_displacement'}
CONDITIONS={'constant_coefficients':'Kredsløbs- og mekaniske koefficienter er konstante',
    'uniform_normal_B':'Normalfeltet er homogent over fladen',
    'negligible_self_inductance':'Kredsens selvinduktans kan negligeres',
    'stationary_return_path':'Returledningen er stationær',
    'no_friction':'Friktion kan negligeres',
    'uniform_axial_E':'Det aksiale elektriske felt er homogent',
    'circular_symmetry':'Der er cirkulær symmetri',
    'negligible_edge_effects':'Randeffekter kan negligeres',
    'vacuum_gap':'Der er vakuum mellem pladerne',
    'positive_area_on_interval':'Arealet er positivt i hele det anvendte tidsinterval'}


def expression_input(text):
    """Lists of mathematical expressions without eval or requiring JSON quotes."""
    text=text.strip()
    if not text.startswith('['):return text
    tree=ast.parse(text,mode='eval')
    def decode(node):
        if isinstance(node,(ast.List,ast.Tuple)):return [decode(child) for child in node.elts]
        return ast.get_source_segment(text,node)
    if not isinstance(tree.body,ast.List):raise ValueError('Vektorer/grænser skal være lister.')
    return decode(tree.body)


class DynPanel(QWidget):
    solutionReady=Signal(dict)
    activityChanged=Signal(bool)

    def __init__(self,python_exe=None,repository=None,parent=None,allowed_models=None):
        super().__init__(parent)
        self.python_exe=str(python_exe or sys.executable)
        self.repository=str(repository or Path(__file__).resolve().parents[1])
        self.cards=catalog();self.fields={};self.conditions={};self.last_reply=None
        self._loading=False;self._active_request=None
        self.process=QProcess(self)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._process_error)
        layout=QVBoxLayout(self)
        self.editor=QWidget();edit=QVBoxLayout(self.editor)
        edit.addWidget(QLabel('Indsæt opgaveteksten'))
        self.text=QPlainTextEdit();self.text.setMaximumHeight(160);edit.addWidget(self.text)
        self.analyze=QPushButton('Analysér opgave');edit.addWidget(self.analyze)
        self.suggestions=QLabel('Forslag er ikke bekræftede fysiske oplysninger.');self.suggestions.setWordWrap(True);edit.addWidget(self.suggestions)
        self.model=QComboBox()
        for key in allowed_models or self.cards['models']:self.model.addItem(LABELS[key],key)
        edit.addWidget(self.model)
        self.model_form=QWidget();self.form=QFormLayout(self.model_form);edit.addWidget(self.model_form)
        edit.addWidget(QLabel('Symboler: angiv enheder og eventuelle tal med enheder. Markér kun bekræftede positive symboler.'))
        self.symbols=QTableWidget(0,4);self.symbols.setHorizontalHeaderLabels(['Symbol','Enhed','Tal med enhed (valgfrit)','Positiv'])
        self.symbols.setMaximumHeight(190);edit.addWidget(self.symbols)
        row=QHBoxLayout();self.add_symbol=QPushButton('Tilføj symbol');row.addWidget(self.add_symbol)
        self.scan=QPushButton('Find symboler i mine udtryk');row.addWidget(self.scan);edit.addLayout(row)
        self.wanted=QLineEdit();self.wanted.setPlaceholderText('Søgte størrelser, adskilt med komma');edit.addWidget(self.wanted)
        self.wanted_help=QLabel();edit.addWidget(self.wanted_help)
        self.conditions_box=QWidget();self.condition_layout=QVBoxLayout(self.conditions_box);edit.addWidget(self.conditions_box)
        self.orientation=QCheckBox();self.orientation.setText('Jeg bekræfter ovenstående orientering og modelbetingelser');edit.addWidget(self.orientation)
        self.confirm=QCheckBox('Jeg bekræfter at model, givne data, enheder og søgte størrelser svarer til opgaven');edit.addWidget(self.confirm)
        self.solve=QPushButton('Løs opgave');edit.addWidget(self.solve)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(self.editor);layout.addWidget(scroll,2)
        self.status=QLabel('Model: ikke bekræftet. Ingen beregning kørt.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.output=QTextBrowser();self.output.setOpenExternalLinks(False);layout.addWidget(self.output,2)
        self.copy=QPushButton('Kopiér løsning');layout.addWidget(self.copy)
        self.analyze.clicked.connect(self._analyze);self.model.currentIndexChanged.connect(self._build_form)
        self.scan.clicked.connect(self._scan_symbols);self.add_symbol.clicked.connect(lambda:self._add_symbol())
        self.solve.clicked.connect(self._solve);self.copy.clicked.connect(lambda:QApplication.clipboard().setText(self.output.toPlainText()))
        self.text.textChanged.connect(self._invalidate);self.wanted.textChanged.connect(self._invalidate)
        self.symbols.itemChanged.connect(self._invalidate)
        self.confirm.toggled.connect(self._confirmation_changed)
        self.orientation.toggled.connect(self._invalidate)
        self._build_form()

    @property
    def busy(self):return self.process.state()!=QProcess.NotRunning

    def _confirmation_changed(self,checked):
        if not self._loading and not self.busy:
            if not checked:self.last_reply=None;self.output.clear()
            self.status.setText('Model: bekræftet af dig; endnu ikke beregnet.' if checked else 'Model: ikke bekræftet.')

    def _invalidate(self,*args):
        if self._loading:return
        self.last_reply=None;self.confirm.setChecked(False)
        self.output.clear();self.status.setText('Input ændret. Modellen skal bekræftes igen; ingen aktuel løsning.')

    def _clear_layout(self,layout):
        while layout.count():
            item=layout.takeAt(0)
            if item.widget():item.widget().deleteLater()

    def _build_form(self,*args):
        self._loading=True;self._clear_layout(self.form);self._clear_layout(self.condition_layout)
        self.fields={};self.conditions={};self.symbols.setRowCount(0)
        self.card=self.cards['models'][self.model.currentData()]
        for key in self.card['required']+self.card['optional']:
            field=QLineEdit();self.fields[key]=field
            unit=self.cards['variable_units'].get(key,'')
            field.setPlaceholderText(unit+(' – valgfrit' if key in self.card['optional'] else ' – skal angives'))
            field.textChanged.connect(self._invalidate)
            self.form.addRow(FIELDS.get(key,key),field)
        orientation=QLabel(self.card['orientation']);orientation.setWordWrap(True);self.condition_layout.addWidget(orientation)
        # Optional circuit/area conditions remain explicit and unchecked.
        required=list(self.card['assumptions'])
        if self.card['family'] in ('faraday','motional_emf'):required.append('negligible_self_inductance')
        if self.card['family']=='motional_emf':required.append('stationary_return_path')
        if self.model.currentData()=='faraday_uniform':required.append('positive_area_on_interval')
        for key in dict.fromkeys(required):
            box=QCheckBox(CONDITIONS.get(key,key));box.setToolTip(key);box.toggled.connect(self._invalidate)
            self.conditions[key]=box;self.condition_layout.addWidget(box)
        self.wanted_help.setText('Mulige resultater: '+WANTED[self.model.currentData()])
        self.wanted.clear();self.orientation.setChecked(False)
        self.confirm.setChecked(False);self._loading=False;self._invalidate()

    def _analyze(self):
        try:
            suggestions=plan(self.text.toPlainText())
            names=[LABELS[c['model']] for c in suggestions['candidates']]
            self.suggestions.setText('Mulige modeller (skal vælges/bekræftes): '+', '.join(names) if names else 'Ingen sikker modelgenkendelse. Vælg selv en DYN-model; der er ikke udledt givne data.')
        except ValueError as exc:self.status.setText(str(exc))

    def _add_symbol(self,name='',unit=''):
        row=self.symbols.rowCount();self.symbols.insertRow(row)
        for col,value in enumerate([name,unit,'']):self.symbols.setItem(row,col,QTableWidgetItem(value))
        item=QTableWidgetItem();item.setFlags(item.flags()|Qt.ItemIsUserCheckable);item.setCheckState(Qt.Unchecked);self.symbols.setItem(row,3,item)

    def _scan_symbols(self):
        known={self.symbols.item(row,0).text() for row in range(self.symbols.rowCount()) if self.symbols.item(row,0)}
        reserved={'pi','oo','sin','cos','tan','exp','log','sqrt','Abs','asin','acos','atan','epsilon_0','mu_0'}
        for key,field in self.fields.items():
            raw=field.text().strip()
            for name in re.findall(r'\b[A-Za-z_]\w*\b',raw):
                if name in known or name in reserved:continue
                role=self.cards['variable_units'].get(key,'')
                unit=role if raw==name and '(' not in role and ' ' not in role else ''
                self._add_symbol(name,unit);known.add(name)
        self._invalidate()

    def request(self):
        units={};numbers={};positive=[]
        for row in range(self.symbols.rowCount()):
            cells=[self.symbols.item(row,col).text().strip() if self.symbols.item(row,col) else '' for col in range(3)]
            name,unit,number=cells
            if not name and not unit and not number:continue
            if not re.fullmatch(r'[A-Za-z_]\w*',name) or not unit:raise ValueError('Hvert symbol skal have et gyldigt navn og en enhed.')
            if name in units:raise ValueError('Gentaget symbol: '+name)
            units[name]=unit
            if number:numbers[name]=number
            if self.symbols.item(row,3).checkState()==Qt.Checked:positive.append(name)
        variables={key:expression_input(field.text()) for key,field in self.fields.items() if field.text().strip()}
        return dict(schema_version=VERSION,text=self.text.toPlainText(),confirmed=self.confirm.isChecked(),variables=variables,
            units=units,numbers=numbers,positive=positive,assumptions=[key for key,box in self.conditions.items() if box.isChecked()],
            subproblems=[dict(id='a',model=self.model.currentData(),wanted=[v.strip() for v in self.wanted.text().split(',') if v.strip()],orientation_confirmed=self.orientation.isChecked())])

    def _solve(self):
        if self.busy:return
        try:
            request=self.request();payload=json.dumps(request,ensure_ascii=False,allow_nan=False).encode('utf-8')
        except (ValueError,SyntaxError) as exc:self.status.setText('Ret input: '+str(exc));return
        self._active_request=request;self.last_reply=None;self.output.clear()
        environment=QProcessEnvironment.systemEnvironment();environment.insert('PYTHONUTF8','1')
        environment.remove('PYTHONPATH')
        self.process.setProcessEnvironment(environment);self.process.setWorkingDirectory(self.repository)
        self.editor.setEnabled(False);self.activityChanged.emit(True)
        self.status.setText('Beregner offline. Modelbekræftelse er din; beregningskontroller vises bagefter.')
        self.process.start(self.python_exe,['-m','em1_solver.assisted_backend'])
        self.process.write(payload);self.process.closeWriteChannel()

    def _process_error(self,error):
        if error==QProcess.FailedToStart:
            self.editor.setEnabled(True);self.activityChanged.emit(False)
            self.status.setText('Backend kunne ikke startes: '+self.process.errorString())

    def _finished(self,code,exit_status):
        self.editor.setEnabled(True);self.activityChanged.emit(False)
        try:
            if code!=0 or exit_status!=QProcess.NormalExit:raise ValueError('Backendprocessen fejlede: '+bytes(self.process.readAllStandardError()).decode('utf-8',errors='replace')[-2000:])
            reply=json.loads(bytes(self.process.readAllStandardOutput()).decode('utf-8'))
            if reply.get('schema_version')!=VERSION:raise ValueError('Backend returnerede en forkert kontraktversion.')
            self.last_reply=reply;self._render(reply);self.solutionReady.emit(reply)
        except (ValueError,UnicodeError,KeyError,TypeError) as exc:
            self.last_reply=None;self.output.clear();self.status.setText('Ingen gyldig løsning: '+str(exc))

    def _render(self,reply):
        escape=lambda x:html.escape(str(x))
        state=reply['status']
        labels={'needs_confirmation':'Mangler oplysninger eller bekræftelse','not_solved':'Afstået – ingen løsning',
            'partial':'Delvist resultat – se uafklarede kontroller','calculated_under_confirmed_model':'Beregnet under din bekræftede model'}
        self.status.setText(labels.get(state,state)+'. Fortolkningen af opgaveteksten er ikke maskinverificeret.')
        parts=[]
        if reply.get('questions'):parts.append('<h3>Oplysninger der mangler</h3>'+''.join('<p>'+escape(q['message'])+'</p>' for q in reply['questions']))
        for error in reply.get('errors',[]):parts.append('<p>'+escape(error)+'</p>')
        for part in reply.get('subproblems',[]):
            for error in part.get('errors',[]):parts.append('<p>'+escape(error)+'</p>')
            s=part.get('solution')
            if not s:continue
            parts.extend(['<h3>Model bekræftet af dig</h3><p>'+escape(LABELS[part['model']])+'</p>',
                '<p>'+escape(self.cards['models'][part['model']]['orientation'])+'</p>',
                '<h3>Givet</h3><pre>'+escape(json.dumps(self._active_request['variables'],ensure_ascii=False,indent=2))+'</pre>',
                '<h3>Søges</h3><p>'+escape(', '.join(self._active_request['subproblems'][0]['wanted']))+'</p>',
                '<h3>Metode</h3><p>'+escape(s['method'])+'</p><p>'+escape(s['reasoning'])+'</p>',
                '<h3>Udregning</h3>'])
            for step in s['steps']:parts.append('<p>'+escape(step['text'])+'</p><pre>'+escape(step['latex'] or '')+'</pre>')
            parts.append('<h3>Resultat</h3>')
            for name,value in s['views']['result']['results'].items():parts.append('<pre>'+escape(name+' = '+value['expression']+' ['+str(value['unit'])+']')+'</pre>')
            for name,value in s['views']['result']['numerical'].items():parts.append('<pre>'+escape(name+' = '+value['value']+' ['+str(value['unit'])+']')+'</pre>')
            parts.append('<p>'+escape(s['direction'])+'</p><h3>Faktisk udførte beregningskontroller</h3>')
            for check in s['checks']:
                mark='Bestået' if check['passed'] is True else 'Fejlet' if check['passed'] is False else 'Uafklaret'
                parts.append('<p>'+escape(mark+': '+check['name'])+'</p>')
            parts.append('<p>'+escape(part['verification']['limitation'])+'</p>')
            for warning in s['warnings']:parts.append('<p>Advarsel: '+escape(warning)+'</p>')
        self.output.setHtml(''.join(parts))

    def closeEvent(self,event):
        if self.busy:event.ignore();self.status.setText('Afvent den igangværende afgrænsede backendberegning før lukning.')
        else:super().closeEvent(event)


def main():
    app=QApplication(sys.argv);panel=DynPanel();panel.setWindowTitle('EM1 – assisteret DYN (integrationstest)')
    panel.resize(950,850);panel.show();sys.exit(app.exec())


if __name__=='__main__':main()
