from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

parser = Parser()
evaluator = Evaluator(sheet)


# --------------------------------------------------
# ABS
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=ABS(-10)")
) == 10

print("ABS: PASS")


assert evaluator.evaluate(
    parser.parse("=ABS(10)")
) == 10

print("ABS positive: PASS")


# --------------------------------------------------
# ROUND
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=ROUND(3.14159,2)")
) == 3.14

print("ROUND decimals: PASS")


assert evaluator.evaluate(
    parser.parse("=ROUND(3.6)")
) == 4

print("ROUND integer: PASS")


# --------------------------------------------------
# INT
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=INT(3.9)")
) == 3

print("INT positive: PASS")


assert evaluator.evaluate(
    parser.parse("=INT(-3.2)")
) == -4

print("INT negative: PASS")


# --------------------------------------------------
# MOD
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=MOD(10,3)")
) == 1

print("MOD: PASS")


# --------------------------------------------------
# Combined formula
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=ABS(-5)+MOD(10,3)")
) == 6

print("Combined math: PASS")


# --------------------------------------------------
# Invalid argument counts
# --------------------------------------------------

try:
    evaluator.evaluate(
        parser.parse("=ABS(1,2)")
    )

    raise AssertionError(
        "ABS accepted invalid arguments"
    )

except ValueError:
    print("ABS validation: PASS")


try:
    evaluator.evaluate(
        parser.parse("=MOD(10)")
    )

    raise AssertionError(
        "MOD accepted invalid arguments"
    )

except ValueError:
    print("MOD validation: PASS")


# --------------------------------------------------
# MOD by zero
# --------------------------------------------------

try:
    evaluator.evaluate(
        parser.parse("=MOD(10,0)")
    )

    raise AssertionError(
        "MOD accepted zero divisor"
    )

except ZeroDivisionError:
    print("MOD zero validation: PASS")


print("MATH FUNCTIONS: PASS")