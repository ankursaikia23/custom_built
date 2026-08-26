from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

# --------------------------------------------------
# Workbook setup
# --------------------------------------------------

workbook = Workbook()

sheet1 = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Sheet2")
sales = workbook.add_sheet("Sales Data")

sheet1.set_cell("A1", 10)
sheet1.set_cell("B1", "Hello")

sheet2.set_cell("A1", 20)
sheet2.set_cell("B1", 30)
sheet2.set_cell("A2", 40)
sheet2.set_cell("B2", 50)

sales.set_cell("A1", 100)
sales.set_cell("B1", 200)

parser = Parser()
evaluator = Evaluator(
    sheet1,
    workbook
)


# --------------------------------------------------
# Text values
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=B1")
) == "Hello"

print("Text values: PASS")


# --------------------------------------------------
# Boolean comparisons
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1<Sheet2!A1")
) is True

print("Cross-sheet comparison: PASS")


# --------------------------------------------------
# Cross-sheet cell
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=Sheet2!A1")
) == 20

print("Cross-sheet cell: PASS")


# --------------------------------------------------
# Cross-sheet range
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=SUM(Sheet2!A1:B2)"
    )
) == 140

print("Cross-sheet range: PASS")


# --------------------------------------------------
# Quoted sheet name
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=SUM('Sales Data'!A1:B1)"
    )
) == 300

print("Quoted sheet range: PASS")


# --------------------------------------------------
# Formula dependency chain
# --------------------------------------------------

sheet1.set_cell(
    "C1",
    "=A1+Sheet2!A1"
)

sheet1.set_cell(
    "D1",
    "=C1*2"
)

assert evaluator.evaluate_cell(
    "C1"
) == 30

print("Cross-sheet dependency: PASS")


assert evaluator.evaluate_cell(
    "D1"
) == 60

print("Dependency chain: PASS")


# --------------------------------------------------
# Change source and recalculate
# --------------------------------------------------

sheet2.set_cell(
    "A1",
    50
)

assert evaluator.evaluate_cell(
    "C1"
) == 60

print("Cross-sheet source change: PASS")


assert evaluator.evaluate_cell(
    "D1"
) == 120

print("Dependent recalculation: PASS")


# --------------------------------------------------
# Logical function + comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=AND(A1<Sheet2!A1,A1<20)"
    )
) is True

print("Logical integration: PASS")


# --------------------------------------------------
# Math function + cell reference
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=ABS(A1-Sheet2!A1)"
    )
) == 40

print("Math integration: PASS")


# --------------------------------------------------
# Existing arithmetic regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=A1+5"
    )
) == 15

print("Arithmetic regression: PASS")


# --------------------------------------------------
# Existing range functions regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=AVERAGE(Sheet2!A1:B2)"
    )
) == 42.5

print("AVERAGE regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=MAX(Sheet2!A1:B2)"
    )
) == 50

print("MIN regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=MAX(Sheet2!A1:B2)"
    )
) == 50

print("MAX regression: PASS")


# --------------------------------------------------
# Phase result
# --------------------------------------------------

print("PHASE 14 INTEGRATION: PASS")