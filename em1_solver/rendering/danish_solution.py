import sympy as sp

NOTATION={'E':r'\mathbf E','E_vector':r'\mathbf E','B':r'\mathbf B','F':r'\mathbf F','V':'V','rho':r'\rho','Q':'Q','Q_enc':r'Q_{enc}','I':'I','I_charge':r'I_{charge}','P':'P','W':'W','U':'U','Phi':r'\Phi_B','EMF':r'\mathcal E','C':'C','L':'L','M':'M','v':'v','v_infinity':r'v_\infty','tau':r'\tau'}

def latex(value):
    if isinstance(value,dict):
        return r'\begin{aligned}'+r'\\'.join(sp.latex(k)+' &= '+latex(v) for k,v in value.items())+r'\end{aligned}'
    if isinstance(value,(list,tuple)):
        return sp.latex(sp.Tuple(*[sp.Tuple(*v) if isinstance(v,(list,tuple)) else v for v in value]))
    return sp.latex(value)

def render_detailed(st,solution,mode='Forklaring'):
    st.subheader('Genkendelse');st.write(solution.recognition)
    st.subheader('Metode');st.write(solution.method)
    st.subheader('Hvorfor?');st.write(solution.reasoning)
    st.subheader('Givet')
    for name,value in solution.givens.items():
        st.write(name)
        try:st.latex(latex(value))
        except (TypeError,ValueError,AttributeError):st.write(str(value))
    st.subheader('Søges');st.write(', '.join(solution.wanted) or 'De størrelser, som denne metode kan bestemme ud fra input.')
    st.subheader('Startformler')
    for eq in solution.equations:st.latex(eq)
    st.subheader('Mellemregninger')
    for step in solution.steps:
        st.write(step.text)
        if step.expression is not None:
            try:st.latex(latex(step.expression))
            except (TypeError,ValueError,AttributeError):st.write(str(step.expression))
    st.subheader('Resultat')
    for name,value in solution.symbolic_result.items():
        if mode=='Eksamen' and solution.wanted and name not in solution.wanted:continue
        st.write(name + (f" [{solution.units[name]}]" if name in solution.units else ''))
        try:st.latex(r'\boxed{'+NOTATION.get(name,sp.latex(sp.Symbol(name)))+'='+latex(value)+'}')
        except (TypeError,ValueError,AttributeError):st.write(str(value))
    st.subheader('Retning');st.write(solution.direction or 'Se fortegn og komponenter i resultatet.')
    st.subheader('Numerisk indsættelse')
    if not solution.numerical_result:st.write('Ingen fuldt numeriske resultater med de angivne værdier.')
    for key,value in solution.numerical_result.items():
        st.write(key+' '+solution.units.get(key,''));st.latex(latex(value))
    st.subheader('Kontrol')
    if not solution.checks:st.write('Ingen automatiske identitetskontroller udført for denne inputtype.')
    for check in solution.checks:
        st.write(('Bestået' if check.passed is True else 'Fejlet' if check.passed is False else 'Uafklaret')+': '+check.name)
        if check.detail:st.write(check.detail)
    st.caption('Enhedsetiketter er SI-konventioner; de er ikke i sig selv en gennemført dimensionskontrol af symbolske input.')
    st.subheader('Advarsler')
    for warning in solution.warnings:st.warning(warning)
    if solution.stable:st.caption('Stable: gyldigt familiecertifikat og beståede fysiske og symbolske dimensionskontroller for dette input.')
    else:st.caption('Experimental for dette input: certifikat og/eller tilstrækkelige dimensionskontroller mangler.')


def render(st,solution,mode='Forklaring'):
    if mode!='Eksamen':return render_detailed(st,solution,mode)
    st.subheader('Metode');st.write(solution.method)
    st.subheader('Givet');st.write(solution.givens)
    st.subheader('Søges');st.write(', '.join(solution.wanted))
    st.subheader('Startformler')
    for eq in solution.equations:st.latex(eq)
    st.subheader('Mellemregninger')
    for step in solution.steps:
        st.write(step.text)
        if step.expression is not None:
            try:st.latex(latex(step.expression))
            except (TypeError,ValueError,AttributeError):st.write(str(step.expression))
    st.subheader('Resultat')
    for name,value in solution.symbolic_result.items():
        if solution.wanted and name not in solution.wanted:continue
        st.write(name+' '+solution.units.get(name,''))
        try:st.latex(r'\boxed{'+NOTATION.get(name,sp.latex(sp.Symbol(name)))+'='+latex(value)+'}')
        except (TypeError,ValueError,AttributeError):st.write(str(value))
    for name,value in solution.numerical_result.items():
        if solution.wanted and name not in solution.wanted:continue
        st.write(name+' '+solution.units.get(name,''));st.latex(latex(value))
    st.subheader('Retning');st.write(solution.direction or 'Se fortegn og de angivne komponenter/basis.')
    st.subheader('Kontrol')
    for check in solution.checks:st.write(('Bestået: ' if check.passed is True else 'Fejlet: ' if check.passed is False else 'Uafklaret: ')+check.name)
    if solution.warnings:
        st.subheader('Advarsler')
        for warning in solution.warnings:st.warning(warning)
