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
        master.geometry("980x620")

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

        # --- Paneles: resultados y gráfico ---
        mid = ttk.PanedWindow(master, orient=tk.HORIZONTAL)
        mid.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Resultados
        left = ttk.Frame(mid, padding=8)
        mid.add(left, weight=1)
        self.results = tk.Text(left, height=20, wrap="word")
        self.results.pack(fill="both", expand=True)

        # Gráfico
        right = ttk.Frame(mid, padding=8)
        mid.add(right, weight=1)
        self.plot_area = ttk.Frame(right)
        self.plot_area.pack(fill="both", expand=True)

        self.parser = FunctionParser()

    def on_analyze(self):
        fx_text = self.fun_entry.get().strip()
        x_text = self.x_entry.get().strip()
        x_value: Optional[float] = None
        if x_text:
            try:
                x_value = float(x_text.replace(",", "."))
            except Exception:
                messagebox.showerror("Error", "x debe ser un número real (usa punto decimal).")
                return

        try:
            parsed = self.parser.parse(fx_text)
            analyzer = FunctionAnalyzer(parsed.expr)
            report = analyzer.analyze(x_value=x_value)
        except Exception as e:
            messagebox.showerror("Error al analizar", str(e))
            return

        # --- Mostrar resultados ---
        self.results.delete("1.0", tk.END)
        self.results.insert(tk.END, f"Función: f(x) = {report.expr_str}\n\n")
        self.results.insert(tk.END, f"Dominio: {report.domain_str}\n")
        self.results.insert(tk.END, f"Recorrido: {report.range_str}\n\n")

        self.results.insert(tk.END, f"Intersecciones con el eje X: ")
        if report.x_intercepts:
            self.results.insert(tk.END, ", ".join([f"(x={xi})" for xi in report.x_intercepts]) + "\n")
        else:
            self.results.insert(tk.END, "—\n")

        self.results.insert(tk.END, f"Intersección con el eje Y: ")
        if report.y_intercept is not None:
            self.results.insert(tk.END, f"(0, {report.y_intercept})\n\n")
        else:
            self.results.insert(tk.END, "—\n\n")

        if report.steps_for_x:
            self.results.insert(tk.END, "Cálculo paso a paso:\n")
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

def launch_app():
    root = tk.Tk()
    AnalyzerApp(root)
    root.mainloop()