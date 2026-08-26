from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

evaluator = Evaluator(
    sheet,
    workbook
)

parser = Parser()


# --------------------------------------------------
# Division by zero
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=10/0")
) == "#DIV/0!"

print("Division by zero: PASS")


# --------------------------------------------------
# MOD by zero
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=MOD(10,0)")
) == "#DIV/0!"

print("MOD division by zero: PASS")


# --------------------------------------------------
# Error propagation
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")

assert evaluator.evaluate_cell(
    "A1"
) == "#DIV/0!"

print("Error in formula cell: PASS")


sheet.set_cell(
    "B1",
    "=A1+10"
)

assert evaluator.evaluate_cell(
    "B1"
) == "#DIV/0!"

print("Error propagation: PASS")


# --------------------------------------------------
# Normal arithmetic regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=10+5")
) == 15

assert evaluator.evaluate(
    parser.parse("=10*5")
) == 50

assert evaluator.evaluate(
    parser.parse("=10-5")
) == 5

assert evaluator.evaluate(
    parser.parse("=10/2")
) == 5

print("Arithmetic regression: PASS")


# --------------------------------------------------
# Normal MOD regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=MOD(10,3)")
) == 1

print("MOD regression: PASS")


print("ERROR ARITHMETIC: PASS")