from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet = workbook.add_sheet("Sheet1")
other = workbook.add_sheet("Other")

parser = Parser()
evaluator = Evaluator(sheet, workbook)


# --------------------------------------------------
# Helper
# --------------------------------------------------

def check(formula, expected, label):
    result = evaluator.evaluate(
        parser.parse(formula)
    )
    assert result == expected, (
        f"{label}: expected {expected!r}, "
        f"got {result!r}"
    )
    print(f"{label}: PASS")


# --------------------------------------------------
# Direct error values
# --------------------------------------------------

check(
    "=10/0",
    "#DIV/0!",
    "DIV/0"
)

check(
    '=ABS("abc")',
    "#VALUE!",
    "VALUE"
)

check(
    "=UNKNOWN(10)",
    "#NAME?",
    "NAME"
)


# --------------------------------------------------
# Stored error cells
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")
sheet.set_cell("A2", '=ABS("abc")')
sheet.set_cell("A3", "=UNKNOWN(10)")

assert evaluator.evaluate_cell("A1") == "#DIV/0!"
print("Stored DIV/0: PASS")

assert evaluator.evaluate_cell("A2") == "#VALUE!"
print("Stored VALUE: PASS")

assert evaluator.evaluate_cell("A3") == "#NAME?"
print("Stored NAME: PASS")


# --------------------------------------------------
# Arithmetic propagation
# --------------------------------------------------

check(
    "=A1+10",
    "#DIV/0!",
    "DIV/0 arithmetic propagation"
)

check(
    "=A2+10",
    "#VALUE!",
    "VALUE arithmetic propagation"
)

check(
    "=A3+10",
    "#NAME?",
    "NAME arithmetic propagation"
)


# --------------------------------------------------
# Multiplication / division / power
# --------------------------------------------------

check(
    "=A1*2",
    "#DIV/0!",
    "DIV/0 multiplication propagation"
)

check(
    "=A2/2",
    "#VALUE!",
    "VALUE division propagation"
)

check(
    "=A3^2",
    "#NAME?",
    "NAME power propagation"
)


# --------------------------------------------------
# Math functions
# --------------------------------------------------

check(
    "=SUM(A1,10)",
    "#DIV/0!",
    "DIV/0 SUM propagation"
)

check(
    "=AVERAGE(A2,10)",
    "#VALUE!",
    "VALUE AVERAGE propagation"
)

check(
    "=MIN(A3,10)",
    "#NAME?",
    "NAME MIN propagation"
)

check(
    "=MAX(A1,10)",
    "#DIV/0!",
    "DIV/0 MAX propagation"
)

check(
    "=ABS(A2)",
    "#VALUE!",
    "VALUE ABS propagation"
)

check(
    "=ROUND(A3,2)",
    "#NAME?",
    "NAME ROUND propagation"
)

check(
    "=INT(A1)",
    "#DIV/0!",
    "DIV/0 INT propagation"
)

check(
    "=MOD(A2,2)",
    "#VALUE!",
    "VALUE MOD propagation"
)


# --------------------------------------------------
# Logical functions
# --------------------------------------------------

check(
    "=AND(A1,TRUE())",
    "#DIV/0!",
    "DIV/0 AND propagation"
)

check(
    "=OR(A2,TRUE())",
    "#VALUE!",
    "VALUE OR propagation"
)

check(
    "=NOT(A3)",
    "#NAME?",
    "NAME NOT propagation"
)

check(
    "=XOR(A1,FALSE())",
    "#DIV/0!",
    "DIV/0 XOR propagation"
)


# --------------------------------------------------
# Text functions
# --------------------------------------------------

check(
    "=CONCAT(A1,\"x\")",
    "#DIV/0!",
    "DIV/0 CONCAT propagation"
)

check(
    "=CONCATENATE(A2,\"x\")",
    "#VALUE!",
    "VALUE CONCATENATE propagation"
)

check(
    "=LEFT(A3,2)",
    "#NAME?",
    "NAME LEFT propagation"
)

check(
    "=RIGHT(A1,2)",
    "#DIV/0!",
    "DIV/0 RIGHT propagation"
)

check(
    "=LEN(A2)",
    "#VALUE!",
    "VALUE LEN propagation"
)

check(
    "=UPPER(A3)",
    "#NAME?",
    "NAME UPPER propagation"
)

check(
    "=LOWER(A1)",
    "#DIV/0!",
    "DIV/0 LOWER propagation"
)

check(
    "=TRIM(A2)",
    "#VALUE!",
    "VALUE TRIM propagation"
)


# --------------------------------------------------
# Comparisons
# --------------------------------------------------

check(
    "=A1=10",
    "#DIV/0!",
    "DIV/0 equality propagation"
)

check(
    "=A2<>10",
    "#VALUE!",
    "VALUE inequality propagation"
)

check(
    "=A3>10",
    "#NAME?",
    "NAME greater-than propagation"
)

check(
    "=A1<=10",
    "#DIV/0!",
    "DIV/0 less/equal propagation"
)


# --------------------------------------------------
# IF condition errors
# --------------------------------------------------

check(
    '=IF(A1>10,"YES","NO")',
    "#DIV/0!",
    "DIV/0 IF condition"
)

check(
    '=IF(A2>10,"YES","NO")',
    "#VALUE!",
    "VALUE IF condition"
)

check(
    '=IF(A3>10,"YES","NO")',
    "#NAME?",
    "NAME IF condition"
)


# --------------------------------------------------
# IF branch errors
# --------------------------------------------------

check(
    '=IF(TRUE(),A1,"SAFE")',
    "#DIV/0!",
    "DIV/0 IF selected branch"
)

check(
    '=IF(TRUE(),A2,"SAFE")',
    "#VALUE!",
    "VALUE IF selected branch"
)

check(
    '=IF(TRUE(),A3,"SAFE")',
    "#NAME?",
    "NAME IF selected branch"
)


# --------------------------------------------------
# Lazy IF isolation
# --------------------------------------------------

check(
    '=IF(TRUE(),"SAFE",A1)',
    "SAFE",
    "DIV/0 IF unselected branch"
)

check(
    '=IF(TRUE(),"SAFE",A2)',
    "SAFE",
    "VALUE IF unselected branch"
)

check(
    '=IF(TRUE(),"SAFE",A3)',
    "SAFE",
    "NAME IF unselected branch"
)


# --------------------------------------------------
# IFS
# --------------------------------------------------

check(
    '=IFS(TRUE(),"SAFE",A1,"BAD")',
    "SAFE",
    "IFS lazy error isolation"
)

check(
    '=IFS(A1,"YES",TRUE(),"SAFE")',
    "#DIV/0!",
    "IFS condition error"
)


# --------------------------------------------------
# Nested formulas
# --------------------------------------------------

check(
    "=SUM(ABS(A1),10)",
    "#DIV/0!",
    "Nested DIV/0 propagation"
)

check(
    '=IF(TRUE(),SUM(A2,10),"SAFE")',
    "#VALUE!",
    "Nested VALUE propagation"
)

check(
    '=IF(TRUE(),UPPER(A3),"SAFE")',
    "#NAME?",
    "Nested NAME propagation"
)


# --------------------------------------------------
# Cross-sheet errors
# --------------------------------------------------

other.set_cell("A1", "=10/0")
other.set_cell("A2", '=ABS("abc")')
other.set_cell("A3", "=UNKNOWN(10)")

check(
    "=Other!A1",
    "#DIV/0!",
    "Cross-sheet DIV/0"
)

check(
    "=Other!A2",
    "#VALUE!",
    "Cross-sheet VALUE"
)

check(
    "=Other!A3",
    "#NAME?",
    "Cross-sheet NAME"
)


# --------------------------------------------------
# Cross-sheet function propagation
# --------------------------------------------------

check(
    "=SUM(Other!A1,10)",
    "#DIV/0!",
    "Cross-sheet DIV/0 SUM"
)

check(
    "=ABS(Other!A2)",
    "#VALUE!",
    "Cross-sheet VALUE ABS"
)

check(
    '=IF(Other!A3="x","YES","NO")',
    "#NAME?",
    "Cross-sheet NAME IF"
)


# --------------------------------------------------
# Circular reference
# --------------------------------------------------

sheet.set_cell("B1", "=B2")
sheet.set_cell("B2", "=B1")

assert evaluator.evaluate_cell("B1") == "#CIRC!"
print("Circular reference: PASS")

assert evaluator.evaluate_cell("B2") == "#CIRC!"
print("Circular reference reverse: PASS")


# --------------------------------------------------
# Final
# --------------------------------------------------

print("========================================")
print("PHASE 17 PART 2: PASS")
print("========================================")