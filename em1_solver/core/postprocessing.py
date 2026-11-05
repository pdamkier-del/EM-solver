"""Bounded-worker symbolic result operations, independent of solver family."""
import re
import sympy as sp
from .new_problem import build,symbols_for
from .parsing import expression
from .problem import InputError
from .solution import Check
from .dimensions import dimension,unit_dimension,check_solution
from .units import si,numerical


def apply(parsed,answer):
    problem=build(parsed);symbols=symbols_for(parsed)
    numeric={k:sp.Float(str(si(v,problem.numerical_units[k]).magnitude)) for k,v in problem.numerical_values.items()}
    for operation in parsed.data.get('operations',[]):
        kind=operation['kind'];key=operation['result'];name=operation['id']
        if key not in answer.symbolic_result:raise InputError('Ukendt resultat til efterbehandling: '+key)
        if name in answer.symbolic_result:raise InputError('Efterbehandling må ikke overskrive '+name)
        variable=symbols.get(operation['variable'])
        if not isinstance(variable,sp.Symbol):raise InputError('Efterbehandling kræver et koordinat-/parameternavn.')
        value=answer.symbolic_result[key];unit=answer.units.get(key)
        argument=expression(operation.get('value','0'),symbols)
        if kind in ('evaluate','limit') and argument not in (sp.oo,-sp.oo) and argument!=0:
            expected=problem.symbol_units.get(variable)
            if expected and dimension(argument,problem.symbol_units)!=unit_dimension(expected):raise InputError('Evalueringspunktets enhed passer ikke til '+str(variable))
        if kind=='differentiate':
            result=sp.simplify(sp.diff(value,variable))
            if operation.get('at') is not None:
                at=expression(operation['at'],symbols)
                if at!=0 and dimension(at,problem.symbol_units)!=unit_dimension(problem.symbol_units[variable]):raise InputError('Den afledtes evalueringspunkt har forkert enhed.')
                result=result.subs(variable,at)
            vunit=problem.symbol_units.get(variable)
            if not unit or not vunit:raise InputError('Angiv enheder før differentiation af resultatet.')
            outunit=f'({unit})/({vunit})'
            answer.add('Differentier '+key+' med hensyn til '+str(variable),result,law='Symbolsk differentiation',reasoning='Den afledte beregnes af det allerede fundne resultat; et eventuelt punkt indsættes bagefter.')
        elif kind=='evaluate':
            result=sp.simplify(value.subs(variable,argument));outunit=unit
            answer.add('Evaluér '+key+' ved '+str(variable)+'='+str(argument),result,law='Indsættelse i beregnet resultat')
        elif kind=='limit':
            from .validation import regional_limit
            f=lambda v:regional_limit(v,variable,argument,operation.get('direction','+'))
            result=value.applyfunc(f) if isinstance(value,sp.MatrixBase) else f(value);outunit=unit
            answer.add('Grænse af '+key+' ved '+str(variable)+' → '+str(argument),result,law='Symbolsk grænseberegning')
        elif kind=='integrate':
            low=expression(operation['lower'],symbols);high=expression(operation['upper'],symbols)
            vunit=problem.symbol_units.get(variable)
            if not unit or not vunit:raise InputError('Integration kræver kendte enheder.')
            for endpoint in (low,high):
                if endpoint not in (0,sp.oo,-sp.oo) and dimension(endpoint,problem.symbol_units)!=unit_dimension(vunit):raise InputError('Integrationsgrænse har forkert enhed.')
            if sp.simplify((high-low).subs(numeric)).is_positive is not True:raise InputError('Integrationsintervallet skal være bevist positivt.')
            result=sp.integrate(value,(variable,low,high));outunit=f'({unit})*({vunit})'
            answer.add('Integrer '+key+' over det eksplicit angivne interval',sp.Integral(value,(variable,low,high)),law='Bestemt integration')
            answer.add('Evaluér integralet',result)
        elif kind=='transform':
            outunit=operation['unit'];aliases={n:sp.Symbol(n,real=True) for n in answer.symbolic_result}
            symbolic=expression(operation['value'],symbols|aliases)
            dimensions=dict(problem.symbol_units)|{aliases[n]:u for n,u in answer.units.items() if n in aliases}
            if dimension(symbolic,dimensions)!=unit_dimension(outunit):raise InputError('Den sammensatte formel har forkert eller ukendt dimension.')
            result=sp.simplify(symbolic.subs({aliases[n]:v for n,v in answer.symbolic_result.items()},simultaneous=True))
            answer.add('Anvend den eksplicit bekræftede resultatforbindelse',sp.Eq(sp.Symbol(name),symbolic),law='Brugerangivet fysisk sammenhæng',reasoning='Enheder kontrolleres før de tidligere resultater indsættes. Sammenhængens fysiske relevans skal bekræftes af brugeren.')
            answer.add('Indsæt de beregnede resultater',result)
        elif kind=='linear_ode':
            a=expression(operation['coefficient'],symbols);b=expression(operation['resistance'],symbols)
            initial=expression(operation['initial'],symbols);outunit=operation['unit'];tunit=problem.symbol_units.get(variable)
            if not unit or not tunit:raise InputError('Differentialligningen kræver kendte kilde- og tidsenheder.')
            if a.has(variable) or b.has(variable) or initial.has(variable):raise InputError('Dette ODE-trin kræver konstante koefficienter og en konstant begyndelsesværdi.')
            if sp.simplify(a.subs(numeric)).equals(0):raise InputError('Differentialkoefficienten må ikke være nul.')
            if dimension(a,problem.symbol_units)!=unit_dimension(f'({unit})*({tunit})/({outunit})') or dimension(b,problem.symbol_units)!=unit_dimension(f'({unit})/({outunit})'):raise InputError('ODE-koefficienternes enheder passer ikke til kilde og svar.')
            if initial!=0 and dimension(initial,problem.symbol_units)!=unit_dimension(outunit):raise InputError('Begyndelsesværdien har forkert enhed.')
            y=sp.Function(name)(variable);equation=sp.Eq(a*sp.diff(y,variable)+b*y,value)
            solved=sp.dsolve(equation,ics={y.subs(variable,0):initial});result=sp.simplify(solved.rhs)
            answer.add('Opstil a dy/dt + b y = '+key+' med y(0) givet',equation,law='Lineær førsteordens differentialligning')
            answer.add('Løs den drevne differentialligning med begyndelsesbetingelsen',solved)
            answer.check(name+': differentialligning',a*sp.diff(result,variable)+b*result-value)
            answer.check(name+': begyndelsesbetingelse',result.subs(variable,0)-initial)
        elif kind=='solve':
            if isinstance(value,sp.MatrixBase):raise InputError('Vælg et skalart resultat til ligningsløsning.')
            if argument!=0 and dimension(argument,problem.symbol_units)!=unit_dimension(unit):raise InputError('Ligningens mål og resultat har forskellige enheder.')
            residual=sp.simplify(value-argument)
            if residual==0 or sp.simplify(residual.subs(numeric))==0:
                answer.warnings.append(name+': ligningen er en identitet; ingen entydig løsning.')
                answer.checks.append(Check(name+': entydig løsning',None,None,'Alle tilladte værdier opfylder ligningen.'));continue
            try:roots=sp.solve(residual,variable)
            except (NotImplementedError,ValueError):
                answer.warnings.append(name+': ligningen kunne ikke løses symbolsk; basisresultaterne bevares.')
                answer.checks.append(Check(name+': løsning fundet',None,None,'Symbolsk ligningsløsning ikke afsluttet.'));continue
            accepted=[];conditional=bool(residual.has(sp.sin,sp.cos,sp.tan))
            for root in roots:
                sample=sp.simplify(root.subs(numeric))
                if sample.has(sp.nan,sp.zoo,sp.oo,-sp.oo) or sample.is_real is False or sample.is_finite is False:continue
                if operation.get('domain')=='nonnegative' and sample.is_negative is True:continue
                unknown=sample.is_real is not True or sample.is_finite is not True
                if operation.get('domain')=='nonnegative':unknown |= sample.is_nonnegative is not True
                accepted.append(sp.simplify(root));conditional |= unknown
            if not accepted:
                answer.warnings.append(name+': ingen påvist reel løsning i det valgte domæne. Ingen tid opfindes.')
                answer.checks.append(Check(name+': løsning fundet',None,None,'Ligningen har ingen påvist endelig tilladt løsning.'));continue
            result=accepted[0] if len(accepted)==1 else sp.FiniteSet(*accepted);outunit=problem.symbol_units.get(variable)
            if not outunit:raise InputError('Mangler enhed for den ubekendte '+str(variable))
            answer.add('Løs '+key+' = '+str(argument)+' for '+str(variable),result,law='Symbolsk ligningsløsning',reasoning='Alle fundne reelle grene bevares; ingen gren vælges ud fra et forventet svar.')
            for root in accepted:answer.check(name+': indsættelse i oprindelig ligning',residual.subs(variable,root))
            if name=='extremum_times' and 'I' in answer.symbolic_result:
                for root in accepted:
                    curvature=sp.simplify(sp.diff(answer.symbolic_result['I'],variable,2).subs(variable,root))
                    sample=sp.simplify(curvature.subs(numeric))
                    classification='lokalt maksimum' if sample.is_negative is True else 'lokalt minimum' if sample.is_positive is True else 'stationært punkt; andenafledte-testen afgør ikke typen'
                    answer.add('Andenafledte-test ved den stationære tid: '+classification,curvature,law='Klassifikation af stationære punkter')
                    answer.warnings.append('Stationær tid '+str(root)+': '+classification+'. Endepunkter og globalt ekstremum er ikke bestemt af denne test.')
            if conditional or len(accepted)>1:
                answer.checks.append(Check(name+': domæne/entydighed',None,None,'Løsningen kræver realitets-/domænebetingelser eller har flere grene.'))
                answer.warnings.append(name+': kontrollér gren og gyldighed; resultatet er betinget.')
        else:raise InputError('Ukendt efterbehandling.')
        answer.symbolic_result[name]=result;answer.units[name]=outunit
    answer.wanted=list(parsed.data.get('requested_wanted',parsed.wanted))
    check_solution(answer,problem.symbol_units)
    if problem.numerical_values:numerical(answer,problem.numerical_values,problem.numerical_units)
    return answer


def validate_operations(operations):
    if not isinstance(operations,list) or len(operations)>8:raise InputError('Højst otte efterbehandlinger.')
    ids=set()
    for op in operations:
        if not isinstance(op,dict) or set(op)-{'kind','result','variable','value','id','at','domain','direction','lower','upper','unit','coefficient','resistance','initial'}:raise InputError('Ugyldig efterbehandling.')
        if op.get('kind') not in ('differentiate','evaluate','limit','solve','integrate','transform','linear_ode'):raise InputError('Ukendt efterbehandlingstype.')
        if any(not isinstance(op.get(k),str) or not re.fullmatch(r'[A-Za-z_]\w*',op[k]) for k in ('id','result','variable')):raise InputError('Resultat, id og ubekendt skal være navne.')
        if op['id'] in ids:raise InputError('Efterbehandlingers id skal være unikke.')
        ids.add(op['id'])
        if op.get('domain','real') not in ('real','nonnegative') or op.get('direction','+') not in ('+','-'):raise InputError('Ugyldigt domæne eller grænseretning.')
        required={'integrate':('lower','upper'),'transform':('value','unit'),'linear_ode':('coefficient','resistance','initial','unit')}.get(op['kind'],())
        if any(not op.get(k) for k in required):raise InputError('Efterbehandlingen mangler: '+', '.join(required))
        for key in ('value','at','lower','upper','coefficient','resistance','initial','unit'):
            if key in op and (not isinstance(op[key],str) or len(op[key])>2000):raise InputError('Efterbehandlingsudtryk skal være kort tekst.')
