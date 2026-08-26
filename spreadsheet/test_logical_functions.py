from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

parser = Parser()
evaluator = Evaluator(
    sheet,
    workbook
)


# --------------------------------------------------
# TRUE
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=TRUE()")
) is True

print("TRUE: PASS")


# --------------------------------------------------
# FALSE
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=FALSE()")
) is False

print("FALSE: PASS")


# --------------------------------------------------
# TRUE/FALSE argument validation
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=TRUE(1)")
) == "#VALUE!"

print("TRUE argument error: PASS")


assert evaluator.evaluate(
    parser.parse("=FALSE(1)")
) == "#VALUE!"

print("FALSE argument error: PASS")


# --------------------------------------------------
# XOR — two arguments
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=XOR(TRUE(),FALSE())"
    )
) is True

print("XOR true/false: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=XOR(TRUE(),TRUE())"
    )
) is False

print("XOR true/true: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=XOR(FALSE(),FALSE())"
    )
) is False

print("XOR false/false: PASS")


# --------------------------------------------------
# XOR — multiple arguments
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=XOR(TRUE(),FALSE(),FALSE())"
    )
) is True

print("XOR one true: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=XOR(TRUE(),TRUE(),TRUE())"
    )
) is True

print("XOR three true: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=XOR(TRUE(),TRUE(),FALSE())"
    )
) is False

print("XOR two true: PASS")


# --------------------------------------------------
# XOR — numeric values
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=XOR(1,0)"
    )
) is True

print("XOR numeric: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=XOR(1,1)"
    )
) is False

print("XOR numeric pair: PASS")


# --------------------------------------------------
# XOR — no arguments
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=XOR()"
    )
) == "#VALUE!"

print("XOR missing arguments: PASS")


# --------------------------------------------------
# Existing logical functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=AND(TRUE(),TRUE())"
    )
) is True

print("AND regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=OR(FALSE(),TRUE())"
    )
) is True

print("OR regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=NOT(TRUE())"
    )
) is False

print("NOT regression: PASS")


# --------------------------------------------------
# Comparison regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=10>5"
    )
) is True

print("Comparison regression: PASS")


# --------------------------------------------------
# Final
# --------------------------------------------------

print("LOGICAL FUNCTIONS: PASS")