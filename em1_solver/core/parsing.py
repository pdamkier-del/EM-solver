"""A small arithmetic AST interpreter. Never eval or sympify untrusted text."""
import ast
import operator
import sympy as sp
from .problem import InputError

FUNCTIONS = {k:getattr(sp,k) for k in ('sin','cos','tan','exp','log','sqrt','Abs','asin','acos','atan')}
OPS = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul, ast.Div:operator.truediv, ast.Pow:operator.pow}


def expression(text, symbols):
    if not isinstance(text, str) or len(text)>2000:
        raise InputError('Udtryk skal være en tekst på højst 2000 tegn.')
    try:
        tree = ast.parse(text.replace('^','**'), mode='eval')
        if len(list(ast.walk(tree))) > 300:
            raise InputError('Udtrykket er for stort.')
        def visit(node):
            if isinstance(node, ast.Expression): return visit(node.body)
            if isinstance(node, ast.Constant) and type(node.value) in (int,float):
                return sp.Rational(str(node.value))
            if isinstance(node, ast.Name) and node.id in (symbols | {'pi':sp.pi,'oo':sp.oo}):
                return (symbols | {'pi':sp.pi,'oo':sp.oo})[node.id]
            if isinstance(node, ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
                return visit(node.operand) * (-1 if isinstance(node.op,ast.USub) else 1)
            if isinstance(node, ast.BinOp) and type(node.op) in OPS:
                left,right=visit(node.left),visit(node.right)
                if isinstance(node.op,ast.Pow) and (right.is_number and abs(right)>100):
                    raise InputError('Eksponentens størrelse må højst være 100.')
                return OPS[type(node.op)](left,right)
            if isinstance(node, ast.Call) and isinstance(node.func,ast.Name) and node.func.id in FUNCTIONS and len(node.args)==1 and not node.keywords:
                return FUNCTIONS[node.func.id](visit(node.args[0]))
            if isinstance(node, (ast.List,ast.Tuple)):
                return [visit(n) for n in node.elts]
            raise InputError('Ikke tilladt udtryk; brug kendte symboler og matematiske funktioner.')
        return visit(tree)
    except (SyntaxError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise InputError('Ugyldigt matematisk udtryk.') from exc
