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


# ==================================================
# 1. Basic arithmetic regression
# ==================================================

check("=10+20", 30, "Arithmetic addition")
check("=20-5", 15, "Arithmetic subtraction")
check("=6*7", 42, "Arithmetic multiplication")
check("=20/4", 5, "Arithmetic division")
check("=2^5", 32, "Arithmetic power")


# ==================================================
# 2. Error values
# ==================================================

check("=10/0", "#DIV/0!", "Direct DIV/0")
check('=ABS("abc")', "#VALUE!", "Direct VALUE")
check("=UNKNOWN(10)", "#NAME?", "Direct NAME")


# ==================================================
# 3. Error propagation
# ==================================================

check("=10+(10/0)", "#DIV/0!", "Nested DIV/0")
check('=10+ABS("abc")', "#VALUE!", "Nested VALUE")
check("=10+UNKNOWN(10)", "#NAME?", "Nested NAME")


# ==================================================
# 4. Cell errors
# ==================================================

sheet.set_cell("A1", "=10/0")
sheet.set_cell("A2", '=ABS("abc")')
sheet.set_cell("A3", "=UNKNOWN(10)")

check_cell("A1", "#DIV/0!", "Cell DIV/0")
check_cell("A2", "#VALUE!", "Cell VALUE")
check_cell("A3", "#NAME?", "Cell NAME")


# ==================================================
# 5. Cell dependency propagation
# ==================================================

sheet.set_cell("B1", "=A1+10")
sheet.set_cell("B2", "=A2+10")
sheet.set_cell("B3", "=A3+10")

check_cell("B1", "#DIV/0!", "Dependent DIV/0")
check_cell("B2", "#VALUE!", "Dependent VALUE")
check_cell("B3", "#NAME?", "Dependent NAME")


# ==================================================
# 6. Error recovery
# ==================================================

sheet.set_cell("A1", 10)
sheet.set_cell("A2", 20)
sheet.set_cell("A3", 30)

check_cell("B1", 20, "DIV/0 recovery")
check_cell("B2", 30, "VALUE recovery")
check_cell("B3", 40, "NAME recovery")


# ==================================================
# 7. Reintroduce errors
# ==================================================

sheet.set_cell("A1", "=10/0")
sheet.set_cell("A2", '=ABS("abc")')
sheet.set_cell("A3", "=UNKNOWN(10)")

check_cell("B1", "#DIV/0!", "DIV/0 reintroduced")
check_cell("B2", "#VALUE!", "VALUE reintroduced")
check_cell("B3", "#NAME?", "NAME reintroduced")


# ==================================================
# 8. Range calculations
# ==================================================

sheet.set_cell("C1", 10)
sheet.set_cell("C2", 20)
sheet.set_cell("C3", 30)

check("=SUM(C1:C3)", 60, "SUM regression")
check("=AVERAGE(C1:C3)", 20, "AVERAGE regression")
check("=MIN(C1:C3)", 10, "MIN regression")
check("=MAX(C1:C3)", 30, "MAX regression")
check("=COUNT(C1:C3)", 3, "COUNT regression")


# ==================================================
# 9. Range error propagation
# ==================================================

sheet.set_cell("C2", "=10/0")

check(
    "=SUM(C1:C3)",
    "#DIV/0!",
    "Range DIV/0"
)

check(
    "=AVERAGE(C1:C3)",
    "#DIV/0!",
    "Range AVERAGE DIV/0"
)

check(
    "=MIN(C1:C3)",
    "#DIV/0!",
    "Range MIN DIV/0"
)

check(
    "=MAX(C1:C3)",
    "#DIV/0!",
    "Range MAX DIV/0"
)

check(
    "=COUNT(C1:C3)",
    "#DIV/0!",
    "Range COUNT DIV/0"
)


# ==================================================
# 10. Range recovery
# ==================================================

sheet.set_cell("C2", 20)

check("=SUM(C1:C3)", 60, "Range recovery SUM")
check("=AVERAGE(C1:C3)", 20, "Range recovery AVERAGE")
check("=MIN(C1:C3)", 10, "Range recovery MIN")
check("=MAX(C1:C3)", 30, "Range recovery MAX")
check("=COUNT(C1:C3)", 3, "Range recovery COUNT")


# ==================================================
# 11. Logical functions
# ==================================================

check("=TRUE()", True, "TRUE")
check("=FALSE()", False, "FALSE")
check("=AND(TRUE(),TRUE())", True, "AND")
check("=OR(FALSE(),TRUE())", True, "OR")
check("=NOT(FALSE())", True, "NOT")
check("=XOR(TRUE(),FALSE())", True, "XOR")


# ==================================================
# 12. Logical error propagation
# ==================================================

sheet.set_cell("D1", "=10/0")

check(
    "=AND(D1,TRUE())",
    "#DIV/0!",
    "AND error"
)

check(
    "=OR(D1,FALSE())",
    "#DIV/0!",
    "OR error"
)

check(
    "=NOT(D1)",
    "#DIV/0!",
    "NOT error"
)

check(
    "=XOR(D1,TRUE())",
    "#DIV/0!",
    "XOR error"
)


# ==================================================
# 13. IF lazy evaluation
# ==================================================

check(
    '=IF(TRUE(),10,10/0)',
    10,
    "IF lazy true"
)

check(
    '=IF(FALSE(),10,20)',
    20,
    "IF false"
)

check(
    '=IF(TRUE(),"SAFE",UNKNOWN(10))',
    "SAFE",
    "IF NAME isolation"
)

check(
    '=IF(TRUE(),"SAFE",ABS("abc"))',
    "SAFE",
    "IF VALUE isolation"
)


# ==================================================
# 14. IFS lazy evaluation
# ==================================================

check(
    '=IFS(TRUE(),100,TRUE(),10/0)',
    100,
    "IFS lazy evaluation"
)

check(
    '=IFS(FALSE(),10,TRUE(),200)',
    200,
    "IFS second condition"
)


# ==================================================
# 15. Text functions
# ==================================================

check(
    '=CONCAT("Hello"," ","World")',
    "Hello World",
    "CONCAT"
)

check(
    '=CONCATENATE("A","B","C")',
    "ABC",
    "CONCATENATE"
)

check(
    '=LEFT("Hello",2)',
    "He",
    "LEFT"
)

check(
    '=RIGHT("Hello",2)',
    "lo",
    "RIGHT"
)

check(
    '=LEN("Hello")',
    5,
    "LEN"
)

check(
    '=UPPER("hello")',
    "HELLO",
    "UPPER"
)

check(
    '=LOWER("HELLO")',
    "hello",
    "LOWER"
)

check(
    '=TRIM("  hello   world  ")',
    "hello world",
    "TRIM"
)


# ==================================================
# 16. Text error propagation
# ==================================================

sheet.set_cell("E1", "=10/0")

check(
    '=CONCAT("Value: ",E1)',
    "#DIV/0!",
    "CONCAT error"
)

check(
    "=LEN(E1)",
    "#DIV/0!",
    "LEN error"
)

check(
    "=UPPER(E1)",
    "#DIV/0!",
    "UPPER error"
)


# ==================================================
# 17. Comparisons
# ==================================================

check("=10=10", True, "Equality")
check("=10<>20", True, "Inequality")
check("=20>10", True, "Greater")
check("=10<20", True, "Less")
check("=20>=20", True, "Greater equal")
check("=20<=20", True, "Less equal")


# ==================================================
# 18. Boolean comparison restriction
# ==================================================

check(
    "=TRUE()=TRUE()",
    True,
    "Boolean equality"
)

check(
    "=TRUE()<>FALSE()",
    True,
    "Boolean inequality"
)

try:
    evaluator.evaluate(
        parser.parse("=TRUE()>FALSE()")
    )
    raise AssertionError(
        "Boolean ordering should have failed"
    )
except ValueError:
    print("Boolean ordering error: PASS")


# ==================================================
# 19. Math functions
# ==================================================

check("=ABS(-10)", 10, "ABS")
check("=ROUND(12.345,2)", 12.35, "ROUND")
check("=INT(12.9)", 12, "INT")
check("=MOD(10,3)", 1, "MOD")


# ==================================================
# 20. Math error propagation
# ==================================================

check(
    "=ABS(10/0)",
    "#DIV/0!",
    "ABS error"
)

check(
    "=ROUND(10/0,2)",
    "#DIV/0!",
    "ROUND error"
)

check(
    "=INT(10/0)",
    "#DIV/0!",
    "INT error"
)

check(
    "=MOD(10/0,3)",
    "#DIV/0!",
    "MOD error"
)


# ==================================================
# 21. Cross-sheet references
# ==================================================

other.set_cell("A1", 100)
other.set_cell("A2", 200)
other.set_cell("A3", 300)

check(
    "=Other!A1",
    100,
    "Cross-sheet cell"
)

check(
    "=SUM(Other!A1:A3)",
    600,
    "Cross-sheet range"
)

check(
    "=Other!A1+50",
    150,
    "Cross-sheet arithmetic"
)


# ==================================================
# 22. Cross-sheet error propagation
# ==================================================

other.set_cell("A1", "=10/0")

check(
    "=Other!A1",
    "#DIV/0!",
    "Cross-sheet DIV/0"
)

check(
    "=SUM(Other!A1:A3)",
    "#DIV/0!",
    "Cross-sheet range error"
)

check(
    "=Other!A1+10",
    "#DIV/0!",
    "Cross-sheet arithmetic error"
)


# ==================================================
# 23. Cross-sheet recovery
# ==================================================

other.set_cell("A1", 100)

check(
    "=Other!A1",
    100,
    "Cross-sheet recovery"
)

check(
    "=SUM(Other!A1:A3)",
    600,
    "Cross-sheet range recovery"
)


# ==================================================
# 24. Circular references
# ==================================================

sheet.set_cell("F1", "=F2")
sheet.set_cell("F2", "=F1")

check_cell(
    "F1",
    "#CIRC!",
    "Circular reference"
)

check_cell(
    "F2",
    "#CIRC!",
    "Circular reverse reference"
)


# ==================================================
# 25. Circular recovery
# ==================================================

sheet.set_cell("F2", 500)

check_cell(
    "F1",
    500,
    "Circular recovery"
)


# ==================================================
# 26. Unknown sheet
# ==================================================

check(
    "=Missing!A1",
    "#REF!",
    "Missing sheet reference"
)


# ==================================================
# 27. Error type preservation through chains
# ==================================================

sheet.set_cell("G1", "=10/0")
sheet.set_cell("G2", "=G1+10")
sheet.set_cell("G3", "=SUM(G2,50)")

check_cell(
    "G1",
    "#DIV/0!",
    "Chain source error"
)

check_cell(
    "G2",
    "#DIV/0!",
    "Chain middle error"
)

check_cell(
    "G3",
    "#DIV/0!",
    "Chain final error"
)


# ==================================================
# 28. Chain recovery
# ==================================================

sheet.set_cell("G1", 25)

check_cell(
    "G1",
    25,
    "Chain source recovery"
)

check_cell(
    "G2",
    35,
    "Chain middle recovery"
)

check_cell(
    "G3",
    85,
    "Chain final recovery"
)


# ==================================================
# 29. Repeated evaluation stability
# ==================================================

sheet.set_cell("H1", "=10/0")
sheet.set_cell("H2", "=H1+1")

for _ in range(10):
    assert evaluator.evaluate_cell("H2") == "#DIV/0!"

sheet.set_cell("H1", 99)

for _ in range(10):
    assert evaluator.evaluate_cell("H2") == 100

print("Repeated evaluation stability: PASS")


# ==================================================
# 30. Final mixed expression
# ==================================================

sheet.set_cell("A1", 10)
sheet.set_cell("A2", 20)
sheet.set_cell("A3", 30)

check(
    '=IF(SUM(A1:A3)=60,CONCAT("TOTAL: ","60"),"ERROR")',
    "TOTAL: 60",
    "Final mixed expression"
)


# ==================================================
# FINAL
# ==================================================

print("========================================")
print("PHASE 17 PART 6: PASS")
print("========================================")
print("PHASE 17 COMPLETE")
print("========================================")