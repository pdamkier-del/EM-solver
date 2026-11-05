"""Text-first exam flow. Only unresolved root fields become form inputs."""
import copy
import streamlit as st
from .text_parser import analyze,solve_text
from .text_parser import local_state
from .text_parser.parser import GEOMETRY_LABELS
from .rendering.text_task import render
from .rendering.plain import text as plain
from .ui_assisted import exports

LABELS={'geometry':'Geometri','source':'Kilde','source_formula':'Given funktion','domain':'Område','regions':'Ladede/strømførende områder','orientation':'Orientering','wanted':'Søges','method':'Metode','units':'Enheder','extent':'Kildens udstrækning','radius':'Ydre radius','coordinate':'Radial afstand','plane':'Løkkens plan','normal':'Positiv normalretning','current':'Strømretning','current_sense':'Strømretning','point':'Feltpunkt','axis':'Linjens akse','bounds':'Integrationsgrænser','time':'Tidssymbol','area':'Løkkens areal','turns':'Antal vindinger','resistance':'Modstand','B':'Magnetfeltets retning','time_bounds':'Tidsinterval','negligible_inductance':'Kan selvinduktansen negligeres?','center':'Kurvens centrum','coordinate_system':'Koordinatsystem','material':'Materiale','symmetry':'Symmetri'}
OPTIONS={'finite':'Endelig','infinite':'Uendelig','counterclockwise':'Mod uret','clockwise':'Med uret','yes':'Ja','no':'Nej','origin':'Ja, i origo','other':'Nej','cartesian':'Kartesisk','cylindrical':'Cylindrisk','spherical':'Sfærisk'}
EDITABLE=set(LABELS)-{'domain','orientation','method','source'}

def restore():
    data=local_state.load()
    if data:
        st.session_state['tp_text']=data['text'];st.session_state['tp_corrections']=data['corrections']
        st.session_state.pop('tp_answer',None);st.session_state.pop('tp_interpretation',None)

def analyze_and_solve(original,corrections,solve=False):
    st.session_state.pop('tp_answer',None)
    try:
        interpreted=analyze(original,corrections);st.session_state['tp_interpretation']=interpreted
        if interpreted.ready and solve:
            with st.spinner('Beregner lokalt …'):
                interpreted,answer=solve_text(original,corrections)
            st.session_state['tp_answer']=answer
            local_state.save(original,corrections,plain(answer))
        else:local_state.save(original,corrections)
    except (ValueError,TypeError,KeyError,OSError) as exc:
        st.session_state['tp_failure']=str(exc)


def text_mode(mode):
    st.subheader('Indsæt opgaven')
    original=st.text_area('Indsæt opgaveteksten',height=220,key='tp_text',placeholder='Indsæt én delopgave med de nødvendige givne oplysninger.')
    changed=st.session_state.get('tp_analyzed_text')!=original
    if st.button('Analysér opgave',type='primary',disabled=not original.strip()):
        st.session_state['tp_corrections']={};st.session_state['tp_analyzed_text']=original
        st.session_state.pop('tp_failure',None)
        # Widget edits from an earlier problem must never leak into this one.
        for key in list(st.session_state):
            if key.startswith('tp_input_'):del st.session_state[key]
        analyze_and_solve(original,{})
        changed=False
    if changed and st.session_state.get('tp_interpretation'):st.info('Teksten er ændret. Vælg Analysér opgave for at bruge den nye opgave.')
    interpreted=None if changed else st.session_state.get('tp_interpretation')
    if interpreted:
        green={k:v for k,v in interpreted.fields.items() if v.status=='GREEN'}
        title='Fortolkning – alt ser korrekt ud' if interpreted.ready else 'Fortolkning – genkendte oplysninger'
        with st.expander(title,expanded=False):
            for key,field in green.items():
                if key=='units':continue
                label=LABELS.get(key,key)
                value=GEOMETRY_LABELS.get(field.value,field.value) if isinstance(field.value,str) else field.value
                if key=='regions' and isinstance(value,list):
                    st.markdown('**Områder**')
                    for row in value:st.write(str(row['lower'])+' < afstand < '+str(row['upper'])+': tæthed = '+str(row['density']))
                else:st.write(label+': '+str(value))
            st.caption('GREEN betyder, at reglen fandt de nødvendige tekstlige oplysninger. Det er ikke en statistisk sandsynlighed eller et bevis på fuld tekstforståelse.')
        questions=interpreted.questions
        if questions:
            st.subheader('Kontrollér disse oplysninger')
            editable={k:v for k,v in questions.items() if k in EDITABLE}
            for key,field in questions.items():
                if key not in EDITABLE:st.error(field.message)
            if len(questions)>3:st.info('Denne opgave kræver flere afklaringer. Avanceret / Manuel kan være hurtigere.')
            with st.form('tp_clarifications'):
                for key,field in editable.items():
                    st.caption(field.message)
                    if field.options:
                        st.selectbox(LABELS[key],['']+field.options,key='tp_input_'+key,format_func=lambda v:'Vælg …' if v=='' else OPTIONS.get(v,GEOMETRY_LABELS.get(v,v)))
                    else:st.text_input(LABELS[key],key='tp_input_'+key)
                continued=st.form_submit_button('FORTSÆT',disabled=not editable)
            if continued:
                corrections=copy.deepcopy(st.session_state.get('tp_corrections',{}))
                corrections.update({k:st.session_state['tp_input_'+k] for k in editable if st.session_state['tp_input_'+k]})
                st.session_state['tp_corrections']=corrections;st.session_state.pop('tp_failure',None)
                analyze_and_solve(original,corrections);st.rerun()
            if any(k not in EDITABLE for k in questions):st.info('Den eksisterende fulde formular findes under Avanceret / Manuel. Du kan også præcisere teksten ovenfor.')
    if not changed and st.session_state.get('tp_failure'):st.error(st.session_state['tp_failure'])
    if interpreted:
        with st.expander('Ret fortolkningen'):
            field=st.selectbox('Oplysning',sorted(EDITABLE),format_func=lambda k:LABELS[k],key='tp_edit_field')
            value=st.text_input('Ny værdi',key='tp_edit_value',help='Funktion: rho(s)=k*s. Geometri: brug de danske valg i afklaringspanelet, eller skriv fx cylinder. Region: a<s<b.')
            if st.button('Anvend rettelse',disabled=not value.strip()):
                corrections=copy.deepcopy(st.session_state.get('tp_corrections',{}))
                reverse={v:k for k,v in GEOMETRY_LABELS.items()}|{v:k for k,v in OPTIONS.items()}
                corrections[field]=reverse.get(value,value)
                st.session_state['tp_corrections']=corrections;analyze_and_solve(original,corrections);st.rerun()
        if interpreted.ready:
            st.success('Fortolkningen er klar til kontrol. Ret eventuelle fejl før beregning.')
            numerical=st.radio('Løsningstype',['Symbolsk','Symbolsk og numerisk'],horizontal=True,key='tp_solution_type')
            if st.button('Løs opgave',type='primary'):
                st.session_state.pop('tp_failure',None)
                analyze_and_solve(original,st.session_state.get('tp_corrections',{}),solve=True)
        if not changed and st.session_state.get('tp_failure'):st.error(st.session_state['tp_failure'])
    if interpreted and st.session_state.get('tp_answer'):
        answer=copy.deepcopy(st.session_state['tp_answer'])
        if st.session_state.get('tp_solution_type')=='Symbolsk':answer.numerical_result={}
        answer.recognition=GEOMETRY_LABELS.get(interpreted.facts['geometry'],'EM1-opgave')
        render(st,answer,interpreted,mode);exports(answer)
    with st.expander('Gendan seneste lokale tekstopgave'):
        try:
            saved=local_state.load()
            if saved:
                st.button('Gendan tekst',on_click=restore)
                if saved.get('answer'):st.text_area('Senest gemte løsning',saved['answer'],height=160,disabled=True)
            else:st.caption('Ingen tekstopgave gemt endnu.')
        except (OSError,ValueError) as exc:st.warning('Autosave kunne ikke læses: '+str(exc))
