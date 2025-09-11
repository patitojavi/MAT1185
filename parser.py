from dataclasses import dataclass
from typing import Dict, Any
import sympy as sp

# Conjunto seguro de funciones permitidas para evitar código arbitrario en sympify
ALLOWED_FUNCS: Dict[str, Any] = {
    # aritmética / álgebra
    "Abs": sp.Abs,  # valor absoluto
    "abs": sp.Abs, # valor absoluto
    "sqrt": sp.sqrt, # raíz cuadrada

    # trigonometría
    "sin": sp.sin,
    "cos": sp.cos, 
    "tan": sp.tan,
    "asin": sp.asin, 
    "acos": sp.acos, 
    "atan": sp.atan,
    "sec": sp.sec, 
    "csc": sp.csc, 
    "cot": sp.cot,

    # hiperbólicas
    "sinh": sp.sinh, 
    "cosh": sp.cosh, 
    "tanh": sp.tanh,

    # exp / log
    "exp": sp.exp, 
    "log": sp.log, 
    "ln": sp.log,

    # varias
    "floor": sp.floor, 
    "ceiling": sp.ceiling, 
    "Piecewise": sp.Piecewise,
    "Max": sp.Max, 
    "Min": sp.Min,

    # constantes
    "E": sp.E, 
    "pi": sp.pi,
}

x = sp.symbols('x')

@dataclass
class ParseResult:
    expr: sp.Expr  # expresión SymPy
    text: str      # texto original/normalizado

class FunctionParser:
    """Parsea una función f(x) en texto a una expresión de SymPy permitiendo solo símbolos seguros."""
    def __init__(self) -> None:
        self._locals = {**ALLOWED_FUNCS, "x": x}

    def parse(self, text: str) -> ParseResult:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Ingresa una función no vacía, por ejemplo: sin(x) + 1/x")
        cleaned = text.strip()
        try:
            expr = sp.sympify(cleaned, locals=self._locals, evaluate=True)
        except Exception as e:
            raise ValueError(f"No pude interpretar la función. Revisa la sintaxis. Detalle: {e}")

        # Debe depender sólo de x (o ser constante)
        free = expr.free_symbols
        if free and not (free <= {x}):
            raise ValueError("La función solo puede depender de 'x'.")

        return ParseResult(expr=sp.simplify(expr), text=cleaned)