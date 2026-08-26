from core.workbook import Workbook

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
sheet.hide_row(2)
sheet.hide_column("B")
assert sheet.is_row_hidden(2) is True
assert sheet.is_column_hidden("B") is True
print("Hide row/column: PASS")
sheet.show_row(2)
sheet.show_column("B")
assert sheet.is_row_hidden(2) is False
assert sheet.is_column_hidden("B") is False
print("Show row/column: PASS")
sheet.hide_row(3)
sheet.hide_column("C")
sheet.insert_rows(2)
assert sheet.is_row_hidden(4) is True
print("Hidden row shift: PASS")
sheet.delete_rows(2)
assert sheet.is_row_hidden(3) is True
print("Hidden row restore: PASS")
sheet.insert_columns(2)
assert sheet.is_column_hidden("D") is True
print("Hidden column shift: PASS")
sheet.delete_columns(2)
assert sheet.is_column_hidden("C") is True
print("Hidden column restore: PASS")
for row in [0,-1]:
    try:
        sheet.hide_row(row)
    except ValueError:
        print("Invalid row rejected:",row)
    else:
        raise AssertionError("Invalid row accepted")
for column in ["","1","@"]:
    try:
        sheet.hide_column(column)
    except ValueError:
        print("Invalid column rejected:",column)
    else:
        raise AssertionError("Invalid column accepted")