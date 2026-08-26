from core.workbook import Workbook
from commands.history import History
from commands.format_commands import (
    FormatCellCommand,
    RowHeightCommand,
    ColumnWidthCommand,
)


workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")
history = History()


# --------------------------------------------------
# 1. Cell formatting
# --------------------------------------------------

sheet.set_cell("A1", "Hello")

original_font = sheet.get_cell("A1").format.font_size
original_bold = sheet.get_cell("A1").format.bold

history.execute(
    FormatCellCommand(
        sheet,
        "A1",
        {
            "font_size": 18,
            "bold": True,
        },
    )
)

assert sheet.get_cell("A1").format.font_size == 18
assert sheet.get_cell("A1").format.bold is True

print("Format cell: PASS")


# --------------------------------------------------
# 2. Undo formatting
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("A1").format.font_size == original_font
assert sheet.get_cell("A1").format.bold == original_bold

print("Undo formatting: PASS")


# --------------------------------------------------
# 3. Redo formatting
# --------------------------------------------------

assert history.redo() is True

assert sheet.get_cell("A1").format.font_size == 18
assert sheet.get_cell("A1").format.bold is True

print("Redo formatting: PASS")


# --------------------------------------------------
# 4. Row height
# --------------------------------------------------

original_height = sheet.get_row_height(5)

history.execute(
    RowHeightCommand(sheet, 5, 35)
)

assert sheet.get_row_height(5) == 35

print("Row height change: PASS")


assert history.undo() is True

assert sheet.get_row_height(5) == original_height

print("Undo row height: PASS")


assert history.redo() is True

assert sheet.get_row_height(5) == 35

print("Redo row height: PASS")


# --------------------------------------------------
# 5. Column width
# --------------------------------------------------

original_width = sheet.get_column_width("C")

history.execute(
    ColumnWidthCommand(sheet, "C", 25)
)

assert sheet.get_column_width("C") == 25

print("Column width change: PASS")


assert history.undo() is True

assert sheet.get_column_width("C") == original_width

print("Undo column width: PASS")


assert history.redo() is True

assert sheet.get_column_width("C") == 25

print("Redo column width: PASS")


print("FORMAT/DIMENSION UNDO/REDO: PASS")