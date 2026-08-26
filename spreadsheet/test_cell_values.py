from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

sheet.set_cell("A1", "Hello")
sheet.set_cell("B1", "Hello")
sheet.set_cell("C1", "World")

sheet.set_cell("A2", 10)
sheet.set_cell("B2", "20")

parser = Parser()
evaluator = Evaluator(sheet)


# --------------------------------------------------
# Text cell
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1")
) == "Hello"

print("Text cell: PASS")


# --------------------------------------------------
# Text comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1=B1")
) is True

print("Equal text comparison: PASS")


assert evaluator.evaluate(
    parser.parse("=A1=C1")
) is False

print("Unequal text comparison: PASS")


# --------------------------------------------------
# Numeric cells remain numeric
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A2")
) == 10

print("Numeric cell: PASS")


# --------------------------------------------------
# Numeric string remains numeric
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=B2")
) == 20

print("Numeric string: PASS")


# --------------------------------------------------
# Existing arithmetic remains functional
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A2+5")
) == 15

print("Numeric arithmetic: PASS")


# --------------------------------------------------
# Empty cell behavior remains unchanged
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=D1")
) == 0

print("Empty cell: PASS")


# --------------------------------------------------
# Text arithmetic should fail
# --------------------------------------------------

try:
    evaluator.evaluate(
        parser.parse("=A1+5")
    )

    raise AssertionError(
        "Text arithmetic was accepted"
    )

except (TypeError, ValueError):
    print("Text arithmetic rejected: PASS")


print("TEXT VALUES: PASS")