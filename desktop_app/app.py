"""EM1 Solver Windows desktop frontend and optional pinned offline Codex backend."""
from __future__ import annotations
import json
import csv
import math
import io
import html
import re
from functools import lru_cache
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from backend_bridge import translate_backend
from backend_paths import location as backend_location

from PySide6.QtCore import Qt, QTimer, QUrl, QProcess, QProcessEnvironment
from PySide6.QtGui import QAction, QDesktopServices, QFont, QKeySequence, QPixmap, QImage
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QPlainTextEdit, QTextBrowser, QListWidget, QListWidgetItem,
    QComboBox, QDoubleSpinBox, QLineEdit, QFileDialog, QMessageBox, QSplitter,
    QStackedWidget, QTabWidget, QFrame, QSizePolicy, QScrollArea, QSpinBox, QInputDialog
)

ROOT = Path(__file__).resolve().parent
RESOURCE_DIR = ROOT / "resources"
DATA_DIR = Path(os.getenv("APPDATA", str(Path.home() / ".local" / "share"))) / "EM1SolverDesktop"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB = DATA_DIR / "notes.db"
ASSETS_DIR = DATA_DIR / "attachments"
ASSETS_DIR.mkdir(exist_ok=True)

BG = "#f7f8fa"
INK = "#18202b"
MUTED = "#697483"
ACCENT = "#2358d8"
STYLE = f"""
QMainWindow, QWidget#main, QStackedWidget {{ background: {BG}; color: {INK}; }}
QWidget {{ font-family: 'Segoe UI'; font-size: 12px; color: {INK}; }}
QFrame#sidebar {{ background: #151b26; border: none; }}
QFrame#sidebar QLabel {{ color: #e7ebf2; background: transparent; }}
QPushButton#nav {{ text-align: left; padding: 12px 15px; background: transparent; color: #b9c4d7; border-radius: 8px; font-weight: 600; }}
QPushButton#nav:hover {{ background: #263348; color: white; }}
QPushButton#nav[active='true'] {{ background: #304a83; color: white; }}
QPushButton#primary {{ background: {ACCENT}; border: 1px solid {ACCENT}; color: white; padding: 10px 15px; border-radius: 8px; font-weight: 600; }}
QPushButton#primary:hover {{ background: #1643af; }}
QPushButton {{ background: white; border: 1px solid #dce1e9; border-radius: 7px; padding: 8px 12px; }}
QPushButton:hover {{ background: #edf2fb; }}
QPlainTextEdit, QTextBrowser, QListWidget, QLineEdit, QComboBox, QDoubleSpinBox {{ background: white; border: 1px solid #dce1e9; border-radius: 8px; padding: 7px; selection-background-color: #cbdafa; }}
QTabWidget::pane {{ border: 1px solid #dce1e9; background: white; border-radius: 8px; }}
QTabBar::tab {{ padding: 11px 20px; background: #e9edf3; border: none; margin-right: 3px; }}
QTabBar::tab:selected {{ background: white; color: {ACCENT}; font-weight: 700; }}
QSplitter::handle {{ background: #e0e5eb; width: 5px; }}
"""



# Matplotlib mathtext renders actual vector-quality math glyphs to a PNG in memory.
# It is bundled with the desktop app and does not need a browser, LaTeX distribution or network.
# Important: mathtext supports a useful subset of LaTeX, not arbitrary TeX documents.
@lru_cache(maxsize=350)
def formula_png(formula: str, fontsize: int = 19) -> bytes:
    from matplotlib.mathtext import math_to_image
    expr = formula.strip().strip('$').strip()
    expr = re.sub(r'\\mathbf\s+([A-Za-z])', r'\\mathbf{\1}', expr)
    expr = re.sub(r'\\(mathcal|mathrm|mathsf)\s+([A-Za-z])',r'\\\1{\2}',expr)
    expr = expr.replace(r'\limits','')
    expr = expr.replace(r'\\boxed{', r'\\mathrm{') # MathText lacks \boxed; preserve readable equation
    # The matplotlib mathtext grammar uses \mathrm but not every LaTeX macro.
    if not expr:
        return b''
    out = io.BytesIO()
    math_to_image('$' + expr + '$', out, dpi=155, format='png', color=INK, prop=None)
    return out.getvalue()


class MathDocument(QScrollArea):
    """Readable, document-style solution viewer with separate typeset equations.

    This only displays supplied content; it does not generate or verify physics.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet('QScrollArea{background:white;border:none;}')
        self.canvas = QWidget()
        self.canvas.setStyleSheet('background:white;')
        self.v = QVBoxLayout(self.canvas)
        self.v.setContentsMargins(32, 22, 36, 30)
        self.v.setSpacing(8)
        self.setWidget(self.canvas)
        self.set_text('')

    def _paragraph(self, text, kind='body'):
        text=text.strip()
        if not text:return
        styles={
            'title': ('20px', '#18202b', '700', '14px 0 7px 0'),
            'heading': ('15px', '#18202b', '650', '14px 0 4px 0'),
            'body': ('13px', '#283342', '400', '3px 0 3px 0'),
            'note': ('12px', '#59697d', '400', '6px 0 2px 0'),
        }
        size,color,weight,margin=styles[kind]
        # Escape arbitrary input, then permit only simple emphasis (`**...**`, `...`).
        safe=html.escape(text).replace('\n',' ')
        safe=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',safe)
        safe=re.sub(r'`([^`]+)`',r'<code>\1</code>',safe)
        w=QLabel()
        w.setWordWrap(True)
        w.setTextFormat(Qt.TextFormat.RichText)
        w.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        w.setText(f'<div style="font-family:Segoe UI; font-size:{size};color:{color};font-weight:{weight};line-height:145%;margin:{margin};">{safe}</div>')
        w.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        self.v.addWidget(w)

    def _rule(self):
        line=QFrame();line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet('color:#e7ebf1;background:#e7ebf1;border:none;max-height:1px;')
        self.v.addSpacing(8)
        self.v.addWidget(line)
        self.v.addSpacing(5)

    def set_text(self, text):
        while self.v.count():
            item=self.v.takeAt(0)
            if item.widget():item.widget().deleteLater()
        # Display math is atomic and cannot be damaged by prose/markdown layout.
        parts=re.split(r'(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\])',text)
        for part in parts:
            if not part.strip():continue
            if part.startswith('$$'):
                self.math_item(part[2:-2])
                continue
            if part.startswith('\\['):
                self.math_item(part[2:-2])
                continue
            for raw in re.split(r'\n\s*\n',part):
                block=raw.strip()
                if not block:continue
                for line in block.splitlines():
                    line=line.strip()
                    if not line:continue
                    if line=='---':self._rule()
                    elif line.startswith('## '):self._paragraph(line[3:],'heading')
                    elif line.startswith('# '):self._paragraph(line[2:],'title')
                    elif line.startswith('> '):self._paragraph(line[2:],'note')
                    elif re.fullmatch(r'\$(.+)\$',line):self.math_item(line[1:-1],16)
                    else:self._paragraph(line)
        self.v.addStretch(1)

    def math_item(self, formula, fontsize=18):
        formula=formula.strip()
        if not formula:return
        matrix=re.search(r'^(.*?)\\left\[\s*\\begin\{matrix\}(.*?)\\end\{matrix\}\\right\](.*)$',formula,re.S)
        if matrix:
            rows=[row.strip() for row in re.split(r'\\\\',matrix.group(2)) if row.strip()]
            if all('&' not in row for row in rows):
                self.math_item(matrix.group(1)+r'\left('+r',\ '.join(rows)+r'\right)'+matrix.group(3),fontsize)
            else:
                if matrix.group(1):self._paragraph(matrix.group(1))
                for i,row in enumerate(rows):
                    self._paragraph('Matrix, række '+str(i+1))
                    self.math_item(r'\left('+r',\ '.join(row.split('&'))+r'\right)',fontsize)
                if matrix.group(3):self._paragraph(matrix.group(3))
            return
        # MathText does not implement AMS cases. Display each physical branch
        # as a separate clean mathematical line, preserving the branch condition.
        m=re.search(r'^(.*?)\\begin\{cases\}(.*?)\\end\{cases\}(.*)$',formula,re.S)
        if m:
            prefix=m.group(1).strip().rstrip('=')
            rows=re.split(r'\\\\',m.group(2))
            if prefix:self._paragraph(prefix+' =','body')
            for row in rows:
                if not row.strip():continue
                parts=row.split('&',1)
                expression=parts[0].strip()
                if expression:self.math_item(expression,fontsize)
                if len(parts)>1:
                    condition=parts[1].strip()
                    condition=condition.replace(r'\text{for}', 'for').replace(r'\text{otherwise}','ellers')
                    condition=condition.replace(r'\:', ' ').replace(r'\geq','≥').replace(r'\leq','≤')
                    self._paragraph('Betingelse: '+condition,'note')
            return
        try:
            pix=QPixmap()
            if not pix.loadFromData(formula_png(formula,fontsize)):
                raise ValueError('Matematikbilledet kunne ikke læses')
            view=QLabel()
            view.setPixmap(pix)
            view.setMinimumWidth(pix.width()+8)
            view.setToolTip(formula)
            view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            view.setStyleSheet('background:transparent;padding:7px 2px 10px 8px;')
            self.v.addWidget(view)
        except Exception as e:
            self._paragraph('Kunne ikke vise matematik: '+formula+' ['+str(e)[:100]+']','note')


def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, chapter TEXT, body TEXT, updated TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, title TEXT, prompt TEXT, result TEXT, created TEXT)")
        if c.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
            examples = [
                ("Egne noter – startside", "Generelt", "# Mine EM1-noter\n\nHer kan jeg skrive og redigere noter.\n\nDen originale EM-formelsamling ligger under Kilder, så den ikke bliver ændret ved et uheld."),
                ("Gauss' lov – arbejdsnote", "2 Elektrostatik", "# Gauss' lov\n\nIntegralloven: ∮ E · da = Q_indesluttet / ε₀.\n\nMetoden kan bruges direkte til at bestemme E ved tilstrækkelig høj symmetri: sfærisk, cylindrisk eller plan.\n\nTilføj dine egne kommentarer her."),
                ("Dielektrika – arbejdsnote", "4 Dielektrika", "# Polarisation\n\nBundne ladninger: ρ_b = −∇·P og σ_b = P·n.\n\nD = ε₀ E + P, og ∮ D·da = Q_fri.\n\nTilføj egne udledninger og figurer her."),
            ]
            c.executemany("INSERT INTO notes (title,chapter,body,updated) VALUES (?,?,?,?)", [(t,ch,b,datetime.now().isoformat()) for t,ch,b in examples])


def label(text, size=12, bold=False, color=INK):
    w = QLabel(text)
    w.setWordWrap(True)
    w.setStyleSheet(f"color:{color};font-size:{size}px;font-weight:{700 if bold else 400};")
    return w


def header(title, subtitle=""):
    box = QWidget(); v = QVBoxLayout(box); v.setContentsMargins(0,0,0,12); v.setSpacing(3)
    v.addWidget(label(title, 25, True))
    if subtitle: v.addWidget(label(subtitle, 12, False, MUTED))
    return box


def card():
    w = QFrame(); w.setStyleSheet("QFrame{background:white;border:1px solid #dce1e9;border-radius:11px;}")
    return w


class PDFReader(QWidget):
    """Native Qt display of ORIGINAL PDF pages, not lossy extracted text.

    Uses PyMuPDF for rasterization, with no WebEngine/embedded browser.
    """
    def __init__(self, path=None, parent=None):
        super().__init__(parent)
        self.path = None
        self.document = None
        self.page_index = 0
        self.zoom = 1.25
        self._cache = {}
        vertical = QVBoxLayout(self); vertical.setContentsMargins(0,0,0,0)
        toolbar = QHBoxLayout()
        self.prev_btn=QPushButton('◀'); self.next_btn=QPushButton('▶')
        self.page_box=QSpinBox(); self.page_box.setMinimum(1); self.page_box.setMaximum(1)
        self.total=label('/ 0',11,False,MUTED)
        self.zoom_out=QPushButton('−'); self.zoom_in=QPushButton('+')
        self.zoom_label=label('125 %',11,False,MUTED)
        for widget in (self.prev_btn,self.page_box,self.total,self.next_btn,self.zoom_out,self.zoom_label,self.zoom_in):
            toolbar.addWidget(widget)
        toolbar.addStretch()
        vertical.addLayout(toolbar)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.page_view=QLabel('Vælg en PDF-side'); self.page_view.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.page_view.setStyleSheet('background: white; padding: 10px;')
        self.scroll.setWidget(self.page_view); vertical.addWidget(self.scroll,1)
        self.prev_btn.clicked.connect(lambda:self.goto(self.page_index))
        self.next_btn.clicked.connect(lambda:self.goto(self.page_index+2))
        self.page_box.valueChanged.connect(self.goto)
        self.zoom_out.clicked.connect(lambda:self.set_zoom(self.zoom/1.2))
        self.zoom_in.clicked.connect(lambda:self.set_zoom(self.zoom*1.2))
        if path:self.open_pdf(path)

    def open_pdf(self, path, page=1):
        path=Path(path)
        if not path.is_file():
            self.page_view.setText('PDF mangler: '+str(path)); return
        try:
            import fitz
            if self.document:self.document.close()
            self.document=fitz.open(str(path))
            self.path=path
            self._cache.clear()
            self.page_box.blockSignals(True)
            self.page_box.setMaximum(max(1,len(self.document)))
            self.page_box.blockSignals(False)
            self.total.setText('/ '+str(len(self.document)))
            self.goto(page)
        except Exception as exc:
            self.page_view.setText('PDF kunne ikke åbnes: '+str(exc))

    def set_zoom(self, value):
        self.zoom=max(0.65,min(2.8,value))
        self.zoom_label.setText(f'{round(self.zoom*100)} %')
        self._cache.clear()
        self.render()

    def goto(self, page):
        if not self.document:return
        self.page_index=max(0,min(len(self.document)-1,int(page)-1))
        self.page_box.blockSignals(True);self.page_box.setValue(self.page_index+1);self.page_box.blockSignals(False)
        self.render()

    def render(self):
        if not self.document:return
        try:
            key=(self.page_index,round(self.zoom,2))
            if key not in self._cache:
                import fitz
                page=self.document[self.page_index]
                pix=page.get_pixmap(matrix=fitz.Matrix(1.35*self.zoom,1.35*self.zoom),alpha=False)
                qimg=QImage(pix.samples,pix.width,pix.height,pix.stride,QImage.Format.Format_RGB888).copy()
                self._cache[key]=QPixmap.fromImage(qimg)
                if len(self._cache)>9:self._cache={key:self._cache[key]}
            self.page_view.setPixmap(self._cache[key])
            self.page_view.adjustSize()
        except Exception as exc:
            self.page_view.setText('PDF-side kunne ikke vises: '+str(exc))


class NotesPanel(QWidget):
    def __init__(self, compact=False, parent=None):
        super().__init__(parent); self.compact = compact; self.current_id=None; self.dirty=False
        lay=QVBoxLayout(self); lay.setContentsMargins(8,8,8,8); lay.setSpacing(8)
        lay.addWidget(label("Mine noter" if compact else "Notesamling", 18, True))
        self.search=QLineEdit(); self.search.setPlaceholderText("Søg i noter ..."); lay.addWidget(self.search)
        self.chapters=QComboBox(); self.chapters.addItems(["Alle emner", "Generelt", "1 Vektoranalyse", "2 Elektrostatik", "3 Specialteknikker", "4 Dielektrika", "5 Magnetostatik", "6 Magnetiske medier", "7 Elektrodynamik"])
        lay.addWidget(self.chapters)
        self.list=QListWidget(); self.list.setMaximumHeight(160 if compact else 260); lay.addWidget(self.list)
        top=QHBoxLayout(); self.new=QPushButton("+ Ny note"); self.delete=QPushButton("Slet"); top.addWidget(self.new); top.addWidget(self.delete); lay.addLayout(top)
        self.title=QLineEdit(); self.title.setPlaceholderText("Notetitel"); lay.addWidget(self.title)
        self.editor=QPlainTextEdit(); self.editor.setPlaceholderText("Skriv noter her. Matematik kan indsættes som LaTeX eller almindelig tekst.")
        self.editor.setMinimumHeight(180)
        self.math_preview=MathDocument()
        math_tools=QHBoxLayout()
        for caption,insert in [("Brøk",r"\[\frac{a}{b}\]"),("Integral",r"\[\int_a^b f(x)\,dx\]"),("Vektor",r"\[\mathbf{E}=E\hat{\mathbf{r}}\]"),("Gauss",r"\[\oint_S\mathbf{E}\cdot d\mathbf{a}=\frac{Q_{\mathrm{enc}}}{\varepsilon_0}\]")]:
            btn=QPushButton(caption);btn.setToolTip("Indsæt LaTeX-formel i noten")
            btn.clicked.connect(lambda checked=False, t=insert: self.insert_math(t))
            math_tools.addWidget(btn)
        math_tools.addStretch()
        lay.addLayout(math_tools)
        self.note_tabs=QTabWidget();self.note_tabs.addTab(self.editor,"Redigér");self.note_tabs.addTab(self.math_preview,"Matematikvisning")
        lay.addWidget(self.note_tabs,1)
        self.note_tabs.currentChanged.connect(self.update_math_preview)
        bottom=QHBoxLayout(); self.status=label("",11,False,MUTED); bottom.addWidget(self.status,1)
        self.save=QPushButton("Gem nu"); bottom.addWidget(self.save); lay.addLayout(bottom)
        self.search.textChanged.connect(self.reload); self.chapters.currentTextChanged.connect(self.reload)
        self.list.currentItemChanged.connect(self.load_note)
        self.new.clicked.connect(self.new_note); self.delete.clicked.connect(self.delete_note); self.save.clicked.connect(self.commit)
        self.editor.textChanged.connect(self.schedule_save); self.title.textChanged.connect(self.schedule_save)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(700); self.timer.timeout.connect(self.commit)
        self.reload()

    def reload(self,*_):
        key=self.search.text().lower(); chapter=self.chapters.currentText()
        with sqlite3.connect(DB) as c: rows=c.execute("SELECT id,title,chapter,body FROM notes ORDER BY updated DESC").fetchall()
        self.list.blockSignals(True); self.list.clear()
        for note_id,title,ch,body in rows:
            if key not in (title+" "+(body or "")).lower(): continue
            if chapter != "Alle emner" and ch!=chapter: continue
            item=QListWidgetItem(title); item.setData(Qt.ItemDataRole.UserRole,note_id); self.list.addItem(item)
        self.list.blockSignals(False)
        if self.current_id is None and self.list.count(): self.list.setCurrentRow(0)

    def load_note(self,item,previous=None):
        if not item: return
        self.timer.stop()
        note_id=item.data(Qt.ItemDataRole.UserRole)
        with sqlite3.connect(DB) as c: row=c.execute("SELECT title,body FROM notes WHERE id=?",(note_id,)).fetchone()
        if not row: return
        self.current_id=note_id; self.dirty=False
        self.title.blockSignals(True); self.editor.blockSignals(True)
        self.title.setText(row[0]); self.editor.setPlainText(row[1] or "")
        self.title.blockSignals(False); self.editor.blockSignals(False)
        self.status.setText("Redigérbar note · lokal lagring"); self.update_math_preview()

    def insert_math(self, latex):
        self.note_tabs.setCurrentIndex(0)
        cursor=self.editor.textCursor()
        cursor.insertText("\n"+latex+"\n")
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def update_math_preview(self,*_):
        self.math_preview.set_text(self.editor.toPlainText())

    def schedule_save(self):
        if self.current_id:
            self.dirty=True
            self.status.setText("Gemmer ...")
            self.timer.start()

    def commit(self):
        if not self.current_id or not self.dirty: return
        with sqlite3.connect(DB) as c:
            c.execute("UPDATE notes SET title=?,body=?,updated=? WHERE id=?", (self.title.text().strip() or "Uden titel",self.editor.toPlainText(),datetime.now().isoformat(),self.current_id))
        self.dirty=False
        self.status.setText("Gemt lokalt ✓")
        # Do not refresh list on each keystroke; avoids moving the current selection.

    def new_note(self):
        self.commit()
        ch=self.chapters.currentText(); ch="Generelt" if ch=="Alle emner" else ch
        with sqlite3.connect(DB) as c:
            cur=c.execute("INSERT INTO notes(title,chapter,body,updated) VALUES(?,?,?,?)",("Ny note",ch,"",datetime.now().isoformat()))
            self.current_id=cur.lastrowid; self.dirty=False
        self.reload()
        for idx in range(self.list.count()):
            if self.list.item(idx).data(Qt.ItemDataRole.UserRole)==self.current_id: self.list.setCurrentRow(idx);break
        self.title.setFocus(); self.title.selectAll()

    def delete_note(self):
        if self.current_id is None:return
        if QMessageBox.question(self,"Slet note","Vil du slette den valgte note? ")!=QMessageBox.StandardButton.Yes:return
        with sqlite3.connect(DB) as c:c.execute("DELETE FROM notes WHERE id=?",(self.current_id,))
        self.current_id=None; self.dirty=False; self.title.clear(); self.editor.clear(); self.reload()

    def insert_text_as_note(self,title,text,chapter="Generelt"):
        with sqlite3.connect(DB) as c:c.execute("INSERT INTO notes(title,chapter,body,updated) VALUES (?,?,?,?)",(title,chapter,text,datetime.now().isoformat()))
        self.current_id=None; self.reload()



# Indexed source pages are bundled at build time, preserving PDF originals.
# Rendering plain extracted text is a reading/search aid, not a faithful typesetting
# of mathematical formulas. The original PDF remains authoritative.
# Topic-driven retrieval is intentionally independent of the unfinished physics solver.
# Suggestions are references, not evidence that a mathematical solution is valid.
TOPIC_RULES = [
    ("Gauss og cylindersymmetri", [r"\bgauss\b", r"cylinder", r"cylindrisk", r"\blinje\s*ladning", r"linjeladning"],
     ["gauss", "cylinder", "linjeladning", "symmetri"]),
    ("Gauss og sfærisk symmetri", [r"\bkugle", r"sfær", r"spherical", r"kugleskal"],
     ["kugle", "gauss", "sfær"]),
    ("Polarisation og dielektrika", [r"polarisation", r"polariser", r"dielektr", r"\bbundne\b", r"\bD.felt\b"],
     ["polarisation", "dielektr", "bundet", "d-felt"]),
    ("Potentiale og randværdier", [r"potential", r"laplace", r"poisson", r"randbeting", r"spejl", r"lederplan"],
     ["potential", "laplace", "poisson", "spejl"]),
    ("Ampère og magnetfelter", [r"amp[eè]re", r"magnetfelt", r"str[oø]m", r"biot", r"solenoid", r"toroid"],
     ["ampere", "ampère", "biot", "magnet", "strøm"]),
    ("Faraday og induktion", [r"faraday", r"inducer", r"induktion", r"magnetisk flux", r"elektromotor"],
     ["faraday", "induktion", "flux", "bevægelig"]),
    ("Coulomb og ladningsfordelinger", [r"coulomb", r"punktladning", r"fladeladning", r"ladningsfordeling"],
     ["coulomb", "punktladning", "ladningsfordeling", "separationsvektor"]),
    ("Vektorregning og integration", [r"gradient", r"divergens", r"rotation", r"integral", r"koordinatsystem"],
     ["gradient", "divergens", "integral", "koordinater"]),
]


def related_note_pages(prompt, entries, limit=6):
    """Return ranked, source-anchored PDF pages. Never claim physics verification."""
    text=prompt.casefold().strip()
    if not text:return []
    words={w for w in re.findall(r"[a-zæøå]{4,}", text) if w not in {
        'bestem','beregn','findes','givet','hvilket','hvilken','elektriske',
        'feltet','radius','kendes','homogen','denne','med','hvor','skal',
        'vis','mellem','udenfor','indenfor','udledning','opgaven'}}
    topic_terms=[]
    topics=[]
    for topic,patterns,terms in TOPIC_RULES:
        if any(re.search(pattern,text) for pattern in patterns):
            topics.append(topic);topic_terms.extend(terms)
    scored=[]
    for page in entries:
        title=page.get('title','').casefold()
        chapter=page.get('chapter','').casefold()
        body=page.get('body','').casefold()
        # Bound score contributions so very long pages don't dominate.
        title_score=sum(8 for w in words if w in title)
        topic_score=sum(12 for w in topic_terms if w in title)
        body_score=sum(2 for w in words if w in body)
        tag_score=sum(3 for w in topic_terms if w in chapter)
        score=title_score+topic_score+min(body_score,14)+tag_score
        if score>0:scored.append((score,page))
    scored.sort(key=lambda x:(-x[0],x[1].get('group',''),x[1].get('page',0)))
    # Avoid filling all suggestions with adjacent pages of the same source.
    result=[];seen=set()
    for score,page in scored:
        key=page.get('id')
        if key not in seen:
            result.append({'entry':page,'score':score});seen.add(key)
        if len(result)>=limit:break
    return {'topics':topics, 'results':result}


class SourceNotesPanel(QWidget):
    def __init__(self, create_editable, parent=None):
        super().__init__(parent)
        self.create_editable = create_editable
        self.entries = json.loads((RESOURCE_DIR / "note_index.json").read_text(encoding="utf-8"))
        self.current = None
        lay = QVBoxLayout(self); lay.setContentsMargins(8,8,8,8);lay.setSpacing(8)
        lay.addWidget(label("Dine eksisterende EM1-noter", 17, True))
        lay.addWidget(label("Søg i formelsamlingen og geometriarket. PDF-originalen bevarer figurer og matematik.",11,False,MUTED))
        self.search = QLineEdit();self.search.setPlaceholderText("Søg fx Gauss, spejling, cylinder, Faraday...");lay.addWidget(self.search)
        self.topic = QComboBox();self.topic.addItems(["Alle emner", "Formelsamling", "Geometri og regneteknik"]);lay.addWidget(self.topic)
        self.found=label('',11,False,MUTED);lay.addWidget(self.found)
        self.list=QListWidget();self.list.setMinimumHeight(155);lay.addWidget(self.list,1)
        self.head=label('Vælg et opslag',14,True);lay.addWidget(self.head)
        self.reader=PDFReader();lay.addWidget(self.reader,4)
        bar=QHBoxLayout()
        self.open_pdf=QPushButton('Åbn original PDF-side')
        self.copy_note=QPushButton('Lav redigerbar kopi')
        bar.addWidget(self.open_pdf);bar.addWidget(self.copy_note);lay.addLayout(bar)
        lay.addWidget(label('Original PDF-side · matematik og figurer vises med deres oprindelige layout.',10,False,MUTED))
        self.search.textChanged.connect(self.reload)
        self.topic.currentTextChanged.connect(self.reload)
        self.list.currentItemChanged.connect(self.select)
        self.open_pdf.clicked.connect(self.open_source)
        self.copy_note.clicked.connect(self.make_editable)
        self.reload()

    def reload(self,*_):
        q=self.search.text().strip().casefold()
        group=self.topic.currentText()
        previous=self.current['id'] if self.current else None
        self.list.blockSignals(True)
        self.list.clear()
        self.visible=[]
        for item in self.entries:
            if group!='Alle emner' and item['group']!=group:continue
            if q and q not in (item['title']+' '+item['body']+' '+item['chapter']).casefold():continue
            self.visible.append(item)
            it=QListWidgetItem(f"{item['title']}  ·  s. {item['page']}")
            it.setData(Qt.ItemDataRole.UserRole,item['id'])
            it.setToolTip(item['group']+' · '+item['chapter'])
            self.list.addItem(it)
        self.list.blockSignals(False)
        self.found.setText(f"{len(self.visible)} opslag")
        target=next((i for i,r in enumerate(self.visible) if r['id']==previous),0)
        if self.visible:self.list.setCurrentRow(target);self.show_entry(self.visible[target])
        else:self.current=None;self.head.setText('Ingen opslag');self.reader.page_view.clear()

    def select(self,item,previous=None):
        if item is None:return
        match=next((r for r in self.visible if r['id']==item.data(Qt.ItemDataRole.UserRole)),None)
        if match:self.show_entry(match)

    def show_entry(self,entry):
        self.current=entry
        self.head.setText(f"{entry['group']}  ·  side {entry['page']}")
        self.reader.open_pdf(RESOURCE_DIR/entry['file'],int(entry['page']))

    def open_source(self):
        if not self.current:return
        path=RESOURCE_DIR/self.current['file']
        if not path.exists():QMessageBox.warning(self,'Fil mangler',str(path));return
        url=QUrl.fromLocalFile(str(path));url.setFragment('page='+str(self.current['page']))
        QDesktopServices.openUrl(url)

    def make_editable(self):
        if not self.current:return
        item=self.current
        # User can edit only an explicit copy, never silently mutate source material.
        text=(f"# {item['title']}\n\n"
              f"Kilde: {item['group']}, side {item['page']} ({item['file']})\n"
              "OBS: Tekst udtrukket fra PDF – kontroller figurer og formler mod originalen.\n\n"
              +item['body'])
        self.create_editable(item['title']+' (min kopi)',text,item['chapter'])

    def focus_source(self,entry_id):
        target=next((x for x in self.entries if x['id']==entry_id),None)
        if target is None:return False
        self.topic.setCurrentIndex(0)
        self.search.clear()
        for idx,entry in enumerate(self.visible):
            if entry['id']==entry_id:
                self.list.setCurrentRow(idx)
                self.show_entry(entry)
                return True
        return False

    def suggest_for(self,prompt):
        """Open the highest-ranked PDF source page, where available."""
        ranking=related_note_pages(prompt,self.entries)
        results=ranking['results'] if ranking else []
        if not results:return False
        return self.focus_source(results[0]['entry']['id'])


class IntegratedNotes(QWidget):
    """Same local editable notes and source index in both full-page and sidebar."""
    def __init__(self,compact=False,parent=None):
        super().__init__(parent)
        self.tabs=QTabWidget()
        self.edits=NotesPanel(compact=compact)
        self.sources=SourceNotesPanel(self.create_copy)
        self.tabs.addTab(self.edits,'Mine noter')
        self.tabs.addTab(self.sources,'Kilder · søg')
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.addWidget(self.tabs)

    def create_copy(self,title,text,chapter):
        self.edits.insert_text_as_note(title,text,chapter)
        self.tabs.setCurrentIndex(0)
        self.edits.current_id=None
        self.edits.reload()
        # select the newest matching note immediately
        for i in range(self.edits.list.count()):
            if self.edits.list.item(i).text()==title:
                self.edits.list.setCurrentRow(i)
                break

    def insert_text_as_note(self,title,text,chapter='Generelt'):
        self.edits.insert_text_as_note(title,text,chapter)

    def commit(self):self.edits.commit()
    def reload(self):self.edits.reload();self.sources.reload()
    @property
    def current_id(self):return self.edits.current_id
    @current_id.setter
    def current_id(self,value):self.edits.current_id=value

EXAMPLES = {
    "Uendelig cylinder (Gauss)": {
        "prompt":"En uendelig lang massiv cylinder med radius R og homogen volumenladningstæthed ρ er omgivet af vakuum. Bestem E(s) for s<R og s>R.",
        "result":r"""# Elektrisk felt
Indenfor, s < R:
\[\mathbf{E}(s)=\frac{\rho s}{2\varepsilon_0}\hat{\mathbf{s}}\]
Udenfor, s > R:
\[\mathbf{E}(s)=\frac{\rho R^2}{2\varepsilon_0s}\hat{\mathbf{s}}\]""",
        "derive":r"""# Gauss’ lov
Ved cylindersymmetri er feltet radialt.
\[\oint_S\mathbf E\cdot d\mathbf a=\frac{Q_{\mathrm{enc}}}{\varepsilon_0}\]
# Indenfor cylinderen
\[Q_{\mathrm{enc}}=\rho\pi s^2L\]
\[E(s)2\pi sL=\frac{\rho\pi s^2L}{\varepsilon_0}\]
\[E(s)=\frac{\rho s}{2\varepsilon_0}\]
# Udenfor cylinderen
\[Q_{\mathrm{enc}}=\rho\pi R^2L\]
\[E(s)=\frac{\rho R^2}{2\varepsilon_0s}\]""",
        "explain":"Den cylindriske symmetri gør feltet radialt. Indenfor vokser den omsluttede ladning med s², mens Gauss-fladens areal vokser med s. Udenfor er den omsluttede ladning konstant, så feltet aftager som 1/s. Retningen bestemmes af fortegnet på ρ.",
        "method":"Gauss' lov · cylindersymmetri",
    },
    "Uendelig linjeladning": {
        "prompt":"En uendelig lang, tynd ledning har en homogen linjeladningstæthed λ. Bestem det elektriske felt i afstanden s.",
        "result":r"\[\mathbf E(s)=\frac{\lambda}{2\pi\varepsilon_0s}\hat{\mathbf s}\]",
        "derive":r"""# Gauss-cylinder
\[Q_{\mathrm{enc}}=\lambda L\]
\[E(s)2\pi sL=\frac{\lambda L}{\varepsilon_0}\]
\[E(s)=\frac{\lambda}{2\pi\varepsilon_0s}\]""",
        "explain":"En uendelig linjeladning har cylindersymmetri. Fluxen gennem endefladerne er nul; kun cylinderens krumme side bidrager.",
        "method":"Gauss' lov · linjeladning",
    },
    "Punktladning (Coulomb)": {
        "prompt":"En punktladning q er placeret i origo. Bestem det elektriske felt i afstanden r.",
        "result":r"\[\mathbf E(r)=\frac{q}{4\pi\varepsilon_0r^2}\hat{\mathbf r}\]",
        "derive":r"""# Sfærisk symmetri
\[E(r)4\pi r^2=\frac{q}{\varepsilon_0}\]
\[E(r)=\frac{q}{4\pi\varepsilon_0r^2}\]""",
        "explain":"En isoleret punktladning giver et radialt felt. Feltets styrke aftager med kvadratet på afstanden; fortegnet på q giver retningen.",
        "method":"Coulomb / Gauss · sfærisk symmetri",
    },
}


# A solution is a sequence of *justified* physical/mathematical steps, rather
# than an unstructured answer string. The future Codex backend can return the
# same schema. All entries below are manually reviewed illustrative examples.
EXPLANATION_STEPS = {
    "Uendelig cylinder (Gauss)": [
        {"title":"1. Aflæs geometrien og vælg metode",
         "why":"Jeg bruger Gauss' lov, fordi cylinderen er uendelig lang, har konstant ladningstæthed og derfor har fuld rotations- og translationssymmetri. Feltet må være radialt og afhænge kun af afstanden s fra aksen. På en koaksial Gauss-cylinder er feltets størrelse konstant på sidefladen; et direkte Coulomb-integral ville være mere besværligt.",
         "math":r"\[\mathbf{E}(s)=E(s)\hat{\mathbf{s}}\]",
         "check":"Forudsætninger: uendelig cylinder, homogen volumenladning og vakuum. Uden disse antagelser kan Gauss' lov stadig gælde, men metoden bliver ikke nødvendigvis simpel."},
        {"title":"2. Vælg en passende Gauss-flade",
         "why":"Jeg vælger en tænkt koaksial cylinder med radius s og længde L. På endefladerne er feltet parallelt med fladerne, så fluxen er nul. På den krumme sideflade er feltet vinkelret på fladen og har konstant størrelse.",
         "math":r"\[\oint_S\mathbf{E}\cdot d\mathbf{a}=E(s)\,2\pi sL=\frac{Q_{\mathrm{enc}}}{\varepsilon_0}\]",
         "check":"Radius s er afstanden til det punkt, hvor vi søger feltet. R er cylinderens faste fysiske radius."},
        {"title":"3. Beregn omsluttet ladning indenfor (s<R)",
         "why":"Når Gauss-fladen ligger inde i cylinderen, er kun volumenet inden for radius s omsluttet. Ladningen er volumen gange den konstante ladningstæthed.",
         "math":r"\[Q_{\mathrm{enc}}=\rho\,\pi s^2 L\]",
         "check":"Her bruger vi volumenladningstæthed ρ med enheden C/m³, ikke en flade- eller linjeladningstæthed."},
        {"title":"4. Isolér feltet indenfor (s<R)",
         "why":"Jeg indsætter den omsluttede ladning i Gauss' lov og forkorter de fælles faktorer. Feltet vokser lineært med s, fordi Q_enc vokser som s², mens sidefladens areal vokser som s.",
         "math":r"\[E(s)\,2\pi sL=\frac{\rho\pi s^2L}{\varepsilon_0}\]"+"\n"+r"\[\mathbf{E}(s)=\frac{\rho s}{2\varepsilon_0}\hat{\mathbf{s}}\]",
         "check":"Ved s→0 går feltet mod nul, som symmetrien kræver."},
        {"title":"5. Beregn feltet udenfor (s>R)",
         "why":"Udenfor omslutter Gauss-fladen hele den fysiske cylinders tværsnit. Ladningen vokser derfor ikke længere med s. Til gengæld vokser fluxarealet fortsat med s, så feltet aftager som 1/s.",
         "math":r"\[Q_{\mathrm{enc}}=\rho\pi R^2L\]"+"\n"+r"\[\mathbf{E}(s)=\frac{\rho R^2}{2\varepsilon_0s}\hat{\mathbf{s}}\]",
         "check":"Indsættes s=R i begge udtryk, fås ρR/(2ε₀). Det elektriske felt er kontinuerligt ved randen, da der ikke er en særskilt overfladeladning."},
        {"title":"6. Kontrollér fortegn og enheder",
         "why":"Den radiale enhedsvektor peger væk fra aksen. For ρ>0 peger E udad; for ρ<0 peger E indad, fordi fortegnet indgår i udtrykket.",
         "math":r"\[\left[\frac{\rho s}{\varepsilon_0}\right]=\mathrm{N/C}\]",
         "check":"Kontrollen gælder under de angivne antagelser og er ikke en erstatning for en generel symbolsk verifikator."},
    ],
    "Uendelig linjeladning": [
        {"title":"1. Vælg Gauss ud fra symmetrien", "why":"Jeg bruger Gauss' lov, fordi en uendelig, ensartet linjeladning er uforandret ved rotation om ledningen og forskydning langs den. Feltet er derfor radialt og afhænger kun af s.", "math":r"\[\mathbf E(s)=E(s)\hat{\mathbf s}\]", "check":"En endelig ledning har ikke samme translationssymmetri; så kan vi ikke bruge dette enkle udtryk."},
        {"title":"2. Vælg Gauss-cylinder og find flux", "why":"Jeg lægger en tænkt cylinder koaksialt med ledningen. Der er ingen flux gennem endefladerne, da E ligger i deres plan. Kun den krumme sideflade bidrager.", "math":r"\[\oint\mathbf E\cdot d\mathbf a=E(s)\,2\pi sL\]", "check":"Fladens længde L kan vælges vilkårligt og skal bortfalde i resultatet."},
        {"title":"3. Find ladning og isolér feltet", "why":"En linjeladningstæthed λ er ladning pr. længdeenhed. Den omsluttede ladning er derfor λL. Jeg indsætter i Gauss' lov og forkorter L.", "math":r"\[Q_{\mathrm{enc}}=\lambda L\]"+"\n"+r"\[\mathbf E(s)=\frac{\lambda}{2\pi\varepsilon_0s}\hat{\mathbf s}\]", "check":"Feltet aftager som 1/s, og fortegnet på λ bestemmer retningen."},
    ],
    "Punktladning (Coulomb)": [
        {"title":"1. Identificér punktladning og metode", "why":"Jeg bruger Coulombs lov, fordi kilden er en enkelt punktladning, og observationspunktets afstand r er givet. Alternativt kan Gauss' lov bruges direkte på grund af den sfæriske symmetri.", "math":r"\[\mathbf E(r)=E(r)\hat{\mathbf r}\]", "check":"Feltet er radialt; et eventuelt negativt q vender retningen."},
        {"title":"2. Indsæt i Coulombs lov", "why":"Afstanden fra ladningen i origo til feltpunktet er r. Coulombs lov giver feltets styrke og retning i ét trin.", "math":r"\[\mathbf E(r)=\frac{q}{4\pi\varepsilon_0r^2}\hat{\mathbf r}\]", "check":"Feltet aftager som 1/r² og er ikke defineret i r=0, hvor idealiseringen placerer punktladningen."},
        {"title":"3. Uafhængig kontrol med Gauss' lov", "why":"Som kontrol kan jeg vælge en kugleflade med radius r. Feltet er konstant på kuglen og parallelt med dens udadrettede normal.", "math":r"\[E(r)\,4\pi r^2=\frac{q}{\varepsilon_0}\]", "check":"Dette giver samme resultat som Coulombs lov og bekræfter symmetriargumentet."},
    ],
}


def format_reasoned_steps(steps, include_reasons=True):
    """Common structured format for demos and eventual backend-produced steps."""
    out=["# Udledning med fysiske begrundelser" if include_reasons else "# Matematisk udledning"]
    for step in steps:
        out.append("\n# "+step["title"])
        if include_reasons and step.get("why"):
            out.append("Hvorfor: "+step["why"])
        if step.get("math"):
            out.append(step["math"])
        if include_reasons and step.get("check"):
            out.append("Kontrol: "+step["check"])
    return "\n".join(out)


def format_full_explanation(steps):
    return format_reasoned_steps(steps, include_reasons=True)


class RelatedNotesBox(QFrame):
    """A simple suggestion strip: click a result to open its exact source page."""
    def __init__(self, open_callback, parent=None):
        super().__init__(parent)
        self.setObjectName('related-notes')
        self.setStyleSheet("QFrame#related-notes{background:#eef3fc;border:1px solid #d6e2f5;border-radius:9px;}")
        self.open_callback=open_callback
        self.entries=json.loads((RESOURCE_DIR/'note_index.json').read_text(encoding='utf-8'))
        v=QVBoxLayout(self);v.setContentsMargins(12,9,12,9);v.setSpacing(5)
        heading=QHBoxLayout()
        heading.addWidget(label('Relaterede noter',13,True))
        self.context=label('Ingen opgave indsat',10,False,MUTED)
        heading.addWidget(self.context,1)
        v.addLayout(heading)
        self.info=label('Indsæt en opgavetekst for at finde opslag i dine PDF-noter.',11,False,MUTED)
        v.addWidget(self.info)
        self.buttons=[]
        for _ in range(4):
            b=QPushButton('');b.setStyleSheet('text-align:left;padding:6px 9px;')
            b.hide();v.addWidget(b);self.buttons.append(b)
        self.refresh('')

    def refresh(self,prompt):
        rank=related_note_pages(prompt,self.entries)
        items=rank['results'] if rank else []
        topics=rank['topics'] if rank else []
        self.context.setText('Forslag ud fra opgavetekst · ikke fagligt verificeret')
        self.info.setText(('Emner: '+', '.join(topics[:2]) if topics else 'Søger ud fra ord i opgaveteksten') if items else 'Ingen sikre tekstmatch. Søg manuelt under Kilder · søg.')
        for i,b in enumerate(self.buttons):
            if i<len(items):
                entry=items[i]['entry'];b.setText(f"{entry['group']} · s. {entry['page']} · {entry['title'][:64]}")
                try:b.clicked.disconnect()
                except (RuntimeError,TypeError):pass
                b.clicked.connect(lambda checked=False,k=entry['id']:self.open_callback(k))
                b.show()
            else:b.hide()


def _as_text(value):
    if value is None:return ''
    if isinstance(value,str):return value
    if isinstance(value,(int,float,bool)):return str(value)
    if isinstance(value,list):return ', '.join(_as_text(x) for x in value)
    if isinstance(value,dict):return ', '.join(f'{k}: {_as_text(v)}' for k,v in value.items())
    return str(value)


def present_backend_json(payload):
    """Conservative DISPLAY adapter; cannot certify backend computations.

    The schema in docs/VIEWER_EXCHANGE.md is the exact stable viewer contract.
    Other JSON dictionaries are explicitly rejected, not guessed into physics.
    """
    if not isinstance(payload,dict) or payload.get('viewer_schema')!='em1.desktop.solution.v1':
        raise ValueError('Ukendt JSON-format. Se docs/VIEWER_EXCHANGE.md for eksportformatet.')
    status=payload.get('status','unverified')
    if status not in ('verified','assumptions','partial','unsolved','unverified'):
        raise ValueError('Ukendt verifikationsstatus: '+str(status))
    steps=payload.get('steps',[])
    if not isinstance(steps,list):raise ValueError('steps skal være en liste')
    if len(steps)>500:raise ValueError('For mange løsningstrin')
    result=payload.get('result',{})
    if not isinstance(result,dict):raise ValueError('result skal være et objekt')
    heading=payload.get('title','Importeret EM1-besvarelse')
    interpret=payload.get('interpretation',{})
    if not isinstance(interpret,dict):raise ValueError('interpretation skal være et objekt')
    answer='# '+str(heading)+'\n'
    symbolic=result.get('symbolic_latex','')
    if symbolic: answer+='\\['+str(symbolic)+'\\]\n'
    extra_latex=result.get('extra_latex',[])
    if isinstance(extra_latex,list):
        for extra in extra_latex[:10]:
            if isinstance(extra,str) and extra.strip():answer+='\\['+extra+'\\]\n'
    if result.get('numeric_text'):answer+='Numerisk: '+_as_text(result['numeric_text'])+'\n'
    if result.get('units'):answer+='Enhed: '+_as_text(result['units'])+'\n'
    if not symbolic and not result.get('numeric_text'):answer+='Intet verificeret slutresultat leveret.\n'
    derivation=['# Udledning'];explanation=['# Fysisk forklaring']
    for ix,step in enumerate(steps):
        if not isinstance(step,dict):raise ValueError('Løsningstrin skal være objekter')
        title=_as_text(step.get('title','Trin '+str(ix+1)))
        reason=_as_text(step.get('reason','')).strip()
        eq=step.get('latex','')
        check=_as_text(step.get('check','')).strip()
        substitution=_as_text(step.get('substitution','')).strip()
        operation=_as_text(step.get('operation','')).strip()
        # A single continuous textbook-like derivation, not a collection of field labels.
        if ix:derivation.append('---');explanation.append('---')
        derivation.append('## '+title)
        explanation.append('## '+title)
        if reason:derivation.append(reason);explanation.append(reason)
        if substitution:derivation.append(substitution);explanation.append(substitution)
        if operation:derivation.append(operation);explanation.append(operation)
        if eq:derivation.append(str(eq) if str(eq).lstrip().startswith('\\[') else '\\['+str(eq)+'\\]')
        if check:
            derivation.append('> Kontrol: '+check)
            explanation.append('> Kontrol: '+check)
    if status in ('unsolved','partial'):
        alert='Backend har ikke leveret en fuldt verificeret løsning.'
        details=payload.get('warnings') or []
        if details:
            alert+='\n\n'+ '\n\n'.join(str(x) for x in details[:8])
        answer+='\n\n'+alert
        derivation.append(alert)
        explanation.append(alert)
    audit=payload.get('audit','')
    if audit:
        explanation.append('---')
        explanation.append(str(audit))
        if status in ('verified','assumptions'):
            answer+='\n\nKontrolstatus: Se fanen Forklaring for beståede kontroller og gyldighedsbetingelser.\n'
    interp='Metode: '+html.escape(_as_text(interpret.get('method','ikke angivet')))+'<br>'
    interp+='Geometri: '+html.escape(_as_text(interpret.get('geometry','ikke angivet')))+'<br>'
    interp+='Status: '+html.escape(status)
    if payload.get('warnings'):interp+='<br>Bemærk: '+html.escape(_as_text(payload['warnings']))
    return {'result':answer,'derive':'\n\n'.join(derivation),'explain':'\n\n'.join(explanation),
            'interp':interp, 'status':status,'warnings':payload.get('warnings',[])}


class SolverPage(QWidget):
    """One display path for examples and imported adapter JSON.

    This is deliberately not an autonomous physics solver.
    """
    def __init__(self, add_note_callback, open_source_callback, parent=None):
        super().__init__(parent)
        self.add_note_callback=add_note_callback
        self.last_payload=None
        root=QVBoxLayout(self); root.setContentsMargins(26,19,26,20);root.setSpacing(11)
        top=QHBoxLayout()
        top.addWidget(header('Opgaveløser','Indsæt opgave → løs offline → se metode og udledning.'),1)
        self.notes_button=QPushButton('Vis noter'); top.addWidget(self.notes_button)
        root.addLayout(top)
        row=QHBoxLayout()
        row.addWidget(label('Testbesvarelse',12,True))
        self.sample=QComboBox();self.sample.addItem('Vælg testopgave …','')
        for path in sorted((ROOT/'examples'/'viewer_cases').glob('*.json')):
            try:
                item=json.loads(path.read_text(encoding='utf-8'))
                self.sample.addItem(item.get('title',path.stem),str(path))
            except Exception:pass
        row.addWidget(self.sample,1)
        self.load_test=QPushButton('Vis testbesvarelse');self.load_test.setObjectName('primary');row.addWidget(self.load_test)
        root.addLayout(row)
        self.prompt=QPlainTextEdit();self.prompt.setPlaceholderText('Indsæt din EM1-opgavetekst her, og tryk Løs opgave med backend.')
        self.prompt.setMinimumHeight(85);self.prompt.setMaximumHeight(155)
        root.addWidget(label('Opgavetekst',12,True));root.addWidget(self.prompt)
        actions=QHBoxLayout()
        self.review_button=QPushButton('Analysér opgave');self.review_button.setObjectName('primary');actions.addWidget(self.review_button)
        self.solve_button=QPushButton('Løs direkte med backend');self.solve_button.setObjectName('primary');actions.addWidget(self.solve_button)
        self.assist_button=QPushButton('Ret fortolkning'); self.assist_button.setEnabled(False); actions.addWidget(self.assist_button)
        self.physical_model_button=QPushButton('Vælg fysisk model');actions.addWidget(self.physical_model_button)
        self.import_button=QPushButton('Åbn opgavetekst');actions.addWidget(self.import_button)
        self.json_button=QPushButton('Importér solver-JSON');actions.addWidget(self.json_button)
        actions.addStretch(1)
        self.save_note=QPushButton('Gem besvarelse');actions.addWidget(self.save_note)
        root.addLayout(actions)
        self.warning=label('KLAR TIL TEST · Testopgaverne er ikke genereret af Codex.',11,False,'#845a13')
        self.warning.setStyleSheet('background:#fff5d9; color:#6c4b14; border:1px solid #f0d99e; border-radius:7px; padding:9px;')
        root.addWidget(self.warning)
        self.interpret=QTextBrowser();self.interpret.setOpenExternalLinks(False);self.interpret.setMaximumHeight(84);self.interpret.setMinimumHeight(64)
        root.addWidget(self.interpret)
        self.tabs=QTabWidget();self.result=MathDocument();self.derivation=MathDocument();self.explanation=MathDocument()
        for name,widget in [('Resultat',self.result),('Udledning',self.derivation),('Forklaring',self.explanation)]:
            self.tabs.addTab(widget,name)
        self.tabs.setCurrentIndex(1)
        root.addWidget(self.tabs,1)
        self.load_test.clicked.connect(self.load_selected_test)
        self.sample.activated.connect(lambda _:self.load_selected_test())
        self.import_button.clicked.connect(self.import_txt)
        self.solve_button.clicked.connect(self.solve_live)
        self.assist_button.clicked.connect(self.assist_interpretation)
        self.json_button.clicked.connect(self.import_json)
        self.save_note.clicked.connect(self.to_note)
        self.result.set_text('# Resultat\n\nVælg en testopgave ovenfor eller importér en JSON-besvarelse.')
        self.derivation.set_text('# Udledning\n\nHer vises de fysiske begrundelser mellem regnetrin. Ingen motor er tilkoblet endnu.')
        self.explanation.set_text('# Forklaring\n\nVælg et testcase for at se en fuld besvarelse.')
        self.interpret.setHtml('<b>Tilstand:</b> Klar til en installeret, låst offline-backend. Demoerne er stadig tilgængelige.')
        self._backend_process=None
        self._backend_task_path=None
        self._backend_reply_path=None
        self._backend_requested_text=''
        self._backend_errors=[]
        self._backend_corrections={}
        self._backend_reply=None
        self.assisted=None
        self.task_review=None
        self.review_button.clicked.connect(self.open_task_review)
        self.physical_model_button.clicked.connect(self.open_physical_model)
        self.prompt.textChanged.connect(self._sync_assisted_prompt)

    def open_task_review(self):
        if self.task_review is None:
            backend_root,python=backend_location(assisted=True)
            sys.path.insert(0,str(backend_root))
            from desktop_integration.task_review import TaskReview
            self.task_review=TaskReview(python,backend_root,parent=self)
            self.task_review.solutionReady.connect(self._review_completed)
            self.task_review.modelInvalidated.connect(self._clear_assisted_result)
            self.review_index=self.tabs.addTab(self.task_review,'Bekræft opgaven')
        self.tabs.setCurrentIndex(self.review_index)
        self.warning.setText('GENNEMGANG · Kontrollér læste data og de fysiske betingelser før beregning.')
        self.interpret.hide()
        self.task_review.analyze(self.prompt.toPlainText())

    def _review_completed(self,reply):
        from backend_bridge import translate_assisted
        payload=translate_assisted(reply,self.prompt.toPlainText())
        proposal=self.task_review.proposal
        labels={'density_amplitude':proposal.get('normalization_symbol','J0'),'normalized_B':'B'}
        for i,point in enumerate(proposal.get('points',[])):
            labels['B_point_'+str(i+1)]='B_'+str(i+1)
        for key,value in payload.get('result',{}).items():
            if isinstance(value,str):
                for old,new in labels.items():value=value.replace(old+' =',new+' =').replace(old+':',new+':')
                payload['result'][key]=value
            elif isinstance(value,list):
                for i,line in enumerate(value):
                    for old,new in labels.items():line=line.replace(old+' =',new+' =')
                    value[i]=line
        if proposal.get('points'):
            legend=', '.join('B_'+str(i+1)+' ved '+proposal.get('coordinate','s')+'='+v for i,v in enumerate(proposal['points']))
            payload['audit']+='\n\nEvalueringspunkter: '+legend
            if payload.get('result'):payload['result']['numeric_text']=legend+'\n'+payload['result'].get('numeric_text','')
        self.show_solution(payload,origin='ASSISTED')
        if not any(p.get('solution') for p in reply.get('subproblems',[])):self.tabs.setCurrentIndex(self.review_index)

    def open_physical_model(self):
        if self.assisted is None:
            try:
                backend_root,python=backend_location(assisted=True)
                sys.path.insert(0,str(backend_root))
                from desktop_integration.dyn_panel import DynPanel
                self.assisted=DynPanel(python_exe=python,repository=backend_root,parent=self)
                self.assisted.solutionReady.connect(self._assisted_completed)
                self.assisted.modelInvalidated.connect(self._clear_assisted_result)
                self.assisted.text.textChanged.connect(self._sync_main_prompt)
                self.assisted.output.hide();self.assisted.copy.hide()
                self.assisted_index=self.tabs.addTab(self.assisted,'Fysisk model')
            except (ImportError,OSError) as exc:
                QMessageBox.warning(self,'Assisteret backend mangler','Installér den samlede app med INSTALL_WINDOWS.bat. '+str(exc));return
        self._sync_assisted_prompt()
        self.assisted._analyze()
        self.tabs.setCurrentIndex(self.assisted_index)

    def _sync_assisted_prompt(self):
        if self.task_review is not None:self.task_review.invalidate_text(self.prompt.toPlainText())
        if self.assisted is not None and self.assisted.text.toPlainText()!=self.prompt.toPlainText():
            self.assisted.text.setPlainText(self.prompt.toPlainText())

    def _sync_main_prompt(self):
        if self.assisted is not None and self.prompt.toPlainText()!=self.assisted.text.toPlainText():
            self.prompt.setPlainText(self.assisted.text.toPlainText())

    def _clear_assisted_result(self):
        if self.last_payload and self.last_payload.get('backend_schema')=='assisted-1.0':
            self.last_payload=None
            for view in (self.result,self.derivation,self.explanation):view.set_text('Input ændret. Bekræft modellen og beregn igen.')
            self.warning.setText('MODEL ÆNDRET · Ingen aktuel besvarelse.')

    def _assisted_completed(self,reply):
        from backend_bridge import translate_assisted
        payload=translate_assisted(reply,self.prompt.toPlainText())
        self.show_solution(payload,origin='ASSISTED')
        if not any(p.get('solution') for p in reply.get('subproblems',[])):
            self.tabs.setCurrentIndex(self.assisted_index)
            self.assisted.output.show()
        else:self.assisted.output.hide()

    def assist_interpretation(self):
        """Allow informed user choices, never fabricate physical assumptions."""
        fields=(self._backend_reply or {}).get('interpretation',{}).get('fields',{})
        if not isinstance(fields,dict): fields={}
        chosen=dict(self._backend_corrections)
        specifications=[
          ('geometry','Geometri',['cylinder','sphere','spherical_shell','hollow_cylinder','slab','line','wire','field']),
          ('coordinate','Radialkoordinat',['s','r','z']),
          ('extent','Udstrækning',['infinite','finite']),
          ('radius','Ydre radius',['R','a','b','S']),
          ('source_formula','Givet ladnings- eller strømtæthed',[]),
        ]
        missing=set()
        for k,v in fields.items():
            if isinstance(v,dict) and v.get('value') is None and v.get('required',True):missing.add(k)
        if not missing:missing={'geometry','coordinate','extent','radius'}
        count=0
        for key,title,defaults in specifications:
            if key not in missing and key not in chosen:continue
            data=fields.get(key,{})
            options=data.get('options',[]) if isinstance(data,dict) else []
            if not isinstance(options,list):options=[]
            options=[str(x) for x in options if isinstance(x,(str,int))] or defaults
            if key=='source_formula':
                value,ok=QInputDialog.getText(self,'Ret fortolkning',title+' (fx rho(s)=rho0):',text=chosen.get(key,''))
            else:
                options=list(dict.fromkeys([chosen.get(key,'')]+options))
                options=[x for x in options if x]
                value,ok=QInputDialog.getItem(self,'Ret fortolkning',title+':',options,0,True)
            if not ok:break
            if str(value).strip():chosen[key]=str(value).strip();count+=1
        if count:
            self._backend_corrections=chosen
            self.solve_live(reuse_corrections=True)

    def solve_live(self, reuse_corrections=False):
        if not isinstance(reuse_corrections,bool):reuse_corrections=False  # Qt clicked(bool)
        text=self.prompt.toPlainText().strip()
        if not reuse_corrections:self._backend_corrections={}
        self.assist_button.setEnabled(False)
        if not text:
            QMessageBox.information(self, 'Manglende opgave', 'Indsæt først opgaveteksten.')
            return
        backend_root,backend_python=backend_location()
        if not (backend_root/'em1_solver'/'backend_client.py').is_file() or not backend_python.is_file():
            QMessageBox.warning(self,'Installer backend først',
                'Fysikmotoren mangler. Kør SETUP_BACKEND_WINDOWS.bat fra programmappen én gang.\n'
                'Denne pakke bruger Python 3.13 x64. Kør INSTALL_WINDOWS.bat. Dine fem demoopgaver virker uden installation.')
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
        self._backend_process.start(str(backend_python), [str(ROOT/'backend_runner.py'),'--input',str(self._backend_task_path),'--output',str(self._backend_reply_path),'--corrections',json.dumps(self._backend_corrections,ensure_ascii=False)])
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
            self._backend_reply=data
            payload=translate_backend(data,self._backend_requested_text)
            self.show_solution(payload,origin='BACKEND')
            if data.get('status') in ('not_solved','partial'):
                self.assist_button.setEnabled(True)
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

    def load_selected_test(self):
        selected=self.sample.currentData()
        if not selected:return
        try:
            payload=json.loads(Path(selected).read_text(encoding='utf-8'))
            self.show_solution(payload,origin='TESTDATA')
        except (OSError,ValueError,TypeError) as exc:
            QMessageBox.warning(self,'Testopgave kunne ikke indlæses',str(exc))

    def show_solution(self,payload,origin):
        self.interpret.show()
        view=present_backend_json(payload)
        self.last_payload=payload
        self.prompt.setPlainText(_as_text(payload.get('prompt','')))
        self.interpret.setHtml(view['interp'])
        self.result.set_text(view['result'])
        self.derivation.set_text(view['derive'] or 'Ingen udledning er leveret.')
        self.explanation.set_text(view['explain'] or 'Ingen særskilt forklaring er leveret.')
        self.tabs.setCurrentIndex(1)
        status=view['status']
        if origin=='TESTDATA':
            note='TESTDATA · Illustrativt eksempel. Ikke beregnet eller verificeret af den autonome EM1-motor.'
        elif origin=='BACKEND':
            note='LIVE BACKEND · '+_as_text(payload.get('backend_status',status))+'. Kun backendens faktisk gennemførte kontroller ligger bag status. Læs antagelser og advarsler.'
            if self._backend_corrections:note+=' · Manuelle modelvalg: '+', '.join(k+'='+str(v) for k,v in self._backend_corrections.items())
        elif origin=='ASSISTED':
            note='ASSISTERET · '+_as_text(payload.get('backend_status'))+'. Fysisk model bekræftet af dig; opgavetekstens fortolkning er ikke maskinverificeret. Se udførte kontroller i Forklaring.'
        else:
            note='IMPORTERET · Status oplyst af afsender: '+status+'. Desktopappen kontrollerer ikke fysikkens korrekthed.'
        self.warning.setText(note)

    def import_json(self):
        filename,_=QFileDialog.getOpenFileName(self,'Indlæs visnings-JSON',str(Path.home()),'JSON (*.json)')
        if not filename:return
        try:
            path=Path(filename)
            if path.stat().st_size>2_000_000:raise ValueError('JSON-filen er for stor')
            payload=json.loads(path.read_text(encoding='utf-8'))
            if isinstance(payload,dict) and payload.get('schema_version')=='1.0':
                payload=translate_backend(payload,self.prompt.toPlainText())
            self.show_solution(payload,origin='IMPORT')
        except (OSError,ValueError,TypeError) as exc:
            QMessageBox.warning(self,'JSON kunne ikke indlæses',str(exc))

    def import_txt(self):
        filename,_=QFileDialog.getOpenFileName(self,'Vælg opgavetekst',str(Path.home()),'Tekst (*.txt *.md *.tex)')
        if filename:
            self.prompt.setPlainText(Path(filename).read_text(encoding='utf-8',errors='replace'))
            self.sample.setCurrentIndex(0)
            self.last_payload=None
            self.warning.setText('OPGAVETEKST INDLÆST · Klik Løs opgave med backend for at forsøge en offline løsning.')

    def to_note(self):
        if not self.last_payload:
            QMessageBox.information(self,'Ingen besvarelse','Indlæs først en testbesvarelse eller resultat-JSON.')
            return
        p=self.last_payload
        view=present_backend_json(p)
        body='# Opgave\n'+_as_text(p.get('prompt',''))+'\n\n'+view['result']+'\n\n'+view['derive']+'\n\n'+view['explain']
        self.add_note_callback(_as_text(p.get('title','EM1-besvarelse')),body)
        QMessageBox.information(self,'Gemt','Besvarelsen er gemt som lokal note.')


class LibraryPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        v=QVBoxLayout(self);v.setContentsMargins(23,19,23,18)
        v.addWidget(header('Formelsamling', 'Din originale formelsamling – præcis opsætning, direkte i Windows-appen.'))
        self.pdf=PDFReader(RESOURCE_DIR/'EM_formelsamling_GAMMEL_2026-10-30.pdf')
        v.addWidget(self.pdf,1)
        line=QHBoxLayout()
        self.open_tex=QPushButton('Åbn LaTeX-kilde')
        self.open_pdf=QPushButton('Åbn PDF i standardlæser')
        self.open_tex.clicked.connect(lambda:open_file(RESOURCE_DIR/'EM_formelsamling_source.tex'))
        self.open_pdf.clicked.connect(lambda:open_file(RESOURCE_DIR/'EM_formelsamling_GAMMEL_2026-10-30.pdf'))
        line.addWidget(self.open_tex);line.addWidget(self.open_pdf);line.addStretch()
        v.addLayout(line)


def open_file(path):
    if not Path(path).exists():QMessageBox.warning(None,"Fil mangler",str(path));return
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


class ResourcePage(QWidget):
    def __init__(self,title,subtitle,resources,parent=None):
        super().__init__(parent); v=QVBoxLayout(self);v.setContentsMargins(23,19,23,18)
        v.addWidget(header(title,subtitle))
        for name,fn,desc in resources:
            line=QFrame();line.setStyleSheet("QFrame {background:white;border:1px solid #e3e6ec;border-radius:9px;}")
            row=QHBoxLayout(line);t=QVBoxLayout();t.addWidget(label(name,13,True));t.addWidget(label(desc,11,False,MUTED));row.addLayout(t,1)
            btn=QPushButton("Åbn fil");btn.clicked.connect(lambda checked=False, p=RESOURCE_DIR/fn:open_file(p));row.addWidget(btn);v.addWidget(line)
        v.addStretch()


class ExamReferencePage(QWidget):
    """Official solution book, with lazy PDF loading and dated task navigation.

    These solutions are reference material only; they are NOT autonomous verification
    of a different, new exercise.
    """
    def __init__(self,parent=None):
        super().__init__(parent)
        layout=QVBoxLayout(self);layout.setContentsMargins(23,19,23,18);layout.setSpacing(10)
        layout.addWidget(header("Eksamen", "Tidligere opgaver og officielle løsningsforslag – facit bruges som reference, ikke som automatisk bevis"))
        controls=QHBoxLayout()
        self.date=QComboBox();self.task=QComboBox()
        self.go=QPushButton("Vis facit for opgaven");self.go.setObjectName('primary')
        self.full=QPushButton("Åbn hele løsnings-PDF'en")
        self.tasks_pdf=QPushButton("Åbn eksamensopgaver")
        for widget in (self.date,self.task,self.go,self.full,self.tasks_pdf):controls.addWidget(widget)
        layout.addLayout(controls)
        self.status=label("Vælg dato og opgave. Facit-PDF indlæses først, når du klikker på 'Vis facit'.",11,False,MUTED)
        layout.addWidget(self.status)
        self.reader=PDFReader()
        layout.addWidget(self.reader,1)
        self.rows=[]
        index=RESOURCE_DIR/'EM1_facit_testindeks.csv'
        if index.exists():
            with index.open(encoding='utf-8-sig',newline='') as fh:
                self.rows=list(csv.DictReader(fh))
        dates=list(dict.fromkeys(r['exam_date'] for r in self.rows))
        for date in dates:self.date.addItem(date,date)
        self.date.currentIndexChanged.connect(self.update_tasks)
        self.go.clicked.connect(self.show_solution)
        self.full.clicked.connect(lambda:open_file(RESOURCE_DIR/'EM1_officielle_loesninger_2021-2026.pdf'))
        self.tasks_pdf.clicked.connect(lambda:open_file(RESOURCE_DIR/'EM1_eksamenssaet.pdf'))
        self.update_tasks()
        if not self.rows:self.status.setText('Facit-indekset mangler. Den originale PDF kan stadig åbnes.')

    def update_tasks(self,*args):
        self.task.clear()
        date=self.date.currentData()
        for item in self.rows:
            if item['exam_date']==date:
                self.task.addItem('Opgave '+item['task_number'],item)

    def show_solution(self):
        selected=self.task.currentData()
        if not selected:
            self.status.setText('Ingen opgave valgt.')
            return
        path=RESOURCE_DIR/'EM1_officielle_loesninger_2021-2026.pdf'
        page=int(selected['page_start'])
        # PDFReader supports direct navigation after a one-time lazy load.
        if self.reader.path!=path or not self.reader.document:
            self.reader.open_pdf(path,page)
        else:
            self.reader.goto(page)
        end=int(selected['page_end'])
        self.status.setText(f"{selected['exam_date']} · Opgave {selected['task_number']} · PDF-side {page}" +
                            (f"–{end}" if end>page else "") +
                            ". Kontroller formler visuelt; automatisk PDF-tekst kan forvanske tegn.")


class HistoryPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); v=QVBoxLayout(self);v.setContentsMargins(23,19,23,18)
        v.addWidget(header("Historik", "Lokale, gemte løsningsforsøg vises her, når backend integreres."))
        v.addWidget(label("I denne prototype gemmes opgaveløsninger via 'Gem som note' i Notesamling.",13))
        v.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle("EM1 Solver · Desktop v1.0.2"); self.resize(1450,880); self.setMinimumSize(1020,650)
        central=QWidget();central.setObjectName("main");self.setCentralWidget(central)
        main=QHBoxLayout(central);main.setContentsMargins(0,0,0,0);main.setSpacing(0)
        left=QFrame();left.setObjectName("sidebar");left.setFixedWidth(205)
        nav=QVBoxLayout(left);nav.setContentsMargins(13,23,13,18);nav.setSpacing(8)
        logo=label("◈  EM1 Solver",20,True,"white");nav.addWidget(logo);nav.addWidget(label("ELEKTROMAGNETISME 1",10,False,"#a0aec4"));nav.addSpacing(24)
        main.addWidget(left)
        self.splitter=QSplitter(Qt.Orientation.Horizontal);self.splitter.setHandleWidth(5)
        self.pages=QStackedWidget(); self.notes_full=IntegratedNotes(); self.notes_side=IntegratedNotes(compact=True)
        self.solver=SolverPage(self.save_solver_note, self.open_recommended_source)
        self.pages.addWidget(self.solver);self.pages.addWidget(self.notes_full);self.pages.addWidget(LibraryPage())
        self.pages.addWidget(ExamReferencePage())
        self.pages.addWidget(HistoryPage())
        self.splitter.addWidget(self.pages);self.splitter.addWidget(self.notes_side);self.splitter.setSizes([1150,0]);self.splitter.setStretchFactor(0,4);self.splitter.setStretchFactor(1,1)
        main.addWidget(self.splitter,1)
        navitems=[("⌗   Opgaveløser",0),("▤   Mine noter",1),("∑   Formler",2),("▣   Eksamen",3),("◷   Historik",4)]
        self.buttons=[]
        for title,index in navitems:
            b=QPushButton(title);b.setObjectName("nav");b.clicked.connect(lambda checked=False,i=index:self.show_page(i));self.buttons.append(b);nav.addWidget(b)
        nav.addStretch();nav.addWidget(label("OFFLINE · LOKALE FILER",10,False,"#93a2b8"));nav.addWidget(label("Desktop v0.7 · løsningsvisning",11,False,"#93a2b8"))
        self.solver.notes_button.clicked.connect(self.toggle_notes)
        
        self.show_page(0)
        sc=QAction("Skift noter",self);sc.setShortcut(QKeySequence("Ctrl+Shift+N"));sc.triggered.connect(self.toggle_notes);self.addAction(sc)

    def show_page(self,index):
        self.notes_full.commit();self.notes_side.commit()
        self.pages.setCurrentIndex(index)
        for idx,b in enumerate(self.buttons):b.setProperty("active",str(idx==index).lower());b.style().unpolish(b);b.style().polish(b)
        if index==1:self.notes_side.hide();self.notes_full.current_id=None;self.notes_full.reload()
        elif index==0:self.notes_side.hide();self.notes_side.current_id=None;self.notes_side.reload()
        else:self.notes_side.hide()

    def toggle_notes(self):
        if self.pages.currentIndex()!=0:self.show_page(0)
        self.notes_side.setVisible(not self.notes_side.isVisible())

    def open_recommended_source(self,entry_id):
        self.notes_side.show()
        self.splitter.setSizes([900,420])
        self.notes_side.tabs.setCurrentIndex(1)
        if not self.notes_side.sources.focus_source(entry_id):
            QMessageBox.information(self,'Notekilde mangler','Kunne ikke finde den valgte PDF-side.')

    def save_solver_note(self,title,body):
        self.notes_full.insert_text_as_note(title,body,"2 Elektrostatik")
        self.notes_side.current_id=None;self.notes_side.reload()

    def closeEvent(self,event):
        if self.solver.task_review is not None and self.solver.task_review.busy:
            self.solver.warning.setText('Afvent den igangværende beregning.');event.ignore();return
        if self.solver.assisted is not None and self.solver.assisted.busy:
            self.solver.warning.setText('Afvent backendberegningen før lukning.');event.ignore();return
        if self.solver._backend_process and self.solver._backend_process.state()!=QProcess.NotRunning:
            self.solver.warning.setText('Afvent den igangværende backendberegning før lukning.');event.ignore();return
        self.notes_full.commit();self.notes_side.commit();super().closeEvent(event)


def main():
    init_db()
    app=QApplication(sys.argv);app.setStyle("Fusion");app.setStyleSheet(STYLE)
    wnd=MainWindow();wnd.show()
    sys.exit(app.exec())

if __name__=="__main__":main()
