from core.workbook import Workbook
from commands.copy_paste import Clipboard

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

sheet.set_cell("A1", "=1+2")
sheet.get_cell("A1").format.set_font("Calibri", 16, True)
sheet.get_cell("A1").format.set_colors("#FF0000", "#FFFF00")

sheet.set_cell("B1", "Original")
sheet.get_cell("B1").format.set_font("Arial", 10, False)

clipboard = Clipboard()

clipboard.copy(sheet, "A1", "A1")

clipboard.paste(sheet, "B1", "values")

assert sheet.get_cell("B1").value == "=1+2"
assert sheet.get_cell("B1").format.font_family == "Arial"
assert sheet.get_cell("B1").format.font_size == 10
assert sheet.get_cell("B1").format.bold is False
print("Values only: PASS")

sheet.set_cell("C1", "Keep me")
sheet.get_cell("C1").format.set_font("Arial", 11, False)

clipboard.paste(sheet, "C1", "formulas")

assert sheet.get_cell("C1").value == "=1+2"
assert sheet.get_cell("C1").format.font_family == "Arial"
assert sheet.get_cell("C1").format.font_size == 11
assert sheet.get_cell("C1").format.bold is False
print("Formulas only: PASS")

sheet.set_cell("D1", "Keep value")
sheet.get_cell("D1").format.set_font("Arial", 9, False)

clipboard.paste(sheet, "D1", "formatting")

assert sheet.get_cell("D1").value == "Keep value"
assert sheet.get_cell("D1").format.font_family == "Calibri"
assert sheet.get_cell("D1").format.font_size == 16
assert sheet.get_cell("D1").format.bold is True
assert sheet.get_cell("D1").format.text_color == "#FF0000"
assert sheet.get_cell("D1").format.background_color == "#FFFF00"
print("Formatting only: PASS")

try:
    clipboard.paste(sheet, "E1", "invalid")
except ValueError:
    print("Invalid paste mode rejected: PASS")
else:
    raise AssertionError("Invalid paste mode accepted")