from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

parser=Parser()
evaluator=Evaluator()
tests={
    "=1+2":3,
    "=10-4":6,
    "=5*6":30,
    "=20/4":5,
    "=2^3":8,
    "=1+2*3":7,
    "=(1+2)*3":9,
    "=10/(2+3)":2,
}
for formula,expected in tests.items():
    result=evaluator.evaluate(parser.parse(formula))
    print(formula,"=",result,"Expected:",expected)
    assert result==expected
try:
    evaluator.evaluate(parser.parse("=10/0"))
except ZeroDivisionError:
    print("Division by zero: PASS")
else:
    raise AssertionError("Division by zero was not detected")