from core.workbook import Workbook

workbook=Workbook()
sheet1=workbook.add_sheet("Sheet1")
sheet2=workbook.add_sheet("Sheet2")
sheet3=workbook.add_sheet("Sheet3")
assert workbook.sheet_names()==["Sheet1","Sheet2","Sheet3"]
print("Initial order: PASS")
workbook.rename_sheet("Sheet2","Data")
assert workbook.sheet_names()==["Sheet1","Data","Sheet3"]
assert workbook.get_sheet("Data") is sheet2
print("Rename sheet: PASS")
try:
    workbook.rename_sheet("Data","Sheet1")
except ValueError:
    print("Duplicate rename rejected: PASS")
else:
    raise AssertionError("Duplicate rename accepted")
workbook.set_active_sheet("Data")
workbook.move_sheet_left("Data")
assert workbook.sheet_names()==["Data","Sheet1","Sheet3"]
assert workbook.get_active_sheet() is sheet2
print("Move sheet left: PASS")
workbook.move_sheet_right("Data")
assert workbook.sheet_names()==["Sheet1","Data","Sheet3"]
assert workbook.get_active_sheet() is sheet2
print("Move sheet right: PASS")
workbook.move_sheet("Data",2)
assert workbook.sheet_names()==["Sheet1","Sheet3","Data"]
assert workbook.get_active_sheet() is sheet2
print("Move sheet to position: PASS")
workbook.move_sheet("Data",0)
assert workbook.sheet_names()==["Data","Sheet1","Sheet3"]
assert workbook.get_active_sheet() is sheet2
print("Move active sheet: PASS")
for name in ["", "A"*32, "Sheet:1", "Sheet/1", "Sheet*1"]:
    try:
        workbook.rename_sheet("Data",name)
    except ValueError:
        print("Invalid sheet name rejected:",repr(name))
    else:
        raise AssertionError("Invalid sheet name accepted")
try:
    workbook.move_sheet("Data",-1)
except ValueError:
    print("Invalid negative index rejected: PASS")
else:
    raise AssertionError("Invalid negative index accepted")
try:
    workbook.move_sheet("Data",10)
except ValueError:
    print("Invalid large index rejected: PASS")
else:
    raise AssertionError("Invalid large index accepted")