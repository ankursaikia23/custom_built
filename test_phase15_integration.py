from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet1 = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Sheet2")

parser = Parser()
evaluator = Evaluator(
    sheet1,
    workbook
)


# --------------------------------------------------
# Normal arithmetic
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=10+5")
) == 15

print("Arithmetic: PASS")


# --------------------------------------------------
# Division error
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=10/0")
) == "#DIV/0!"

print("Division error: PASS")


# --------------------------------------------------
# Function error
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=ABS(1,2)")
) == "#VALUE!"

print("Function argument error: PASS")


# --------------------------------------------------
# Unknown function
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=UNKNOWN(10)")
) == "#NAME?"

print("Unknown function error: PASS")


# --------------------------------------------------
# Missing sheet
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=Missing!A1")
) == "#REF!"

print("Reference error: PASS")


# --------------------------------------------------
# Cross-sheet range error
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=SUM(Missing!A1:B2)"
    )
) == "#REF!"

print("Range reference error: PASS")


# --------------------------------------------------
# Valid cross-sheet reference
# --------------------------------------------------

sheet2.set_cell("A1", 20)
sheet2.set_cell("B1", 30)

assert evaluator.evaluate(
    parser.parse(
        "=Sheet2!A1+Sheet2!B1"
    )
) == 50

print("Cross-sheet reference: PASS")


# --------------------------------------------------
# Valid cross-sheet range
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=SUM(Sheet2!A1:B1)"
    )
) == 50

print("Cross-sheet range: PASS")


# --------------------------------------------------
# Formula dependency
# --------------------------------------------------

sheet1.set_cell("A1", 10)
sheet1.set_cell("B1", "=A1+5")
sheet1.set_cell("C1", "=B1*2")

assert evaluator.evaluate_cell(
    "C1"
) == 30

print("Formula dependency: PASS")


# --------------------------------------------------
# Dependency recalculation
# --------------------------------------------------

sheet1.set_cell("A1", 20)

assert evaluator.evaluate_cell(
    "C1"
) == 50

print("Dependency recalculation: PASS")


# --------------------------------------------------
# Error propagation through dependency
# --------------------------------------------------

sheet1.set_cell(
    "A1",
    "=10/0"
)

assert evaluator.evaluate_cell(
    "B1"
) == "#DIV/0!"

print("Error propagation: PASS")


# --------------------------------------------------
# Circular reference
# --------------------------------------------------

sheet1.set_cell(
    "A1",
    "=B1+1"
)

sheet1.set_cell(
    "B1",
    "=A1+1"
)

assert evaluator.evaluate_cell(
    "A1"
) == "#CIRC!"

print("Circular reference: PASS")


# --------------------------------------------------
# Recovery after circular reference
# --------------------------------------------------

sheet1.set_cell(
    "A1",
    100
)

sheet1.set_cell(
    "B1",
    "=A1+1"
)

assert evaluator.evaluate_cell(
    "B1"
) == 101

print("Circular recovery: PASS")


# --------------------------------------------------
# Quoted sheet name
# --------------------------------------------------

sales = workbook.add_sheet(
    "Sales Data"
)

sales.set_cell("A1", 100)
sales.set_cell("B1", 200)

assert evaluator.evaluate(
    parser.parse(
        "=SUM('Sales Data'!A1:B1)"
    )
) == 300

print("Quoted sheet reference: PASS")


# --------------------------------------------------
# Existing functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=AVERAGE(10,20)")
) == 15

print("AVERAGE: PASS")


assert evaluator.evaluate(
    parser.parse("=MIN(10,20)")
) == 10

print("MIN: PASS")


assert evaluator.evaluate(
    parser.parse("=MAX(10,20)")
) == 20

print("MAX: PASS")


assert evaluator.evaluate(
    parser.parse("=ABS(-10)")
) == 10

print("ABS: PASS")


assert evaluator.evaluate(
    parser.parse("=ROUND(10.55,1)")
) == 10.6

print("ROUND: PASS")


assert evaluator.evaluate(
    parser.parse("=INT(10.9)")
) == 10

print("INT: PASS")


assert evaluator.evaluate(
    parser.parse("=MOD(10,3)")
) == 1

print("MOD: PASS")


# --------------------------------------------------
# Final
# --------------------------------------------------

print("PHASE 15 INTEGRATION: PASS")