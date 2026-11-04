"""Local plain text export suitable for copy/paste."""
def text(answer):
    lines=['Metode: '+answer.method,'Givet: '+str(answer.givens),'Søges: '+', '.join(answer.wanted),'Hvorfor: '+answer.reasoning,'Startformler:',*answer.equations,'Mellemregninger:']
    for step in answer.steps:lines.append(step.text+(' = '+str(step.expression) if step.expression is not None else ''))
    lines+=['Resultat:']+[k+' = '+str(v)+' ['+answer.units.get(k,'')+']' for k,v in answer.symbolic_result.items()]
    lines+=['Numeriske værdier:']+[k+' = '+str(v)+' ['+answer.units.get(k,'')+']' for k,v in answer.numerical_result.items()]
    lines+=['Retning: '+answer.direction,'Kontrol:']+[c.name+': '+str(c.passed) for c in answer.checks]
    lines+=['Advarsler:',*answer.warnings]
    return '\n'.join(lines)
