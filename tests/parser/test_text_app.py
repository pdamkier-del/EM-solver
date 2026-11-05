"""Actual Streamlit widget flow with outbound sockets blocked by the test fixture."""
from streamlit.testing.v1 import AppTest
import pytest

CASES=[
 ('EV','En uendelig massiv cylinder med radius R=4 cm har ρ(s)=αs². Bestem E.'),
 ('BA','En uendelig cylinder med radius R har J(s)=k*s. Strømmen går i +z. Bestem B.'),
 ('DYN','En cirkulær loop i xy-plan med radius R har en vinding. B(t)=B0*cos(omega*t) langs +z. Normalen er i +z. Bestem EMF.')]

def click(app,label):next(b for b in app.button if b.label==label).click().run()
def start(text):
    app=AppTest.from_file('app.py',default_timeout=40).run()
    assert app.radio[0].value=='Ny opgave'
    next(a for a in app.text_area if a.key=='tp_text').set_value(text).run()
    click(app,'Analysér opgave')
    assert not app.exception and not app.error,[e.value for e in app.error]
    return app

@pytest.mark.parametrize('domain,text',CASES)
def test_paste_review_solve_and_export(domain,text):
    app=start(text)
    assert not any(s.value=='Resultat' for s in app.subheader)
    assert any(e.label=='Fortolkning – alt ser korrekt ud' for e in app.expander)
    click(app,'Løs opgave')
    assert not app.exception and not app.error,[e.value for e in app.error]
    assert any(s.value=='Resultat' for s in app.subheader)
    assert app.latex
    assert app.code and len(app.get('download_button'))>=2


def test_one_unknown_field_and_no_default_guess():
    app=start('En massiv cylinder med radius R har rho(s)=k*s. Bestem E.')
    box=next(b for b in app.selectbox if b.key=='tp_input_extent')
    assert box.value==''
    assert not any(b.label=='Løs opgave' for b in app.button)
    box.set_value('infinite').run();click(app,'FORTSÆT')
    assert not app.exception and not app.error
    click(app,'Løs opgave')
    assert any(s.value=='Resultat' for s in app.subheader)
    # A new text must hide the old result until it is reanalysed.
    next(a for a in app.text_area if a.key=='tp_text').set_value('Bestem noget andet.').run()
    assert not any(s.value=='Resultat' for s in app.subheader)


def test_edit_green_formula_then_recompute_and_restore():
    app=start('En massiv kugle med radius R har rho(r)=k*r. Bestem E.')
    next(s for s in app.selectbox if s.key=='tp_edit_field').set_value('source_formula').run()
    next(a for a in app.text_input if a.key=='tp_edit_value').set_value('rho(r)=k*r**2').run()
    click(app,'Anvend rettelse')
    assert not app.exception
    click(app,'Løs opgave')
    assert not app.error and any(s.value=='Resultat' for s in app.subheader)

def test_text_autosave_survives_a_fresh_app_session():
    source='En massiv kugle med radius R har rho(r)=k*r. Bestem E.'
    app=start(source);click(app,'Løs opgave')
    fresh=AppTest.from_file('app.py',default_timeout=40).run()
    click(fresh,'Gendan tekst')
    assert not fresh.exception
    assert next(a for a in fresh.text_area if a.key=='tp_text').value==source
    assert any(a.label=='Senest gemte løsning' for a in fresh.text_area)
    assert not any(s.value=='Resultat' for s in fresh.subheader)
