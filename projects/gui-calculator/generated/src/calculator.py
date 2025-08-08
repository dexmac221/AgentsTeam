import ast
from typing import Union

class Calculator:
    """
    Core calculator logic for parsing and evaluating arithmetic expressions.
    Supports +, -, *, /, and parentheses. Handles errors gracefully.
    """

    def __init__(self) -> None:
        self._expression: str = ""

    @property
    def expression(self) -> str:
        """Return the current expression string."""
        return self._expression

    def input(self, value: str) -> None:
        """
        Append a character or string to the current expression.
        :param value: A digit, operator, or parenthesis.
        """
        self._expression += value

    def clear(self) -> None:
        """Reset the current expression to an empty string."""
        self._expression = ""

    def delete(self) -> None:
        """Remove the last character from the current expression."""
        self._expression = self._expression[:-1]

    def evaluate(self) -> str:
        """
        Evaluate the current expression and return the result as a string.
        On error, the expression is cleared and the exception is re-raised.
        :return: Result of the evaluation.
        """
        try:
            result = self._safe_eval(self._expression)
            if isinstance(result, float) and result.is_integer():
                result_str = str(int(result))
            else:
                result_str = str(result)
            self._expression = result_str
            return result_str
        except Exception as exc:
            self._expression = ""
            raise exc

    def _safe_eval(self, expr: str) -> Union[int, float]:
        """
        Safely evaluate an arithmetic expression using AST parsing.
        Only allows numeric literals and +, -, *, / operators.
        :param expr: Expression string.
        :return: Numeric result.
        """
        try:
            node = ast.parse(expr, mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"Invalid syntax: {expr}") from exc

        return self._eval_node(node.body)

    def _eval_node(self, node: ast.AST) -> Union[int, float]:
        """
        Recursively evaluate an AST node.
        :param node: AST node.
        :return: Numeric result.
        """
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type is ast.Add:
                return left + right
            if op_type is ast.Sub:
                return left - right
            if op_type is ast.Mult:
                return left * right
            if op_type is ast.Div:
                return left / right
            if op_type is ast.Pow:
                return left ** right
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

        if isinstance(node, ast.Num):  # For Python <3.8
            return node.n

        if isinstance(node, ast.Constant):  # For Python >=3.8
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)

        raise ValueError(f"Unsupported expression node: {type(node).__name__}")

    def __repr__(self) -> str:
        return f"<Calculator expression='{self._expression}'>"

    def __str__(self) -> str:
        return self._expression


if __name__ == "__main__":
    calc = Calculator()
    calc.input("2+3*4")
    print(f"Expression: {calc.expression}")
    print(f"Result: {calc.evaluate()}")
    calc.clear()
    calc.input("(1+2)/3")
    print(f"Expression: {calc.expression}")
    print(f"Result: {calc.evaluate()}")
    try:
        calc.input("5/0")
        calc.evaluate()
    except ZeroDivisionError:
        print("Caught division by zero as expected.")