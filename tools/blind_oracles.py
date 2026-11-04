"""Independent reference checks. Test IDs occur only in evaluation code."""
import sympy as s
from em1_solver.core.new_problem import symbols_for
from em1_solver.core.parsing import expression
from em1_solver.core.validation import EPS0,MU0

def verify(id,p,out):
 sy=symbols_for(p);sy.update(eps0=EPS0,mu0=MU0)
 def e(v):return expression(v,sy)
 def equals(key,value,at=None):
  actual=out.symbolic_result[key]
  if at:actual=actual.subs({sy[k]:e(v) for k,v in at.items()},simultaneous=True)
  expected=s.Matrix([e(v) for v in value]) if isinstance(value,list) else e(value)
  residual=s.simplify(s.expand(actual-expected))
  assert all(x.equals(0) is True for x in residual) if isinstance(residual,s.MatrixBase) else residual.equals(0) is True,(key,actual,expected)
 if id=='EV01':
  equals('E','rho0*r*(4*R-3*r)/(12*R*eps0)',{'r':'R/3'}) if False else None
  equals('E','rho0*(R/3)*(4*R-R)/(12*R*eps0)',{'r':'R/3'});equals('E','rho0*R/(48*eps0)',{'r':'2*R'})
 elif id=='EV04':equals('E','rho0*(R/6-R/27)/eps0',{'s':'R/3'});equals('E','rho0*R/(12*eps0)',{'s':'2*R'})
 elif id in ('EV05','BA02'):
  equals('E' if id=='EV05' else 'B','0',{'s':'a/2'})
  if id=='EV05':equals('E','k*((a+h/2)**3-a**3)/(3*eps0*(a+h/2))',{'s':'a+h/2'});equals('E','k*((a+h)**3-a**3)/(3*eps0*(a+2*h))',{'s':'a+2*h'})
  else:equals('B','mu0*k*h/(2*(a+h/2))',{'s':'a+h/2'});equals('B','mu0*k*h/(a+2*h)',{'s':'a+2*h'})
 elif id=='EV06':equals('E','rho0*a**3/(24*eps0)',{'z':'a/2'});equals('E','-rho0*a**3/(3*eps0)',{'z':'-2*a'})
 elif id in ('EV09','EV11','BA05'):
  # A correct unevaluated source integral is acceptable; its geometry is checked independently.
  from em1_solver.core.problem import InputError
  from em1_solver.core.curve import line_integrals
  u=sy['u' if id!='EV11' else 'phi']
  if id=='EV09':
   integrands={'V':e('lam/(4*pi*eps0*sqrt(u**2+a**2))'),'E':s.Matrix([e('-lam*u/(4*pi*eps0*(u**2+a**2)**(3/2))'),e('lam*a/(4*pi*eps0*(u**2+a**2)**(3/2))'),0])};bounds=(-sy['L'],sy['L'])
  elif id=='EV11':
   integrands={'V':e('lambda0*(1+cos(phi))/(4*pi*eps0)'),'E':s.Matrix([e('-lambda0*(1+cos(phi))*cos(phi)/(4*pi*eps0*R)'),e('-lambda0*(1+cos(phi))*sin(phi)/(4*pi*eps0*R)'),0])};bounds=(0,2*s.pi)
  else:integrands={'B':s.Matrix([0,e('mu0*I*a/(4*pi*(a**2+u**2)**(3/2))'),0])};bounds=(-sy['L'],sy['L'])
  for key,v in integrands.items():
   expected=v.applyfunc(lambda x:s.Integral(x,(u,*bounds))) if isinstance(v,s.MatrixBase) else s.Integral(v,(u,*bounds))
   actual=out.symbolic_result[key];residual=actual-expected
   for r in list(residual) if isinstance(residual,s.MatrixBase) else [residual]:assert s.simplify(r).equals(0) is True
 elif id=='EV16':
  equals('D','rho_f*R/6',{'s':'R/3'});equals('E','rho_f*R/(6*eps)',{'s':'R/3'});equals('E','rho_f*R/(4*eps0)',{'s':'2*R'});equals('P','(eps-eps0)*rho_f*R/(6*eps)',{'s':'R/3'})
 elif id=='EV19':equals('V_inside','V1*(r/R)*cos(theta)+V2*(r/R)**2*(3*cos(theta)**2-1)/2');equals('V_outside','V1*(R/r)**2*cos(theta)+V2*(R/r)**3*(3*cos(theta)**2-1)/2')
 elif id=='BA01':equals('B','mu0*J0*(R/6-R/27)',{'s':'R/3'});equals('B','mu0*J0*R/12',{'s':'2*R'})
 elif id=='BA10':equals('B',['B0*x/L','-B0*y/L','0'])
 elif id=='BA15':
  equals('B','N*I/(l/mu+g/mu0)');equals('H_0','N*I/(l+g*mu/mu0)');equals('H_1','N*I/(l*mu0/mu+g)')
 elif id=='DYN01':equals('Phi','2*pi*beta*t*R**3/3');equals('EMF','-2*pi*beta*R**3/3')
 elif id=='DYN02':equals('Phi','B0*exp(-t/tau)*(a0+v*t)**2');equals('EMF','B0*exp(-t/tau)*((a0+v*t)**2/tau-2*v*(a0+v*t))')
 elif id=='DYN03':equals('B','mu0*eps0*E0*t*R/3',{'s':'R/3'});equals('B','mu0*eps0*E0*t*R/2',{'s':'2*R'})
 elif id=='DYN07':equals('v_infinity','F0*Z/(B**2*l**2)');equals('tau','m*Z/(B**2*l**2)');equals('v','F0*Z/(B**2*l**2)*(1-exp(-t*B**2*l**2/(m*Z)))')
 elif id=='DYN13':equals('E_phi','-R*dBdt/6',{'s':'R/3'});equals('E_phi','-R*dBdt/4',{'s':'2*R'})
 elif id=='GEN02':
  equals('curl_E',['-beta','-gamma','-alpha']);assert any('ikke være elektrostatisk' in w for w in out.warnings)
 else:raise AssertionError('No independent oracle for '+id)
 assert out.steps and out.equations,'Incomplete pedagogical output/direction'
 dimensions=[c for c in out.checks if c.name.startswith('Dimension:')]
 assert dimensions and all(c.passed is True for c in dimensions),'Units not verified'
 if id!='GEN02':assert all(c.passed is not False for c in out.checks),'Runtime contradiction'
 return True

# Each check is an independently reviewed equation or reference limit, not a solver snapshot.
REFERENCES={
 'EV02':[('delta_V','rho0*R**2/(24*eps0)',{'r':'2*R'}),('delta_V','rho0*(2*R**3-2*R*(R/3)**2+(R/3)**3)/(12*R*eps0)',{'r':'R/3'})],
 'EV03':[('E','0',{'r':'a/2'}),('E','k*h/(2*eps0*(a+h/2)**2)',{'r':'a+h/2'}),('E','k*h/(eps0*(a+2*h)**2)',{'r':'a+2*h'})],
 'EV07':[('E',['-2*V0*x/L**2','2*V0*y/L**2','0'],{}),('rho','0',{})],
 'EV08':[('E',['-V0*y*z/L**3','-V0*x*z/L**3','-V0*x*y/L**3'],{}),('rho','0',{})],
 'EV10':[('V','lam/(4*eps0)',{}),('E',['0','-lam/(2*pi*eps0*R)','0'],{})],
 'EV12':[('C','4*pi*eps0*a*(a+h)/h',{}),('V','Q/(4*pi*eps0)*(1/a-1/(a+h))',{}),('E','Q/(4*pi*eps0*(a+h/2)**2)',{'r':'a+h/2'})],
 'EV13':[('C','Area*(eps1+eps2)/(2*d)',{})],
 'EV14':[('C','Area/(d1/eps1+d2/eps2)',{})],
 'EV15':[('rho_bound','-2*k',{}),('sigma_bound','k*R',{}),('lambda_volume','-2*pi*k*R**2',{}),('lambda_surface','2*pi*k*R**2',{}),('lambda_total','0',{})],
 'EV17':[('F',['-q**2/(16*pi*eps0*d**2)','0','0'],{}),('U','-q**2/(16*pi*eps0*d)',{})],
 'BA03':[('B_positive',['0','-mu0*K0/2','0'],{}),('B_negative',['0','mu0*K0/2','0'],{})],
 'BA04':[('B_above',['0','0','0'],{}),('B_between',['0','mu0*K0','0'],{}),('B_below',['0','0','0'],{})],
 'BA06':[('B',['0','0','mu0*I/(2*R)'],{})],
 'BA07':[('B',['0','0','mu0*I*R**2/(2*(R**2+z**2)**(3/2))'],{})],
 'BA08':[('B',['0','0','mu0*I*theta/(4*pi*R)'],{})],
 'BA09':[('B',['0','0','mu0*(I1/R1-I2/R2)/2'],{})],
 'BA11':[('B',['0','0','3*A0*s'],{})],
 'BA12':[('solved_vx','0',{}),('solved_vy','-E0/B0',{})],
 'BA13':[('F_signed_attraction','mu0*I1*I2*l/(2*pi*d)',{})],
 'BA14':[('torque',['0','-m0*B0*sin(theta)','0'],{}),('U','-m0*B0*cos(theta)',{})],
 'BA16':[('inside.J_bound',['0','0','0'],{}),('inside.K_bound',['0','M0','0'],{}),('inside.B',['0','0','mu0*M0'],{}),('outside.B',['0','0','0'],{})],
 'DYN04':[('L','mu0/(2*pi)*log((a+h)/a)',{}),('U','mu0*I**2/(4*pi)*log((a+h)/a)',{})],
 'DYN05':[('R','L*log(2)/(sigma0*Area)',{}),('E','I/(Area*sigma0*(1+x/L))',{}),('rho','-eps0*I/(Area*sigma0*L*(1+x/L)**2)',{})],
 'DYN06':[('Phi','B*Area*cos(omega*t)',{}),('EMF','B*Area*omega*sin(omega*t)',{})],
 'DYN08':[('EMF','-B*l*v',{}),('I','-B*l*v/Z',{}),('F_magnetic',['-B**2*l**2*v/Z','0','0'],{})],
 'DYN09':[('L','mu0*N**2*Area/ell',{})],
 'DYN10':[('M','mu0*N1*N2*Area/ell',{})],
 'DYN11':[('I','V0/Z*(1-exp(-Z*t/Ind))',{}),('tau','Ind/Z',{}),('U_infinity','Ind*(V0/Z)**2/2',{})],
 'DYN12':[('Q','Q0*exp(-t/(Z*C))',{}),('I_charge','-Q0/(Z*C)*exp(-t/(Z*C))',{}),('U','Q0**2/(2*C)*exp(-2*t/(Z*C))',{})],
 'DYN14':[('EMF','B*omega*L**2/2',{})],
 'DYN15':[('Phi','B0*a**2/L*(x0+v*t+a/2)',{}),('EMF','-B0*a**2*v/L',{})],
 'GEN03':[('div_B','3*alpha',{})],
}

_original_verify=verify

def verify(id,p,out):
 if id in ('EV18','GEN01'):
  sy=symbols_for(p);sy.update(eps0=EPS0,mu0=MU0)
  if id=='EV18':
   z=sy['z'];actual=s.limit(out.symbolic_result['V_far']*z**3,z,s.oo)
   assert s.simplify(out.symbolic_result['V_far']+sy['q']*sy['a']**2/(4*s.pi*EPS0*z**3)).equals(0)
   assert s.simplify(actual+sy['q']*sy['a']**2/(4*s.pi*EPS0)).equals(0)
  else:
   phi=sy['phi'];a,b,lam=sy['a'],sy['b'],sy['lam']
   expected=s.Integral(lam*s.sqrt(a*a*s.sin(phi)**2+b*b*s.cos(phi)**2)/(4*s.pi*EPS0*s.sqrt(a*a*s.cos(phi)**2+b*b*s.sin(phi)**2)),(phi,0,2*s.pi))
   assert s.simplify(out.symbolic_result['V']-expected).equals(0)
 elif id in REFERENCES:
  sy=symbols_for(p);sy.update(eps0=EPS0,mu0=MU0)
  for key,formula,at in REFERENCES[id]:
   actual=out.symbolic_result[key]
   if at:actual=actual.subs({sy[k]:expression(v,sy) for k,v in at.items()},simultaneous=True)
   expected=s.Matrix([expression(v,sy) for v in formula]) if isinstance(formula,list) else expression(formula,sy)
   if actual.has(s.Integral):actual=actual.doit()
   residual=s.simplify(s.expand_log(actual-expected))
   assert all(v.equals(0) is True for v in residual) if isinstance(residual,s.MatrixBase) else residual.equals(0) is True,(key,actual,expected)
  if id=='GEN03':assert any(c.passed is False and 'divergens' in c.name for c in out.checks)
 else:return _original_verify(id,p,out)
 assert out.steps and out.equations
 dims=[c for c in out.checks if c.name.startswith('Dimension:')]
 assert dims and all(c.passed is True for c in dims),'Units not verified'
 if id!='GEN03':assert not any(c.passed is False for c in out.checks),'Runtime contradiction'
 return True
