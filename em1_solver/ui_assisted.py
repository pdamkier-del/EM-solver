"""The primary exam form: one confirmation panel, geometry-specific fields."""
import json,copy
from dataclasses import asdict
import streamlit as st
from .core.assisted import P,F,ORIENT,AXES,WANTS,defaults,default_regions,compile_problem,validate
from .core.new_problem import parse
from .core.problem import InputError
from .core.task_runtime import run_confirmed
from .core import local_state
from .rendering.danish_solution import render
from .rendering.latex import document
from .rendering.plain import text


def guess_preset(parsed):
    d=parsed.data;g=parsed.geometry
    if 'J' in d:return 'ba_cylinder'
    if 'A' in d:return 'ba_vector_potential'
    if 'B' in d and 'time' in d:return 'dyn_fixed'
    if 'V' in d:return 'ev_potential'
    if 'rho' in d:return {'kugle':'ev_sphere','kugleskal':'ev_shell','cylinder':'ev_cylinder','cylinderskal':'ev_hollow','plan':'ev_slab'}.get(g,'ev_cylinder')
    if 'lambda' in d or g in ('ring','bue','linje'):return {'ring':'ev_ring','bue':'ev_arc','linje':'ev_line'}.get(g,'ev_line')
    return 'ev_points'


def seed(key,parsed=None):
    preset=P[key]
    st.session_state['af_preset']=key;st.session_state['af_domain']=preset.domain
    for name,value in defaults(key,parsed).items():st.session_state['af_'+name]=value
    rows=default_regions(key) if preset.regions else []
    if parsed and parsed.data.get('regions'):rows=copy.deepcopy(parsed.data['regions'])
    for i,row in enumerate(rows):
        source=parsed.data.get(preset.source,parsed.data.get('density')) if parsed else None
        row['density']='@source' if not parsed or not parsed.data.get('regions') or row.get('density')==source else row.get('density','@source')
        for name,value in row.items():st.session_state[f'af_region_{i}_{name}']=str(value)
    st.session_state['af_region_count']=len(rows)
    st.session_state['af_method']=preset.family
    options=WANTS[preset.family]
    wanted=[w for w in parsed.wanted if w in options] if parsed else []
    st.session_state['af_wanted']=wanted or [next((w for w in options if w in ('E','B','EMF','C','F','torque_magnitude','L','I','P')),options[0])]
    st.session_state['af_assumptions']=list(preset.assumptions)
    st.session_state['af_source_type']=preset.source
    st.session_state['af_charge_records']=[dict(q='q',x='0',y='0',z='0')]
    st.session_state['af_confirm']=False
    st.session_state['af_dirty']=False
    st.session_state.pop('af_answer',None)
    if parsed and parsed.data.get('orientation',{}).get('plane'):st.session_state['af_plane']=parsed.data['orientation']['plane']
    if parsed:
        st.session_state['af_numbers']=json.dumps(parsed.quantities,ensure_ascii=False)
        st.session_state['af_units']=json.dumps(parsed.units,ensure_ascii=False)


def exports(answer):
    st.download_button('Eksportér LaTeX',document(answer),file_name='em1_solution.tex')
    st.download_button('Gem som tekst',text(answer),file_name='em1_solution.txt',mime='text/plain')
    with st.expander('Kopiér løsning'):
        st.code(text(answer),language=None)
    with st.expander('Kopiér slutresultat'):
        st.code('\n'.join(k+' = '+str(v)+' '+answer.units.get(k,'') for k,v in answer.symbolic_result.items() if not answer.wanted or k in answer.wanted),language=None)


def dirty():st.session_state['af_dirty']=True

def change_domain():
    seed(next(k for k,p in P.items() if p.domain==st.session_state['af_domain']));dirty()

def change_preset():
    seed(st.session_state['af_preset']);dirty()

def preserve_source():
    st.session_state['af_original']=st.session_state.get('exam_text',st.session_state.get('af_original',''))
    st.session_state['af_known']=st.session_state.get('exam_known',st.session_state.get('af_known',''))

def restore_saved():
    saved=local_state.load();payload=saved['problem'];seed(payload['preset'])
    st.session_state['exam_text']=payload['original'];st.session_state['exam_known']=payload['known']
    st.session_state['af_original']=payload['original'];st.session_state['af_known']=payload['known']
    st.session_state['af_analyzed_text']=(payload['original'],payload['known']);st.session_state['af_parsed']={}
    for name,value in payload['values'].items():st.session_state['af_'+name]=value
    st.session_state['af_region_count']=len(payload['regions'])
    for i,row in enumerate(payload['regions']):
        for name,value in row.items():st.session_state[f'af_region_{i}_{name}']=str(value)
    st.session_state['af_wanted']=payload['wanted'];st.session_state['af_assumptions']=payload['assumptions']
    st.session_state['af_numbers']=payload['numbers'] if isinstance(payload['numbers'],str) else json.dumps(payload['numbers'])
    st.session_state['af_units']=payload['units'] if isinstance(payload['units'],str) else json.dumps(payload['units'])
    restorekeys={'plane':'af_plane','normal':'af_normal','current':'af_curve_current' if payload['preset'] in ('ba_line','ba_ring','ba_arc') else 'af_current','velocity':'af_v_axis','B':'af_B_axis','E':'af_E_axis'}
    for name,key in restorekeys.items():st.session_state[key]=payload['orientation'][name]
    if payload.get('charges'):
        st.session_state['af_charge_records']=[dict(q=q,x=pos[0],y=pos[1],z=pos[2]) for q,pos in payload['charges']]
        st.session_state.pop('af_charges',None)
    st.session_state['af_dirty']=False

def assisted_mode(mode,manual=False):
    st.subheader('Manuel solver' if manual else 'Ny opgave')
    if not manual:
        if 'exam_text' not in st.session_state:st.session_state['exam_text']=st.session_state.get('af_original','')
        if 'exam_known' not in st.session_state:st.session_state['exam_known']=st.session_state.get('af_known','')
        original=st.text_area('Indsæt opgaveteksten',key='exam_text',height=200,on_change=preserve_source)
        known=st.text_area('Givne størrelser (valgfrit, én pr. linje)',key='exam_known',height=70,on_change=preserve_source)
        st.session_state['af_original']=original;st.session_state['af_known']=known
        if st.button('Analysér opgave'):
            try:
                parsed=parse(original,known)
                st.session_state['af_parsed']=asdict(parsed)
                st.session_state['af_analyzed_text']=(original,known)
                seed(guess_preset(parsed),parsed)
                st.session_state['af_dirty']=True
            except InputError as exc:st.error(str(exc))
        if 'af_parsed' not in st.session_state:
            st.caption('Indsæt tekst, eller vælg Manuel solver. Alle antagelser og input skal bekræftes før løsning.')
            restore_panel();return
    else:
        original=st.session_state.get('af_original','');known=st.session_state.get('af_known','')
        if 'af_preset' not in st.session_state:seed('ev_cylinder')
    source_changed=not manual and st.session_state.get('af_analyzed_text')!=(original,known)
    if source_changed:st.warning('Teksten er ændret. Analysér igen; den tidligere løsning er skjult.')
    st.subheader('Bekræft problem')
    st.caption('Preset er en synlig, redigerbar model. Bekræft at den matcher opgaven; formularen må ikke erstatte din fysiske vurdering.')
    for note in st.session_state.get('af_parsed',{}).get('warnings',[]):st.caption('Kontrollér: '+note)
    columns=st.columns([1,2,1])
    domain=columns[0].selectbox('Område',['EV','BA','DYN'],key='af_domain',on_change=change_domain)
    keys=[k for k,p in P.items() if p.domain==domain]
    key=columns[1].selectbox('Geometri / preset',keys,format_func=lambda k:P[k].label,key='af_preset',on_change=change_preset)
    preset=P[key]
    source=columns[2].selectbox('Kilde',['q','lambda','sigma','rho','E','V','I','J','B','A','P','M'],key='af_source_type',on_change=dirty)
    method=st.selectbox('Metode',[preset.family]+[f for f in WANTS if f!=preset.family],key='af_method',on_change=dirty)
    fields={}
    # Related scalar inputs share rows. Source function occupies the full width.
    dipole_vector=key=='ba_dipole' and st.selectbox('Dipolform',['Størrelse + vinkel','Vektorer'],key='af_dipole_form')=='Vektorer'
    for field in preset.fields:
        if dipole_vector:
            fields[field.key]=field.default
            continue
        label=field.label+(' ['+field.unit+']' if field.unit!='1' else '')
        fields[field.key]=st.text_input(label,key='af_'+field.key,on_change=dirty)
    if dipole_vector:
        fields['moment_vector']=st.text_input('Dipolmoment (mx,my,mz) [A*m²]',value='[m0,0,0]',key='af_m_vector',on_change=dirty)
        fields['B_vector']=st.text_input('Magnetfelt (Bx,By,Bz) [T]',value='[0,0,B0]',key='af_B_vector',on_change=dirty)
    charges=None
    if key=='ev_points':
        import pandas as pd
        table=st.data_editor(pd.DataFrame(st.session_state.get('af_charge_records',[dict(q='q',x='0',y='0',z='0')])),num_rows='dynamic',key='af_charges',hide_index=True,on_change=dirty)
        charges=[[str(row.q),[str(row.x),str(row.y),str(row.z)]] for row in table.itertuples()]
    regions=[]
    if preset.regions:
        st.markdown('**Regioner** — kilde/materiale; tomrum udenfor udfyldes af solveren. `@source` bruger kildefunktionen ovenfor.')
        c1,c2=st.columns(2)
        if c1.button('Tilføj region'):
            i=st.session_state['af_region_count'];previous_upper=st.session_state.get(f'af_region_{i-1}_upper','0')
            for name,value in dict(lower=previous_upper,upper='R+h',density='@source',permittivity='epsilon_0').items():st.session_state[f'af_region_{i}_{name}']=value
            st.session_state['af_region_count']=i+1;dirty();st.rerun()
        if c2.button('Fjern sidste region',disabled=st.session_state['af_region_count']==0):st.session_state['af_region_count']-=1;dirty();st.rerun()
        for i in range(st.session_state['af_region_count']):
            cols=st.columns(4);row={}
            for col,name,label in zip(cols,['lower','upper','density','permittivity'],['Fra','Til','Tæthed','Permittivitet']):row[name]=col.text_input(f'{label} – region {i+1}',key=f'af_region_{i}_{name}',on_change=dirty)
            regions.append(row)
    wanted=st.multiselect('Søges',WANTS[preset.family],key='af_wanted',on_change=dirty)
    if key=='ev_capacitor' and set(wanted)&{'V','U'}:fields['charge']=st.text_input('Given ladning [C]',value='Q',key='af_charge',on_change=dirty)
    if key=='ev_points' and 'F' in wanted:fields['test_charge']=st.text_input('Testladning [C]',value='q_test',key='af_test_charge',on_change=dirty)
    if key in ('dyn_fixed','dyn_moving') and 'W' in wanted:
        fields['time_start']=st.text_input('Starttid [s]',value='0',key='af_time_start',on_change=dirty)
        fields['time_end']=st.text_input('Sluttid [s] (efter start)',value='T',key='af_time_end',on_change=dirty)
    orientation=ORIENT.copy()
    with st.expander('Orientering og fortegn',expanded=True):
        if key in ('ev_line','ev_ring','ev_arc','ba_line','ba_ring','ba_arc','ev_infinite_line','dyn_fixed','dyn_moving','ba_sheet','ev_plane','ev_slab'):
            orientation['plane']=st.selectbox('Plan',['xy','yz','zx'],key='af_plane',on_change=dirty)
            orientation['normal']=st.selectbox('Normal',list(AXES),index=4,key='af_normal',on_change=dirty)
        if key in ('ba_line','ba_ring','ba_arc'):
            orientation['current']=st.selectbox('Positiv strøm langs kurven',['+parameter','-parameter'],key='af_curve_current',on_change=dirty)
            st.caption('Kurvens voksende parameter bestemmer den positive strømretning.')
        if key=='ba_sheet':orientation['current']=st.selectbox('Strømretning',list(AXES),key='af_current',on_change=dirty)
        if key in ('dyn_fixed','dyn_moving','dyn_sliding','dyn_rotating','ba_lorentz'):orientation['B']=st.selectbox('B-retning',list(AXES),index=4,key='af_B_axis',on_change=dirty)
        if key in ('dyn_sliding','ba_lorentz'):orientation['velocity']=st.selectbox('Hastighedsretning',list(AXES),key='af_v_axis',on_change=dirty)
        if key=='ba_lorentz':orientation['E']=st.selectbox('E-retning',list(AXES),key='af_E_axis',on_change=dirty)
        if key=='ba_dipole':st.caption('Theta måles fra B mod m; torque_theta er positiv mod voksende theta. Vektormoment vises med højrehåndsreglen.')
        if key=='dyn_rotating':st.caption('Stang langs +x; rotation om +z. Lokal hastighed er +y gange omega·afstand.')
        if preset.family in ('gauss_radial','ampere'):
            st.caption('EV: positiv radial/normal afstand og modsat retning på modsatte side af et plan. BA: aksial strøm +z giver B i +phi. Negative kildefunktioner vender retningen.')
        if key=='ba_material':st.caption('Aksial magnetisering +z; normal på cylinderfladen +s. Funktionen kan have negativt fortegn.')
    assumptions=st.multiselect('Bekræft fysiske vilkår',list(dict.fromkeys([*preset.assumptions,'linear_isotropic_dielectric','off_source'])),key='af_assumptions',on_change=dirty)
    with st.expander('Tal, enheder og avanceret kontrol',expanded=False):
        numbers=st.text_area('Numeriske værdier med enheder',value='{}',key='af_numbers',on_change=dirty)
        units=st.text_area('Ekstra/ændrede symbolenheder',value='{}',key='af_units',on_change=dirty)
        st.caption('Alle viste enheder og antagelser er en del af den bekræftede model. Brug radius R og modstand Z i samme problem.')
    evaluate=st.checkbox('Evaluér kurveintegraler analytisk (med tidsgrænse)',value=False)
    confirmed=st.checkbox('Jeg har verificeret geometri, kilder, enheder, retning og antagelser',key='af_confirm',on_change=dirty)
    payload=dict(original=original,known=known,preset=key,values=fields,regions=regions,wanted=wanted,orientation=orientation,assumptions=assumptions,numbers=numbers,units=units,method=method,charges=charges)
    draft_signature=json.dumps(payload,sort_keys=True,ensure_ascii=False)
    if st.session_state.get('af_dirty') and st.session_state.get('af_last_draft')!=draft_signature:
        try:local_state.save(payload);st.session_state['af_last_draft']=draft_signature
        except (OSError,ValueError) as exc:st.warning('Autosave kunne ikke skrives: '+str(exc))
    parsed=None;notes=[]
    try:
        if source!=preset.source:raise InputError('Kildetypen passer ikke til preset. Vælg en geometri/metode for den valgte kilde.')
        parsed=compile_problem(key,fields,regions,wanted,orientation,assumptions,original,json.loads(numbers),json.loads(units),method=method,charges=charges)
        problem,notes=validate(parsed)
        status='GREEN' if confirmed and not notes and not source_changed else 'YELLOW'
        (st.success if status=='GREEN' else st.warning)(status+' — '+('de krævede input og udførte forhåndskontroller er bekræftet.' if status=='GREEN' else 'kontrollér input, vilkår og orientering før løsning.'))
        for note in notes:st.warning(note)
    except (InputError,ValueError,TypeError,KeyError) as exc:st.error('RED — '+str(exc));parsed=None
    if parsed:
        signature=json.dumps(payload,sort_keys=True,ensure_ascii=False)
    else:signature=None
    if st.button('Løs opgave',disabled=parsed is None or not confirmed or source_changed) and parsed is not None and confirmed and not source_changed:
        st.session_state.pop('af_answer',None)
        try:
            with st.spinner('Beregner lokalt …'):answer=run_confirmed(parsed,evaluate)
            st.session_state['af_answer']=answer;st.session_state['af_signature']=signature
            local_state.save(payload,dict(text=text(answer),latex=document(answer),result={k:str(v) for k,v in answer.symbolic_result.items()}))
        except (InputError,OSError,ValueError) as exc:st.error(str(exc))
    if not source_changed and st.session_state.get('af_signature')==signature and 'af_answer' in st.session_state:
        answer=st.session_state['af_answer']
        more=st.button('Forklar mere')
        render(st,answer,'Forklaring' if more else mode)
        exports(answer)
    restore_panel()


def restore_panel():
    with st.expander('Gendan seneste lokale arbejde'):
        try:saved=local_state.load()
        except (OSError,ValueError) as exc:st.warning('Autosave kunne ikke læses: '+str(exc));return
        if not saved:st.caption('Der er endnu intet gemt lokalt.');return
        st.caption(str(local_state.path()))
        st.button('Gendan opgave',on_click=restore_saved)
        if saved.get('answer'):
            st.text_area('Senest gemte løsning (historisk kopi)',saved['answer']['text'],height=180)
            st.download_button('Hent senest gemte tekst',saved['answer']['text'],file_name='gendannet_losning.txt')
