from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Sheet2")

parser = Parser()
evaluator = Evaluator(
    sheet,
    workbook
)


# --------------------------------------------------
# Direct circular reference
# --------------------------------------------------

sheet.set_cell(
    "A1",
    "=A1+1"
)

assert evaluator.evaluate_cell(
    "A1"
) == "#CIRC!"

print("Direct circular reference: PASS")


# --------------------------------------------------
# Two-cell circular reference
# --------------------------------------------------

sheet.set_cell(
    "A1",
    "=B1+1"
)

sheet.set_cell(
    "B1",
    "=A1+1"
)

assert evaluator.evaluate_cell(
    "A1"
) == "#CIRC!"

print("Two-cell circular reference: PASS")


# --------------------------------------------------
# Three-cell circular reference
# --------------------------------------------------

sheet.set_cell(
    "A1",
    "=B1+1"
)

sheet.set_cell(
    "B1",
    "=C1+1"
)

sheet.set_cell(
    "C1",
    "=A1+1"
)

assert evaluator.evaluate_cell(
    "A1"
) == "#CIRC!"

print("Three-cell circular reference: PASS")


# --------------------------------------------------
# Circular dependency must propagate
# --------------------------------------------------

sheet.set_cell(
    "D1",
    "=A1+100"
)

assert evaluator.evaluate_cell(
    "D1"
) == "#CIRC!"

print("Circular error propagation: PASS")


# --------------------------------------------------
# Valid formula after circular formula
# --------------------------------------------------

sheet.set_cell(
    "A1",
    "=10+5"
)

sheet.set_cell(
    "B1",
    "=A1+5"
)

assert evaluator.evaluate_cell(
    "B1"
) == 20

print("Post-circular recovery: PASS")


# --------------------------------------------------
# Cross-sheet circular reference
# --------------------------------------------------

sheet.set_cell(
    "A2",
    "=Sheet2!A2+1"
)

sheet2.set_cell(
    "A2",
    "=Sheet1!A2+1"
)

assert evaluator.evaluate_cell(
    "A2"
) == "#CIRC!"

print("Cross-sheet circular reference: PASS")


# --------------------------------------------------
# Cross-sheet valid formula
# --------------------------------------------------

sheet2.set_cell(
    "A2",
    50
)

sheet.set_cell(
    "A2",
    "=Sheet2!A2+10"
)

assert evaluator.evaluate_cell(
    "A2"
) == 60

print("Cross-sheet recovery: PASS")


# --------------------------------------------------
# Normal formula regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=10*5+2")
) == 52

print("Arithmetic regression: PASS")


print("CIRCULAR REFERENCES: PASS")