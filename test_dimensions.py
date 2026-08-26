from core.workbook import Workbook

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
assert sheet.get_row_height(1)==20
assert sheet.get_column_width("A")==80
print("Default dimensions: PASS")
sheet.set_row_height(1,30)
sheet.set_column_width("A",120)
assert sheet.get_row_height(1)==30
assert sheet.get_column_width("A")==120
print("Custom dimensions: PASS")
sheet.set_default_row_height(25)
sheet.set_default_column_width(100)
assert sheet.get_row_height(2)==25
assert sheet.get_column_width("B")==100
print("Default dimension update: PASS")
sheet.set_row_height(3,40)
sheet.set_column_width("C",150)
sheet.insert_rows(2)
assert sheet.get_row_height(4)==40
assert sheet.get_row_height(3)==25
print("Row dimension shift: PASS")
sheet.delete_rows(2)
assert sheet.get_row_height(3)==40
print("Row dimension restore: PASS")
sheet.insert_columns(2)
assert sheet.get_column_width("D")==150
assert sheet.get_column_width("C")==100
print("Column dimension shift: PASS")
sheet.delete_columns(2)
assert sheet.get_column_width("C")==150
print("Column dimension restore: PASS")
for value in [0,-1]:
    try:
        sheet.set_row_height(1,value)
    except ValueError:
        print("Invalid row height rejected:",value)
    else:
        raise AssertionError("Invalid row height accepted")
    try:
        sheet.set_column_width("A",value)
    except ValueError:
        print("Invalid column width rejected:",value)
    else:
        raise AssertionError("Invalid column width accepted")