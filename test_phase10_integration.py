from core.workbook import Workbook
from commands.copy_paste import Clipboard
from commands.autofill import Autofill

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")
clipboard = Clipboard()
autofill = Autofill()
sheet.set_cell("A1", 10)
sheet.set_cell("A2", 20)
sheet.set_cell("B1", "=A1*2")
sheet.get_cell("A1").format.set_font("Calibri", 14, True)
sheet.get_cell("A1").format.set_colors("#FF0000", "#FFFF00")
assert sheet.get_cell("A1").value == 10
assert sheet.get_cell("A2").value == 20
assert sheet.get_cell("B1").value == "=A1*2"
print("Initial source state: PASS")
clipboard.copy(sheet, "A1", "B2")
clipboard.paste(sheet, "D4")
assert sheet.get_cell("D4").value == 10
assert sheet.get_cell("D5").value == 20
assert sheet.get_cell("E4").value == "=A1*2"
assert sheet.get_cell("D4").format.bold is True
assert sheet.get_cell("D4").format.font_size == 14
assert sheet.get_cell("D4").format.text_color == "#FF0000"
print("Range copy with formatting: PASS")
sheet.get_cell("D4").value = 999
sheet.get_cell("D4").format.set_font("Arial", 20, False)
assert sheet.get_cell("A1").value == 10
assert sheet.get_cell("A1").format.bold is True
assert sheet.get_cell("A1").format.font_size == 14
print("Independent copy: PASS")
sheet.set_cell("F1", "Move me")
sheet.set_cell("F2", "Also move")
clipboard.cut(sheet, "F1", "F2")
clipboard.paste(sheet, "G1")
assert sheet.get_cell("F1") is None
assert sheet.get_cell("F2") is None
assert sheet.get_cell("G1").value == "Move me"
assert sheet.get_cell("G2").value == "Also move"
print("Cut/paste range: PASS")
sheet.set_cell("A5", 10)
sheet.set_cell("A6", 20)
sheet.set_cell("B5", "=A5*2")
autofill.fill(sheet, "B5", "B8")
assert sheet.get_cell("B6").value == "=A6*2"
assert sheet.get_cell("B7").value == "=A7*2"
assert sheet.get_cell("B8").value == "=A8*2"
print("Formula autofill: PASS")
sheet.set_cell("D10", 1)
sheet.set_cell("D11", 2)
autofill.fill(sheet, "D10", "D15")
assert sheet.get_cell("D12").value == 3
assert sheet.get_cell("D13").value == 4
assert sheet.get_cell("D14").value == 5
assert sheet.get_cell("D15").value == 6
print("Numeric autofill: PASS")
sheet.set_cell("F5", "=1+2")
sheet.set_cell("G5", "Original")
clipboard.copy(sheet, "F5", "F5")
clipboard.paste(sheet, "G5", "values")
assert sheet.get_cell("G5").value == "=1+2"
print("Paste special values: PASS")
sheet.set_cell("H5", "Keep")
sheet.get_cell("H5").format.set_font("Arial", 9, False)
sheet.get_cell("F5").format.set_font("Calibri", 14, True)
sheet.get_cell("F5").format.set_colors("#FF0000", "#FFFF00")
clipboard.copy(sheet, "F5", "F5")
clipboard.paste(sheet, "H5", "formatting")
assert sheet.get_cell("H5").value == "Keep"
assert sheet.get_cell("H5").format.font_family == "Calibri"
assert sheet.get_cell("H5").format.font_size == 14
assert sheet.get_cell("H5").format.bold is True
print("Paste special formatting: PASS")
sheet.set_cell("I5", "Original")
sheet.get_cell("I5").format.set_font("Arial", 8, False)
clipboard.paste(sheet, "I5", "formulas")
assert sheet.get_cell("I5").value == "=1+2"
assert sheet.get_cell("I5").format.font_family == "Arial"
assert sheet.get_cell("I5").format.font_size == 8
assert sheet.get_cell("I5").format.bold is False
print("Paste special formulas: PASS")
sheet.get_cell("D4").value = "Changed again"
assert sheet.get_cell("A1").value == 10
assert sheet.get_cell("D4").value == "Changed again"
print("Final independence check: PASS")
print("PHASE 10 INTEGRATION: PASS")