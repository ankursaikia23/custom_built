from core.workbook import Workbook
from commands.copy_paste import Clipboard

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
sheet.set_cell("A1","Hello")
sheet.set_cell("B1",123)
sheet.set_cell("A2","World")
sheet.get_cell("A1").format.set_font("Calibri",14,True)
sheet.get_cell("A1").format.set_colors("#FF0000","#FFFF00")
clipboard=Clipboard()
clipboard.copy(sheet,"A1","A1")
clipboard.paste(sheet,"C3")
assert sheet.get_cell("C3").value=="Hello"
assert sheet.get_cell("C3").format.bold is True
assert sheet.get_cell("C3").format.font_size==14
assert sheet.get_cell("C3").format.text_color=="#FF0000"
assert sheet.get_cell("C3").format.background_color=="#FFFF00"
print("Single cell copy/paste: PASS")
sheet.get_cell("C3").value="Changed"
assert sheet.get_cell("A1").value=="Hello"
assert sheet.get_cell("C3").value=="Changed"
print("Independent copy: PASS")
clipboard.copy(sheet,"A1","B2")
clipboard.paste(sheet,"D4")
assert sheet.get_cell("D4").value=="Hello"
assert sheet.get_cell("E4").value==123
assert sheet.get_cell("D5").value=="World"
print("Range copy/paste: PASS")
sheet.set_cell("A4","Original")
clipboard.copy(sheet,"A4","A4")
clipboard.paste(sheet,"B4")
assert sheet.get_cell("B4").value=="Original"
print("Second paste: PASS")
clipboard.clear()
try:
    clipboard.paste(sheet,"C1")
except ValueError:
    print("Empty clipboard rejected: PASS")
else:
    raise AssertionError("Empty clipboard accepted")
try:
    clipboard.copy(sheet,"B2","A1")
except ValueError:
    print("Invalid copy range rejected: PASS")
else:
    raise AssertionError("Invalid copy range accepted")