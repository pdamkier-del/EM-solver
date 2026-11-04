"""Small forward-chaining physics engine with explicit geometry prerequisites."""
from dataclasses import dataclass
import sympy as sp
from .problem import Problem, InputError
from .solution import solution
from .validation import EPS0, calculus, finite_integral, positive


@dataclass(frozen=True)
class Rule:
    name: str
    requires: tuple
    produces: str
    evaluate: object
    assumption: str | None = None
    equation: str = ''


def rules():
    return [
        Rule('Gradient af potentiale',('V','coordinates','system'),'E',lambda d:-calculus(d['coordinates'],d['system'])[0](d['V']),equation=r'\mathbf E=-\nabla V'),
        Rule('Gauss differentiallov',('E','coordinates','system'),'rho',lambda d:EPS0*calculus(d['coordinates'],d['system'])[1](d['E']),equation=r'\rho=\epsilon_0\nabla\cdot\mathbf E'),
        Rule('Rotation af vektorpotentiale',('A','coordinates','system'),'B',lambda d:calculus(d['coordinates'],d['system'])[2](d['A']),equation=r'\mathbf B=\nabla\times\mathbf A'),
        Rule('Normalfelt ved parameteriseret flade',('B','surface','coordinates','parameters'),'B_on_surface',lambda d:sp.Matrix(d['B']).subs(dict(zip(d['coordinates'],d['surface'])), simultaneous=True)),
        Rule('Orienteret fladeintegral',('B_on_surface','surface','parameters','surface_bounds'),'Phi',_surface_flux),
        Rule('Homogen magnetisk flux',('B_normal','area'),'Phi',lambda d:d['B_normal']*d['area'],'uniform_normal_B',r'\Phi=B_n A'),
        Rule('Faradays lov',('Phi','time','N'),'EMF',lambda d:-d['N']*sp.diff(d['Phi'],d['time']),equation=r'\mathcal E=-N\partial_t\Phi'),
        Rule('Ohms lov',('EMF','R'),'I',_ohm,'negligible_self_inductance',r'I=\mathcal E/R'),
        Rule('Joules lov',('I','R'),'P',_power,equation=r'P=I^2R'),
        Rule('Integreret varme',('P','time','time_bounds'),'W',lambda d:finite_integral(d['P'],(d['time'],*d['time_bounds'])),equation=r'W=\int Pdt'),
        Rule('Potentialforskel langs radial retning',('E_radial','coordinate','start','end'),'delta_V',lambda d:-finite_integral(d['E_radial'],(d['coordinate'],d['start'],d['end'])),equation=r'\Delta V=-\int E_r dr'),
        Rule('Arbejde på testladning',('test_charge','delta_V'),'W_external',lambda d:d['test_charge']*d['delta_V'],equation=r'W_{ext}=q\Delta V'),
    ]


def _ohm(data):
    positive(data['R'],'Resistans')
    return sp.simplify(data['EMF']/data['R'])


def _power(data):
    positive(data['R'],'Resistans')
    return sp.simplify(data['I']**2*data['R'])


def _surface_flux(d):
    if len(d['parameters'])!=2 or len(d['surface_bounds'])!=2:
        raise InputError('Fladeintegralet kræver to parametre og to grænsesæt.')
    surf=sp.Matrix(d['surface']);u,v=d['parameters']
    normal_area=surf.diff(u).cross(surf.diff(v))
    return finite_integral(sp.Matrix(d['B_on_surface']).dot(normal_area),*[(x,*b) for x,b in zip(d['parameters'],d['surface_bounds'])])


def derive(problem):
    """Return deterministic rule applications and unresolved requests, never guesses."""
    facts=dict(problem.variables|problem.functions)
    result=solution(problem,'Deterministisk kædning af fysiske relationer',
        'En relation anvendes kun når alle nødvendige størrelser og fysiske antagelser er angivet. Hvert nyt resultat har en navngivet regel og en startligning.',[])
    # The radial Gauss solver can seed the chain, only with full explicit context.
    if problem.regions and all(k in facts for k in ('coordinate','symmetry')):
        from ..solvers.electrostatics import gauss_radial
        seed=gauss_radial(problem)
        facts['Q_enc']=seed.symbolic_result['Q_enc'];facts['E_radial']=seed.symbolic_result['E']
        result.steps.extend(seed.steps)
        result.equations.extend(seed.equations)
    pending=list(rules())
    for _ in range(len(pending)+1):
        changed=False
        for rule in pending[:]:
            if rule.produces in facts:
                pending.remove(rule);continue
            if all(key in facts for key in rule.requires) and (rule.assumption is None or rule.assumption in problem.assumptions):
                computed=sp.simplify(rule.evaluate(facts))
                if isinstance(computed,sp.Basic) and computed.has(sp.zoo,sp.nan,sp.oo,-sp.oo):
                    raise InputError(f'{rule.name} gav et udefineret resultat.')
                facts[rule.produces]=computed
                result.add(rule.name,computed)
                if rule.equation:result.equations.append(rule.equation)
                pending.remove(rule);changed=True
        if not changed:break
    missing=[name for name in problem.wanted if name not in facts]
    result.symbolic_result={k:v for k,v in facts.items() if k not in problem.variables and k not in problem.functions}
    if missing:
        result.warnings.append('Kan ikke bestemme: '+', '.join(missing)+'. Mangler data, geometrikontekst eller eksplicitte antagelser.')
    result.direction='Retninger følger inputbasis og orienteringen af fladens parameterisering.'
    return result
