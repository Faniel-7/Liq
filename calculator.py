import ast
import operator as op
import re

# Supported operators
OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

WORD_REPLACEMENTS = [
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    (r"\btimes\b", "*"),
    (r"\bmultiplied by\b", "*"),
    (r"\bmultiplied\b", "*"),
    (r"\bx\b", "*"),
    (r"\bdivided by\b", "/"),
    (r"\bover\b", "/"),
    (r"\bmod\b", "%"),
    (r"\bpercent of\b", "% of"),
]

def _normalize_expression(text: str) -> str:
    expr = text.lower().strip()

    
    expr = re.sub(r"^(what is|calculate|compute|solve)\s+", "", expr)

    for pattern, replacement in WORD_REPLACEMENTS:
        expr = re.sub(pattern, replacement, expr)

  
    expr = re.sub(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", r"(\1/100)*\2", expr)

    expr = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)", expr)

    expr = re.sub(r"[^0-9\.\+\-\*\/%\(\)\s]", "", expr)

    return expr.strip()

def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)

    if isinstance(node, ast.Num):  # Python <3.8 compatibility
        return node.n

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        operator_type = type(node.op)

        if operator_type in OPERATORS:
            return OPERATORS[operator_type](left, right)

        raise ValueError("Unsupported operator")

    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        operator_type = type(node.op)

        if operator_type in OPERATORS:
            return OPERATORS[operator_type](operand)

        raise ValueError("Unsupported unary operator")

    raise ValueError("Unsupported expression")

def calculate(question: str):
    expr = _normalize_expression(question)

    if not expr:
        return None

    try:
        parsed = ast.parse(expr, mode="eval")
        result = _safe_eval(parsed)

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        return f"The answer is {result}."
    except Exception:
        return None
    
    