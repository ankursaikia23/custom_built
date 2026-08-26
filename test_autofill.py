from core.workbook import Workbook
from commands.autofill import Autofill

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
autofill=Autofill()
sheet.set_cell("A1",1)
sheet.set_cell("A2",2)
autofill.fill(sheet,"A1","A5")
assert sheet.get_cell("A3").value==3
assert sheet.get_cell("A4").value==4
assert sheet.get_cell("A5").value==5
print("Vertical number sequence: PASS")
sheet.set_cell("C1",10)
sheet.set_cell("D1",20)
autofill.fill(sheet,"C1","G1")
assert sheet.get_cell("E1").value==30
assert sheet.get_cell("F1").value==40
assert sheet.get_cell("G1").value==50
print("Horizontal number sequence: PASS")
sheet.set_cell("A7","Hello")
autofill.fill(sheet,"A7","A9")
assert sheet.get_cell("A8").value=="Hello"
assert sheet.get_cell("A9").value=="Hello"
print("Text repetition: PASS")
sheet.set_cell("C3","=A3+B3")
autofill.fill(sheet,"C3","C6")
assert sheet.get_cell("C4").value=="=A4+B4"
assert sheet.get_cell("C5").value=="=A5+B5"
assert sheet.get_cell("C6").value=="=A6+B6"
print("Vertical formula autofill: PASS")
sheet.set_cell("E3","=A3+B3")
autofill.fill(sheet,"E3","H3")
assert sheet.get_cell("F3").value=="=B3+C3"
assert sheet.get_cell("G3").value=="=C3+D3"
assert sheet.get_cell("H3").value=="=D3+E3"
print("Horizontal formula autofill: PASS")
sheet.set_cell("A11",100)
sheet.get_cell("A11").format.set_font("Calibri",16,True)
sheet.get_cell("A11").format.set_colors("#FF0000","#FFFF00")
autofill.fill(sheet,"A11","A12")
assert sheet.get_cell("A12").value==100
assert sheet.get_cell("A12").format.bold is True
assert sheet.get_cell("A12").format.font_size==16
assert sheet.get_cell("A12").format.text_color=="#FF0000"
assert sheet.get_cell("A12").format.background_color=="#FFFF00"
print("Formatting autofill: PASS")