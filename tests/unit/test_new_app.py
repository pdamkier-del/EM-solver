from streamlit.testing.v1 import AppTest

def test_new_problem_confirmation_and_local_exports():
    app=AppTest.from_file('app.py',default_timeout=40).run()
    assert app.radio[0].value=='Ny opgave'
    source='En uendelig cylinder med radius R har rho(s)=rho0(1-s/R). Bestem E(s).'
    next(x for x in app.text_area if x.key=='exam_text').set_value(source)
    next(x for x in app.button if x.label=='Analysér opgave').click().run()
    assert not app.exception
    assert next(x for x in app.button if x.label=='Løs opgave').disabled
    next(x for x in app.checkbox if x.key=='af_confirm').check().run()
    next(x for x in app.button if x.label=='Løs opgave').click().run()
    assert not app.exception and not app.error
    assert any(x.value=='Resultat' for x in app.subheader)
    next(x for x in app.text_area if x.key=='exam_text').set_value(source+' Ny oplysning.').run()
    assert not any(x.value=='Resultat' for x in app.subheader)
    assert next(x for x in app.button if x.label=='Løs opgave').disabled


def test_manual_structuring_preserves_problem_and_region_builder():
    app=AppTest.from_file('app.py',default_timeout=40).run()
    original='En ukendt konstruktion med et hulrum.'
    next(x for x in app.text_area if x.key=='exam_text').set_value(original)
    app.radio[0].set_value('Manuel solver').run()
    assert next(x for x in app.text_input if x.key=='af_function')
    next(x for x in app.button if x.label=='Tilføj region').click().run()
    assert len([x for x in app.text_input if 'region_' in (x.key or '') and x.key.endswith('lower')])==2
    next(x for x in app.button if x.label=='Fjern sidste region').click().run()
    app.radio[0].set_value('Ny opgave').run()
    assert next(x for x in app.text_area if x.key=='exam_text').value==original


def test_autosave_restore_in_fresh_app_session():
    app=AppTest.from_file('app.py',default_timeout=40).run()
    source='En uendelig cylinder med radius R har rho(s)=rho0. Bestem E(s).'
    next(x for x in app.text_area if x.key=='exam_text').set_value(source)
    next(x for x in app.button if x.label=='Analysér opgave').click().run()
    next(x for x in app.checkbox if x.key=='af_confirm').check().run()
    next(x for x in app.button if x.label=='Løs opgave').click().run()
    assert not app.error and not app.exception
    fresh=AppTest.from_file('app.py',default_timeout=40).run()
    next(x for x in fresh.button if x.label=='Gendan opgave').click().run()
    assert not fresh.exception
    assert next(x for x in fresh.text_area if x.key=='exam_text').value==source
    assert next(x for x in fresh.button if x.label=='Løs opgave').disabled
    assert any('Senest gemte løsning' in x.label for x in fresh.text_area)


def test_ba_and_dyn_text_confirmation_paths():
    examples=[('A=(B0*x*y/L) zhat. Bestem B.','ba_vector_potential'),('Et loop har B(t)=B0*cos(omega*t). Find flux og emf.','dyn_fixed')]
    for source,preset in examples:
        app=AppTest.from_file('app.py',default_timeout=40).run()
        next(x for x in app.text_area if x.key=='exam_text').set_value(source)
        next(x for x in app.button if x.label=='Analysér opgave').click().run()
        assert not app.exception
        assert next(x for x in app.selectbox if x.key=='af_preset').value==preset
        next(x for x in app.checkbox if x.key=='af_confirm').check().run()
        next(x for x in app.button if x.label=='Løs opgave').click().run()
        assert not app.exception and not app.error
        assert any(x.value=='Resultat' for x in app.subheader)


def test_original_specialized_solver_remains_available_without_source_code():
    app=AppTest.from_file('app.py',default_timeout=40).run()
    app.radio[0].set_value('Manuel solver').run()
    next(x for x in app.selectbox if x.label=='Formular').set_value('Specialiseret metode').run()
    next(x for x in app.selectbox if x.key=='special_family').set_value('laplace_legendre').run()
    assert not app.exception and not app.error
    next(x for x in app.checkbox if x.key=='special_confirm').check().run()
    next(x for x in app.button if x.key=='special_solve').click().run()
    assert not app.exception and not app.error
    assert any(x.value=='Resultat' for x in app.subheader)
    from em1_solver.core.local_state import load
    assert load('specialized.json')['answer']['text']
