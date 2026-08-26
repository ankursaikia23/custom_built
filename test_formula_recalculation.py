from core.workbook import Workbook
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet = workbook.add_sheet("Sheet1")

sheet.set_cell("A1", 10)
sheet.set_cell("B1", "=A1+5")
sheet.set_cell("C1", "=B1*2")

evaluator = Evaluator(
    sheet,
    workbook
)


# --------------------------------------------------
# Basic formula cell
# --------------------------------------------------

assert evaluator.evaluate_cell(
    "B1"
) == 15

print("Basic formula cell: PASS")


# --------------------------------------------------
# Formula chain
# --------------------------------------------------

assert evaluator.evaluate_cell(
    "C1"
) == 30

print("Formula dependency chain: PASS")


# --------------------------------------------------
# Change source cell
# --------------------------------------------------

sheet.set_cell("A1", 20)

assert evaluator.evaluate_cell(
    "B1"
) == 25

print("Source change recalculation: PASS")


assert evaluator.evaluate_cell(
    "C1"
) == 50

print("Dependent recalculation: PASS")


# --------------------------------------------------
# Formula with function
# --------------------------------------------------

sheet.set_cell(
    "D1",
    "=SUM(A1,B1)"
)

assert evaluator.evaluate_cell(
    "D1"
) == 45

print("Formula function recalculation: PASS")


# --------------------------------------------------
# Formula referencing formula + cell
# --------------------------------------------------

sheet.set_cell(
    "E1",
    "=C1+A1"
)

assert evaluator.evaluate_cell(
    "E1"
) == 70

print("Mixed dependency: PASS")


# --------------------------------------------------
# Non-formula text
# --------------------------------------------------

sheet.set_cell(
    "F1",
    "Hello"
)

assert evaluator.evaluate_cell(
    "F1"
) == "Hello"

print("Text cell regression: PASS")


# --------------------------------------------------
# Direct numeric cell
# --------------------------------------------------

assert evaluator.evaluate_cell(
    "A1"
) == 20

print("Numeric cell regression: PASS")


print("FORMULA RECALCULATION: PASS")