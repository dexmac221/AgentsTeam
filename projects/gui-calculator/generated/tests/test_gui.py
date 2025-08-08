import tkinter as tk
import pytest

from calculator_gui import CalculatorGUI


def find_button(root: tk.Tk, text: str) -> tk.Button:
"""
Helper function to locate a Button widget by its displayed text.
"""
for widget in root.winfo_children():
if isinstance(widget, tk.Button) and widget.cget("text") == text:
return widget
raise ValueError(f"Button with text '{text}' not found.")


@pytest.fixture
def gui():
"""
Pytest fixture that creates a Tkinter root window and an instance of the calculator GUI.
The root window is destroyed after the test to avoid resource leaks.
"""
root = tk.Tk()
root.withdraw()
calculator = CalculatorGUI(root)
yield calculator
root.destroy()


def test_display_updates_on_number_press(gui: CalculatorGUI):
"""
Verify that pressing number buttons updates the display correctly.
"""
for digit in ("1", "2", "3"):
button = find_button(gui.root, digit)
button.invoke()
gui.root.update_idletasks()

display_value = gui.display_var.get()
assert display_value == "123", f"Expected display to be '123', got '{display_value}'"


def test_addition_operation(gui: CalculatorGUI):
"""
Verify that a simple addition operation works as expected.
"""
for char in ("1", "+", "2", "="):
button = find_button(gui.root, char)
button.invoke()
gui.root.update_idletasks()

result = gui.display_var.get()
assert result == "3", f"Expected result to be '3', got '{result}'"


def test_division_by_zero(gui: CalculatorGUI):
"""
Verify that division by zero is handled gracefully.
"""
for char in ("1", "/", "0", "="):
button = find_button(gui.root, char)
button.invoke()
gui.root.update_idletasks()

result = gui.display_var.get()
assert result.lower() in ("error", "inf", "nan"), f"Unexpected result for division by zero: '{result}'"


def test_clear_functionality(gui: CalculatorGUI):
"""
Verify that the clear button resets the display.
"""
for char in ("9", "8", "7", "C"):
button = find_button(gui.root, char)
button.invoke()
gui.root.update_idletasks()

result = gui.display_var.get()
assert result == "", f"Expected display to be cleared, got '{result}'"


def test_multiple_operations(gui: CalculatorGUI):
"""
Verify that the calculator can handle a sequence of operations.
"""
for char in ("2", "*", "3", "+", "4", "="):
button = find_button(gui.root, char)
button.invoke()
gui.root.update_idletasks()

result = gui.display_var.get()
assert result == "10", f"Expected result to be '10', got '{result}'"