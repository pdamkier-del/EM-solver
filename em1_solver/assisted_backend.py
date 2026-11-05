"""Explicit, offline DYN modelling boundary; separate from frozen raw-text API.

No example values, orientations or initial conditions become physical givens.
Every subproblem shares declared data but is solved independently: no hidden
transfer of results, recipe lookup or interpretation of the prose.
"""
import copy
import json
import re
from .core.new_problem import Parsed
from .core.task_runtime import run_confirmed
from .rendering.structured import serialize

VERSION = 'assisted-1.0'
VARIABLE_UNITS={'time':'s','flux':'Wb','N':'1','B_normal':'T','area':'m^2','R':'ohm',
    'source':'m (vektor)','v':'m/s (vektor)','B':'T (vektor)','mass':'kg',
    'coupling':'T*m','voltage':'V','drive_force':'N','initial_velocity':'m/s',
    'C':'F','Q0':'C','L':'H','I0':'A','E':'V/m','coordinate':'m','plate_radius':'m',
    'fraction':'1','time_bounds':'s (to grænser)',
    'parameter':'enhed som kurveparameteren kræver','bounds':'grænser med tilhørende koordinatenhed',
    'flux_integrand':'Wb divideret med integrationskoordinaternes samlede enhed'}
MODELS = {
    'faraday_integral': dict(family='faraday', required=['time','flux_integrand','bounds','N'], optional=['R','time_bounds'],
        assumptions=[], orientation='Integranden indeholder B dot normal og hele areal-Jacobianen; bounds angiver fladekoordinater med grænser. Positivt omløb følger normalen.'),
    'faraday_flux': dict(family='faraday', required=['time','flux','N'], optional=['R','time_bounds'],
        assumptions=[], orientation='Flux pr. vinding er fortegnet i den valgte fladenormal; positiv strøm følger højrehåndsreglen.'),
    'faraday_uniform': dict(family='faraday', required=['time','B_normal','area','N'], optional=['R','time_bounds'],
        assumptions=['uniform_normal_B'], orientation='B_normal er den signerede normalprojektion; area er positivt. Positiv strøm følger fladenormalens højrehåndsregel.'),
    'motional_curve': dict(family='motional_emf', required=['source','parameter','bounds','v','B','time'], optional=['R','time_bounds'],
        assumptions=[], orientation='source med stigende parameter definerer den positive lederretning; v og B er kartesiske komponenter.'),
    'feedback': dict(family='feedback', required=['mass','R','coupling','voltage','drive_force','time','initial_velocity'], optional=['time_bounds'],
        assumptions=['constant_coefficients','negligible_self_inductance','no_friction'], orientation='Vælg retninger så EMF=k*v, kraft=k*I og I=(voltage-k*v)/R; coupling=k er fortegnet.'),
    'RC_discharge': dict(family='rc_transient', required=['time','R','C','Q0'], optional=['fraction'], fixed={'kind':'RC'},
        assumptions=['constant_coefficients'], orientation='Kildekoblingen er afbrudt ved t=0. Q(0)=Q0; I er positiv afladningsstrøm og I_charge=dQ/dt.'),
    'RL_step': dict(family='rc_transient', required=['time','R','L','voltage','I0'], optional=[], fixed={'kind':'RL'},
        assumptions=['constant_coefficients'], orientation='Seriekreds: L*dI/dt+R*I=voltage for t>=0, I(0)=I0; spændingen er konstant.'),
    'displacement_disk': dict(family='ampere_maxwell', required=['E','time','coordinate','plate_radius'], optional=[],
        assumptions=['uniform_axial_E','circular_symmetry','negligible_edge_effects','vacuum_gap'], orientation='E er den signerede +z-komponent; coordinate er positiv cylindrisk afstand; B er +phi-komponenten.'),
}


def validate_card(parsed):
    """Runs only in the bounded, network-blocked worker; no GUI-thread SymPy."""
    import sympy as sp
    from .core.new_problem import build
    from .core.validation import positive
    from .core.units import si
    problem=build(parsed);v=problem.variables;model=parsed.data['assisted_model_card']
    t=v.get('time')
    if not isinstance(t,sp.Symbol):raise ValueError('Tid skal være et variabelnavn, ikke et tal eller udtryk.')
    numbers={k:sp.Float(str(si(value,problem.numerical_units[k]).magnitude)) for k,value in problem.numerical_values.items()}
    positive_fields={'R','C','L','mass','N','plate_radius'}
    if model=='faraday_uniform':positive_fields.add('area')
    if model=='displacement_disk':positive_fields.add('coordinate')
    constants={'R','C','L','mass','N','plate_radius'}
    if model in ('RC_discharge','RL_step'):constants|={'Q0','I0','voltage'}
    for key in constants & set(v):
        if sp.sympify(v[key]).has(t):raise ValueError(key+' skal være tidsuafhængig i denne model.')
    for key in positive_fields & set(v):
        value=sp.sympify(v[key]).subs(numbers)
        if key=='area' and value.has(t):
            if 'positive_area_on_interval' not in problem.assumptions:raise ValueError('Bekræft positive_area_on_interval for det tidsafhængige areals anvendelsesinterval.')
        else:positive(value,key)
    if 'time_bounds' in v:
        lo,hi=v['time_bounds']
        positive(sp.simplify((hi-lo).subs(numbers)),'Tidsintervallets længde')
    if model=='motional_curve':
        if not isinstance(v['parameter'],sp.Symbol):raise ValueError('Kurveparameteren skal være et variabelnavn.')
        lo,hi=v['bounds'];positive(sp.simplify((hi-lo).subs(numbers)),'Kurveintervallets længde')


def catalog():
    """No values are filled automatically. A frontend can render these cards."""
    return dict(schema_version=VERSION, domain='DYN', models=copy.deepcopy(MODELS),
                variable_units=dict(VARIABLE_UNITS),
                note='Brugeren bekræfter modellen; programmet verificerer ikke at modellen svarer til råteksten.')


def plan(text):
    """Suggest modelling cards, never physical data or an autonomous answer."""
    if not isinstance(text,str) or len(text)>16000:raise ValueError('Opgaveteksten skal være højst 16000 tegn.')
    patterns={
        'feedback':r'friktion|masse|terminalhastighed|stangens hastighed',
        'motional_curve':r'bevægelig|metalstang|roterende|skinner|bevægelsesinduktion',
        'RC_discharge':r'aflad|RC[- ]|initial.*ladning',
        'RL_step':r'RL[- ]|selvindukt.*modstand|spole.*modstand',
        'displacement_disk':r'forskydningsstrøm|ampère.maxwell|cirkulære plader',
        'faraday_uniform':r'homogent.*magnetfelt|magnetfelt.*homogent|faraday|induktion',
        'faraday_integral':r'fluxintegral|inhomogent.*magnetfelt|magnetfelt.*inhomogent',
        'faraday_flux':r'flux|fluxkobling',
    }
    candidates=[]
    for model,pattern in patterns.items():
        match=re.search(pattern,text,re.I)
        if match:candidates.append(dict(model=model,evidence=match.group(),status='suggestion_requires_confirmation'))
    return dict(schema_version=VERSION,status='needs_confirmation',interpretation_status='unconfirmed',
        candidates=candidates,models=catalog()['models'],
        subproblem_markers=list(dict.fromkeys(re.findall(r'(?:^|\n)\s*([a-h])\)',text))),
        variable_units=dict(VARIABLE_UNITS),
        shared_data_instruction='Indtast fælles givne data én gang; vælg model og søgte størrelser for hvert delspørgsmål. Ingen delspørgsmålsresultater overføres automatisk.',
        idealization_suggestion='Lang cylinder/ledning kan foreslås som uendelig idealmodel, men kræver særskilt bekræftelse; den er ikke en DYN-model her.' if re.search(r'lang\w*\s+(?:cylinder|ledning)',text,re.I) else None)


def _strings(value, name):
    if not isinstance(value,list) or not all(isinstance(x,str) and x for x in value):
        raise ValueError(name+' skal være en liste af ikke-tomme strenge.')
    return value


def respond(request, *, solve=False):
    """Return questions or a conditional calculation. Never claim verified prose."""
    out=dict(schema_version=VERSION,status='needs_confirmation',questions=[],errors=[],subproblems=[],
             interpretation_status='unconfirmed',verification_scope='Ingen automatisk verifikation af opgavetekstens fortolkning.')
    try:
        if not isinstance(request,dict) or request.get('schema_version')!=VERSION:
            raise ValueError('Forventet schema_version '+VERSION)
        allowed={'schema_version','text','confirmed','units','numbers','positive','assumptions','variables','subproblems'}
        if set(request)-allowed:raise ValueError('Ukendte inputfelter: '+', '.join(sorted(set(request)-allowed)))
        if len(json.dumps(request,ensure_ascii=False,allow_nan=False))>24000:raise ValueError('Input overstiger 24000 tegn.')
        if not isinstance(request.get('text',''),str):raise ValueError('text skal være tekst.')
        if not isinstance(request.get('confirmed',False),bool):raise ValueError('confirmed skal være boolesk.')
        shared=request.get('variables',{});units=request.get('units',{});numbers=request.get('numbers',{})
        for name,value in [('variables',shared),('units',units),('numbers',numbers)]:
            if not isinstance(value,dict) or not all(isinstance(k,str) for k in value):raise ValueError(name+' skal være et objekt.')
        if not all(isinstance(v,str) and v for v in [*units.values(),*numbers.values()]):raise ValueError('Enheder og numeriske værdier skal være strenge med SI-kompatible enheder.')
        positive=_strings(request.get('positive',[]),'positive')
        assumptions=_strings(request.get('assumptions',[]),'assumptions')
        parts=request.get('subproblems')
        if not isinstance(parts,list) or not 1<=len(parts)<=8:raise ValueError('Angiv 1–8 eksplicitte delspørgsmål.')
        ids=set();prepared=[]
        declared=set()
        for part in parts:
            if not isinstance(part,dict) or set(part)-{'id','model','variables','wanted','assumptions','orientation_confirmed'}:raise ValueError('Ugyldigt delspørgsmål.')
            id=part.get('id');model=part.get('model')
            if not isinstance(id,str) or not id or id in ids:raise ValueError('Delspørgsmål skal have unikke ikke-tomme id.')
            ids.add(id)
            if model not in MODELS:
                out['questions'].append(dict(subproblem=id,field='model',message='Vælg en understøttet fysisk model.',options=list(MODELS)));continue
            spec=MODELS[model];local=part.get('variables',{})
            if not isinstance(local,dict):raise ValueError('Delspørgsmålets variables skal være et objekt.')
            # Shared data may contain quantities for other parts. Only this card's
            # declared variables enter its solver. Local typos are rejected.
            keys=set(spec['required']+spec['optional'])
            declared.update(keys)
            if set(local)-keys:raise ValueError('Ukendte modelvariable: '+', '.join(sorted(set(local)-keys)))
            variables={k:v for k,v in shared.items() if k in keys}|local
            missing=[k for k in spec['required'] if k not in variables]
            for key in missing:out['questions'].append(dict(subproblem=id,field=key,message='Angiv '+key+' fra opgaven; ingen eksempelværdi indsættes.'))
            conditions=list(dict.fromkeys(assumptions+_strings(part.get('assumptions',[]),'assumptions')))
            required=list(spec['assumptions'])
            if 'R' in variables and spec['family'] in ('faraday','motional_emf'):required.append('negligible_self_inductance')
            if 'R' in variables and spec['family']=='motional_emf':required.append('stationary_return_path')
            for key in required:
                if key not in conditions:out['questions'].append(dict(subproblem=id,field='assumptions',value=key,message='Bekræft eller afvis modelbetingelsen '+key))
            if part.get('orientation_confirmed') is not True:
                out['questions'].append(dict(subproblem=id,field='orientation_confirmed',message=spec['orientation']))
            wanted=_strings(part.get('wanted',[]),'wanted')
            if not wanted:out['questions'].append(dict(subproblem=id,field='wanted',message='Hvilke resultater søges?'))
            prepared.append((id,model,variables|spec.get('fixed',{}),conditions,wanted))
        if not out['questions'] and set(shared)-declared:
            raise ValueError('Fælles variable bruges ikke af nogen valgt model: '+', '.join(sorted(set(shared)-declared)))
        if request.get('confirmed') is not True:out['questions'].append(dict(field='confirmed',message='Bekræft at de indtastede data, model, betingelser og retninger svarer til opgaven.'))
        if out['questions']:return out
        out['interpretation_status']='user_confirmed'
        out['confirmed_model']=copy.deepcopy(request)
        out['status']='ready'
        if not solve:return out
        for id,model,variables,conditions,wanted in prepared:
            record=dict(id=id,model=model,status='not_solved',solution=None,errors=[])
            try:
                parsed=Parsed(request.get('text',''),MODELS[model]['orientation'],
                    dict(assisted_model_card=model,solver_spec=dict(domain='DYN',family=MODELS[model]['family'],variables=variables,wanted=wanted)),
                    wanted,dict(numbers),dict(units),list(positive),conditions)
                answer=run_confirmed(parsed)
                failed=[c.name for c in answer.checks if c.passed is False]
                if failed:raise ValueError('Fejlede kontroller: '+', '.join(failed))
                solution=serialize(answer)
                missing_results=set(wanted)-set(solution['results'])
                if missing_results:raise ValueError('Modellen bestemmer ikke: '+', '.join(sorted(missing_results)))
                dimensions=[c for c in answer.checks if c.name.startswith('Dimension:')]
                import sympy as sp
                formal=any(v.has(sp.Integral) for v in answer.symbolic_result.values() if isinstance(v,(sp.Basic,sp.MatrixBase)))
                unresolved=formal or not dimensions or any(c.passed is not True for c in answer.checks)
                record.update(status='partial' if unresolved else 'calculated_under_confirmed_model',solution=solution,
                    verification=dict(interpretation='user_confirmed_not_machine_verified',
                        dimensions='passed' if dimensions and all(c.passed is True for c in dimensions) else 'incomplete',
                        physical_checks=[c.name for c in answer.checks if not c.name.startswith('Dimension:')],
                        completeness='partial' if unresolved else 'requested_results_present',
                        limitation='Kontrollerne er solverens konkrete residualer; de beviser ikke hele modellens fysiske gyldighed.'))
            except (ValueError,TypeError,KeyError) as exc:record['errors'].append(str(exc))
            out['subproblems'].append(record)
        states=[p['status'] for p in out['subproblems']]
        out['status']='not_solved' if all(s=='not_solved' for s in states) else 'calculated_under_confirmed_model' if all(s=='calculated_under_confirmed_model' for s in states) else 'partial'
    except (ValueError,TypeError,KeyError) as exc:
        out.update(status='not_solved',errors=[str(exc)])
    return out


def main():
    import sys
    from multiprocessing import freeze_support
    freeze_support()
    try:
        raw=sys.stdin.buffer.read(96001)
        if len(raw)>96000:raise ValueError('JSON-input overstiger 96000 UTF-8 bytes.')
        request=json.loads(raw.decode('utf-8-sig'))
        reply=plan(request['text']) if sys.argv[1:]==['--plan'] and isinstance(request,dict) and set(request)=={'text'} else respond(request,solve=True)
    except (ValueError,UnicodeError) as exc:reply=dict(schema_version=VERSION,status='not_solved',errors=[str(exc)])
    sys.stdout.buffer.write((json.dumps(reply,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))


if __name__=='__main__':main()
