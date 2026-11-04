import sympy as s
import pytest
from em1_solver.core.dimensions import dimension,unit_dimension,DimensionError,check_solution
from em1_solver import Problem,solve

@pytest.mark.dimensions
@pytest.mark.parametrize('expr,units,expected',[('E',{'E':'J'},'V/m'),('B',{'B':'A/m'},'T'),('V',{'V':'V'},'V/m'),('L/t^2',{'L':'m','t':'s'},'m/s'),('E+U',{'E':'V/m','U':'J'},'V/m'),('exp(t)',{'t':'s'},'1')])
def test_dimensional_errors_detected(expr,units,expected):
 from em1_solver.core.parsing import expression
 symbols={k:s.Symbol(k,positive=True) for k in units}
 try:actual=dimension(expression(expr,symbols),{symbols[k]:v for k,v in units.items()})
 except DimensionError:return
 assert actual!=unit_dimension(expected)

@pytest.mark.dimensions
@pytest.mark.parametrize('unit',['cm','mm','micrometer','nC','uC','mA','kA','mT','uF','mF'])
def test_prefixes_do_not_change_dimensions(unit):
 assert unit_dimension(unit)==unit_dimension(str(__import__('em1_solver.core.units',fromlist=['UNITS']).UNITS.Quantity(1,unit).to_base_units().units))

@pytest.mark.dimensions
def test_wrong_E_warns_and_cannot_be_stable():
 x,y,z,energy=s.symbols('x y z energy',real=True)
 out=solve(Problem('EV','field_calculus',variables={'coordinates':[x,y,z],'system':'cartesian','E':[energy*x,0,0]},symbol_units={x:'m',y:'m',z:'m',energy:'J'}))
 assert any('WARNING: dimensional inconsistency' in w for w in out.warnings)
 assert not out.stable

@pytest.mark.dimensions
def test_compensating_wrong_input_units_are_not_certified():
 q,v,b=s.symbols('q v B',positive=True)
 # Product q*v*B has force dimensions, but both q and B have wrong individual units.
 out=solve(Problem('BA','lorentz_force',variables={'q':q,'v':[v,0,0],'B':[0,0,b],'E':[0,0,0]},
 symbol_units={q:'C*m',v:'m/s',b:'T/m'}))
 assert any('input q' in w for w in out.warnings)
 assert any('input B' in w for w in out.warnings)
 assert not out.stable
