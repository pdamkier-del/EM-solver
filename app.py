"""The offline exam application. No user needs to open solver code."""
import streamlit as st
from em1_solver.core.startup import check
from em1_solver.ui_assisted import assisted_mode
from em1_solver.ui_workflows import historical_mode

TECH_CSS = r"""
<style>
:root {
  --em-bg: #07110e;
  --em-panel: #0d1a16;
  --em-panel-2: #11251e;
  --em-line: rgba(91,255,180,.20);
  --em-accent: #63ffb1;
  --em-text: #e5fff2;
  --em-muted: #8fb7a4;
}
html, body, [data-testid="stAppViewContainer"] {
  background:
    linear-gradient(rgba(99,255,177,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99,255,177,.025) 1px, transparent 1px),
    var(--em-bg);
  background-size: 28px 28px;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], #MainMenu, footer { visibility: hidden; height: 0; }
.block-container {
  max-width: 1480px;
  padding-top: 1.35rem;
  padding-bottom: 3rem;
}
h1, h2, h3 {
  letter-spacing: .025em;
}
h1 {
  font-family: Consolas, "Cascadia Mono", monospace !important;
  font-weight: 700 !important;
  text-transform: uppercase;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--em-line) !important;
  background: rgba(13,26,22,.65);
}
div.stButton > button, div.stDownloadButton > button {
  border: 1px solid rgba(99,255,177,.34);
  background: linear-gradient(180deg, rgba(99,255,177,.10), rgba(99,255,177,.035));
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
  border-color: var(--em-accent);
  color: var(--em-accent);
}
input, textarea {
  font-family: Consolas, "Cascadia Mono", monospace !important;
}
.em-topline {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:1rem;
  border-bottom:1px solid var(--em-line);
  padding:0 0 .8rem 0;
  margin-bottom:.65rem;
}
.em-kicker {
  font-family:Consolas,"Cascadia Mono",monospace;
  color:var(--em-muted);
  font-size:.78rem;
  letter-spacing:.14em;
  text-transform:uppercase;
}
.em-statuses {
  display:flex;
  flex-wrap:wrap;
  gap:.45rem;
  justify-content:flex-end;
}
.em-chip {
  font-family:Consolas,"Cascadia Mono",monospace;
  font-size:.72rem;
  letter-spacing:.06em;
  padding:.28rem .52rem;
  border:1px solid rgba(99,255,177,.28);
  border-radius:999px;
  color:var(--em-accent);
  background:rgba(99,255,177,.06);
}
.em-sub {
  color:var(--em-muted);
  font-family:Consolas,"Cascadia Mono",monospace;
  margin-top:-.35rem;
  margin-bottom:1.1rem;
}
</style>
"""

def main():
    st.set_page_config(page_title='EM1 Solver', page_icon='⚡', layout='wide')
    st.markdown(TECH_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="em-topline">
          <div>
            <div class="em-kicker">LOCAL ELECTROMAGNETICS WORKSTATION</div>
          </div>
          <div class="em-statuses">
            <span class="em-chip">● LOCAL ENGINE</span>
            <span class="em-chip">NO NETWORK</span>
            <span class="em-chip">NO AI</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title('EM1 // FIELD SOLVER')
    st.markdown(
        '<div class="em-sub">Deterministisk lokal beregning · 127.0.0.1 · eksamensværktøj</div>',
        unsafe_allow_html=True,
    )

    @st.cache_resource(show_spinner=False)
    def readiness():
        return check()

    errors=readiness()
    if errors:
        st.error('Systemstatus: Ikke klar')
        for error in errors:
            st.error(error)
        st.stop()

    workflow=st.radio(
        'Arbejdsgang',
        ['Ny opgave','Historiske opgaver','Manuel solver','Hjælp'],
        horizontal=True,
    )
    exam=st.toggle('Eksamenstilstand',value=True)
    mode='Eksamen' if exam else 'Forklaring'

    if workflow=='Ny opgave':
        assisted_mode(mode)
    elif workflow=='Manuel solver':
        form=st.selectbox('Formular',['Geometri-formular','Specialiseret metode'])
        if form=='Geometri-formular':
            assisted_mode(mode,manual=True)
        else:
            from em1_solver.ui_specialized import specialized
            specialized(mode)
    elif workflow=='Historiske opgaver':
        historical_mode(mode)
    else:
        st.subheader('Kort eksamens-runbook')
        st.markdown(
            '1. Indsæt opgaven og vælg **Analysér opgave**, eller gå direkte til **Manuel solver**.\n'
            '2. Vælg område og geometri; ret kilde, regioner og søges.\n'
            '3. Kontrollér orientering, enheder og de synlige fysiske vilkår.\n'
            '4. Bekræft input, og vælg **Løs opgave**.\n'
            '5. Kontrollér resultatets fortegn, regiongrænser og warnings. Gem tekst eller LaTeX lokalt.'
        )
        st.markdown(
            '**EV:** Gauss kræver radial/plan symmetri; ellers Coulomb. '
            '**BA:** Ampère kræver passende symmetri; ellers Biot–Savart. '
            '**DYN:** Integrer den orienterede flux, og differentier hele tidsafhængigheden. '
            'Lenz bestemmer fortegnet.'
        )
        st.info(
            'GREEN gælder den bekræftede struktur og de udførte kontroller. '
            'Det beviser ikke, at tekstparseren har forstået hele opgaven.'
        )
        st.caption(
            'Brug positive symboler til radier og modstande. Ordning a<b kan skrives b=a+h med h>0. '
            'Autosave gemmes kun lokalt i brugerens EM1Solver-mappe.'
        )

if __name__=='__main__':
    main()
