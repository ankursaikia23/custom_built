from core.workbook import Workbook
from services.formula.ast import ErrorNode
from services.formula.evaluator import Evaluator

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

evaluator = Evaluator(
    sheet,
    workbook
)


# --------------------------------------------------
# Basic error node
# --------------------------------------------------

node = ErrorNode("#DIV/0!")

assert evaluator.evaluate(node) == "#DIV/0!"

print("DIV/0 error node: PASS")


# --------------------------------------------------
# VALUE error
# --------------------------------------------------

node = ErrorNode("#VALUE!")

assert evaluator.evaluate(node) == "#VALUE!"

print("VALUE error node: PASS")


# --------------------------------------------------
# REF error
# --------------------------------------------------

node = ErrorNode("#REF!")

assert evaluator.evaluate(node) == "#REF!"

print("REF error node: PASS")


# --------------------------------------------------
# NAME error
# --------------------------------------------------

node = ErrorNode("#NAME?")

assert evaluator.evaluate(node) == "#NAME?"

print("NAME error node: PASS")


# --------------------------------------------------
# Normal evaluation regression
# --------------------------------------------------

from services.formula.parser import Parser

assert evaluator.evaluate(
    Parser().parse("=10+5")
) == 15

print("Normal evaluation regression: PASS")


print("ERROR NODE: PASS")