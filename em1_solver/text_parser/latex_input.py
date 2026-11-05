"""Bounded conversion of a small explicit LaTeX input grammar. No TeX execution."""
import re

def plain(text,depth=0):
    if depth>12:raise ValueError('LaTeX er for dybt indlejret.')
    text=text.replace(r'\left','').replace(r'\right','')
    text=re.sub(r'\\(?:,|;|!|quad\b|qquad\b)', ' ',text)
    for delimiter in (r'\(',r'\)',r'\[',r'\]'):text=text.replace(delimiter,'')
    text=text.replace('$','')
    def group(start):
        while start<len(text) and text[start].isspace():start+=1
        if start>=len(text) or text[start]!='{':raise ValueError('LaTeX kræver en afgrænset {...}-gruppe.')
        level=1;i=start+1
        while i<len(text) and level:
            if text[i]=='{':level+=1
            if text[i]=='}':level-=1
            if level>12:raise ValueError('LaTeX-grupper er for dybt indlejret.')
            i+=1
        if level:raise ValueError('LaTeX-gruppen mangler en afsluttende }.')
        return plain(text[start+1:i-1],depth+1),i
    result=[];i=0
    while i<len(text):
        command=re.match(r'\\(dfrac|frac|mathrm|mathbf|vec|hat)\b',text[i:])
        if command:
            name=command[1];value,end=group(i+len(command[0]))
            if name in ('frac','dfrac'):
                denominator,end=group(end);value='(('+value+')/('+denominator+'))'
            elif name=='hat':
                axis=value.strip().lstrip('\\')
                if axis not in ('x','y','z','r','s','phi','theta'):raise ValueError('Ukendt basis i LaTeX-hat.')
                value=' '+axis+'hat '
            result.append(value);i=end
        elif text[i] in '^_' and i+1<len(text) and text[i+1]=='{':
            value,end=group(i+1)
            if text[i]=='_' and not re.fullmatch(r'[A-Za-z0-9]+',value):raise ValueError('Indeks skal være et simpelt navn eller tal.')
            result.append('^('+value+')' if text[i]=='^' else '_'+value);i=end
        else:result.append(text[i]);i+=1
    text=''.join(result)
    return re.sub(r'\\(sin|cos|tan|exp|log|ln|sqrt)\b',r'\1',text)
