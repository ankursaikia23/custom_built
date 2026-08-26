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
# Basic IF
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=IF(1=1,10,20)")
) == 10

print("IF true: PASS")


assert evaluator.evaluate(
    parser.parse("=IF(1=2,10,20)")
) == 20

print("IF false: PASS")


# --------------------------------------------------
# IF without false branch
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=IF(1=1,10)")
) == 10

print("IF true without false branch: PASS")


assert evaluator.evaluate(
    parser.parse("=IF(1=2,10)")
) is False

print("IF false without false branch: PASS")


# --------------------------------------------------
# Text results
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(1=1,"YES","NO")'
    )
) == "YES"

print("IF text result: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF(1=2,"YES","NO")'
    )
) == "NO"

print("IF false text result: PASS")


# --------------------------------------------------
# Cell comparison
# --------------------------------------------------

sheet.set_cell("A1", 100)
sheet.set_cell("B1", 50)

assert evaluator.evaluate(
    parser.parse(
        '=IF(A1>B1,"HIGH","LOW")'
    )
) == "HIGH"

print("IF cell comparison: PASS")


# --------------------------------------------------
# Nested IF
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(10>20,"A",IF(10>5,"B","C"))'
    )
) == "B"

print("Nested IF: PASS")


# --------------------------------------------------
# Error propagation
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(10/0,1,2)'
    )
) == "#DIV/0!"

print("IF condition error: PASS")


# --------------------------------------------------
# Lazy branch evaluation
# --------------------------------------------------

result = evaluator.evaluate(
    parser.parse(
        '=IF(1=1,10,10/0)'
    )
)

print("DEBUG IF lazy result:", result)

assert result == 10

print("IF lazy true branch: PASS")

# --------------------------------------------------
# IF argument count
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IF(1=1)'
    )
) == "#VALUE!"

print("IF missing result: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IF(1=1,10,20,30)'
    )
) == "#VALUE!"

print("IF excessive arguments: PASS")


# --------------------------------------------------
# IFS
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IFS(1=2,"A",2=2,"B",3=3,"C")'
    )
) == "B"

print("IFS first matching condition: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IFS(1=2,"A",2=3,"B")'
    )
) == "#VALUE!"

print("IFS no match: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IFS(1=2,"A",10>5,"B",3=3,"C")'
    )
) == "B"

print("IFS later matching condition: PASS")


# --------------------------------------------------
# IFS validation
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IFS(1=1,"A",2)'
    )
) == "#VALUE!"

print("IFS incomplete pair: PASS")


assert evaluator.evaluate(
    parser.parse(
        '=IFS()'
    )
) == "#VALUE!"

print("IFS empty: PASS")


# --------------------------------------------------
# IFS lazy evaluation
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse(
        '=IFS(1=1,10,1=1,10/0)'
    )
) == 10

print("IFS lazy evaluation: PASS")


# --------------------------------------------------
# Existing formula regression
# --------------------------------------------------

assert evaluator.evaluate(
    parser.parse("=10+5")
) == 15

print("Arithmetic regression: PASS")


assert evaluator.evaluate(
    parser.parse("=ABS(-10)")
) == 10

print("Math regression: PASS")


print("CONDITIONAL FUNCTIONS: PASS")