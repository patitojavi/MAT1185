import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Tuple
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from parser import FunctionParser
from analyzer import FunctionAnalyzer
from plotter import FunctionPlotter


class AnalyzerApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("Analizador de Funciones")
        master.geometry("1020x680")

        # --- Top bar ---
        top = ttk.Frame(master, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="f(x) =").grid(row=0, column=0, sticky="w")
        self.fun_entry = ttk.Entry(top, width=60)
        self.fun_entry.grid(row=0, column=1, sticky="we", padx=6)
        self.fun_entry.insert(0, "sin(x) + 1/x")

        ttk.Label(top, text="x para evaluar (opcional):").grid(row=0, column=2, padx=(10, 0))
        self.x_entry = ttk.Entry(top, width=10)
        self.x_entry.grid(row=0, column=3, sticky="w")

        self.analyze_btn = ttk.Button(top, text="Analizar y Graficar", command=self.on_analyze)
        self.analyze_btn.grid(row=0, column=4, padx=(10, 0))

        top.columnconfigure(1, weight=1)
        keypad = ttk.Frame(master, padding=(10,0))
        keypad.pack(fill="x", pady=(0,8))

        # --- Keypad ---
        keypad = ttk.Frame(master, padding=(10, 0))
        keypad.pack(fill="x", pady=(0, 8))
        self._build_keypad(keypad)

        # --- Paned window: results | plot ---
        mid = tk.PanedWindow(master, orient=tk.HORIZONTAL)
        mid.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Left: results
        left = ttk.Frame(mid, padding=8)
        mid.add(left)
        self.results = tk.Text(left, height=20, wrap="word")
        self.results.pack(fill="both", expand=True)

        # Right: plot
        right = ttk.Frame(mid, padding=8)
        mid.add(right, minsize=400)
        self.plot_area = ttk.Frame(right)
        self.plot_area.pack(fill="both", expand=True)

        self._show_blank_plot()

        # Parser
        self.parser = FunctionParser()

        # Matplotlib connections (para evitar duplicados)
        self._mpl_cids: List[Tuple[FigureCanvasTkAgg, int]] = []

        # Mantener referencias a canvas/toolbar
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.toolbar: Optional[NavigationToolbar2Tk] = None

    # ------------------------------
    # Helpers para conexiones Matplotlib
    # ------------------------------
    def _clear_mpl_connections(self):
        """Desconecta handlers previos de Matplotlib si existen."""
        if hasattr(self, "_mpl_cids") and self._mpl_cids:
            try:
                for canvas, cid in self._mpl_cids:
                    canvas.mpl_disconnect(cid)
            except Exception:
                pass
        self._mpl_cids = []

    def _attach_scroll_zoom(self, canvas: FigureCanvasTkAgg, fig):
        """Zoom con la rueda del mouse, centrado en el puntero y limitado al eje."""
        # Limpia conexiones anteriores (si re-graficaste)
        self._clear_mpl_connections()

        if not fig.axes:
            return
        ax = fig.axes[0]

        def on_scroll(event):
            # Solo si el cursor está dentro del eje
            if event.inaxes != ax:
                return

            # factor de zoom: rueda arriba acerca, abajo aleja
            scale = 0.9 if event.button == "up" else 1.1

            xdata, ydata = event.xdata, event.ydata
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            # Modos con modificadores:
            #   Shift: zoom solo X
            #   Ctrl:  zoom solo Y
            only_x = bool(event.key) and "shift" in event.key
            only_y = bool(event.key) and "control" in event.key

            if not only_y:
                new_xlim = (
                    xdata + (xlim[0] - xdata) * scale,
                    xdata + (xlim[1] - xdata) * scale
                )
                ax.set_xlim(new_xlim)
            if not only_x:
                new_ylim = (
                    ydata + (ylim[0] - ydata) * scale,
                    ydata + (ylim[1] - ydata) * scale
                )
                ax.set_ylim(new_ylim)

            canvas.draw_idle()

        cid = canvas.mpl_connect("scroll_event", on_scroll)
        self._mpl_cids.append((canvas, cid))

    # ------------------------------
    # Keypad
    # ------------------------------
    def _build_keypad(self, parent: ttk.Frame):

        rows = [
            [("7", "7", None), ("8", "8", None), ("9", "9", None),
             ("÷", "/", None), ("×", "*", None), ("−", "-", None), ("+", "+", None)],
            [("4", "4", None), ("5", "5", None), ("6", "6", None),
             ("(", "(", None), (")", ")", None), ("^", "^", None), (",", ",", None)],
            [("1", "1", None), ("2", "2", None), ("3", "3", None),
             ("π", "pi", None), ("e", "E", None), ("|x|", "Abs(x)", None), ("√", "sqrt()", "in_parens")],
            [("0", "0", None), (".", ".", None), ("sin", "sin()", "in_parens"),
             ("cos", "cos()", "in_parens"), ("tan", "tan()", "in_parens"),
             ("log", "log()", "in_parens"), ("exp", "exp()", "in_parens")],
        ]

        def insert_token(token: str, post: Optional[str] = None):
            e = self.fun_entry
            # Reemplaza selección si hay
            try:
                sel_start = e.index("sel.first")
                sel_end = e.index("sel.last")
                e.delete(sel_start, sel_end)
                e.icursor(sel_start)
            except tk.TclError:
                pass
            idx = e.index(tk.INSERT)
            e.insert(idx, token)
            if post == "in_parens":
                try:
                    if token.endswith("()"):
                        e.icursor(e.index(tk.INSERT) - 1)  # cursor entre paréntesis
                except Exception:
                    pass
            e.focus_set()

        for r, row in enumerate(rows):
            fr = ttk.Frame(parent)
            fr.pack(anchor="w", pady=2)
            for (label, token, post) in row:
                ttk.Button(
                    fr, text=label, width=6,
                    command=lambda t=token, p=post: insert_token(t, p)
                ).pack(side="left", padx=2)

            if r == 3:
                ttk.Button(fr, text="DEL", width=6,
                           command=self._del_char).pack(side="left", padx=(12, 2))
                ttk.Button(fr, text="←", width=4,
                           command=lambda: self._move_cursor(-1)).pack(side="left", padx=2)
                ttk.Button(fr, text="→", width=4,
                           command=lambda: self._move_cursor(+1)).pack(side="left", padx=2)
                ttk.Button(fr, text="Borrar", width=8,
                           command=lambda: self.fun_entry.delete(0, tk.END)).pack(side="left", padx=(10, 2))

    def _del_char(self):
        e = self.fun_entry
        try:
            sel_start = e.index("sel.first")
            sel_end = e.index("sel.last")
            e.delete(sel_start, sel_end)
        except tk.TclError:
            idx = e.index(tk.INSERT)
            e.delete(idx)

    def _move_cursor(self, delta: int):
        e = self.fun_entry
        idx = e.index(tk.INSERT)
        new_idx = max(0, min(len(e.get()), int(idx) + delta))
        e.icursor(new_idx)
        e.focus_set()

    # ------------------------------
    # Analizar y graficar
    # ------------------------------
    def on_analyze(self):
        fx_text = self.fun_entry.get().strip()
        x_text = self.x_entry.get().strip()
        x_value: Optional[float] = None

        if x_text:
            try:
                x_value = float(x_text.replace(",", "."))
            except Exception:
                messagebox.showerror("Error", "x debe ser un número real (usa punto decimal).")
                self._show_blank_plot("Error — listo para reintentar")
                return

        try:
            parsed = self.parser.parse(fx_text)
            analyzer = FunctionAnalyzer(parsed.expr)
            report = analyzer.analyze(x_value=x_value)
        except Exception as e:
            messagebox.showwarning("Error al analizar", f"No pude analizar/graficar: {e}")
            self._show_blank_plot("Error al analizar — listo para reintentar")
            return

        self.results.delete("1.0", tk.END)
        self.results.insert(tk.END, f"Función: f(x) = {report.expr_str}\n\n")
        self.results.insert(tk.END, f"Dominio: {report.domain_str}\n")
        self.results.insert(tk.END, f"Recorrido: {report.range_str}\n\n")

        self.results.insert(tk.END, "Intersecciones con el eje X: ")
        if report.x_intercepts:
            self.results.insert(tk.END, ", ".join([f"(x={xi})" for xi in report.x_intercepts]) + "\n")
        else:
            self.results.insert(tk.END, "—\n")

        self.results.insert(tk.END, "Intersección con el eje Y: ")
        if report.y_intercept is not None:
            self.results.insert(tk.END, f"(0, {report.y_intercept})\n\n")
        else:
            self.results.insert(tk.END, "—\n\n")

        if hasattr(report, "steps_y_intercept") and report.steps_y_intercept:
            self.results.insert(tk.END, "\n" + report.steps_y_intercept + "\n")

        if hasattr(report, "steps_x_intercepts") and report.steps_x_intercepts:
            self.results.insert(tk.END, "\n" + report.steps_x_intercepts + "\n")

        if report.steps_for_x:
            self.results.insert(tk.END, "\nCálculo paso a paso (x evaluada):\n")
            self.results.insert(tk.END, report.steps_for_x + "\n")

        for w in self.plot_area.winfo_children():
            w.destroy()

        try:
            plotter = FunctionPlotter(parsed.expr)
            pr = plotter.make_figure(x_value=x_value)

            # Mantén referencias en self para que no se recolecten
            self.canvas = FigureCanvasTkAgg(pr.fig, master=self.plot_area)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill="both", expand=True)

            # Toolbar
            toolbar_frame = ttk.Frame(self.plot_area)
            toolbar_frame.pack(fill="x")
            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame, pack_toolbar=False)
            self.toolbar.update()
            self.toolbar.pack(side="left")

            # Scroll zoom centrado en el puntero
            self._attach_scroll_zoom(self.canvas, pr.fig)

        except Exception as e:
            messagebox.showwarning("Gráfico no disponible", f"No pude generar el gráfico: {e}")
            self._show_blank_plot("Error al graficar — listo para reintentar")

    # ------------------------------
    # Plot vacío de cortesía
    # ------------------------------
    def _show_blank_plot(self, title: str = "Gráfico"):
        from matplotlib.figure import Figure

        # Limpia conexiones y widgets previos
        self._clear_mpl_connections()
        for w in self.plot_area.winfo_children():
            w.destroy()

        fig = Figure(figsize=(6, 4), dpi=110)
        ax = fig.add_subplot(111)
        ax.axhline(0, linewidth=1)
        ax.axvline(0, linewidth=1)
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.set_ylabel("f(x)")
        ax.grid(True, alpha=0.2)

        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)


def launch_app():
    root = tk.Tk()
    # Opcional: tema nativo del sistema
    try:
        style = ttk.Style()
        style.theme_use(style.theme_use())
    except Exception:
        pass
    AnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_app()
