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


def check_cell(reference, expected, label):
    result = evaluator.evaluate_cell(reference)
    assert result == expected, (
        f"{label}: expected {expected!r}, got {result!r}"
    )
    print(f"{label}: PASS")


# --------------------------------------------------
# Basic error -> valid recovery
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")
sheet.set_cell("A2", "=A1+10")

check_cell(
    "A1",
    "#DIV/0!",
    "Initial source error"
)

check_cell(
    "A2",
    "#DIV/0!",
    "Initial dependent error"
)

sheet.set_cell("A1", 20)

check_cell(
    "A1",
    20,
    "Source recovered"
)

check_cell(
    "A2",
    30,
    "Dependent recovered"
)


# --------------------------------------------------
# Valid -> error again
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")

check_cell(
    "A1",
    "#DIV/0!",
    "Source error restored"
)

check_cell(
    "A2",
    "#DIV/0!",
    "Dependent error restored"
)


# --------------------------------------------------
# Multi-level dependency recovery
# --------------------------------------------------

sheet.set_cell("B1", "=A1")
sheet.set_cell("B2", "=B1+10")
sheet.set_cell("B3", "=B2*2")

check_cell(
    "B3",
    "#DIV/0!",
    "Deep dependency error"
)

sheet.set_cell("A1", 5)

check_cell(
    "B1",
    5,
    "Level 1 recovery"
)

check_cell(
    "B2",
    15,
    "Level 2 recovery"
)

check_cell(
    "B3",
    30,
    "Level 3 recovery"
)


# --------------------------------------------------
# Error type changes
# --------------------------------------------------

sheet.set_cell("A1", '=ABS("abc")')

check_cell(
    "A1",
    "#VALUE!",
    "Changed to VALUE error"
)

check_cell(
    "B3",
    "#VALUE!",
    "Dependent VALUE propagation"
)

sheet.set_cell("A1", "=UNKNOWN(10)")

check_cell(
    "A1",
    "#NAME?",
    "Changed to NAME error"
)

check_cell(
    "B3",
    "#NAME?",
    "Dependent NAME propagation"
)

sheet.set_cell("A1", "=10/0")

check_cell(
    "A1",
    "#DIV/0!",
    "Changed back to DIV/0"
)

check_cell(
    "B3",
    "#DIV/0!",
    "Dependent DIV/0 propagation"
)


# --------------------------------------------------
# Recovery from each error type
# --------------------------------------------------

sheet.set_cell("A1", '=ABS("abc")')

check_cell(
    "B3",
    "#VALUE!",
    "VALUE error before recovery"
)

sheet.set_cell("A1", 7)

check_cell(
    "B3",
    34,
    "VALUE error recovery"
)


sheet.set_cell("A1", "=UNKNOWN(10)")

check_cell(
    "B3",
    "#NAME?",
    "NAME error before recovery"
)

sheet.set_cell("A1", 8)

check_cell(
    "B3",
    36,
    "NAME error recovery"
)


sheet.set_cell("A1", "=10/0")

check_cell(
    "B3",
    "#DIV/0!",
    "DIV/0 before recovery"
)

sheet.set_cell("A1", 9)

check_cell(
    "B3",
    38,
    "DIV/0 recovery"
)


# --------------------------------------------------
# Function dependent recovery
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")
sheet.set_cell("C1", "=SUM(A1,10)")
sheet.set_cell("C2", "=AVERAGE(A1,10)")
sheet.set_cell("C3", "=ABS(A1)")

check_cell(
    "C1",
    "#DIV/0!",
    "SUM source error"
)

check_cell(
    "C2",
    "#DIV/0!",
    "AVERAGE source error"
)

check_cell(
    "C3",
    "#DIV/0!",
    "ABS source error"
)

sheet.set_cell("A1", 20)

check_cell(
    "C1",
    30,
    "SUM recovery"
)

check_cell(
    "C2",
    15,
    "AVERAGE recovery"
)

check_cell(
    "C3",
    20,
    "ABS recovery"
)


# --------------------------------------------------
# Logical dependent recovery
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")
sheet.set_cell("D1", "=IF(A1>5,100,200)")
sheet.set_cell("D2", "=AND(A1,TRUE())")
sheet.set_cell("D3", "=OR(A1,FALSE())")

check_cell(
    "D1",
    "#DIV/0!",
    "IF error before recovery"
)

check_cell(
    "D2",
    "#DIV/0!",
    "AND error before recovery"
)

check_cell(
    "D3",
    "#DIV/0!",
    "OR error before recovery"
)

sheet.set_cell("A1", 10)

check_cell(
    "D1",
    100,
    "IF recovery"
)

check_cell(
    "D2",
    True,
    "AND recovery"
)

check_cell(
    "D3",
    True,
    "OR recovery"
)


# --------------------------------------------------
# Text dependent recovery
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")
sheet.set_cell("E1", "=CONCAT(\"Value: \",A1)")
sheet.set_cell("E2", "=LEN(A1)")
sheet.set_cell("E3", "=UPPER(A1)")

check_cell(
    "E1",
    "#DIV/0!",
    "CONCAT error before recovery"
)

check_cell(
    "E2",
    "#DIV/0!",
    "LEN error before recovery"
)

check_cell(
    "E3",
    "#DIV/0!",
    "UPPER error before recovery"
)

sheet.set_cell("A1", 25)

check_cell(
    "E1",
    "Value: 25",
    "CONCAT recovery"
)

check_cell(
    "E2",
    2,
    "LEN recovery"
)

check_cell(
    "E3",
    "25",
    "UPPER recovery"
)


# --------------------------------------------------
# Cross-sheet recovery
# --------------------------------------------------

other.set_cell("A1", "=10/0")
sheet.set_cell("F1", "=Other!A1+10")
sheet.set_cell("F2", "=SUM(Other!A1,20)")

check_cell(
    "F1",
    "#DIV/0!",
    "Cross-sheet error before recovery"
)

check_cell(
    "F2",
    "#DIV/0!",
    "Cross-sheet function error"
)

other.set_cell("A1", 50)

check_cell(
    "F1",
    60,
    "Cross-sheet arithmetic recovery"
)

check_cell(
    "F2",
    70,
    "Cross-sheet function recovery"
)


# --------------------------------------------------
# Cross-sheet error type changes
# --------------------------------------------------

other.set_cell("A1", '=ABS("abc")')

check_cell(
    "F1",
    "#VALUE!",
    "Cross-sheet VALUE error"
)

other.set_cell("A1", "=UNKNOWN(10)")

check_cell(
    "F1",
    "#NAME?",
    "Cross-sheet NAME error"
)

other.set_cell("A1", 100)

check_cell(
    "F1",
    110,
    "Cross-sheet final recovery"
)


# --------------------------------------------------
# Circular reference recovery
# --------------------------------------------------

sheet.set_cell("G1", "=G2")
sheet.set_cell("G2", "=G1")

check_cell(
    "G1",
    "#CIRC!",
    "Circular error"
)

check_cell(
    "G2",
    "#CIRC!",
    "Circular reverse error"
)

sheet.set_cell("G2", 50)

check_cell(
    "G1",
    50,
    "Circular recovery G1"
)

check_cell(
    "G2",
    50,
    "Circular recovery G2"
)


# --------------------------------------------------
# Recovery after repeated evaluations
# --------------------------------------------------

sheet.set_cell("A1", "=10/0")
sheet.set_cell("A2", "=A1+1")

for _ in range(5):
    assert evaluator.evaluate_cell("A2") == "#DIV/0!"

sheet.set_cell("A1", 99)

for _ in range(5):
    assert evaluator.evaluate_cell("A2") == 100

print("Repeated error/recovery evaluation: PASS")


# --------------------------------------------------
# Final
# --------------------------------------------------

print("========================================")
print("PHASE 17 PART 5: PASS")
print("========================================")