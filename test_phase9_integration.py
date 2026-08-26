from core.workbook import Workbook

workbook=Workbook()
sheet1=workbook.add_sheet("Data")
sheet2=workbook.add_sheet("Summary")
sheet1.set_cell("A1","Hello")
sheet1.set_cell("B2",123)
sheet1.set_row_height(2,35)
sheet1.set_column_width("B",120)
sheet1.hide_row(3)
sheet1.hide_column("C")
sheet1.merge_cells("A4","C5")
assert sheet1.get_cell("A1").value=="Hello"
assert sheet1.get_cell("B2").value==123
assert sheet1.get_row_height(2)==35
assert sheet1.get_column_width("B")==120
assert sheet1.is_row_hidden(3)
assert sheet1.is_column_hidden("C")
assert sheet1.is_merged("B5")
print("Initial combined state: PASS")
sheet1.insert_rows(2)
assert sheet1.get_cell("B3").value==123
assert sheet1.get_row_height(3)==35
assert sheet1.is_row_hidden(4)
assert ("A5","C6") in sheet1.merged_ranges
print("Row insertion integration: PASS")
sheet1.insert_columns(2)
assert sheet1.get_cell("C3").value==123
assert sheet1.get_column_width("C")==120
assert sheet1.is_column_hidden("D")
assert ("A5","D6") in sheet1.merged_ranges
print("Column insertion integration: PASS")
sheet1.delete_rows(2)
assert sheet1.get_cell("C2").value==123
assert sheet1.get_row_height(2)==35
assert sheet1.is_row_hidden(3)
assert ("A4","D5") in sheet1.merged_ranges
print("Row deletion integration: PASS")
sheet1.delete_columns(2)
assert sheet1.get_cell("B2").value==123
assert sheet1.get_column_width("B")==120
assert sheet1.is_column_hidden("C")
assert ("A4","C5") in sheet1.merged_ranges
print("Column deletion integration: PASS")
workbook.set_active_sheet("Summary")
workbook.rename_sheet("Summary","Reports")
workbook.move_sheet("Reports",0)
assert workbook.sheet_names()==["Reports","Data"]
assert workbook.get_active_sheet() is sheet2
print("Sheet management integration: PASS")
workbook.set_active_sheet("Data")
workbook.delete_sheet("Reports")
assert workbook.sheet_names()==["Data"]
assert workbook.get_active_sheet() is sheet1
print("Sheet deletion integration: PASS")
try:
    workbook.delete_sheet("Data")
except ValueError:
    print("Final sheet protection: PASS")
else:
    raise AssertionError("Final sheet deletion accepted")
print("PHASE 9 INTEGRATION: PASS")