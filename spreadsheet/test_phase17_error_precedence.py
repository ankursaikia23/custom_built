from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet = workbook.add_sheet("Sheet1")
other = workbook.add_sheet("Other")

parser = Parser()
evaluator = Evaluator(sheet, workbook)


def check(formula, expected, label):
    result = evaluator.evaluate(
        parser.parse(formula)
    )
    assert result == expected, (
        f"{label}: expected {expected!r}, got {result!r}"
    )
    print(f"{label}: PASS")


# --------------------------------------------------
# Create all major error types
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")          # #DIV/0!
sheet.set_cell("A2", '=ABS("abc")')    # #VALUE!
sheet.set_cell("A3", "=UNKNOWN(10)")   # #NAME?


# --------------------------------------------------
# Single-error precedence
# --------------------------------------------------

check(
    "=A1+10",
    "#DIV/0!",
    "Single DIV/0"
)

check(
    "=A2+10",
    "#VALUE!",
    "Single VALUE"
)

check(
    "=A3+10",
    "#NAME?",
    "Single NAME"
)


# --------------------------------------------------
# Two different errors in arithmetic
# --------------------------------------------------

check(
    "=A1+A2",
    "#DIV/0!",
    "DIV/0 left precedence"
)

check(
    "=A2+A1",
    "#VALUE!",
    "VALUE left precedence"
)

check(
    "=A1*A3",
    "#DIV/0!",
    "DIV/0 multiplication precedence"
)

check(
    "=A3*A1",
    "#NAME?",
    "NAME multiplication precedence"
)


# --------------------------------------------------
# Error + ordinary value
# --------------------------------------------------

check(
    "=10+A1",
    "#DIV/0!",
    "Value + DIV/0"
)

check(
    "=10+A2",
    "#VALUE!",
    "Value + VALUE"
)

check(
    "=10+A3",
    "#NAME?",
    "Value + NAME"
)


# --------------------------------------------------
# Errors nested inside functions
# --------------------------------------------------

check(
    "=SUM(A1,A2)",
    "#DIV/0!",
    "SUM DIV/0 then VALUE"
)

check(
    "=SUM(A2,A1)",
    "#VALUE!",
    "SUM VALUE then DIV/0"
)

check(
    "=SUM(A3,A2)",
    "#NAME?",
    "SUM NAME then VALUE"
)

check(
    "=SUM(A2,A3)",
    "#VALUE!",
    "SUM VALUE then NAME"
)


# --------------------------------------------------
# Three errors
# --------------------------------------------------

check(
    "=SUM(A1,A2,A3)",
    "#DIV/0!",
    "Three errors DIV first"
)

check(
    "=SUM(A2,A3,A1)",
    "#VALUE!",
    "Three errors VALUE first"
)

check(
    "=SUM(A3,A1,A2)",
    "#NAME?",
    "Three errors NAME first"
)


# --------------------------------------------------
# Nested functions
# --------------------------------------------------

check(
    "=ABS(A1+A2)",
    "#DIV/0!",
    "Nested DIV/0 first"
)

check(
    "=ABS(A2+A1)",
    "#VALUE!",
    "Nested VALUE first"
)

check(
    "=ABS(A3+A2)",
    "#NAME?",
    "Nested NAME first"
)


# --------------------------------------------------
# Logical functions
# --------------------------------------------------

check(
    "=AND(A1,TRUE())",
    "#DIV/0!",
    "AND DIV/0"
)

check(
    "=AND(A2,TRUE())",
    "#VALUE!",
    "AND VALUE"
)

check(
    "=AND(A3,TRUE())",
    "#NAME?",
    "AND NAME"
)


check(
    "=OR(A1,FALSE())",
    "#DIV/0!",
    "OR DIV/0"
)

check(
    "=OR(A2,FALSE())",
    "#VALUE!",
    "OR VALUE"
)

check(
    "=OR(A3,FALSE())",
    "#NAME?",
    "OR NAME"
)


# --------------------------------------------------
# NOT
# --------------------------------------------------

check(
    "=NOT(A1)",
    "#DIV/0!",
    "NOT DIV/0"
)

check(
    "=NOT(A2)",
    "#VALUE!",
    "NOT VALUE"
)

check(
    "=NOT(A3)",
    "#NAME?",
    "NOT NAME"
)


# --------------------------------------------------
# Text functions
# --------------------------------------------------

check(
    '=CONCAT("x",A1)',
    "#DIV/0!",
    "CONCAT DIV/0"
)

check(
    '=CONCAT("x",A2)',
    "#VALUE!",
    "CONCAT VALUE"
)

check(
    '=CONCAT("x",A3)',
    "#NAME?",
    "CONCAT NAME"
)


# --------------------------------------------------
# Comparisons
# --------------------------------------------------

check(
    "=A1=A2",
    "#DIV/0!",
    "Comparison DIV/0 first"
)

check(
    "=A2=A1",
    "#VALUE!",
    "Comparison VALUE first"
)

check(
    "=A3=A1",
    "#NAME?",
    "Comparison NAME first"
)


# --------------------------------------------------
# IF error precedence
# --------------------------------------------------

check(
    '=IF(A1,"YES","NO")',
    "#DIV/0!",
    "IF DIV/0 condition"
)

check(
    '=IF(A2,"YES","NO")',
    "#VALUE!",
    "IF VALUE condition"
)

check(
    '=IF(A3,"YES","NO")',
    "#NAME?",
    "IF NAME condition"
)


# --------------------------------------------------
# IF branch selection
# --------------------------------------------------

check(
    '=IF(TRUE(),A1,A2)',
    "#DIV/0!",
    "IF selects DIV/0"
)

check(
    '=IF(TRUE(),A2,A1)',
    "#VALUE!",
    "IF selects VALUE"
)

check(
    '=IF(TRUE(),A3,A1)',
    "#NAME?",
    "IF selects NAME"
)


# --------------------------------------------------
# Unselected errors remain isolated
# --------------------------------------------------

check(
    '=IF(TRUE(),10,A1)',
    10,
    "IF ignores unselected DIV/0"
)

check(
    '=IF(TRUE(),10,A2)',
    10,
    "IF ignores unselected VALUE"
)

check(
    '=IF(TRUE(),10,A3)',
    10,
    "IF ignores unselected NAME"
)


# --------------------------------------------------
# IFS error isolation
# --------------------------------------------------

check(
    '=IFS(TRUE(),10,A1,A2)',
    10,
    "IFS ignores later errors"
)

check(
    '=IFS(A1,10,TRUE(),20)',
    "#DIV/0!",
    "IFS DIV/0 condition"
)

check(
    '=IFS(A2,10,TRUE(),20)',
    "#VALUE!",
    "IFS VALUE condition"
)

check(
    '=IFS(A3,10,TRUE(),20)',
    "#NAME?",
    "IFS NAME condition"
)


# --------------------------------------------------
# Error in formula chain
# --------------------------------------------------

sheet.set_cell("B1", "=A1")
sheet.set_cell("B2", "=B1")
sheet.set_cell("B3", "=B2+100")

check(
    "=B1",
    "#DIV/0!",
    "Chain level 1"
)

check(
    "=B2",
    "#DIV/0!",
    "Chain level 2"
)

check(
    "=B3",
    "#DIV/0!",
    "Chain level 3"
)


# --------------------------------------------------
# Different error chain
# --------------------------------------------------

sheet.set_cell("C1", "=A2")
sheet.set_cell("C2", "=C1")
sheet.set_cell("C3", "=C2*10")

check(
    "=C1",
    "#VALUE!",
    "VALUE chain level 1"
)

check(
    "=C2",
    "#VALUE!",
    "VALUE chain level 2"
)

check(
    "=C3",
    "#VALUE!",
    "VALUE chain level 3"
)


# --------------------------------------------------
# Cross-sheet mixed errors
# --------------------------------------------------

other.set_cell("A1", "=10/0")
other.set_cell("A2", '=ABS("abc")')

check(
    "=Other!A1+10",
    "#DIV/0!",
    "Cross-sheet DIV/0 arithmetic"
)

check(
    "=Other!A2+10",
    "#VALUE!",
    "Cross-sheet VALUE arithmetic"
)

check(
    "=SUM(Other!A1,Other!A2)",
    "#DIV/0!",
    "Cross-sheet mixed errors"
)


# --------------------------------------------------
# Error through nested IF
# --------------------------------------------------

check(
    '=IF(TRUE(),IF(TRUE(),A1,10),20)',
    "#DIV/0!",
    "Nested IF DIV/0"
)

check(
    '=IF(TRUE(),IF(TRUE(),A2,10),20)',
    "#VALUE!",
    "Nested IF VALUE"
)

check(
    '=IF(TRUE(),IF(TRUE(),A3,10),20)',
    "#NAME?",
    "Nested IF NAME"
)


# --------------------------------------------------
# Final
# --------------------------------------------------

print("========================================")
print("PHASE 17 PART 4: PASS")
print("========================================")