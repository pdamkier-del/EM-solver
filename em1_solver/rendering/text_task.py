"""Readable text-first presentation; engine metadata stays in the manual/debug flow."""
from .danish_solution import latex,NOTATION
import sympy as sp

def render(st,answer,interpretation,mode):
    f=interpretation.facts
    st.subheader('Metode');st.write(answer.method)
    if mode!='Eksamen':st.write(answer.reasoning)
    st.subheader('Givet')
    for source,detail in f['sources'].items():
        st.write(source+' = '+str(detail['formula']))
    for role,name in f['roles'].items():st.write(role.replace('_',' ')+': '+str(name))
    for name,value in f['numbers'].items():
        if not name.startswith('parser_'):st.write(name+' = '+value)
    region=interpretation.fields.get('regions')
    if region and isinstance(region.value,list):
        for r in region.value:st.write(str(r['lower'])+' < afstand < '+str(r['upper'])+': tæthed '+str(r['density']))
    if f.get('scope'):st.write('Gyldighedsområde: '+f['scope'])
    st.subheader('Søges');st.write(', '.join(answer.wanted))
    st.subheader('Udregning')
    for equation in answer.equations:st.latex(equation)
    for step in answer.steps:
        st.write(step.text)
        if step.expression is not None:st.latex(latex(step.expression))
    st.subheader('Resultat')
    for name,value in answer.symbolic_result.items():
        if answer.wanted and name not in answer.wanted:continue
        st.write(name+' ['+answer.units.get(name,'SI')+']')
        st.latex(r'\boxed{'+NOTATION.get(name,sp.latex(sp.Symbol(name)))+'='+latex(value)+'}')
    for name,value in answer.numerical_result.items():
        if not answer.wanted or name in answer.wanted:st.write(name+' ['+answer.units.get(name,'SI')+']');st.latex(latex(value))
    st.write(answer.direction)
    st.subheader('Kontrol')
    for check in answer.checks:st.write(('Bestået: ' if check.passed is True else 'Fejlet: ' if check.passed is False else 'Uafklaret: ')+check.name)
    for warning in answer.warnings:st.warning(warning)
