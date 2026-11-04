"""Functional EV/BA/DYN preset smoke test with all socket connections forbidden."""
import socket
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def forbidden(*args,**kwargs):raise AssertionError('Network connection attempted during offline smoke test')
socket.socket.connect=forbidden
socket.socket.connect_ex=forbidden
socket.create_connection=forbidden
from streamlit.testing.v1 import AppTest
for question in ['2025-11:2a','2025-01:4a','2025-11:5c']:
 app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
 app.radio[0].set_value('Historiske opgaver').run()
 app.selectbox[0].set_value(question).run()
 assert not app.exception and not app.error,(question,app.exception,app.error)
 assert app.success
 print(question,'OK (all outbound sockets blocked)')
