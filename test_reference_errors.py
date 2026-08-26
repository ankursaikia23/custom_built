from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Sheet2")

sheet.set_cell("A1", 10)
sheet2.set_cell("A1", 20)
sheet2.set_cell("B1", 30)

parser = Parser()
evaluator = Evaluator(
    sheet,
    workbook
)


# --------------------------------------------------
# Missing sheet cell reference
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=Missing!A1")
) == "#REF!"

print("Missing sheet reference: PASS")


# --------------------------------------------------
# Missing sheet range
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=SUM(Missing!A1:B2)"
    )
) == "#REF!"

print("Missing sheet range: PASS")


# --------------------------------------------------
# Existing cross-sheet reference
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=Sheet2!A1")
) == 20

print("Valid cross-sheet reference: PASS")


# --------------------------------------------------
# Existing cross-sheet range
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=SUM(Sheet2!A1:B1)"
    )
) == 50

print("Valid cross-sheet range: PASS")


# --------------------------------------------------
# Missing cell remains zero
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=Z99")
) == 0

print("Missing cell regression: PASS")


# --------------------------------------------------
# Error propagation
# --------------------------------------------------

sheet.set_cell(
    "B1",
    "=Missing!A1+10"
)

assert evaluator.evaluate_cell(
    "B1"
) == "#REF!"

print("Reference error propagation: PASS")


# --------------------------------------------------
# Normal arithmetic regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1+5")
) == 15

print("Arithmetic regression: PASS")


print("REFERENCE ERRORS: PASS")