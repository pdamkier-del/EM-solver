import sympy as sp
from .problem import InputError

EPS0 = sp.Symbol('epsilon_0', positive=True)
MU0 = sp.Symbol('mu_0', positive=True)


def vector(value):
    try:
        result = sp.Matrix(value)
    except (TypeError, ValueError) as exc:
        raise InputError('En vektor skal have tre komponenter.') from exc
    if result.shape != (3, 1):
        raise InputError('En vektor skal have tre komponenter.')
    return result


def positive(value, name):
    if sp.sympify(value).is_positive is not True:
        raise InputError(f'{name} skal være positiv; angiv positive symbolantagelser eller et positivt tal.')


def finite_integral(expr, *limits):
    value = sp.simplify(sp.integrate(expr, *limits))
    if value.has(sp.oo, -sp.oo, sp.zoo, sp.nan):
        raise InputError('Integral divergerer eller er udefineret for de angivne data.')
    return value


def regional_limit(expr,coordinate,point,direction='+'):
    """One-sided region selection before SymPy's scalar limit machinery."""
    if direction not in ('+','-'):raise InputError('Angiv en eksplicit ensidig grænse med + eller -.')
    if isinstance(expr,sp.MatrixBase):return expr.applyfunc(lambda v:regional_limit(v,coordinate,point,direction))
    expr=sp.piecewise_fold(expr)
    def eventual(condition):
        if condition in (True,sp.true):return True
        if condition in (False,sp.false):return False
        if isinstance(condition,sp.And):
            states=[eventual(c) for c in condition.args]
            return False if False in states else True if all(s is True for s in states) else None
        if isinstance(condition,sp.Or):
            states=[eventual(c) for c in condition.args]
            return True if True in states else False if all(s is False for s in states) else None
        if not isinstance(condition,(sp.Lt,sp.Le,sp.Gt,sp.Ge,sp.Eq,sp.Ne)):return None
        delta=condition.lhs-condition.rhs
        limit=sp.limit(delta,coordinate,point,dir=direction)
        if limit==0:
            epsilon=sp.Dummy('epsilon',positive=True)
            shifted=sp.simplify(delta.subs(coordinate,point+(1 if direction=='+' else -1)*epsilon))
            leading=shifted.as_leading_term(epsilon)
        else:leading=limit
        if isinstance(condition,sp.Eq):return True if leading==0 else False if leading.is_zero is False else None
        if isinstance(condition,sp.Ne):return False if leading==0 else True if leading.is_zero is False else None
        if leading.is_positive:return isinstance(condition,(sp.Gt,sp.Ge))
        if leading.is_negative:return isinstance(condition,(sp.Lt,sp.Le))
        if leading==0:return isinstance(condition,(sp.Ge,sp.Le))
        return None
    if isinstance(expr,sp.Piecewise):
        for value,condition in expr.args:
            state=eventual(condition)
            if state is True:return regional_limit(value,coordinate,point,direction)
            if state is None:raise InputError('Regionen ved grænsen kan ikke afgøres ud fra de angivne antagelser.')
        raise InputError('Ingen region omkring den ønskede grænse.')
    return sp.limit(expr,coordinate,point,dir=direction)


def calculus(coordinates, system):
    if len(coordinates) != 3 or not all(isinstance(c, sp.Symbol) for c in coordinates):
        raise InputError('Angiv tre koordinatsymboler.')
    a, b, _ = coordinates
    scales = {'cartesian': (1, 1, 1), 'cylindrical': (1, a, 1), 'spherical': (1, a, a*sp.sin(b))}
    if system not in scales:
        raise InputError('Ukendt koordinatsystem.')
    h = scales[system]
    volume = sp.prod(h)

    def grad(v):
        return sp.Matrix([sp.diff(v, c)/scale for c, scale in zip(coordinates, h)]).applyfunc(sp.simplify)

    def div(v):
        v = vector(v)
        return sp.simplify(sum(sp.diff(volume*v[i]/h[i], coordinates[i]) for i in range(3))/volume)

    def curl(v):
        v = vector(v)
        return sp.Matrix([(sp.diff(h[k]*v[k], coordinates[j])-sp.diff(h[j]*v[j], coordinates[k]))/(h[j]*h[k])
                          for i,j,k in [(0,1,2),(1,2,0),(2,0,1)]]).applyfunc(sp.simplify)

    return grad, div, curl
