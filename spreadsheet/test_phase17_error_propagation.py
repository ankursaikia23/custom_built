from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet = workbook.add_sheet("Sheet1")
other = workbook.add_sheet("Other")

parser = Parser()
evaluator = Evaluator(sheet, workbook)


# --------------------------------------------------
# Direct errors
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=10/0")
) == "#DIV/0!"

print("Direct division error: PASS")


assert evaluator.evaluate(
    parser.parse("=UNKNOWN(10)")
) == "#NAME?"

print("Direct unknown-function error: PASS")


# --------------------------------------------------
# Error in formula cell
# --------------------------------------------------

sheet.set_cell(
    "A1",
    "=10/0"
)

assert evaluator.evaluate_cell("A1") == "#DIV/0!"

print("Formula cell error: PASS")


# --------------------------------------------------
# Error propagation through arithmetic
# --------------------------------------------------

sheet.set_cell(
    "A2",
    "=A1+10"
)

assert evaluator.evaluate_cell("A2") == "#DIV/0!"

print("Arithmetic error propagation: PASS")


# --------------------------------------------------
# Error propagation through multiplication
# --------------------------------------------------

sheet.set_cell(
    "A3",
    "=A1*5"
)

assert evaluator.evaluate_cell("A3") == "#DIV/0!"

print("Multiplication error propagation: PASS")


# --------------------------------------------------
# Error propagation through functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=SUM(A1,10)")
) == "#DIV/0!"

print("SUM error propagation: PASS")


assert evaluator.evaluate(
    parser.parse("=AVERAGE(A1,10)")
) == "#DIV/0!"

print("AVERAGE error propagation: PASS")


# --------------------------------------------------
# Error in logical expression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=AND(A1,TRUE())")
) == "#DIV/0!"

print("AND error propagation: PASS")


# --------------------------------------------------
# Error in comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1=10")
) == "#DIV/0!"

print("Comparison error propagation: PASS")


# --------------------------------------------------
# IF condition error
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(A1=10,"YES","NO")'
    )
) == "#DIV/0!"

print("IF condition error propagation: PASS")


# --------------------------------------------------
# IF branch error — selected branch
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(TRUE(),10/0,"SAFE")'
    )
) == "#DIV/0!"

print("IF selected-branch error: PASS")


# --------------------------------------------------
# IF branch error — unselected branch
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(TRUE(),"SAFE",10/0)'
    )
) == "SAFE"

print("IF unselected-branch isolation: PASS")


# --------------------------------------------------
# Nested error propagation
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=SUM(10,ABS(10/0))'
    )
) == "#DIV/0!"

print("Nested error propagation: PASS")


# --------------------------------------------------
# Cross-sheet error
# --------------------------------------------------

other.set_cell(
    "A1",
    "=10/0"
)

assert evaluator.evaluate(
    parser.parse(
        "=Other!A1"
    )
) == "#DIV/0!"

print("Cross-sheet error propagation: PASS")


# --------------------------------------------------
# Cross-sheet dependent error
# --------------------------------------------------

sheet.set_cell(
    "B1",
    "=Other!A1+10"
)

assert evaluator.evaluate_cell(
    "B1"
) == "#DIV/0!"

print("Cross-sheet dependent error: PASS")


# --------------------------------------------------
# Error through text function
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=UPPER(A1)"
    )
) == "#DIV/0!"

print("Text-function error propagation: PASS")


# --------------------------------------------------
# Error through CONCAT
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=CONCAT("Value: ",A1)'
    )
) == "#DIV/0!"

print("CONCAT error propagation: PASS")


# --------------------------------------------------
# Final
# --------------------------------------------------

print("========================================")
print("PHASE 17 PART 1: PASS")
print("========================================")