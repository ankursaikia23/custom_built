from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

parser = Parser()
evaluator = Evaluator(
    sheet,
    workbook
)


# --------------------------------------------------
# Text equality + IF
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF("PASS"="PASS","YES","NO")'
    )
) == "YES"

print("Text equality + IF: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF("PASS"="FAIL","YES","NO")'
    )
) == "NO"

print("Text inequality + IF: PASS")


# --------------------------------------------------
# Text comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF("A"="A",1,0)'
    )
) == 1

print("Text comparison: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF("A"<>"B",1,0)'
    )
) == 1

print("Text not-equal comparison: PASS")


# --------------------------------------------------
# LEN + IF
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(LEN("Hello")>3,"LONG","SHORT")'
    )
) == "LONG"

print("LEN + IF: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF(LEN("Hi")>3,"LONG","SHORT")'
    )
) == "SHORT"

print("LEN short + IF: PASS")


# --------------------------------------------------
# UPPER + comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(UPPER("yes")="YES","MATCH","NO")'
    )
) == "MATCH"

print("UPPER + comparison: PASS")


# --------------------------------------------------
# LOWER + comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(LOWER("YES")="yes","MATCH","NO")'
    )
) == "MATCH"

print("LOWER + comparison: PASS")


# --------------------------------------------------
# TRIM + comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(TRIM("  PASS  ")="PASS","MATCH","NO")'
    )
) == "MATCH"

print("TRIM + comparison: PASS")


# --------------------------------------------------
# CONCAT + comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(CONCAT("PASS","123")="PASS123",TRUE(),FALSE())'
    )
) is True

print("CONCAT + comparison: PASS")


# --------------------------------------------------
# Text functions + logical functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=AND(LEN("Hello")=5,UPPER("yes")="YES")'
    )
) is True

print("Text + AND: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=OR(LEN("Hi")=5,UPPER("yes")="YES")'
    )
) is True

print("Text + OR: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=NOT(LEN("Hi")=5)'
    )
) is True

print("Text + NOT: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=XOR(LEN("Hi")=2,LEN("Hello")=10)'
    )
) is True

print("Text + XOR: PASS")


# --------------------------------------------------
# Cell text values
# --------------------------------------------------

sheet.set_cell(
    "A1",
    "PASS"
)

sheet.set_cell(
    "B1",
    "FAIL"
)

assert evaluator.evaluate(
    parser.parse(
        '=IF(A1="PASS","CORRECT","WRONG")'
    )
) == "CORRECT"

print("Cell text + IF: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF(B1="PASS","CORRECT","WRONG")'
    )
) == "WRONG"

print("Cell text false + IF: PASS")


# --------------------------------------------------
# Cell text + functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=UPPER(A1)'
    )
) == "PASS"

print("Cell text + UPPER: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=LEN(A1)'
    )
) == 4

print("Cell text + LEN: PASS")


# --------------------------------------------------
# Cell text + nested logic
# --------------------------------------------------

sheet.set_cell(
    "C1",
    '=IF(A1="PASS","YES","NO")'
)

assert evaluator.evaluate_cell(
    "C1"
) == "YES"

print("Formula cell + text logic: PASS")


# --------------------------------------------------
# Nested text functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(TRIM(UPPER("  yes  "))="YES","OK","NO")'
    )
) == "OK"

print("Nested text functions: PASS")


# --------------------------------------------------
# Nested IF + text functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(LEN("Hello")>10,"A",'
        'IF(LEN("Hello")>3,"B","C"))'
    )
) == "B"

print("Nested IF + text: PASS")


# --------------------------------------------------
# Error propagation through IF
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(LEN("A")>0,"OK",10/0)'
    )
) == "OK"

print("Text IF error isolation: PASS")


# --------------------------------------------------
# Existing math regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=SUM(10,20,30)"
    )
) == 60

print("SUM regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=ABS(-10)"
    )
) == 10

print("ABS regression: PASS")


# --------------------------------------------------
# Final
# --------------------------------------------------

print("TEXT + LOGICAL INTEGRATION: PASS")