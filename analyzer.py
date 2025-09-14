from dataclasses import dataclass
from typing import Optional, Tuple, List
import sympy as sp

x = sp.symbols('x')

@dataclass
class AnalysisReport:
    expr_str: str 
    domain_str: str 
    range_str: str  
    x_intercepts: List[str] 
    y_intercept: Optional[str] 
    steps_for_x: Optional[str] 
    steps_y_intercept: Optional[str]
    steps_x_intercepts: Optional[str]

class FunctionAnalyzer:

    def __init__(self, expr: sp.Expr): 
        self.expr = sp.simplify(expr) 

    def _domain(self) -> sp.sets.Set:
        from sympy.calculus.util import continuous_domain 
        try:
            return continuous_domain(self.expr, x, sp.S.Reals)
        except Exception:
            return sp.S.Reals

    def _range(self, domain: sp.sets.Set) -> Optional[sp.sets.Set]:
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
        expr_str = sp.sstr(self.expr)
        # Detectar si el denominador depende de x y se anula en x0
        numer, denom = sp.fraction(self.expr)
        if denom.has(x):
            denom_val = denom.subs(x, x0)
            if denom_val == 0:
                msg = (
                    f"f(x) = {expr_str}\n"
                    f"Sustituyendo x = {x0} ⇒ el denominador se anula: {sp.sstr(denom)} = 0.\n"
                    f"La función racional no está definida en x = {x0} (división por cero)."
                )
                return (msg, None)
        try:
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
            try:
                numer, denom = sp.fraction(self.expr)
                denom_val = denom.subs(x, x0)
                if denom_val == 0:
                    msg = (
                        f"f(x) = {expr_str}\n"
                        f"Sustituyendo x = {x0} ⇒ el denominador se anula: {sp.sstr(denom)} = 0.\n"
                        f"La función racional no está definida en x = {x0} (división por cero)."
                    )
                    return (msg, None)
            except Exception:
                pass
            return (f"No se pudo evaluar en x = {x0}. Detalle: {e}", None)
        
    def _steps_y_intercept(self, domain) -> Optional[str]:
        if 0 not in domain:
            return "La función no está definida en x = 0, no hay corte con Y."
        txt, _ = self._steps_for_value(0)
        return "Intersección con eje Y (x=0):\n" + (txt or "")


    def _steps_x_intercepts(self, domain) -> Optional[str]:
        lines = [f"Intersecciones con eje X (resolver f(x)=0):",
             f"f(x) = {sp.sstr(self.expr)}",
             "Resolver: f(x) = 0"]
        try:
            sol = sp.solveset(sp.Eq(self.expr, 0), x, domain=domain)
            if isinstance(sol, sp.sets.FiniteSet):
                reales = [sp.nsimplify(s) for s in sol if s.is_real]
                if reales:
                    lines.append("Soluciones reales en el dominio: " +
                             ", ".join([f"x = {s}" for s in reales]))
                else:
                    lines.append("No hay soluciones reales en el dominio.")
            else:
                lines.append(f"No se obtuvo un conjunto finito simbólico: {sol}")
        except Exception as e:
            lines.append(f"No se pudo resolver simbólicamente. Detalle: {e}")
        return "\n".join(lines)

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
        stepsY = self._steps_y_intercept(dom)
        stepsX = self._steps_x_intercepts(dom)

        return AnalysisReport(
            expr_str=str(self.expr),
            domain_str=domain_str,
            range_str=range_str,
            x_intercepts=xints_strs,
            y_intercept=yint_str,
            steps_for_x=steps, steps_y_intercept=stepsY,
            steps_x_intercepts=stepsX,
)
