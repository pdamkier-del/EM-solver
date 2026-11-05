"""Python 3.13 migration acceptance: actual runtime, pinned metadata and app data."""
import os,sys,sqlite3
from pathlib import Path
from importlib.metadata import version
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ.setdefault('APPDATA','/tmp/em1-python313-acceptance')
import pytest
from packaging.requirements import Requirement
from packaging.version import Version
from PySide6.QtWidgets import QApplication
from desktop_app import app as host
ROOT=Path(__file__).resolve().parents[2]


def test_runtime_is_standard_python313_x64():
    import struct,sysconfig
    assert sys.version_info[:2]==(3,13)
    assert struct.calcsize('P')==8 and not sysconfig.get_config_var('Py_GIL_DISABLED')


def test_every_locked_runtime_distribution_is_installed_exactly():
    for line in (ROOT/'desktop_app/requirements-windows-lock.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):continue
        r=Requirement(line);assert Version(version(r.name)) in r.specifier


def test_notes_survive_mainwindow_recreation_and_original_pdf_renders():
    q=QApplication.instance() or QApplication([]);host.init_db()
    first=host.MainWindow();first.show()
    first.notes_full.insert_text_as_note('Python313 persistent note','Kontrol: µ og dansk æøå','2 Elektrostatik')
    first.notes_full.commit();first.close();q.processEvents()
    second=host.MainWindow();second.show();second.show_page(1);q.processEvents()
    with sqlite3.connect(host.DB) as connection:
        row=connection.execute('SELECT body FROM notes WHERE title=?',('Python313 persistent note',)).fetchone()
    assert row and row[0]=='Kontrol: µ og dansk æøå'
    pdf=second.pages.widget(2).pdf
    assert pdf.document is not None and len(pdf.document)>0
    assert pdf.page_view.pixmap() is not None and not pdf.page_view.pixmap().isNull()
    pdf.goto(min(2,len(pdf.document)));q.processEvents()
    assert not pdf.page_view.pixmap().isNull()
    second.close();q.processEvents()


def test_windows_entrypoints_are_consistent_and_do_not_reuse_python312():
    desktop=ROOT/'desktop_app'
    for name in ('INSTALL_WINDOWS.bat','START_WINDOWS.bat','TEST_FYSIKMOTOR_WINDOWS.bat'):
        text=(desktop/name).read_text()
        assert 'desktop-python313-20261105' in text
        assert 'backend312' not in text and 'desktop-development-20261105' not in text
    for name in ('INSTALL_WINDOWS.bat','PREPARE_OFFLINE_WINDOWS.bat'):
        assert 'py -3.13' in (desktop/name).read_text()
    assert 'sys.version_info[:2] == (3,13)' in (desktop/'START_WINDOWS.bat').read_text()
    assert 'Invoke-WebRequest' not in (desktop/'SETUP_BACKEND_WINDOWS.ps1').read_text(encoding='utf-8-sig')
