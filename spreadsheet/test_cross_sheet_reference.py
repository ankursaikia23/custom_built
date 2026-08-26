from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet1 = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Sheet2")

sheet1.set_cell("A1", 10)
sheet1.set_cell("B1", 100)

sheet2.set_cell("A1", 20)
sheet2.set_cell("B1", 200)

parser = Parser()
evaluator = Evaluator(
    sheet1,
    workbook
)


# --------------------------------------------------
# Basic cross-sheet reference
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=Sheet2!A1")
) == 20

print("Cross-sheet cell: PASS")


# --------------------------------------------------
# Cross-sheet arithmetic
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=Sheet2!A1+10")
) == 30

print("Cross-sheet arithmetic: PASS")


# --------------------------------------------------
# Multiple cross-sheet references
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=Sheet2!A1+Sheet2!B1"
    )
) == 220

print("Multiple cross-sheet references: PASS")


# --------------------------------------------------
# Cross-sheet comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=Sheet2!A1<Sheet1!B1"
    )
) is True

print("Cross-sheet comparison: PASS")


# --------------------------------------------------
# Quoted sheet name
# --------------------------------------------------

sheet3 = workbook.add_sheet(
    "Sales Data"
)

sheet3.set_cell("A1", 500)

assert evaluator.evaluate(
    parser.parse(
        "='Sales Data'!A1"
    )
) == 500

print("Quoted sheet reference: PASS")


# --------------------------------------------------
# Missing sheet
# --------------------------------------------------

try:
    evaluator.evaluate(
        parser.parse(
            "=Missing!A1"
        )
    )

    raise AssertionError(
        "Missing sheet was accepted"
    )

except ValueError:
    print("Missing sheet validation: PASS")


print("CROSS-SHEET REFERENCES: PASS")