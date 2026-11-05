"""EM1-Math-1: bounded renderer-independent mathematical LaTeX fragments.

Checks the documented macro/structure profile, not mathematical correctness and
not a complete TeX parser. Never invokes a TeX engine or loads external content.
"""
import re
class LatexProfileError(ValueError):pass
PROFILE='EM1-Math-1'
COMMANDS=set('frac dfrac tfrac sqrt left right begin end mathrm mathbf mathit mathsf mathtt mathbb mathcal mathfrak mathscr boldsymbol operatorname text mbox rm bf it vec hat widehat dot ddot overline underline overrightarrow overbrace underbrace partial nabla int iint iiint oint oiint sum prod lim limits nolimits to rightarrow leftarrow infty cdot times div pm mp sin cos tan cot sec csc arcsin arccos arctan sinh cosh tanh log ln exp min max sup inf det gcd arg Re Im conjugate le leq ge geq ne neq lt gt equiv approx simeq sim propto perp parallel in notin ni not neg land lor wedge vee forall exists emptyset varnothing cup cap subset subseteq supset supseteq backslash colon quad qquad displaystyle textstyle scriptstyle scriptscriptstyle big Big bigg Bigg bigl bigr Bigl Bigr biggl biggr lvert rvert lVert rVert vert Vert lbrace rbrace langle rangle lfloor rfloor lceil rceil cdots ldots dots vdots ddots overset underset substack hbar ell wp aleph prime degree'.split())
COMMANDS.update('alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa varkappa lambda mu nu xi omicron pi varpi rho varrho sigma varsigma tau upsilon phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega'.split())
SYMBOLS=set([',',';',':','!',' ','{','}','|','_','%','#','&','\\'])
ENVIRONMENTS={'matrix','pmatrix','bmatrix','vmatrix','Vmatrix','smallmatrix','array','cases','aligned','gathered','split'}

def validate(fragment):
    if not isinstance(fragment,str) or len(fragment)>64000:raise LatexProfileError('LaTeX-fragmentet er for stort eller ikke tekst.')
    if '$' in fragment or re.search(r'<\s*/?\s*(?:script|iframe|img)\b',fragment,re.I):raise LatexProfileError('Forventet matematikfragment uden HTML eller display-delimiters.')
    braces=0;left=0;i=0
    while i<len(fragment):
        char=fragment[i]
        if char=='\\':
            token=re.match(r'\\([A-Za-z]+|[^A-Za-z])',fragment[i:])
            if not token:raise LatexProfileError('Afbrudt LaTeX-kommando.')
            name=token[1]
            if name not in COMMANDS and name not in SYMBOLS:raise LatexProfileError('Kommando uden for EM1-Math-1: '+name)
            if name=='left':left+=1
            if name=='right':
                left-=1
                if left<0:raise LatexProfileError('LaTeX right mangler left.')
            i+=len(token[0]);continue
        if char=='{':braces+=1
        elif char=='}':
            braces-=1
            if braces<0:raise LatexProfileError('LaTeX har en umatchet }.')
        elif char in '%#':raise LatexProfileError('Uescapet LaTeX-kommentar eller makroparameter.')
        i+=1
    if braces or left:raise LatexProfileError('LaTeX-grupper eller left/right er ikke afsluttet.')
    stack=[]
    for command,environment in re.findall(r'\\(begin|end)\{([^{}]+)\}',fragment):
        if environment not in ENVIRONMENTS:raise LatexProfileError('Miljø uden for EM1-Math-1: '+environment)
        if command=='begin':stack.append(environment)
        elif not stack or stack.pop()!=environment:raise LatexProfileError('LaTeX-miljøer matcher ikke.')
    if stack:raise LatexProfileError('LaTeX-miljø mangler end.')
    return fragment
