"""Standalone LaTeX export; no compilation, network or remote rendering."""
import sympy as sp
from .danish_solution import latex,NOTATION

def escape(text):
    replacements={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    for char,command in {'μ':r'\mu','ε':r'\epsilon','π':r'\pi','σ':r'\sigma','τ':r'\tau','Δ':r'\Delta','ρ':r'\rho','φ':r'\phi','θ':r'\theta','∇':r'\nabla','κ':r'\kappa','λ':r'\lambda','ω':r'\omega','∫':r'\int','∞':r'\infty','≤':r'\leq','≥':r'\geq','→':r'\to','×':r'\times','²':r'{}^2','³':r'{}^3','₀':r'{}_0','₁':r'{}_1','₂':r'{}_2','₃':r'{}_3'}.items():
        replacements[char]=r'\ensuremath{'+command+'}'
    return ''.join(replacements.get(c,c) for c in str(text))

def document(answer):
    lines=[r'\documentclass{article}',r'\usepackage[utf8]{inputenc}',r'\usepackage[T1]{fontenc}',
           r'\usepackage{amsmath,amssymb}',r'\begin{document}']
    def section(title,body):lines.extend([r'\section*{'+title+'}',escape(body)])
    section('Genkendelse',answer.recognition);section('Metode',answer.method);section('Hvorfor?',answer.reasoning)
    section('Givet',answer.givens);section('Søges',', '.join(answer.wanted) or 'Se resultaterne nedenfor.')
    lines.append(r'\section*{Startformler}')
    lines += [r'\['+eq+r'\]' for eq in answer.equations]
    lines.append(r'\section*{Mellemregninger}')
    for step in answer.steps:
        lines.append(escape(step.text))
        if step.expression is not None:
            try:lines.append(r'\['+latex(step.expression)+r'\]')
            except (TypeError,ValueError,AttributeError):lines.append(escape(step.expression))
    lines.append(r'\section*{Resultat}')
    for key,value in answer.symbolic_result.items():
        lines.append(escape(key+' ['+answer.units.get(key,'')+']'))
        try:lines.append(r'\[\boxed{'+NOTATION.get(key,sp.latex(sp.Symbol(key)))+'='+latex(value)+r'}\]')
        except (TypeError,ValueError,AttributeError):lines.append(escape(value))
    section('Retning',answer.direction)
    lines.append(r'\section*{Numerisk indsættelse}')
    for key,value in answer.numerical_result.items():lines.extend([escape(key+' '+answer.units.get(key,'')),r'\['+latex(value)+r'\]'])
    section('Kontrol','; '.join(c.name+': '+('bestået' if c.passed else 'fejlet' if c.passed is False else 'uafklaret') for c in answer.checks))
    section('Advarsler','; '.join(answer.warnings))
    lines.append(r'\end{document}')
    return '\n'.join(lines)
