from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator


workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

sheet.set_cell("A1", 10)
sheet.set_cell("B1", 20)

parser = Parser()
evaluator = Evaluator(sheet)


# --------------------------------------------------
# Numeric comparisons
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=1=1")
) is True

print("Equal: PASS")


assert evaluator.evaluate(
    parser.parse("=1<>2")
) is True

print("Not equal: PASS")


assert evaluator.evaluate(
    parser.parse("=5>3")
) is True

print("Greater than: PASS")


assert evaluator.evaluate(
    parser.parse("=3<5")
) is True

print("Less than: PASS")


assert evaluator.evaluate(
    parser.parse("=5>=5")
) is True

print("Greater/equal: PASS")


assert evaluator.evaluate(
    parser.parse("=4<=5")
) is True

print("Less/equal: PASS")


# --------------------------------------------------
# False comparisons
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=1=2")
) is False

assert evaluator.evaluate(
    parser.parse("=5<3")
) is False

assert evaluator.evaluate(
    parser.parse("=5>10")
) is False

print("False comparisons: PASS")


# --------------------------------------------------
# Cell comparisons
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1<B1")
) is True

print("Cell comparison: PASS")


assert evaluator.evaluate(
    parser.parse("=A1>B1")
) is False

print("Cell comparison false: PASS")


# --------------------------------------------------
# Arithmetic still works
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1+B1")
) == 30

assert evaluator.evaluate(
    parser.parse("=A1*2")
) == 20

print("Arithmetic regression: PASS")


# --------------------------------------------------
# Mixed arithmetic + comparison
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1+5>B1")
) is False

assert evaluator.evaluate(
    parser.parse("=A1+10>=B1")
) is True

print("Mixed expression: PASS")


print("COMPARISON EVALUATION: PASS")