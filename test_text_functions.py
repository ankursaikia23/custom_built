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
# CONCAT
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=CONCAT("Hello"," ","World")')
) == "Hello World"

print("CONCAT: PASS")


# --------------------------------------------------
# CONCATENATE
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=CONCATENATE("Hello"," ","World")'
    )
) == "Hello World"

print("CONCATENATE: PASS")


# --------------------------------------------------
# LEFT
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=LEFT("Hello",2)')
) == "He"

print("LEFT: PASS")


# --------------------------------------------------
# LEFT default
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=LEFT("Hello")')
) == "H"

print("LEFT default: PASS")


# --------------------------------------------------
# RIGHT
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=RIGHT("Hello",2)')
) == "lo"

print("RIGHT: PASS")


# --------------------------------------------------
# RIGHT default
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=RIGHT("Hello")')
) == "o"

print("RIGHT default: PASS")


# --------------------------------------------------
# LEN
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=LEN("Hello")')
) == 5

print("LEN: PASS")


# --------------------------------------------------
# UPPER
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=UPPER("hello")')
) == "HELLO"

print("UPPER: PASS")


# --------------------------------------------------
# LOWER
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=LOWER("HELLO")')
) == "hello"

print("LOWER: PASS")


# --------------------------------------------------
# TRIM
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=TRIM("  Hello   World  ")'
    )
) == "Hello World"

print("TRIM: PASS")


# --------------------------------------------------
# Numeric conversion to text
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=CONCAT("Value: ",10)'
    )
) == "Value: 10"

print("Numeric CONCAT: PASS")


# --------------------------------------------------
# LEFT invalid count
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=LEFT("Hello",-1)')
) == "#VALUE!"

print("LEFT invalid count: PASS")


# --------------------------------------------------
# RIGHT invalid count
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=RIGHT("Hello",-1)')
) == "#VALUE!"

print("RIGHT invalid count: PASS")


# --------------------------------------------------
# LEN argument count
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=LEN("A","B")')
) == "#VALUE!"

print("LEN argument count: PASS")


# --------------------------------------------------
# UPPER argument count
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=UPPER("A","B")')
) == "#VALUE!"

print("UPPER argument count: PASS")


# --------------------------------------------------
# LOWER argument count
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=LOWER("A","B")')
) == "#VALUE!"

print("LOWER argument count: PASS")


# --------------------------------------------------
# TRIM argument count
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse('=TRIM("A","B")')
) == "#VALUE!"

print("TRIM argument count: PASS")


# --------------------------------------------------
# Regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=10+5")
) == 15

print("Arithmetic regression: PASS")


print("TEXT FUNCTIONS: PASS")