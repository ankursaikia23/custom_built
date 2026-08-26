from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
sheet.set_cell("A1","10")
sheet.set_cell("A2","20")
sheet.set_cell("A3","30")
sheet.set_cell("B1","5")
sheet.set_cell("B2","15")
parser=Parser()
evaluator=Evaluator(sheet)
tests={
    "=1+2":3,
    "=10-4":6,
    "=5*6":30,
    "=20/4":5,
    "=2^3":8,
    "=A1+B1":15,
    "=A1*10":100,
    "=A1+(B1*2)":20,
    "=SUM(A1:A3)":60,
    "=AVERAGE(A1:A3)":20,
    "=MIN(A1:A3)":10,
    "=MAX(A1:A3)":30,
    "=COUNT(A1:A3)":3,
    "=SUM(A1,B1,5)":20,
}
for formula,expected in tests.items():
    result=evaluator.evaluate(parser.parse(formula))
    print(formula,"=",result,"Expected:",expected)
    assert result==expected
for formula in ["=10/0","=1+@","=SUM(A1:A3"]:
    try:
        parser.parse(formula)
        if formula=="=10/0":
            evaluator.evaluate(parser.parse(formula))
            raise AssertionError("Division by zero was not detected")
        if formula=="=1+@":
            raise AssertionError("Invalid character was not detected")
        if formula=="=SUM(A1:A3":
            raise AssertionError("Missing parenthesis was not detected")
    except (ValueError,ZeroDivisionError):
        print(formula,"Error handling: PASS")