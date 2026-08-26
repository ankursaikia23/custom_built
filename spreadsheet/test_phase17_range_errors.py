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
# Numeric range baseline
# --------------------------------------------------

sheet.set_cell("A1", 10)
sheet.set_cell("A2", 20)
sheet.set_cell("A3", 30)

check(
    "=SUM(A1:A3)",
    60,
    "Clean SUM range"
)

check(
    "=AVERAGE(A1:A3)",
    20,
    "Clean AVERAGE range"
)

check(
    "=MIN(A1:A3)",
    10,
    "Clean MIN range"
)

check(
    "=MAX(A1:A3)",
    30,
    "Clean MAX range"
)

check(
    "=COUNT(A1:A3)",
    3,
    "Clean COUNT range"
)


# --------------------------------------------------
# Error inside range
# --------------------------------------------------

sheet.set_cell("A2", "=10/0")

check(
    "=SUM(A1:A3)",
    "#DIV/0!",
    "SUM range DIV/0"
)

check(
    "=AVERAGE(A1:A3)",
    "#DIV/0!",
    "AVERAGE range DIV/0"
)

check(
    "=MIN(A1:A3)",
    "#DIV/0!",
    "MIN range DIV/0"
)

check(
    "=MAX(A1:A3)",
    "#DIV/0!",
    "MAX range DIV/0"
)

check(
    "=COUNT(A1:A3)",
    "#DIV/0!",
    "COUNT range DIV/0"
)


# --------------------------------------------------
# VALUE error inside range
# --------------------------------------------------

sheet.set_cell("A2", '=ABS("abc")')

check(
    "=SUM(A1:A3)",
    "#VALUE!",
    "SUM range VALUE"
)

check(
    "=AVERAGE(A1:A3)",
    "#VALUE!",
    "AVERAGE range VALUE"
)

check(
    "=MIN(A1:A3)",
    "#VALUE!",
    "MIN range VALUE"
)

check(
    "=MAX(A1:A3)",
    "#VALUE!",
    "MAX range VALUE"
)

check(
    "=COUNT(A1:A3)",
    "#VALUE!",
    "COUNT range VALUE"
)


# --------------------------------------------------
# NAME error inside range
# --------------------------------------------------

sheet.set_cell("A2", "=UNKNOWN(10)")

check(
    "=SUM(A1:A3)",
    "#NAME?",
    "SUM range NAME"
)

check(
    "=AVERAGE(A1:A3)",
    "#NAME?",
    "AVERAGE range NAME"
)

check(
    "=MIN(A1:A3)",
    "#NAME?",
    "MIN range NAME"
)

check(
    "=MAX(A1:A3)",
    "#NAME?",
    "MAX range NAME"
)

check(
    "=COUNT(A1:A3)",
    "#NAME?",
    "COUNT range NAME"
)


# --------------------------------------------------
# Error at beginning of range
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")
sheet.set_cell("A2", 20)
sheet.set_cell("A3", 30)

check(
    "=SUM(A1:A3)",
    "#DIV/0!",
    "Beginning error SUM"
)


# --------------------------------------------------
# Error at end of range
# --------------------------------------------------

sheet.set_cell("A1", 10)
sheet.set_cell("A2", 20)
sheet.set_cell("A3", "=10/0")

check(
    "=SUM(A1:A3)",
    "#DIV/0!",
    "Ending error SUM"
)


# --------------------------------------------------
# Multiple errors
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")
sheet.set_cell("A2", '=ABS("abc")')
sheet.set_cell("A3", "=UNKNOWN(10)")

check(
    "=SUM(A1:A3)",
    "#DIV/0!",
    "Multiple errors SUM"
)

check(
    "=AVERAGE(A1:A3)",
    "#DIV/0!",
    "Multiple errors AVERAGE"
)

check(
    "=MIN(A1:A3)",
    "#DIV/0!",
    "Multiple errors MIN"
)

check(
    "=MAX(A1:A3)",
    "#DIV/0!",
    "Multiple errors MAX"
)

check(
    "=COUNT(A1:A3)",
    "#DIV/0!",
    "Multiple errors COUNT"
)


# --------------------------------------------------
# Error mixed with empty cells
# --------------------------------------------------

sheet.set_cell("A1", None)
sheet.set_cell("A2", "=10/0")
sheet.set_cell("A3", None)

check(
    "=SUM(A1:A3)",
    "#DIV/0!",
    "Error with empty SUM"
)

check(
    "=AVERAGE(A1:A3)",
    "#DIV/0!",
    "Error with empty AVERAGE"
)


# --------------------------------------------------
# Error mixed with text
# --------------------------------------------------

sheet.set_cell("A1", "hello")
sheet.set_cell("A2", "=10/0")
sheet.set_cell("A3", 10)

check(
    "=SUM(A1:A3)",
    "#DIV/0!",
    "Error with text SUM"
)


# --------------------------------------------------
# Cross-sheet ranges
# --------------------------------------------------

other.set_cell("A1", 100)
other.set_cell("A2", "=10/0")
other.set_cell("A3", 300)

check(
    "=SUM(Other!A1:A3)",
    "#DIV/0!",
    "Cross-sheet range error"
)

check(
    "=AVERAGE(Other!A1:A3)",
    "#DIV/0!",
    "Cross-sheet AVERAGE error"
)


# --------------------------------------------------
# Nested range errors
# --------------------------------------------------

check(
    "=ABS(SUM(A1:A3))",
    "#DIV/0!",
    "Nested range error"
)

check(
    '=IF(SUM(A1:A3)=60,"YES","NO")',
    "#DIV/0!",
    "Range error in IF condition"
)

check(
    '=IF(TRUE(),"SAFE",SUM(A1:A3))',
    "SAFE",
    "Range error in unselected IF branch"
)


# --------------------------------------------------
# Final
# --------------------------------------------------

print("========================================")
print("PHASE 17 PART 3: PASS")
print("========================================")