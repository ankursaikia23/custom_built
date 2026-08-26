from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet1 = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Sheet2")

sheet1.set_cell("A1", 100)

sheet2.set_cell("A1", 10)
sheet2.set_cell("B1", 20)
sheet2.set_cell("A2", 30)
sheet2.set_cell("B2", 40)

parser = Parser()
evaluator = Evaluator(
    sheet1,
    workbook
)


# --------------------------------------------------
# SUM cross-sheet range
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=SUM(Sheet2!A1:B2)"
    )
) == 100

print("Cross-sheet SUM: PASS")


# --------------------------------------------------
# AVERAGE cross-sheet range
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=AVERAGE(Sheet2!A1:B2)"
    )
) == 25

print("Cross-sheet AVERAGE: PASS")


# --------------------------------------------------
# MIN / MAX
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=MIN(Sheet2!A1:B2)"
    )
) == 10

print("Cross-sheet MIN: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=MAX(Sheet2!A1:B2)"
    )
) == 40

print("Cross-sheet MAX: PASS")


# --------------------------------------------------
# COUNT
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=COUNT(Sheet2!A1:B2)"
    )
) == 4

print("Cross-sheet COUNT: PASS")


# --------------------------------------------------
# Quoted sheet name
# --------------------------------------------------

sales = workbook.add_sheet(
    "Sales Data"
)

sales.set_cell("A1", 5)
sales.set_cell("B1", 15)
sales.set_cell("A2", 25)
sales.set_cell("B2", 35)

assert evaluator.evaluate(
    parser.parse(
        "=SUM('Sales Data'!A1:B2)"
    )
) == 80

print("Quoted cross-sheet range: PASS")


# --------------------------------------------------
# Existing local range regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=SUM(Sheet2!A1:B2)"
    )
) == 100

print("Range regression: PASS")


# --------------------------------------------------
# Missing sheet
# --------------------------------------------------

try:
    evaluator.evaluate(
        parser.parse(
            "=SUM(Missing!A1:B2)"
        )
    )

    raise AssertionError(
        "Missing sheet was accepted"
    )

except ValueError:
    print("Missing sheet validation: PASS")


print("CROSS-SHEET RANGES: PASS")