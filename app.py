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
    workflow=st.radio('Arbejdsgang',['Ny opgave','Historiske opgaver','Manuel solver','Hjælp'],horizontal=True)
    exam=st.toggle('Eksamenstilstand',value=True)
    mode='Eksamen' if exam else 'Forklaring'
    if workflow=='Ny opgave':assisted_mode(mode)
    elif workflow=='Manuel solver':
        form=st.selectbox('Formular',['Geometri-formular','Specialiseret metode'])
        if form=='Geometri-formular':assisted_mode(mode,manual=True)
        else:
            from em1_solver.ui_specialized import specialized
            specialized(mode)
    elif workflow=='Historiske opgaver':historical_mode(mode)
    else:
        st.subheader('Kort eksamens-runbook')
        st.markdown('1. Indsæt opgaven og vælg **Analysér opgave**, eller gå direkte til **Manuel solver**.\n2. Vælg område og geometri; ret kilde, regioner og søges.\n3. Kontrollér orientering, enheder og de synlige fysiske vilkår.\n4. Bekræft input, og vælg **Løs opgave**.\n5. Kontrollér resultatets fortegn, regiongrænser og warnings. Gem tekst eller LaTeX lokalt.')
        st.markdown('**EV:** Gauss kræver radial/plan symmetri; ellers Coulomb. **BA:** Ampère kræver passende symmetri; ellers Biot–Savart. **DYN:** Integrer den orienterede flux, og differentier hele tidsafhængigheden. Lenz bestemmer fortegnet.')
        st.info('GREEN gælder den bekræftede struktur og de udførte kontroller. Det beviser ikke, at tekstparseren har forstået hele opgaven.')
        st.caption('Brug positive symboler til radier og modstande. Ordning a<b kan skrives b=a+h med h>0. Autosave gemmes kun lokalt i brugerens EM1Solver-mappe.')

if __name__=='__main__':main()
