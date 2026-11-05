"""Separate analytic reference calculations, run only after all app outputs exist.

No EM1 engine imports; expressions are read from our own recorded app JSON.
"""
import json,math
from pathlib import Path
import sympy as sp
import mpmath as mp
OUT=Path(__file__).resolve().parent
assert (OUT/'execution.json').exists(),'Complete the app examination before reference calculations.'
run=json.loads((OUT/'execution.json').read_text());cases=json.loads((OUT/'questions_and_inputs.json').read_text())
eps=8.8541878128e-12;mu=1.25663706212e-6;pi=math.pi;references={};grades=[]

def expr(solution,key,values):
    local={n:sp.Symbol(n,real=True) for n in values};local.update(epsilon_0=sp.Float(eps),mu_0=sp.Float(mu))
    e=sp.sympify(solution['results'][key]['expression'],locals=local)
    e=e.subs({s:values[s.name] for s in e.free_symbols if s.name in values})
    return [float(v.evalf()) for v in e] if isinstance(e,sp.MatrixBase) else float(e.evalf())


def close(x,y):
    if isinstance(y,list):return isinstance(x,list) and len(x)==len(y) and all(close(a,b) for a,b in zip(x,y))
    return math.isfinite(x) and abs(x-y)<=max(2e-17,2e-7*abs(y))


def check(checks,sol,key,expected,values,label=''):
    try:
        actual=expr(sol,key,values);checks.append(dict(result=key,at=label,expected=expected,actual=actual,passed=close(actual,expected)))
    except Exception as exc:checks.append(dict(result=key,at=label,expected=expected,passed=False,error=str(exc)))


def solution(reply):
    if not reply:return None
    if reply.get('subproblems'):return reply['subproblems'][0].get('solution')
    return reply.get('solution')

for record in run['cases']:
    id=record['id'];checks=[];sol=solution(record.get('manual_response') or record.get('guided_response'));note=''
    # Derive from the given source distribution and laws, without reference to
    # the app's chosen algebraic form or historical solutions.
    if id.startswith('1'):
        a=.07;rho=22e-9;total=4*pi*rho*a**3/5;values=dict(a=a,rho0=rho)
        references[id]=dict(law='Qenc(r)=integral_0^r 4*pi*u²*rho0*u²/a² du =4*pi*rho0*r^5/(5*a²). Gauss E=Qenc/(4*pi*eps*r²). V(a)=rho0*a²/(5*eps); integrate E inward to V(0)=rho0*a²/(4*eps).',inputs_SI=values)
        if sol:
            if id=='1a':check(checks,sol,'Q',total,values)
            if id=='1b':
                for r in (.2*a,.8*a,1.4*a,3*a):check(checks,sol,'E',rho*r**3/(5*eps*a*a) if r<a else rho*a**3/(5*eps*r*r),values|dict(r=r),f'r={r} m')
            if id=='1c':
                check(checks,sol,'V_center',rho*a*a/(4*eps),values);check(checks,sol,'V_far',rho*a*a/(10*eps),values)
    if id.startswith('2'):
        q=-5e-9;d=.11;k=1/(4*pi*eps);values=dict(q=q,d=d)
        references[id]=dict(law='Image -q at -d; force Fz=-q²/(16*pi*eps*d²). Induced total=-q. Quasistatic Wext=-integral_d^(2d)Fz(h)dh=q²/(32*pi*eps*d)>0. No fictitious charge-pair energy is used.',inputs_SI=values,reference_work_J=q*q/(32*pi*eps*d))
        if sol:
            if id=='2a':check(checks,sol,'F',[0,0,-q*q/(16*pi*eps*d*d)],values);check(checks,sol,'Q_induced',-q,values)
            else:check(checks,sol,'W',q*q/(32*pi*eps*d),values)
    if id.startswith('3'):
        a=.06;i=5.5;j0=2*i/(pi*a*a);values=dict(a=a,I_given=i,evaluation_radius_1=.03,evaluation_radius_2=.18)
        def field(s):return mu*i/(pi*a*a)*(s-s**3/(2*a*a)) if s<a else mu*i/(2*pi*s)
        references[id]=dict(law='Ienc=2*pi*J0*integral_0^s (u-u³/a²)du=pi*J0*(s²-s^4/(2*a²)). Itotal=pi*J0*a²/2; solve for J0. Bphi=mu*Ienc/(2*pi*s), outside use total I; positive +phi for +z current.',inputs_SI=values)
        if sol:
            if id=='3a':check(checks,sol,'density_amplitude',j0,values)
            if id=='3b':
                for s in (.1*a,.6*a,1.2*a,4*a):check(checks,sol,'normalized_B',field(s),values|dict(s=s),f's={s} m')
            if id=='3c':
                check(checks,sol,'B_point_1',field(.03),values);check(checks,sol,'B_point_2',field(.18),values)
                for key,point in [('B_point_1',.03),('B_point_2',.18)]:checks.append(dict(result='actual numerical '+key,passed=key in sol.get('numerical',{}) and close(float(sol['numerical'][key]['value']),field(point))))
    if id.startswith('4'):
        a=.025;m=600;values=dict(a=a,M0=m)
        references[id]=dict(law='curl(M)=(0,-dMz/ds,0)=(0,-2*M0*s/a²,0); K=M×s_hat=(0,M0,0) at a. No free currents and div M=0, M.n=0 imply zero demagnetizing H with H(infinity)=0: H=0 everywhere, B=mu*M inside, B=0 outside. Tangential B jump matches K_bound.',inputs_SI=values)
        if sol:
            if id=='4a':
                for s in (.2*a,.7*a):check(checks,sol,'J_bound',[0,-2*m*s/(a*a),0],values|dict(s=s),f's={s} m')
                check(checks,sol,'K_bound',[0,m,0],values)
            else:
                for s in (.5*a,2*a):
                    check(checks,sol,'H',[0,0,0],values|dict(s=s),f's={s} m');check(checks,sol,'B',[0,0,mu*m*(s/a)**2] if s<a else [0,0,0],values|dict(s=s),f's={s} m')
    if id.startswith('5'):
        n=3;b=.08;area=.002;tt=.70;r=7;l=.14;tau=l/r;values=dict(N=n,B0=b,A0=area,T=tt,R=r,L=l)
        c=n*b*area/tt
        # Independent convolution with the RL impulse response. The forcing
        # is affine, e(t)=e0+e1*t, so integrate to this elementary expression.
        e0=-1.5*c;e1=-c/tt
        def current(t):return e0/r*(1-math.exp(-t/tau))+e1/r*(t-tau*(1-math.exp(-t/tau)))
        heat=float(mp.quad(lambda u:r*current(float(u))**2,[0,tt]))
        references[id]=dict(law='Phi=B0*A0*(1+t/T)*(1+t/(2T)). emf=-N*dPhi/dt=-N*B0*A0/T*(3/2+t/T). RL current from I(t)=exp(-t/tau)/L*integral_0^t exp(u/tau)*emf(u)du, tau=L/R. Joule heat by independent quadrature of R*I². Negative current is clockwise viewed from +z.',inputs_SI=values,reference_heat_J=heat)
        if sol:
            if id=='5a':
                for t in (0,.13,tt):check(checks,sol,'Phi',b*area*(1+t/tt)*(1+t/(2*tt)),values|dict(t=t),f't={t} s');check(checks,sol,'EMF',e0+e1*t,values|dict(t=t),f't={t} s')
            else:
                for t in (0,.011,.2,tt):check(checks,sol,'I',current(t),values|dict(t=t),f't={t} s')
                check(checks,sol,'heat',heat,values)
                # The requested numerical I(T) must actually be present in the
                # app, not merely obtained by the reference checker.
                numerical=sol.get('numerical',{});checks.append(dict(result='numerical I(T)',passed='I' in numerical and close(float(numerical['I']['value']),current(tt))))
    if id.startswith('6'):
        mass=.035;r=.45;b=.6;ell=.18;force=.012;tt=.8;k=b*ell;tau=mass*r/(k*k);v_inf=force*r/(k*k);values=dict(m=mass,R=r,B=b,ell=ell,F0=force,T=tt)
        def velocity(t):return v_inf*(1-math.exp(-t/tau))
        def current(t):return -k*velocity(t)/r
        heat=(force*force*r/(k*k))*(tt-2*tau*(1-math.exp(-tt/tau))+tau/2*(1-math.exp(-2*tt/tau)))
        references[id]=dict(law='Rod +y moving +x in B+z has emf along -y. I=-B*ell*v/R, drag force along -x. Newton: m vprime=F0-(B*ell)² v/R. v=v_inf(1-exp(-t/tau)), tau=mR/(B*ell)². Joule heat from analytic integral of R I².',inputs_SI=values,reference_heat_J=heat)
        if sol:
            if id=='6a':
                for t in (0,.2,tt,2):check(checks,sol,'v',velocity(t),values|dict(t=t),f't={t} s')
                check(checks,sol,'tau',tau,values);check(checks,sol,'v_infinity',v_inf,values)
                checks.append(dict(result='numerical terminal velocity',passed='v_infinity' in sol.get('numerical',{})))
            else:
                for t in (0,.2,tt,2):check(checks,sol,'I',current(t),values|dict(t=t),f't={t} s')
                check(checks,sol,'W',heat,values)
    if sol:
        # Exact symbolic comparison for entire functions, complementing
        # numerical samples and the app's own dimensional/physical residuals.
        sy={name:sp.Symbol(name,positive=True) if name in ('a','r','s','d','R','L','T','m','B','ell') else sp.Symbol(name,real=True) for name in ('a','r','s','d','q','rho0','I_given','N','B0','A0','R','L','T','t','m','B','ell','F0','M0')}
        sy.update(epsilon_0=sp.Symbol('epsilon_0',positive=True),mu_0=sp.Symbol('mu_0',positive=True))
        def exact(key,expected):
            try:
                actual=sp.sympify(sol['results'][key]['expression'],locals=sy)
                difference=sp.simplify(actual-expected)
                ok=difference==0 or isinstance(difference,sp.MatrixBase) and difference==sp.zeros(*difference.shape)
                checks.append(dict(result=key+' exact symbolic',passed=bool(ok),residual=str(difference)))
            except Exception as exc:checks.append(dict(result=key+' exact symbolic',passed=False,error=str(exc)))
        a,r,rad,ep,mu0=sy['a'],sy['r'],sy['s'],sy['epsilon_0'],sy['mu_0']
        if id=='1a':exact('Q',4*sp.pi*sy['rho0']*a**3/5)
        if id=='1b':exact('E',sp.Piecewise((sy['rho0']*r**3/(5*ep*a*a),r<=a),(sy['rho0']*a**3/(5*ep*r*r),True)))
        if id=='1c':exact('V_center',sy['rho0']*a*a/(4*ep));exact('V_far',sy['rho0']*a*a/(10*ep))
        if id=='2a':exact('F',sp.Matrix([0,0,-sy['q']**2/(16*sp.pi*ep*sy['d']**2)]));exact('Q_induced',-sy['q'])
        if id=='3a':exact('density_amplitude',2*sy['I_given']/(sp.pi*a*a))
        if id=='3b':exact('normalized_B',sp.Piecewise((mu0*sy['I_given']/(sp.pi*a*a)*(rad-rad**3/(2*a*a)),rad<=a),(mu0*sy['I_given']/(2*sp.pi*rad),True)))
        if id=='4a':exact('J_bound',sp.Matrix([0,-2*sy['M0']*rad/a**2,0]));exact('K_bound',sp.Matrix([0,sy['M0'],0]))
        t,tt,R,L=sy['t'],sy['T'],sy['R'],sy['L']
        if id=='5a':exact('Phi',sy['B0']*sy['A0']*(1+t/tt)*(1+t/(2*tt)));exact('EMF',-sy['N']*sy['B0']*sy['A0']/tt*(sp.Rational(3,2)+t/tt))
        if id=='5b':
            e0=-sp.Rational(3,2)*sy['N']*sy['B0']*sy['A0']/tt;e1=-sy['N']*sy['B0']*sy['A0']/tt**2;decay=sp.exp(-R*t/L)
            exact('I',e0/R*(1-decay)+e1/R*(t-L/R*(1-decay)))
        if id in ('6a','6b'):
            kk=sy['B']*sy['ell'];tau_expr=sy['m']*R/kk**2;vinf=sy['F0']*R/kk**2;vel=vinf*(1-sp.exp(-t/tau_expr))
            if id=='6a':exact('v',vel);exact('tau',tau_expr);exact('v_infinity',vinf)
            else:exact('I',-kk*vel/R)
        required_numbers={'1a':['Q'],'1c':['V_center','V_far'],'2a':['F','Q_induced'],'3a':['density_amplitude'],'3c':['B_point_1','B_point_2'],'5b':['I','heat'],'6a':['v_infinity'],'6b':['W']}.get(id,[])
        for key in required_numbers:checks.append(dict(result='numerical display '+key,passed=key in sol.get('numerical',{})))
    raw=record.get('automatic_reply') or {};auto_sol=solution(raw)
    # Every direct text call refused in the observed execution. Keep this an
    # explicit assertion so a future rerun cannot be misreported automatically.
    assert raw.get('status')=='not_solved' and not auto_sol,(id,raw.get('status'))
    if sol:
        bad=[c for c in checks if not c['passed']]
        grade='wrong' if bad else 'partial' if record.get('math_display_errors') else 'fully_correct'
        if id=='5b' and not sol.get('direction'):
            # This subquestion explicitly asks to explain the spatial current
            # direction. Correct signed I(t) alone is a mathematical answer,
            # not the requested explanation. The emitted RL solution has no
            # direction and no mapping to the coil's clockwise orientation.
            note='I(t), I(T) and heat are correct, but an explicit explanation of clockwise current relative to +z is missing.'
            checks.append(dict(result='requested physical current-direction explanation',passed=False,classification='missing_explanation_not_wrong_math',detail=note))
            if grade=='fully_correct':grade='partial'
    else:grade='abstained'
    grades.append(dict(id=id,domain=record['domain'],grade=grade,mode='guided' if record['route']=='guided_shared' else 'manual' if grade!='abstained' else 'abstained',automatic_grade='abstained',checks=checks,model=(record.get('manual_request') or record.get('guided_request') or {}).get('subproblems',[{}])[0].get('model'),manual_semantic_actions=record.get('manual_semantic_actions'),guided_semantic_actions=record.get('guided_semantic_actions'),shared_actions_with=record.get('guided_actions_shared_with'),harness_or_form_error=record.get('harness_or_form_error'),reported_direction=(sol or {}).get('direction'),qualitative_note=note))
counts={g:sum(r['grade']==g for r in grades) for g in ('fully_correct','partial','wrong','abstained')};assert sum(counts.values())==14
summary=dict(total=14,heads=6,counts=counts,full_percent=100*counts['fully_correct']/14,automatic_full=0,automatic_abstained=14,guided_full=sum(g['grade']=='fully_correct' and g['mode']=='guided' for g in grades),manual_full=sum(g['grade']=='fully_correct' and g['mode']=='manual' for g in grades),manual_partial=sum(g['grade']=='partial' and g['mode']=='manual' for g in grades),native_windows_tested=False,externally_independent_blind_test=False,cases=grades)
(OUT/'references.json').write_text(json.dumps(references,ensure_ascii=False,indent=2)+'\n');(OUT/'grading.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='cases'},indent=2))
for g in grades:
 print(g['id'],g['grade'],[c for c in g['checks'] if not c['passed']])
