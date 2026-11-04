"""Parse -> editable confirmation -> bounded local computation."""
import json
from dataclasses import asdict
import streamlit as st
from .core.new_problem import parse,Parsed,GEOMETRIES,WANTED,build
from .core.task_runtime import run_confirmed
from .core.problem import InputError
from .rendering.danish_solution import render
from .rendering.latex import document
from .rendering.plain import text

ASSUMPTIONS=['spherical_symmetry','infinite_cylindrical_symmetry','infinite_planar_symmetry','magnetostatic','electrostatic','uniform_normal_B','negligible_self_inductance','off_source','linear_isotropic_dielectric','axial_symmetry','charge_free_inside_outside','V_infinity_zero','finite_at_origin','uniform_axial_E','circular_symmetry','negligible_edge_effects','uniform_axial_B_inside','negligible_leakage','uniform_cross_section','constant_coefficients','no_friction','stationary_return_path']

def new_mode(mode):
    st.subheader('Ny opgave')
    st.caption('Regelbaseret teksthjælp. Beregning kræver din kontrol af strukturen; ingen AI eller internet.')
    original=st.text_area('Opgavetekst',key='new_original')
    known=st.text_area('Kendte størrelser – én tildeling pr. linje',placeholder='rho(s) = alpha*s**2\nR = 0.05 m',key='new_known')
    geometry=st.selectbox('Geometri',GEOMETRIES,key='new_geometry')
    wanted=st.multiselect('Søges',WANTED,key='new_wanted')
    if st.button('Analysér opgave',key='parse_new'):
        try:
            parsed=parse(original,known,geometry,wanted)
            st.session_state.new_parsed=asdict(parsed)
            st.session_state.new_source=(original,known,geometry,tuple(wanted))
            st.session_state.new_data=json.dumps(parsed.data,ensure_ascii=False,indent=2)
            st.session_state.new_units=json.dumps(parsed.units,ensure_ascii=False,indent=2)
            st.session_state.new_numbers=json.dumps(parsed.quantities,ensure_ascii=False,indent=2)
            st.session_state.new_positive=','.join(parsed.positive)
            st.session_state.new_confirm_geometry=parsed.geometry
            st.session_state.new_wanted_text=','.join(parsed.wanted)
            st.session_state.new_assumptions=[v for v in parsed.assumptions if v in ASSUMPTIONS]
            st.session_state.new_confirm=False
            st.session_state.pop('new_answer',None)
        except InputError as exc:st.error(str(exc))
    if 'new_parsed' not in st.session_state:return
    source_changed=st.session_state.get('new_source')!=(original,known,geometry,tuple(wanted))
    if source_changed:st.warning('Opgaveteksten eller de oprindelige input er ændret. Tryk Analysér opgave igen før beregning.')
    st.subheader('Jeg har forstået opgaven sådan:')
    for warning in st.session_state.new_parsed['warnings']:st.warning(warning)
    corrected_geometry=st.selectbox('Bekræft/ret geometri',GEOMETRIES,key='new_confirm_geometry')
    corrected_wanted=[v.strip() for v in st.text_input('Bekræft/ret søges (kommasepareret)',key='new_wanted_text').split(',') if v.strip()]
    manual=st.checkbox('Manuel strukturering – behold tekst og givne størrelser',key='new_manual')
    st.caption('Ret alle data nedenfor. radius og resistance skal være forskellige symboler. En uendelig geometri er ikke i sig selv bevis for kildens symmetri.')
    with st.expander('Feltnavne og parameteriserede kurver',expanded=manual):
        st.markdown('Radialt: `coordinate`, `radius`, `rho`/`J`, `extent="infinite"`; hule/flerdelte kilder: `regions` med `lower`, `upper`, `density`, eventuelt `permittivity`.\n\nFlux: `B` eller `B_normal`, `area`, `time`, `N`, `resistance`; varme kræver `time_bounds`.\n\nKurve: `source` (tre komponenter), `parameter`, `bounds`, `point`, `lambda` eller `I`. Fx en ellipse i xy-plan: `["a*cos(u)","b*sin(u)","0"]`; angiv selv grænser, retning og feltpunkt.\n\nPunktladninger: `charges=[["q",["0","0","0"]],...]`, `point`. Felt/potentiale: `V`/`E`/`A`, `coordinates`, `system`.')
    data=st.text_area('Problemdata (JSON; alle felter kan rettes)',key='new_data',height=230)
    units=st.text_area('Symbolernes enheder (JSON)',key='new_units',height=90)
    numbers=st.text_area('Numeriske værdier med enheder (JSON)',key='new_numbers',height=90)
    positive=st.text_input('Positive symboler (kommasepareret; fx s,R,alpha)',key='new_positive')
    assumptions=st.multiselect('Fysiske antagelser – bekræft kun det opgaven begrunder',ASSUMPTIONS,key='new_assumptions')
    try:
        parsed=Parsed(st.session_state.new_parsed['text'],corrected_geometry,json.loads(data),corrected_wanted,json.loads(numbers),json.loads(units),[v.strip() for v in positive.split(',') if v.strip()],assumptions)
        problem=build(parsed)
        st.info('GUL – struktur klar til din kontrol. Foreslået metode: '+problem.family+'; '+problem.domain+'. Input og antagelser kontrolleres igen ved løsning.')
    except (InputError,ValueError,TypeError,KeyError) as exc:
        parsed=None;st.error('RØD – kan ikke afgøre problemet entydigt: '+str(exc))
    evaluate=st.checkbox('Forsøg lukket analytisk form for kurveintegraler (begrænset tidsbudget)',value=False)
    numeric=st.checkbox('Numerisk kurveintegral (kræver alle værdier og bekræftet off_source)',value=False)
    if parsed is not None and numeric:parsed.data['numeric_integrals']=True
    confirmed=st.checkbox('Jeg har verificeret geometri, kilder, enheder, retning og antagelser',key='new_confirm')
    if st.button('Løs opgave',disabled=parsed is None or not confirmed or source_changed,key='solve_new'):
        st.session_state.pop('new_answer',None)
        try:
            with st.spinner('Beregner lokalt med tidsgrænse …'):st.session_state.new_answer=run_confirmed(parsed,evaluate)
            st.session_state.new_answer_input=(data,units,numbers,positive,tuple(assumptions),corrected_geometry,tuple(corrected_wanted),evaluate,numeric)
        except InputError as exc:st.error('Kan ikke afgøre problemet entydigt: '+str(exc))
    if not source_changed and 'new_answer' in st.session_state and st.session_state.get('new_answer_input')==(data,units,numbers,positive,tuple(assumptions),corrected_geometry,tuple(corrected_wanted),evaluate,numeric):
        answer=st.session_state.new_answer
        if answer.checks and all(c.passed is True for c in answer.checks):st.success('GRØN – de udførte kontroller består. Kontrollér stadig den bekræftede problemfortolkning.')
        else:st.warning('GUL – beregningen er gennemført med uafklarede eller fejlede kontroller. Se kontrol og advarsler; en fysisk afvisning kan være det korrekte svar.')
        st.caption('Resultatet gælder den sidst bekræftede struktur. Ændrede felter kræver en ny beregning.')
        render(st,answer,mode)
        st.download_button('Eksportér LaTeX',document(answer),file_name='ny_opgave.tex')
        st.download_button('Gem tekst',text(answer),file_name='ny_opgave.txt',mime='text/plain')
        with st.expander('Kopiér løsning lokalt'):
            st.code(text(answer),language=None)
