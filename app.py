"""The offline exam application. No user needs to open solver code."""
import streamlit as st
from em1_solver.core.startup import check
from em1_solver.ui_assisted import assisted_mode
from em1_solver.ui_workflows import historical_mode

def main():
    st.set_page_config(page_title='EM1 Solver',layout='wide')
    st.title('EM1 Solver')
    @st.cache_resource(show_spinner=False)
    def readiness():return check()
    errors=readiness()
    if errors:
        st.error('Systemstatus: Ikke klar')
        for error in errors:st.error(error)
        st.stop()
    st.caption('Systemstatus: Klar · Lokal beregning · Ingen AI eller internet')
    workflow=st.radio('Arbejdsgang',['Ny opgave','Historiske opgaver','Avanceret / Manuel','Hjælp'],horizontal=True)
    exam=st.toggle('Eksamenstilstand',value=True)
    mode='Eksamen' if exam else 'Forklaring'
    if workflow=='Ny opgave':
        from em1_solver.ui_text_parser import text_mode
        text_mode(mode)
    elif workflow=='Avanceret / Manuel':
        form=st.selectbox('Formular',['Geometri-formular','Specialiseret metode','Tekst med fuld bekræftelse'])
        if form=='Geometri-formular':assisted_mode(mode,manual=True)
        elif form=='Tekst med fuld bekræftelse':assisted_mode(mode)
        else:
            from em1_solver.ui_specialized import specialized
            specialized(mode)
    elif workflow=='Historiske opgaver':historical_mode(mode)
    else:
        st.subheader('Kort eksamens-runbook')
        st.markdown('1. Indsæt én delopgave og vælg **Analysér opgave**, eller gå til **Avanceret / Manuel**.\n2. Besvar kun de viste afklaringsspørgsmål.\n3. Kontrollér orientering, enheder og de synlige fysiske vilkår.\n4. Kontrollér fortolkningen, og vælg **Løs opgave**, når alle nødvendige oplysninger er afklaret.\n5. Kontrollér resultatets fortegn, regiongrænser og warnings. Gem tekst eller LaTeX lokalt.')
        st.markdown('**EV:** Gauss kræver radial/plan symmetri; ellers Coulomb. **BA:** Ampère kræver passende symmetri; ellers Biot–Savart. **DYN:** Integrer den orienterede flux, og differentier hele tidsafhængigheden. Lenz bestemmer fortegnet.')
        st.info('GREEN gælder den bekræftede struktur og de udførte kontroller. Det beviser ikke, at tekstparseren har forstået hele opgaven.')
        st.caption('Brug positive symboler til radier og modstande. Ordning a<b kan skrives b=a+h med h>0. Autosave gemmes kun lokalt i brugerens EM1Solver-mappe.')

if __name__=='__main__':main()
