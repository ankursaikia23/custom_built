from core.workbook import Workbook

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
sheet.set_cell("A1","Hello")
sheet.set_cell("B2","123")
sheet.set_cell("C3","ABC")
sheet.insert_rows(1)
assert sheet.get_cell("A2").value=="Hello"
assert sheet.get_cell("B3").value=="123"
assert sheet.get_cell("C4").value=="ABC"
print("Insert row: PASS")
sheet.delete_rows(1)
assert sheet.get_cell("A1").value=="Hello"
assert sheet.get_cell("B2").value=="123"
assert sheet.get_cell("C3").value=="ABC"
print("Delete row: PASS")
sheet.insert_columns(1)
assert sheet.get_cell("B1").value=="Hello"
assert sheet.get_cell("C2").value=="123"
assert sheet.get_cell("D3").value=="ABC"
print("Insert column: PASS")
sheet.delete_columns(1)
assert sheet.get_cell("A1").value=="Hello"
assert sheet.get_cell("B2").value=="123"
assert sheet.get_cell("C3").value=="ABC"
print("Delete column: PASS")
sheet.insert_rows(2,2)
assert sheet.get_cell("A1").value=="Hello"
assert sheet.get_cell("B4").value=="123"
assert sheet.get_cell("C5").value=="ABC"
print("Insert multiple rows: PASS")
sheet.delete_rows(2,2)
assert sheet.get_cell("A1").value=="Hello"
assert sheet.get_cell("B2").value=="123"
assert sheet.get_cell("C3").value=="ABC"
print("Delete multiple rows: PASS")
sheet.insert_columns(2,2)
assert sheet.get_cell("A1").value=="Hello"
assert sheet.get_cell("D2").value=="123"
assert sheet.get_cell("E3").value=="ABC"
print("Insert multiple columns: PASS")
sheet.delete_columns(2,2)
assert sheet.get_cell("A1").value=="Hello"
assert sheet.get_cell("B2").value=="123"
assert sheet.get_cell("C3").value=="ABC"
print("Delete multiple columns: PASS")