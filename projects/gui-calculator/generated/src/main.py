import sys
import logging
from tkinter import Tk
from calculator import Calculator
from gui import CalculatorGUI

def main() -> None:
    """
    Entry point for the calculator GUI application.
    Sets up logging, creates the root window, and starts the main loop.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        root = Tk()
        root.title("Calculator")
        
        calculator = Calculator()
        app = CalculatorGUI(root, calculator)
        
        root.mainloop()
    except Exception as exc:
        logging.exception("Unhandled exception in the main loop: %s", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()