import pytest
from calculator import Calculator

@pytest.fixture
def calc():
return Calculator()

def test_addition(calc):
"""Test simple addition."""
assert calc.add(2, 3) == 5
assert calc.add(-1, 1) == 0
assert calc.add(0, 0) == 0

def test_subtraction(calc):
"""Test simple subtraction."""
assert calc.subtract(5, 3) == 2
assert calc.subtract(0, 5) == -5
assert calc.subtract(-2, -3) == 1

def test_multiplication(calc):
"""Test simple multiplication."""
assert calc.multiply(4, 3) == 12
assert calc.multiply(-2, 3) == -6
assert calc.multiply(0, 100) == 0

def test_division(calc):
"""Test simple division."""
assert calc.divide(10, 2) == 5
assert calc.divide(-9, 3) == -3
assert calc.divide(5, 2) == 2.5

def test_division_by_zero(calc):
"""Division by zero should raise ZeroDivisionError."""
with pytest.raises(ZeroDivisionError):
calc.divide(5, 0)

def test_invalid_input(calc):
"""Operations with non-numeric inputs should raise TypeError."""
with pytest.raises(TypeError):
calc.add("a", 1)
with pytest.raises(TypeError):
calc.subtract(1, None)
with pytest.raises(TypeError):
calc.multiply([1, 2], 3)
with pytest.raises(TypeError):
calc.divide(3, {"x": 1})