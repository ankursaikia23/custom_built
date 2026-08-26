from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

sheet.set_cell("A1", 10)
sheet.set_cell("A2", "Hello")

parser = Parser()
evaluator = Evaluator(
    sheet,
    workbook
)


# --------------------------------------------------
# Missing required values
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=AVERAGE()")
) == "#VALUE!"

print("AVERAGE missing argument: PASS")


assert evaluator.evaluate(
    parser.parse("=MIN()")
) == "#VALUE!"

print("MIN missing argument: PASS")


assert evaluator.evaluate(
    parser.parse("=MAX()")
) == "#VALUE!"

print("MAX missing argument: PASS")


# --------------------------------------------------
# Wrong argument count
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=ABS(1,2)")
) == "#VALUE!"

print("ABS argument count: PASS")


assert evaluator.evaluate(
    parser.parse("=NOT(1,2)")
) == "#VALUE!"

print("NOT argument count: PASS")


assert evaluator.evaluate(
    parser.parse("=MOD(10)")
) == "#VALUE!"

print("MOD argument count: PASS")


# --------------------------------------------------
# Invalid value
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=SUM(A2)")
) == "#VALUE!"

print("SUM invalid value: PASS")


assert evaluator.evaluate(
    parser.parse("=ABS(A2)")
) == "#VALUE!"

print("ABS invalid value: PASS")


# --------------------------------------------------
# Division error
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=MOD(10,0)")
) == "#DIV/0!"

print("MOD division error: PASS")


# --------------------------------------------------
# Unknown function
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=UNKNOWN(10)")
) == "#NAME?"

print("Unknown function: PASS")


# --------------------------------------------------
# Existing valid functions
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=SUM(10,20)")
) == 30

print("SUM regression: PASS")


assert evaluator.evaluate(
    parser.parse("=AVERAGE(10,20)")
) == 15

print("AVERAGE regression: PASS")


assert evaluator.evaluate(
    parser.parse("=MIN(10,20)")
) == 10

print("MIN regression: PASS")


assert evaluator.evaluate(
    parser.parse("=MAX(10,20)")
) == 20

print("MAX regression: PASS")


assert evaluator.evaluate(
    parser.parse("=ABS(-10)")
) == 10

print("ABS regression: PASS")


assert evaluator.evaluate(
    parser.parse("=ROUND(10.55,1)")
) == 10.6

print("ROUND regression: PASS")


assert evaluator.evaluate(
    parser.parse("=INT(10.9)")
) == 10

print("INT regression: PASS")


assert evaluator.evaluate(
    parser.parse("=MOD(10,3)")
) == 1

print("MOD regression: PASS")


print("FUNCTION ERRORS: PASS")