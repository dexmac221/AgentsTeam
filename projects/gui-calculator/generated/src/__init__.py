"""
Package initializer for the calculator module.

calculator logic and the GUI entry point, and provides a convenient
function to launch the application.
"""

from .calculator import Calculator, ExpressionError

from .gui import CalculatorGUI

__all__ = [
"Calculator",
"ExpressionError",
"CalculatorGUI",
"run_calculator",
]

def run_calculator() -> None:
"""
Launch the calculator GUI application.

This helper function creates an instance of :class:`CalculatorGUI`
and starts the Tkinter main loop. It is intended to be used as the
entry point when the package is executed as a script.

Raises:
RuntimeError: If the GUI cannot be initialized.
"""
try:
app = CalculatorGUI()
app.mainloop()
except Exception as exc:
raise RuntimeError("Failed to launch the calculator GUI") from exc