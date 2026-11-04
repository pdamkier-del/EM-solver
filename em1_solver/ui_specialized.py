"""Preserves all original solver interfaces behind the optional advanced form."""
import json
import streamlit as st
from .examples import EXAMPLES
from .core.registry import DOMAINS
from .core.new_problem import Parsed
from .core.task_runtime import run_confirmed
from .core.problem import InputError
from .core.assisted import UNITS
from .ui_assisted import exports
from .rendering.danish_solution import render
from .rendering.plain import text
from .rendering.latex import document
from .core import local_state

def changed():st.session_state['special_dirty']=True

def restore_specialized():
    saved=local_state.load('specialized.json');p=saved['problem'];family=p['family']
    st.session_state['special_domain']=p['domain'];st.session_state['special_family']=family
    for name,value in p['inputs'].items():
        if name in EXAMPLES[family]['variables']:st.session_state['special_'+family+name]=json.dumps(value) if not isinstance(value,str) else value
    for key,value in [('regions',p['regions']),('assumptions',p['assumptions']),('wanted',p['wanted'])]:st.session_state['special_'+key+'_'+family]=value
    st.session_state['special_units']=p['units'];st.session_state['special_numbers']=p['numbers'];st.session_state['special_positive']=p['positive']
    st.session_state['special_extra_records']=[dict(parameter=k,value=json.dumps(v) if not isinstance(v,str) else v) for k,v in p['inputs'].items() if k not in EXAMPLES[family]['variables']]
    st.session_state.pop('special_extra_'+family,None);st.session_state['special_confirm']=False;st.session_state['special_dirty']=False


def specialized(mode):
    st.caption('Specialiserede metoder: alle oprindelige inputmodeller. Matematiske udtryk bruger * og **. Vektorer/lister angives som JSON; ingen Python-kode udføres.')
    domain=st.selectbox('Område',['EV','BA','DYN'],key='special_domain')
    family=st.selectbox('Metode',[f for f in EXAMPLES if f in DOMAINS[domain]],key='special_family')
    spec=EXAMPLES[family]
    inputs={}
    for name,value in spec['variables'].items():
        raw=st.text_area(name,json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value,key='special_'+family+name,height=70,on_change=changed)
        try:inputs[name]=json.loads(raw)
        except ValueError:inputs[name]=raw
    with st.expander('Ekstra/ændrede givne størrelser'):
        import pandas as pd
        extra=st.data_editor(pd.DataFrame(st.session_state.get('special_extra_records',[]),columns=['parameter','value']),num_rows='dynamic',key='special_extra_'+family,hide_index=True,on_change=changed)
        for row in extra.itertuples():
            if not str(row.parameter).strip():continue
            raw=str(row.value)
            if raw=='null':inputs.pop(str(row.parameter),None);continue
            try:inputs[str(row.parameter)]=json.loads(raw)
            except ValueError:inputs[str(row.parameter)]=raw
    if family=='coulomb_integral' and inputs.get('kind')=='line' and len(inputs.get('parameters',[]))==1:
        inputs['parameter']=inputs.pop('parameters')[0]
        inputs['bounds']=inputs['bounds'][0]
    regions=st.text_area('Regioner',json.dumps(spec.get('regions',[])),key='special_regions_'+family,height=90,on_change=changed)
    assumptions=st.text_area('Fysiske vilkår (én pr. linje)','\n'.join(spec.get('assumptions',[])),key='special_assumptions_'+family,height=90,on_change=changed)
    wanted=st.text_input('Søges (kommasepareret)','',key='special_wanted_'+family,on_change=changed)
    units=st.text_area('Symbolenheder',json.dumps(UNITS),key='special_units',height=90,on_change=changed)
    numbers=st.text_area('Numeriske værdier med enheder','{}',key='special_numbers',height=70,on_change=changed)
    positive=st.text_input('Positive symboler','r,s,a,b,d,R,L,q,Q,I,J,rho,sigma,alpha,epsilon_r,epsilon_0,mu_0,m,v,V,B,omega,tau,N,A,k,C,Q0',key='special_positive',on_change=changed)
    payload=dict(domain=domain,family=family,inputs=inputs,regions=regions,assumptions=assumptions,wanted=wanted,units=units,numbers=numbers,positive=positive)
    if st.session_state.get('special_dirty'):
        try:local_state.save(payload,filename='specialized.json')
        except (OSError,ValueError) as exc:st.warning('Autosave: '+str(exc))
    parsed=None
    try:
        from .core.assisted import validate
        data={'solver_spec':dict(domain=domain,family=family,variables=inputs,regions=json.loads(regions),wanted=[w.strip() for w in wanted.split(',') if w.strip()])}
        parsed=Parsed('',data=data,wanted=[w.strip() for w in wanted.split(',') if w.strip()] or ['__all__'],units=json.loads(units),quantities=json.loads(numbers),positive=[v.strip() for v in positive.split(',') if v.strip()],assumptions=assumptions.splitlines())
        _,unknown=validate(parsed)
        st.warning('YELLOW — kontrollér den specialiserede struktur og dens fysiske vilkår før løsning.')
        if unknown:
            with st.expander('Uafklarede enhedskontroller'):
                for note in unknown:st.write(note)
    except (InputError,ValueError,TypeError,KeyError) as exc:st.error('RED — '+str(exc));parsed=None
    confirmed=st.checkbox('Jeg har verificeret den specialiserede struktur',key='special_confirm')
    if st.button('Løs opgave',disabled=not confirmed or parsed is None,key='special_solve') and confirmed and parsed is not None:
        try:
            answer=run_confirmed(parsed,False,timeout=25)
            local_state.save(payload,dict(text=text(answer),latex=document(answer)),filename='specialized.json')
            st.session_state['special_answer']=answer
            st.session_state['special_signature']=json.dumps([domain,family,inputs,regions,assumptions,wanted,units,numbers,positive])
        except (InputError,ValueError,TypeError,KeyError,OSError) as exc:st.error('Kan ikke afgøre problemet entydigt: '+str(exc))
    signature=json.dumps([domain,family,inputs,regions,assumptions,wanted,units,numbers,positive])
    if st.session_state.get('special_signature')==signature and 'special_answer' in st.session_state:
        render(st,st.session_state['special_answer'],mode);exports(st.session_state['special_answer'])

    with st.expander('Gendan specialiseret arbejde lokalt'):
        try:saved=local_state.load('specialized.json')
        except (OSError,ValueError) as exc:st.warning(str(exc));saved=None
        if saved:
            st.button('Gendan specialiseret opgave',on_click=restore_specialized)
            if saved.get('answer'):st.text_area('Gemt specialiseret løsningskopi',saved['answer']['text'],height=120)
