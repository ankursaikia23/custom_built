from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()

sheet1 = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Data Sheet")

parser = Parser()
evaluator = Evaluator(sheet1, workbook)


# --------------------------------------------------
# Setup
# --------------------------------------------------

sheet1.set_cell("A1", 10)
sheet1.set_cell("A2", 20)
sheet1.set_cell("A3", 30)

sheet1.set_cell("B1", "hello")
sheet1.set_cell("B2", " WORLD ")

sheet2.set_cell("A1", 100)
sheet2.set_cell("A2", 200)
sheet2.set_cell("B1", "pass")


# --------------------------------------------------
# Arithmetic
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1+A2")
) == 30

print("Arithmetic: PASS")


assert evaluator.evaluate(
    parser.parse("=A1*A2")
) == 200

print("Multiplication: PASS")


assert evaluator.evaluate(
    parser.parse("=A3/10")
) == 3

print("Division: PASS")


assert evaluator.evaluate(
    parser.parse("=2^3")
) == 8

print("Power: PASS")


# --------------------------------------------------
# Math functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=SUM(A1:A3)")
) == 60

print("SUM range: PASS")


assert evaluator.evaluate(
    parser.parse("=AVERAGE(A1:A3)")
) == 20

print("AVERAGE range: PASS")


assert evaluator.evaluate(
    parser.parse("=MIN(A1:A3)")
) == 10

print("MIN range: PASS")


assert evaluator.evaluate(
    parser.parse("=MAX(A1:A3)")
) == 30

print("MAX range: PASS")


assert evaluator.evaluate(
    parser.parse("=ABS(-25)")
) == 25

print("ABS: PASS")


assert evaluator.evaluate(
    parser.parse("=ROUND(12.345,2)")
) == 12.35

print("ROUND: PASS")


assert evaluator.evaluate(
    parser.parse("=INT(12.9)")
) == 12

print("INT: PASS")


assert evaluator.evaluate(
    parser.parse("=MOD(17,5)")
) == 2

print("MOD: PASS")


# --------------------------------------------------
# Text functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=CONCAT(B1," ",B2)')
) == "hello  WORLD "

print("CONCAT: PASS")


assert evaluator.evaluate(
    parser.parse('=CONCATENATE("A","B","C")')
) == "ABC"

print("CONCATENATE: PASS")


assert evaluator.evaluate(
    parser.parse('=LEFT(B1,2)')
) == "he"

print("LEFT: PASS")


assert evaluator.evaluate(
    parser.parse('=RIGHT(B1,2)')
) == "lo"

print("RIGHT: PASS")


assert evaluator.evaluate(
    parser.parse('=LEN(B1)')
) == 5

print("LEN: PASS")


assert evaluator.evaluate(
    parser.parse('=UPPER(B1)')
) == "HELLO"

print("UPPER: PASS")


assert evaluator.evaluate(
    parser.parse('=LOWER("HELLO")')
) == "hello"

print("LOWER: PASS")


assert evaluator.evaluate(
    parser.parse('=TRIM(B2)')
) == "WORLD"

print("TRIM: PASS")


# --------------------------------------------------
# Logical functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=AND(TRUE(),TRUE())")
) is True

print("AND: PASS")


assert evaluator.evaluate(
    parser.parse("=OR(FALSE(),TRUE())")
) is True

print("OR: PASS")


assert evaluator.evaluate(
    parser.parse("=NOT(FALSE())")
) is True

print("NOT: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=XOR(TRUE(),FALSE())"
    )
) is True

print("XOR: PASS")


# --------------------------------------------------
# Comparisons
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A2>A1")
) is True

print("Numeric comparison: PASS")


assert evaluator.evaluate(
    parser.parse('=B1="hello"')
) is True

print("Text comparison: PASS")


assert evaluator.evaluate(
    parser.parse("=A1<>A2")
) is True

print("Not-equal comparison: PASS")


# --------------------------------------------------
# IF
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(A2>A1,"HIGH","LOW")'
    )
) == "HIGH"

print("IF comparison: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF(A1>A2,"HIGH","LOW")'
    )
) == "LOW"

print("IF false branch: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF(TRUE(),"YES")'
    )
) == "YES"

print("IF without false branch: PASS")


# --------------------------------------------------
# Nested IF
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(A1>20,"A",'
        'IF(A1>5,"B","C"))'
    )
) == "B"

print("Nested IF: PASS")


# --------------------------------------------------
# Text + logical integration
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(UPPER(B1)="HELLO","YES","NO")'
    )
) == "YES"

print("Text + IF: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=AND(LEN(B1)=5,'
        'UPPER(B1)="HELLO")'
    )
) is True

print("Text + logical: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF(TRIM(B2)="WORLD","OK","NO")'
    )
) == "OK"

print("TRIM + IF: PASS")


# --------------------------------------------------
# Cross-sheet references
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "='Data Sheet'!A1"
    )
) == 100

print("Cross-sheet cell: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=SUM('Data Sheet'!A1:A2)"
    )
) == 300

print("Cross-sheet range: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=UPPER(\'Data Sheet\'!B1)'
    )
) == "PASS"

print("Cross-sheet text: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF(\'Data Sheet\'!B1="pass","YES","NO")'
    )
) == "YES"

print("Cross-sheet text + IF: PASS")


# --------------------------------------------------
# Lazy evaluation
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(TRUE(),10,10/0)'
    )
) == 10

print("IF lazy evaluation: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IFS(TRUE(),10,TRUE(),10/0)'
    )
) == 10

print("IFS lazy evaluation: PASS")


# --------------------------------------------------
# Escaped strings
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '="Say ""Hello"""'
    )
) == 'Say "Hello"'

print("Escaped string: PASS")


# --------------------------------------------------
# Formula cell evaluation
# --------------------------------------------------

sheet1.set_cell(
    "C1",
    '=SUM(A1:A3)'
)

assert evaluator.evaluate_cell(
    "C1"
) == 60

print("Formula cell: PASS")


sheet1.set_cell(
    "C2",
    '=IF(C1=60,"PASS","FAIL")'
)

assert evaluator.evaluate_cell(
    "C2"
) == "PASS"

print("Dependent formula cell: PASS")


# --------------------------------------------------
# Error handling
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=10/0")
) == "#DIV/0!"

print("Division error: PASS")


assert evaluator.evaluate(
    parser.parse("=UNKNOWN(10)")
) == "#NAME?"

print("Unknown function: PASS")


# --------------------------------------------------
# Final
# --------------------------------------------------

print("========================================")
print("PHASE 16 FINAL INTEGRATION: PASS")
print("========================================")