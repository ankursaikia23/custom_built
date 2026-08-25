from core.workbook import Workbook
from services.formula.parser import Parser
from services.formula.evaluator import Evaluator

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
sheet.set_cell("A1","10")
sheet.set_cell("A2","20")
sheet.set_cell("A3","30")
sheet.set_cell("A4","40")
parser=Parser()
evaluator=Evaluator(sheet)
tests={
    "=SUM(A1:A4)":100,
    "=AVERAGE(A1:A4)":25,
    "=MIN(A1:A4)":10,
    "=MAX(A1:A4)":40,
    "=COUNT(A1:A4)":4,
    "=SUM(A1,A2,5)":35,
}
for formula,expected in tests.items():
    result=evaluator.evaluate(parser.parse(formula))
    print(formula,"=",result,"Expected:",expected)
    assert result==expected