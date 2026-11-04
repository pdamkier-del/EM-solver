import json
import streamlit as st
from .core.historical import paths,load,run
from .core.planner import propose
from .core.problem import InputError
from .rendering.danish_solution import render
from .rendering.latex import document

def historical_mode(mode):
    recipes=[load(p) for p in paths() if load(p)['status'] in ('executable','partial')]
    byid={r['id']:r for r in recipes}
    months={'01':'Januar','02':'Februar','06':'Juni','11':'November'}
    def label(id):
        date,question=id.split(':');year,month=date.split('-')
        return f'{year} {months.get(month,month)} – Opgave {question}'
    selected=st.selectbox('Historiske opgaver',list(byid),format_func=label)
    recipe=byid[selected]
    st.caption(recipe['source']['answer'])
    st.write('Givet i originalopgaven:',recipe['given_source'])
    st.write('Søges i originalopgaven:',recipe['wanted_source'])
    edited=st.text_area('Maskinlæsbar opskrift (kan redigeres)',json.dumps(recipe,ensure_ascii=False,indent=2),height=220,key=selected)
    try:
        result=run(json.loads(edited))
        if result.passed:st.success('Opskriften reproducerer de gemte facitkontroller.')
        else:st.error('En eller flere facitkontroller fejler. Løsningen er ikke valideret.')
        with st.expander('Diagnostik: certificering og stable-status'):
            from .core.certification import blockers
            parsed=json.loads(edited)
            st.write('Problem: '+selected+'; facit: '+('correct' if result.passed else 'failed'))
            for step in parsed['path']:
                family=step['problem']['family'];answer=result.solutions[step['id']]
                why=blockers(family)
                st.write(family+': '+('stable' if answer.stable else 'experimental'))
                for reason in why:st.write(reason)
                for check in answer.checks:
                    if check.passed is not True:st.write(check.name)
        for name,answer in result.solutions.items():
            st.write('Beregningsled: '+name);render(st,answer,mode=mode)
            st.download_button('Gem LaTeX: '+name,document(answer),file_name=selected.replace(':','_')+'_'+name+'.tex',key='export_'+name)
    except (InputError,ValueError,TypeError,KeyError) as exc:st.error('Opskriften kunne ikke køres: '+str(exc))

def quick_mode():
    area=st.selectbox('Trin 1 – hovedområde',['EV','BA','DYN','Ved ikke'])
    given=st.multiselect('Trin 2 – hvad er givet?',['point charges','rho','sigma','lambda','E','V','J','I','B','A','flux','geometry'])
    wanted=st.multiselect('Trin 3 – hvad søges?',['E','V','rho','B','force','EMF','current','energy','power','inductance'])
    geometry=st.selectbox('Geometri',['Ukendt','Uendelig cylinder','Kuglesymmetri','Uendeligt plan','Generel'])
    symmetric=st.checkbox('Jeg har verificeret den nødvendige symmetri, ikke kun geometriens navn')
    proposals=propose(given,wanted,geometry,symmetric,area)
    if not proposals:
        st.info('Ingen sikker beregningsvej endnu. Angiv flere oplysninger eller brug manuelt metodevalg.');st.stop()
    for index,p in enumerate(proposals):st.write(('Anbefalet metode: ' if index==0 else 'Alternativ metode: ')+p.family+' — '+p.reason)
    selected=st.selectbox('Acceptér en metode eller vælg alternativ',range(len(proposals)),format_func=lambda i:proposals[i].family)
    p=proposals[selected];st.caption('Nødvendige input: '+p.requirements)
    st.info('Forslaget udfylder ikke manglende fysikdata. Tilpas eksempelinputtene nedenfor til din opgave.')
    return p.domain,p.family
