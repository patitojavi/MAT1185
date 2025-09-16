from dataclasses import dataclass
from typing import Optional, Tuple, List
import math
import sympy as sp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

x = sp.symbols('x')

@dataclass
class PlotResult:
    fig: "plt.Figure"
    x_value: Optional[float]
    y_value: Optional[float]

class FunctionPlotter:
    def __init__(self, expr: sp.Expr):
        self.expr = sp.simplify(expr)
        self.f = sp.lambdify(x, self.expr, modules=["math"])

    def sample_points(self, xmin: float, xmax: float, n: int = 1000) -> Tuple[List[float], List[float]]:
        xs, ys = [], []
        step = (xmax - xmin) / (n - 1)
        for i in range(n):
            xi = xmin + i * step
            try:
                yi = self.f(xi)
                if yi is None or isinstance(yi, complex):
                    continue
                if math.isfinite(yi):
                    xs.append(xi); ys.append(yi)
            except Exception:
                continue
        return xs, ys

    def make_figure(self, x_value: Optional[float] = None,
                    window: Tuple[float, float] = (-10, 10)) -> PlotResult:
        xmin, xmax = window
        # Si x_value está fuera del rango, ajusta la ventana para incluirlo
        if x_value is not None:
            margin = 2  # margen extra
            if x_value < xmin:
                xmin = x_value - margin
            if x_value > xmax:
                xmax = x_value + margin
        xs, ys = self.sample_points(xmin, xmax)

        fig, ax = plt.subplots(figsize=(6,4), dpi=110)
        ax.plot(xs, ys, linewidth=2)
        ax.axhline(0, linewidth=1)
        ax.axvline(0, linewidth=1)
        ax.set_title("f(x)")
        ax.set_xlabel("x"); ax.set_ylabel("f(x)")

        yv = None
        if x_value is not None:
            try:
                yv = float(sp.N(self.expr.subs(x, x_value)))
                if math.isfinite(yv):
                    ax.scatter([x_value], [yv], s=40, zorder=5)
                    ax.annotate(f"({x_value:.3g}, {yv:.3g})", (x_value, yv),
                                textcoords="offset points", xytext=(6,6))
            except Exception:
                yv = None

        ax.grid(True, alpha=0.2)
        fig.tight_layout()
        return PlotResult(fig=fig, x_value=x_value, y_value=yv)

    def save_png(self, path: str, x_value: Optional[float] = None,
                 window: Tuple[float, float] = (-10, 10)) -> str:
        pr = self.make_figure(x_value=x_value, window=window)
        pr.fig.savefig(path)
        return path