from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

sheet.set_cell("A1", True)
sheet.set_cell("B1", False)

sheet.set_cell("A2", 10)
sheet.set_cell("B2", 20)

parser = Parser()
evaluator = Evaluator(sheet)


# --------------------------------------------------
# Boolean cell values
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1")
) is True

print("Boolean TRUE cell: PASS")


assert evaluator.evaluate(
    parser.parse("=B1")
) is False

print("Boolean FALSE cell: PASS")


# --------------------------------------------------
# Boolean equality
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1=A1")
) is True

print("Boolean equality: PASS")


assert evaluator.evaluate(
    parser.parse("=A1=B1")
) is False

print("Boolean inequality: PASS")


# --------------------------------------------------
# Boolean NOT equal
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A1<>B1")
) is True

print("Boolean NOT_EQUAL: PASS")


# --------------------------------------------------
# Boolean ordering rejected
# --------------------------------------------------

try:
    evaluator.evaluate(
        parser.parse("=A1>B1")
    )

    raise AssertionError(
        "Boolean ordering was accepted"
    )

except ValueError:
    print("Boolean ordering rejected: PASS")


# --------------------------------------------------
# Numeric comparison unaffected
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=A2<B2")
) is True

print("Numeric comparison: PASS")


# --------------------------------------------------
# Logical functions with booleans
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=AND(A1,A1)")
) is True

print("AND boolean values: PASS")


assert evaluator.evaluate(
    parser.parse("=AND(A1,B1)")
) is False

print("AND mixed booleans: PASS")


assert evaluator.evaluate(
    parser.parse("=OR(B1,A1)")
) is True

print("OR boolean values: PASS")


assert evaluator.evaluate(
    parser.parse("=NOT(B1)")
) is True

print("NOT boolean value: PASS")


print("BOOLEAN VALUES: PASS")