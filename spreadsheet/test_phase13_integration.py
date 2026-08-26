from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

# --------------------------------------------------
# Workbook
# --------------------------------------------------

workbook = Workbook()

sheet = workbook.add_sheet("Sheet1")

sheet.set_cell("A1", 10)
sheet.set_cell("B1", 20)
sheet.set_cell("A2", 5)
sheet.set_cell("B2", 5)

parser = Parser()
evaluator = Evaluator(sheet)


# --------------------------------------------------
# Comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1<B1")
) is True

print("Comparison: PASS")


# --------------------------------------------------
# Arithmetic + comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1+10>=B1")
) is True

print("Arithmetic + comparison: PASS")


# --------------------------------------------------
# Logical functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=AND(A1<B1,A2=B2)"
    )
) is True

print("AND integration: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=OR(A1>B1,A2=B2)"
    )
) is True

print("OR integration: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=NOT(A1>B1)"
    )
) is True

print("NOT integration: PASS")


# --------------------------------------------------
# Mathematical functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        "=ABS(-10)"
    )
) == 10

print("ABS integration: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=ROUND(3.14159,2)"
    )
) == 3.14

print("ROUND integration: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=INT(3.9)"
    )
) == 3

print("INT integration: PASS")


assert evaluator.evaluate(
    parser.parse(
        "=MOD(10,3)"
    )
) == 1

print("MOD integration: PASS")


# --------------------------------------------------
# Combined formula
# --------------------------------------------------

result = evaluator.evaluate(
    parser.parse(
        "=AND("
        "A1<B1,"
        "ABS(-10)=10,"
        "ROUND(3.14159,2)=3.14,"
        "MOD(10,3)=1"
        ")"
    )
)

assert result is True

print("Complex formula: PASS")


# --------------------------------------------------
# Existing functions regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=SUM(A1:B2)")
) == 40

print("SUM regression: PASS")


assert evaluator.evaluate(
    parser.parse("=AVERAGE(A1:B2)")
) == 10

print("AVERAGE regression: PASS")


assert evaluator.evaluate(
    parser.parse("=MIN(A1:B2)")
) == 5

print("MIN regression: PASS")


assert evaluator.evaluate(
    parser.parse("=MAX(A1:B2)")
) == 20

print("MAX regression: PASS")


assert evaluator.evaluate(
    parser.parse("=COUNT(A1:B2)")
) == 4

print("COUNT regression: PASS")


# --------------------------------------------------
# Unary minus regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=-5")
) == -5

print("Unary minus: PASS")


assert evaluator.evaluate(
    parser.parse("=A1*-2")
) == -20

print("Unary minus multiplication: PASS")


# --------------------------------------------------
# Phase result
# --------------------------------------------------

print("PHASE 13 INTEGRATION: PASS")