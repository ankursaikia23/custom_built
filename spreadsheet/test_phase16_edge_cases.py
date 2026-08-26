from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")
other = workbook.add_sheet("Other")

parser = Parser()
evaluator = Evaluator(sheet, workbook)


# --------------------------------------------------
# Empty string
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=""')
) == ""

print("Empty string: PASS")


# --------------------------------------------------
# Empty string length
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=LEN("")')
) == 0

print("Empty string LEN: PASS")


# --------------------------------------------------
# Empty cell in text function
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=LEN(A1)")
) == 0

print("Empty cell LEN: PASS")


# --------------------------------------------------
# Empty cell in IF
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(A1,"YES","NO")'
    )
) == "NO"

print("Empty cell IF: PASS")


# --------------------------------------------------
# Zero condition
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(0,"YES","NO")'
    )
) == "NO"

print("Zero IF condition: PASS")


# --------------------------------------------------
# TRUE condition
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(TRUE(),"YES","NO")'
    )
) == "YES"

print("TRUE IF condition: PASS")


# --------------------------------------------------
# FALSE condition
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(FALSE(),"YES","NO")'
    )
) == "NO"

print("FALSE IF condition: PASS")


# --------------------------------------------------
# String escaping
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '="He said ""Hello"""'
    )
) == 'He said "Hello"'

print("Escaped quotes: PASS")


# --------------------------------------------------
# CONCAT with escaped quotes
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=CONCAT("He said ""","Hello","""")'
    )
) == 'He said "Hello"'

print("CONCAT escaped quotes: PASS")


# --------------------------------------------------
# Nested CONCAT
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=CONCAT("A",CONCAT("B","C"))'
    )
) == "ABC"

print("Nested CONCAT: PASS")


# --------------------------------------------------
# Nested math + text
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=CONCAT("Total: ",SUM(10,20))'
    )
) == "Total: 30"

print("Math + text nesting: PASS")


# --------------------------------------------------
# Text + numeric comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF("10"=10,"YES","NO")'
    )
) == "NO"

print("Text/numeric equality: PASS")


# --------------------------------------------------
# Boolean equality
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=TRUE()=TRUE()'
    )
) is True

print("Boolean equality: PASS")


# --------------------------------------------------
# Boolean inequality
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=TRUE()<>FALSE()'
    )
) is True

print("Boolean inequality: PASS")


# --------------------------------------------------
# Boolean ordering must fail
# --------------------------------------------------

try:
    evaluator.evaluate(
        parser.parse(
            '=TRUE()>FALSE()'
        )
    )

    assert False, (
        "Expected ValueError for "
        "boolean ordering comparison"
    )

except ValueError as error:
    assert str(error) == (
        "Boolean values only support "
        "equality comparisons"
    )

print("Boolean ordering error: PASS")

# --------------------------------------------------
# Mixed AND
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=AND(TRUE(),1,TRUE())'
    )
) is True

print("Mixed AND: PASS")


# --------------------------------------------------
# Mixed OR
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=OR(FALSE(),0,TRUE())'
    )
) is True

print("Mixed OR: PASS")


# --------------------------------------------------
# NOT numeric
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=NOT(0)'
    )
) is True

print("NOT zero: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=NOT(1)'
    )
) is False

print("NOT one: PASS")


# --------------------------------------------------
# XOR mixed values
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=XOR(1,0,0)'
    )
) is True

print("XOR mixed values: PASS")


# --------------------------------------------------
# Cross-sheet text
# --------------------------------------------------

other.set_cell(
    "A1",
    "PASS"
)

assert evaluator.evaluate(
    parser.parse(
        '=Other!A1'
    )
) == "PASS"

print("Cross-sheet text: PASS")


# --------------------------------------------------
# Cross-sheet text + IF
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(Other!A1="PASS","YES","NO")'
    )
) == "YES"

print("Cross-sheet text + IF: PASS")


# --------------------------------------------------
# Cross-sheet text function
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=UPPER(Other!A1)'
    )
) == "PASS"

print("Cross-sheet text function: PASS")


# --------------------------------------------------
# Cross-sheet quoted text
# --------------------------------------------------

other.set_cell(
    "B1",
    "hello"
)

assert evaluator.evaluate(
    parser.parse(
        '=UPPER(Other!B1)'
    )
) == "HELLO"

print("Cross-sheet quoted context: PASS")


# --------------------------------------------------
# Nested conditional
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(TRUE(),IF(FALSE(),"A","B"),"C")'
    )
) == "B"

print("Nested conditional edge case: PASS")


# --------------------------------------------------
# IF must remain lazy
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(TRUE(),1,10/0)'
    )
) == 1

print("IF lazy regression: PASS")


# --------------------------------------------------
# IFS must remain lazy
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IFS(TRUE(),1,TRUE(),10/0)'
    )
) == 1

print("IFS lazy regression: PASS")


# --------------------------------------------------
# Existing functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=AVERAGE(10,20,30)'
    )
) == 20

print("AVERAGE regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=MIN(10,20,5)'
    )
) == 5

print("MIN regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=MAX(10,20,5)'
    )
) == 20

print("MAX regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=ROUND(10.55,1)'
    )
) == 10.6

print("ROUND regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=INT(10.9)'
    )
) == 10

print("INT regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=MOD(10,3)'
    )
) == 1

print("MOD regression: PASS")


# --------------------------------------------------
# Error regressions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=10/0'
    )
) == "#DIV/0!"

print("Division error regression: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=UNKNOWN(10)'
    )
) == "#NAME?"

print("Unknown function regression: PASS")


# --------------------------------------------------
# Final
# --------------------------------------------------

print("PHASE 16 EDGE CASES: PASS")