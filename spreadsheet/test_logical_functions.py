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
# AND
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=AND(1=1,2=2)")
) is True

print("AND true: PASS")


assert evaluator.evaluate(
    parser.parse("=AND(1=1,2=3)")
) is False

print("AND false: PASS")


# --------------------------------------------------
# OR
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=OR(1=2,2=2)")
) is True

print("OR true: PASS")


assert evaluator.evaluate(
    parser.parse("=OR(1=2,2=3)")
) is False

print("OR false: PASS")


# --------------------------------------------------
# NOT
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=NOT(1=2)")
) is True

print("NOT true: PASS")


assert evaluator.evaluate(
    parser.parse("=NOT(1=1)")
) is False

print("NOT false: PASS")


# --------------------------------------------------
# Cell comparisons
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=AND(A1<B1,A1=10)")
) is True

print("AND with cells: PASS")


assert evaluator.evaluate(
    parser.parse("=OR(A1>B1,A1=10)")
) is True

print("OR with cells: PASS")


# --------------------------------------------------
# Invalid NOT argument count
# --------------------------------------------------

try:
    evaluator.evaluate(
        parser.parse("=NOT(1=1,2=2)")
    )

    raise AssertionError(
        "NOT accepted multiple arguments"
    )

except ValueError:
    print("NOT argument validation: PASS")


print("LOGICAL FUNCTIONS: PASS")