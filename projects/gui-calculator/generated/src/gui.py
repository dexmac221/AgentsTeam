import tkinter as tk
from tkinter import ttk
from calculator import Calculator

class CalculatorGUI:
    """Tkinter GUI for the calculator application."""

    def __init__(self, root: tk.Tk, calculator: Calculator) -> None:
        self.root = root
        self.calculator = calculator
        self.root.title("Calculator")
        self.root.resizable(False, False)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(
            "TButton",
            font=("Helvetica", 14),
            padding=10,
            background="#f0f0f0",
            foreground="#000",
        )
        self.style.map(
            "TButton",
            background=[("active", "#d0d0d0")],
            foreground=[("active", "#000")],
        )
        self.style.configure(
            "Display.TEntry",
            font=("Helvetica", 18),
            foreground="#000",
            background="#fff",
            borderwidth=2,
            relief="sunken",
        )

        self._create_widgets()
        self._layout_widgets()

    def _create_widgets(self) -> None:
        """Create all widgets used in the GUI."""
        self.display_var = tk.StringVar()
        self.display = ttk.Entry(
            self.root,
            textvariable=self.display_var,
            state="readonly",
            style="Display.TEntry",
            justify="right",
        )

        self.buttons = [
            ("7", lambda: self._on_digit("7")),
            ("8", lambda: self._on_digit("8")),
            ("9", lambda: self._on_digit("9")),
            ("/", lambda: self._on_operator("/")),
            ("4", lambda: self._on_digit("4")),
            ("5", lambda: self._on_digit("5")),
            ("6", lambda: self._on_digit("6")),
            ("*", lambda: self._on_operator("*")),
            ("1", lambda: self._on_digit("1")),
            ("2", lambda: self._on_digit("2")),
            ("3", lambda: self._on_digit("3")),
            ("-", lambda: self._on_operator("-")),
            ("0", lambda: self._on_digit("0")),
            ("C", self._on_clear),
            ("=", self._on_equals),
            ("+", lambda: self._on_operator("+")),
        ]

        self.button_widgets = [
            ttk.Button(self.root, text=text, command=cmd, style="TButton")
            for text, cmd in self.buttons
        ]

    def _layout_widgets(self) -> None:
        """Place widgets in the window using grid layout."""
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)

        for idx, button in enumerate(self.button_widgets):
            row = (idx // 4) + 1
            col = idx % 4
            button.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

        for i in range(4):
            self.root.columnconfigure(i, weight=1)
        for i in range(5):
            self.root.rowconfigure(i, weight=1)

    def _on_digit(self, digit: str) -> None:
        """Handle digit button press."""
        self.calculator.input(digit)
        self._update_display()

    def _on_operator(self, operator: str) -> None:
        """Handle operator button press."""
        self.calculator.input(operator)
        self._update_display()

    def _on_equals(self) -> None:
        """Handle equals button press."""
        try:
            result = self.calculator.evaluate()
            self.display_var.set(result)
        except Exception as e:
            self.display_var.set("Error")
            self.calculator.clear()

    def _on_clear(self) -> None:
        """Handle clear button press."""
        self.calculator.clear()
        self._update_display()

    def _update_display(self) -> None:
        """Update the display with the current expression."""
        self.display_var.set(self.calculator.expression)

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    calc = Calculator()
    gui = CalculatorGUI(root, calc)
    gui.run()