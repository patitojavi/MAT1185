from dataclasses import dataclass
from typing import Optional, Tuple, List
import sympy as sp

x = sp.symbols('x')

@dataclass
class AnalysisReport:
    expr_str: str # expresión como texto
    domain_str: str # dominio como texto
    range_str: str  # recorrido como texto
    x_intercepts: List[str] # intersecciones con eje X como textos
    y_intercept: Optional[str] # intersección con eje Y como texto
    steps_for_x: Optional[str] # paso a paso para evaluar en x, si se pidió

class FunctionAnalyzer:
    """Calcula dominio, recorrido, cortes con ejes y un paso a paso para evaluar en un punto."""
    def __init__(self, expr: sp.Expr): 
        self.expr = sp.simplify(expr) 

    def _domain(self) -> sp.sets.Set:
        """Usa continuous_domain; si falla, devuelve Reales."""
        from sympy.calculus.util import continuous_domain 
        try:
            return continuous_domain(self.expr, x, sp.S.Reals)
        except Exception:
            return sp.S.Reals

    def _range(self, domain: sp.sets.Set) -> Optional[sp.sets.Set]:
        """Intenta function_range (puede no resolver para algunas funciones)."""
        try:
            from sympy.calculus.util import function_range
            return function_range(self.expr, x, domain)
        except Exception:
            return None

    def _x_intercepts(self, domain: sp.sets.Set) -> List[sp.Number]:
        vals: List[sp.Number] = []
        try:
            solset = sp.solveset(sp.Eq(self.expr, 0), x, domain=domain)
            if isinstance(solset, sp.sets.FiniteSet):
                for s in solset:
                    if s.is_real:
                        vals.append(sp.nsimplify(s))
        except Exception:
            pass
        return vals

    def _y_intercept(self, domain: sp.sets.Set) -> Optional[sp.Number]:
        try:
            if 0 in domain:
                val = sp.simplify(self.expr.subs(x, 0))
                if val.is_real:
                    return sp.nsimplify(val)
        except Exception:
            return None
        return None

    def _steps_for_value(self, x0: float) -> Tuple[Optional[str], Optional[float]]:
        """Texto paso a paso y valor numérico para x = x0."""
        try:
            expr_str = sp.sstr(self.expr)
            sub_expr = self.expr.subs(x, x0)
            sub_str = sp.sstr(sub_expr)
            val = float(sp.N(sub_expr))
            lines = [
                f"f(x) = {expr_str}",
                f"Sustituyendo x = {x0} ⇒ f({x0}) = {sub_str}",
                f"Cálculo numérico ⇒ f({x0}) ≈ {val}",
            ]
            return ("\n".join(lines), val)
        except Exception as e:
            return (f"No se pudo evaluar en x = {x0}. Detalle: {e}", None)

    def analyze(self, x_value: Optional[float] = None) -> AnalysisReport:
        dom = self._domain()
        rng = self._range(dom)

        xints_syms = self._x_intercepts(dom)
        yint_sym = self._y_intercept(dom)

        domain_str = str(dom)
        range_str = str(rng) if rng is not None else "No determinado automáticamente"
        xints_strs = [str(s) for s in xints_syms]
        yint_str = str(yint_sym) if yint_sym is not None else None

        steps = None
        if x_value is not None:
            steps, _ = self._steps_for_value(x_value)

        return AnalysisReport(
            expr_str=str(self.expr),
            domain_str=domain_str,
            range_str=range_str,
            x_intercepts=xints_strs,
            y_intercept=yint_str,
            steps_for_x=steps
        )
