from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
sheet.set_cell("A1","10")
sheet.set_cell("B1","20")
sheet.set_cell("A2","5")
sheet.set_cell("B2","15")
parser=Parser()
evaluator=Evaluator(sheet)
tests={
    "=A1+B1":30,
    "=A1*10":100,
    "=A1-B1":-10,
    "=B1/A1":2,
}
for formula,expected in tests.items():
    result=evaluator.evaluate(parser.parse(formula))
    print(formula,"=",result,"Expected:",expected)
    assert result==expected
print("Range A1:B2:",evaluator.evaluate(parser.parse("=A1:B2")))