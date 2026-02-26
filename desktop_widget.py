import json
import os
import re
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter import ttk

MM_PER_INCH = 25.4


class ConversionWidget(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MM ↔ Inch Desktop Widget")
        self.resizable(False, False)
        self.configure(padx=16, pady=16)

        self._active_source = None
        self._save_job = None

        self.mm_var = tk.StringVar()
        self.inch_var = tk.StringVar()
        self.inch_decimal_var = tk.StringVar(value="—")
        self.inch_fraction_var = tk.StringVar(value="—")
        self.status_var = tk.StringVar(value="")

        self.calc_expr_var = tk.StringVar()
        self.calc_result_var = tk.StringVar(value="Result: —")

        self._build_ui()
        self._bind_events()

        self.attributes("-topmost", True)
        self.after(0, self._restore_or_position)
        self.bind("<Configure>", self._debounced_save)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        title = ttk.Label(self, text="MM ↔ Inch Converter", font=("Segoe UI", 14, "bold"))
        title.grid(column=0, row=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(self, text="Millimeters (mm)").grid(column=0, row=1, sticky="w")
        mm_entry = ttk.Entry(self, textvariable=self.mm_var, width=30)
        mm_entry.grid(column=0, row=2, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(self, text="Inches (in)").grid(column=0, row=3, sticky="w")
        inch_entry = ttk.Entry(self, textvariable=self.inch_var, width=30)
        inch_entry.grid(column=0, row=4, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(self, text="Inch decimal:").grid(column=0, row=5, sticky="w")
        ttk.Label(self, textvariable=self.inch_decimal_var).grid(column=1, row=5, sticky="w")

        ttk.Label(self, text="Inch fraction:").grid(column=0, row=6, sticky="w")
        ttk.Label(self, textvariable=self.inch_fraction_var).grid(column=1, row=6, sticky="w")

        ttk.Label(self, textvariable=self.status_var, foreground="#b91c1c").grid(
            column=0, row=7, columnspan=2, sticky="w", pady=(6, 14)
        )

        ttk.Separator(self, orient="horizontal").grid(column=0, row=8, columnspan=2, sticky="ew", pady=(0, 12))

        ttk.Label(self, text="Quick Calculator", font=("Segoe UI", 12, "bold")).grid(
            column=0, row=9, columnspan=2, sticky="w", pady=(0, 6)
        )
        ttk.Label(self, text="Expression").grid(column=0, row=10, sticky="w")
        calc_entry = ttk.Entry(self, textvariable=self.calc_expr_var, width=30)
        calc_entry.grid(column=0, row=11, sticky="ew", pady=(0, 8))
        ttk.Button(self, text="Clear", command=self._clear_calculator).grid(column=1, row=11, sticky="e", pady=(0, 8))
        calc_entry.grid(column=0, row=11, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(self, textvariable=self.calc_result_var).grid(column=0, row=12, columnspan=2, sticky="w")

        self.mm_entry = mm_entry
        self.inch_entry = inch_entry
        self.calc_entry = calc_entry

    def _bind_events(self) -> None:
        self.mm_entry.bind("<KeyRelease>", self._on_mm_changed)
        self.inch_entry.bind("<KeyRelease>", self._on_inch_changed)
        self.calc_entry.bind("<KeyRelease>", self._on_calc_changed)

    def _state_path(self) -> Path:
        base = Path(os.environ.get("APPDATA", str(Path.home())))
        folder = base / "MMInchWidget"
        folder.mkdir(parents=True, exist_ok=True)
        return folder / "state.json"

    def _save_window_state(self) -> None:
        geom = self.geometry()
        try:
            self._state_path().write_text(json.dumps({"geometry": geom}), encoding="utf-8")
        except Exception:
            pass

    def _load_window_state(self) -> bool:
        try:
            data = json.loads(self._state_path().read_text(encoding="utf-8"))
            geom = data.get("geometry")
            if isinstance(geom, str) and geom:
                self.geometry(geom)
                return True
        except Exception:
            pass
        return False

    def _snap_top_right(self, margin: int = 16) -> None:
        self.update_idletasks()
        win_w = self.winfo_width()
        win_h = self.winfo_height()
        screen_w = self.winfo_screenwidth()
        x = max(margin, screen_w - win_w - margin)
        y = margin
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")

    def _restore_or_position(self) -> None:
        self.update_idletasks()
        restored = self._load_window_state()
        self.update_idletasks()
        if not restored:
            self._snap_top_right()

    def _debounced_save(self, _event=None) -> None:
        if self._save_job is not None:
            self.after_cancel(self._save_job)
        self._save_job = self.after(250, self._save_window_state)

    def _on_close(self) -> None:
        self._save_window_state()
        self.destroy()

    @staticmethod
    def _gcd(a: int, b: int) -> int:
        a, b = abs(a), abs(b)
        while b:
            a, b = b, a % b
        return a or 1

    @staticmethod
    def _format_decimal(value: float, precision: int = 6) -> str:
        text = f"{value:.{precision}f}"
        text = text.rstrip("0").rstrip(".")
        return text if text else "0"

    def _to_mixed_fraction(self, value: float, max_denominator: int = 64) -> str:
        if value != value:
            return "—"

        sign = "-" if value < 0 else ""
        abs_value = abs(value)
        whole = int(abs_value)
        frac = abs_value - whole

        if frac < 1e-12:
            return f"{sign}{whole}"

        best_num, best_den, best_err = 0, 1, float("inf")
        for den in range(1, max_denominator + 1):
            num = round(frac * den)
            err = abs((num / den) - frac)
            if err < best_err:
                best_num, best_den, best_err = num, den, err

        if best_num == 0:
            return f"{sign}{whole}"

        divisor = self._gcd(best_num, best_den)
        num, den = best_num // divisor, best_den // divisor

        if whole == 0:
            return f"{sign}{num}/{den}"
        return f"{sign}{whole} {num}/{den}"

    @staticmethod
    def _parse_inches(text: str):
        value = text.strip()
        if not value:
            return None

        mixed = re.match(r"^(-?\d+)\s+(\d+)\s*/\s*(\d+)$", value)
        if mixed:
            whole = int(mixed.group(1))
            num = int(mixed.group(2))
            den = int(mixed.group(3))
            if den == 0:
                return float("nan")
            sign = -1 if whole < 0 else 1
            return sign * (abs(whole) + (num / den))

        fraction = re.match(r"^(-?\d+)\s*/\s*(\d+)$", value)
        if fraction:
            num = int(fraction.group(1))
            den = int(fraction.group(2))
            if den == 0:
                return float("nan")
            return num / den

        try:
            return float(value)
        except ValueError:
            return float("nan")

    def _set_inch_display(self, inches):
        if inches is None:
            self.inch_decimal_var.set("—")
            self.inch_fraction_var.set("—")
            return
        self.inch_decimal_var.set(self._format_decimal(inches))
        self.inch_fraction_var.set(self._to_mixed_fraction(inches))

    def _on_mm_changed(self, _event=None) -> None:
        if self._active_source == "inch":
            return

        raw = self.mm_var.get().strip()
        if not raw:
            self._active_source = "mm"
            self.inch_var.set("")
            self._active_source = None
            self._set_inch_display(None)
            self.status_var.set("")
            return

        try:
            mm = float(raw)
        except ValueError:
            self.status_var.set("Enter a valid millimeter number.")
            return

        inches = mm / MM_PER_INCH
        self._active_source = "mm"
        self.inch_var.set(self._format_decimal(inches))
        self._active_source = None
        self._set_inch_display(inches)
        self.status_var.set("")

    def _on_inch_changed(self, _event=None) -> None:
        if self._active_source == "mm":
            return

        raw = self.inch_var.get()
        inches = self._parse_inches(raw)

        if inches is None:
            self._active_source = "inch"
            self.mm_var.set("")
            self._active_source = None
            self._set_inch_display(None)
            self.status_var.set("")
            return

        if inches != inches:
            self.status_var.set("Use decimal, fraction (1/4), or mixed fraction (1 1/4).")
            return

        self._active_source = "inch"
        self.mm_var.set(self._format_decimal(inches * MM_PER_INCH))
        self._active_source = None
        self._set_inch_display(inches)
        self.status_var.set("")

    @staticmethod
    def _evaluate_expression(expr: str):
        text = expr.strip()
        if not text:
            return None, None

        if not re.fullmatch(r"[\d+\-*/().\s%]+", text):
            return None, "Only arithmetic characters are allowed."

        try:
            value = eval(text, {"__builtins__": {}}, {})
        except Exception:
            return None, "Invalid expression."

        if not isinstance(value, (int, float)):
            return None, "Invalid expression result."
        if value != value or value in (float("inf"), float("-inf")):
            return None, "Expression must return a finite number."

        return float(value), None

    def _on_calc_changed(self, _event=None) -> None:
        result, error = self._evaluate_expression(self.calc_expr_var.get())
        if error:
            self.calc_result_var.set(f"Result: {error}")
            return
        if result is None:
            self.calc_result_var.set("Result: —")
            return
        self.calc_result_var.set(f"Result: {self._format_decimal(result, 10)}")

    def _clear_calculator(self) -> None:
        self.calc_expr_var.set("")
        self.calc_result_var.set("Result: —")


def _display_hint() -> str:
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return "No GUI display detected. Set DISPLAY (for example: export DISPLAY=:0) or run from a desktop session."
    return "Unable to start Tkinter GUI. Ensure your system has an active graphical display."


def main() -> None:
    try:
        app = ConversionWidget()
        app.mainloop()
    except tk.TclError as error:
        try:
            messagebox.showerror("Widget Error", f"GUI startup error:\n\n{error}\n\n{_display_hint()}")
        except tk.TclError:
            print(f"GUI startup error: {error}", file=sys.stderr)
            print(_display_hint(), file=sys.stderr)
        print(f"GUI startup error: {error}", file=sys.stderr)
        print(_display_hint(), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
