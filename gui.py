import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from parser import FunctionParser
from analyzer import FunctionAnalyzer
from plotter import FunctionPlotter

class AnalyzerApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("Analizador de Funciones")
        master.geometry("1020x680")

        # --- Barra superior de entrada ---
        top = ttk.Frame(master, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="f(x) =").grid(row=0, column=0, sticky="w")
        self.fun_entry = ttk.Entry(top, width=60)
        self.fun_entry.grid(row=0, column=1, sticky="we", padx=6)
        self.fun_entry.insert(0, "sin(x) + 1/x")

        ttk.Label(top, text="x para evaluar (opcional):").grid(row=0, column=2, padx=(10,0))
        self.x_entry = ttk.Entry(top, width=10)
        self.x_entry.grid(row=0, column=3, sticky="w")

        self.analyze_btn = ttk.Button(top, text="Analizar y Graficar", command=self.on_analyze)
        self.analyze_btn.grid(row=0, column=4, padx=(10,0))

        top.columnconfigure(1, weight=1)

        # --- Keypad de símbolos (nuevo) ---
        keypad = ttk.Frame(master, padding=(10,0))
        keypad.pack(fill="x", pady=(0,8))
        self._build_keypad(keypad)

        # --- Paneles: resultados y gráfico ---
        mid = tk.PanedWindow(master, orient=tk.HORIZONTAL)
        mid.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Resultados
        left = ttk.Frame(mid, padding=8)
        mid.add(left)
        self.results = tk.Text(left, height=20, wrap="word")
        self.results.pack(fill="both", expand=True)

        # Gráfico
        right = ttk.Frame(mid, padding=8)
        mid.add(right, minsize=400)
        self.plot_area = ttk.Frame(right)
        # IMPORTANTE: empacar el contenedor del gráfico antes de dibujar
        self.plot_area.pack(fill="both", expand=True)

        # Mostrar un gráfico vacío al iniciar
        self._show_blank_plot()

        self.parser = FunctionParser()

    # ------------ Keypad de símbolos ------------
    def _build_keypad(self, parent: ttk.Frame):
        # Mapa: (texto del botón, token a insertar, acción_post_inserción)
        rows = [
            [("7","7",None), ("8","8",None), ("9","9",None),
             ("÷","/",None), ("×","*",None), ("−","-",None), ("+","+",None)],
            [("4","4",None), ("5","5",None), ("6","6",None),
             ("(","(",None), (")",")",None), ("^","^",None), (",",",",None)],
            [("1","1",None), ("2","2",None), ("3","3",None),
             ("π","pi",None), ("e","E",None), ("|x|","Abs(x)",None), ("√","sqrt()", "in_parens")],
            [("0","0",None), (".",".",None), ("sin","sin()","in_parens"),
             ("cos","cos()","in_parens"), ("tan","tan()","in_parens"),
             ("log","log()","in_parens"), ("exp","exp()","in_parens")],
        ]

        def insert_token(token: str, post: Optional[str] = None):
            e = self.fun_entry
            # Si hay selección, la reemplaza
            try:
                sel_start = e.index("sel.first")
                sel_end   = e.index("sel.last")
                e.delete(sel_start, sel_end)
                e.icursor(sel_start)
            except tk.TclError:
                pass
            idx = e.index(tk.INSERT)
            e.insert(idx, token)
            # Post-acción: dejar cursor dentro de paréntesis
            if post == "in_parens":
                try:
                    if token.endswith("()"):
                        e.icursor(e.index(tk.INSERT) - 1)
                except Exception:
                    pass
            e.focus_set()

        # Construir filas de botones
        for r, row in enumerate(rows):
            fr = ttk.Frame(parent)
            fr.pack(anchor="w", pady=2)
            for (label, token, post) in row:
                ttk.Button(fr, text=label, width=6,
                           command=lambda t=token, p=post: insert_token(t, p)
                           ).pack(side="left", padx=2)

            # Botones de edición a la derecha de la última fila
            if r == 3:
                ttk.Button(fr, text="DEL", width=6,
                           command=lambda: self._del_char()).pack(side="left", padx=(12,2))
                ttk.Button(fr, text="←", width=4,
                           command=lambda: self._move_cursor(-1)).pack(side="left", padx=2)
                ttk.Button(fr, text="→", width=4,
                           command=lambda: self._move_cursor(+1)).pack(side="left", padx=2)
                ttk.Button(fr, text="Borrar", width=8,
                           command=lambda: self.fun_entry.delete(0, tk.END)).pack(side="left", padx=(10,2))

    def _del_char(self):
        e = self.fun_entry
        try:
            # Si hay selección, bórrala
            sel_start = e.index("sel.first")
            sel_end   = e.index("sel.last")
            e.delete(sel_start, sel_end)
        except tk.TclError:
            # Si no hay selección, borra el char en la posición del cursor
            idx = e.index(tk.INSERT)
            e.delete(idx)

    def _move_cursor(self, delta: int):
        e = self.fun_entry
        idx = e.index(tk.INSERT)
        new_idx = max(0, min(len(e.get()), int(idx) + delta))
        e.icursor(new_idx)
        e.focus_set()

    # ------------ Lógica de análisis y gráfico ------------
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

        # --- Mostrar resultados ---
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

        # --- Dibujar gráfico ---
        for w in self.plot_area.winfo_children():
            w.destroy()

        try:
            plotter = FunctionPlotter(parsed.expr)
            pr = plotter.make_figure(x_value=x_value)
            canvas = FigureCanvasTkAgg(pr.fig, master=self.plot_area)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showwarning("Gráfico no disponible", f"No pude generar el gráfico: {e}")
            self._show_blank_plot("Error al graficar — listo para reintentar")

    def _show_blank_plot(self, title: str = "Grafico"):
        from matplotlib.figure import Figure
        for w in self.plot_area.winfo_children():
            w.destroy()
        fig = Figure(figsize=(6, 4), dpi=110)
        ax = fig.add_subplot(111)
        ax.axhline(0, linewidth=1)
        ax.axvline(0, linewidth=1)
        ax.set_title(title)
        ax.set_xlabel("x"); ax.set_ylabel("f(x)")
        ax.grid(True, alpha=0.2)

        canvas = FigureCanvasTkAgg(fig, master=self.plot_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def launch_app():
    root = tk.Tk()
    AnalyzerApp(root)
    root.mainloop()
