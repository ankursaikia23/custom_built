from core.workbook import Workbook

workbook=Workbook()
sheet1=workbook.add_sheet("Sheet1")
assert workbook.get_active_sheet() is sheet1
print("First sheet active: PASS")
sheet2=workbook.add_sheet("Sheet2")
sheet3=workbook.add_sheet("Sheet3")
assert workbook.sheet_names()==["Sheet1","Sheet2","Sheet3"]
print("Multiple sheets: PASS")
workbook.set_active_sheet("Sheet2")
assert workbook.get_active_sheet() is sheet2
print("Switch active sheet: PASS")
try:
    workbook.add_sheet("Sheet2")
except ValueError:
    print("Duplicate sheet rejected: PASS")
else:
    raise AssertionError("Duplicate sheet accepted")
workbook.delete_sheet("Sheet2")
assert workbook.sheet_names()==["Sheet1","Sheet3"]
print("Delete sheet: PASS")
assert workbook.get_active_sheet() is sheet1
print("Active sheet after deletion: PASS")
workbook.delete_sheet("Sheet1")
assert workbook.sheet_names()==["Sheet3"]
assert workbook.get_active_sheet() is sheet3
print("Delete active sheet: PASS")
try:
    workbook.delete_sheet("Sheet3")
except ValueError:
    print("Final sheet deletion rejected: PASS")
else:
    raise AssertionError("Final sheet deletion accepted")
try:
    workbook.set_active_sheet("Missing")
except ValueError:
    print("Missing sheet rejected: PASS")
else:
    raise AssertionError("Missing sheet accepted")