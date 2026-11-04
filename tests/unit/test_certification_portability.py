"""Identical files must have identical certificate hashes on Windows and Unix."""
from pathlib import Path,PureWindowsPath
from em1_solver.core.certification import fingerprint

def test_fingerprint_does_not_depend_on_os_path_separator(monkeypatch):
    expected=fingerprint()
    original=Path.relative_to
    def windows_relative(self,*args,**kwargs):return PureWindowsPath(*original(self,*args,**kwargs).parts)
    monkeypatch.setattr(Path,'relative_to',windows_relative)
    assert fingerprint()==expected
