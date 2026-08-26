from core.workbook import Workbook

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
sheet.set_cell("A1","Merged")
sheet.merge_cells("A1","C2")
assert ("A1","C2") in sheet.merged_ranges
assert sheet.is_merged("A1") is True
assert sheet.is_merged("B1") is True
assert sheet.is_merged("C2") is True
assert sheet.is_merged("D2") is False
assert sheet.get_merge_range("B1")==("A1","C2")
print("Merge cells: PASS")
sheet.unmerge_cells("A1","C2")
assert ("A1","C2") not in sheet.merged_ranges
assert sheet.is_merged("A1") is False
print("Unmerge cells: PASS")
sheet.merge_cells("A1","B2")
try:
    sheet.merge_cells("B2","C3")
except ValueError:
    print("Overlapping merge rejected: PASS")
else:
    raise AssertionError("Overlapping merge accepted")
try:
    sheet.merge_cells("C3","A1")
except ValueError:
    print("Invalid merge range rejected: PASS")
else:
    raise AssertionError("Invalid merge range accepted")
sheet.merge_cells("A1","B2")
sheet.insert_rows(1)
assert ("A2","B3") in sheet.merged_ranges
print("Merge row shift: PASS")
sheet.delete_rows(1)
assert ("A1","B2") in sheet.merged_ranges
print("Merge row restore: PASS")
sheet.insert_columns(1)
assert ("B1","C2") in sheet.merged_ranges
print("Merge column shift: PASS")
sheet.delete_columns(1)
assert ("A1","B2") in sheet.merged_ranges
print("Merge column restore: PASS")