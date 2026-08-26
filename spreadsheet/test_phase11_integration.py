from core.workbook import Workbook
from commands.history import History
from commands.edit_cell import EditCellCommand
from commands.format_commands import (
    FormatCellCommand,
    RowHeightCommand,
    ColumnWidthCommand,
)
from commands.structural_commands import InsertRowsCommand


workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")
history = History()


# --------------------------------------------------
# 1. Cell edit
# --------------------------------------------------

sheet.set_cell("A1", "Original")

history.execute(
    EditCellCommand(sheet, "A1", "Edited")
)

assert sheet.get_cell("A1").value == "Edited"

print("Cell edit: PASS")


# --------------------------------------------------
# 2. Formatting
# --------------------------------------------------

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

print("Formatting: PASS")


# --------------------------------------------------
# 3. Row dimension
# --------------------------------------------------

history.execute(
    RowHeightCommand(sheet, 3, 35)
)

assert sheet.get_row_height(3) == 35

print("Row dimension: PASS")


# --------------------------------------------------
# 4. Column dimension
# --------------------------------------------------

history.execute(
    ColumnWidthCommand(sheet, "C", 25)
)

assert sheet.get_column_width("C") == 25

print("Column dimension: PASS")


# --------------------------------------------------
# 5. Structural operation
# --------------------------------------------------

sheet.set_cell("A3", "Before insertion")

history.execute(
    InsertRowsCommand(sheet, 3, 1)
)

assert sheet.get_cell("A4").value == "Before insertion"

print("Structural operation: PASS")


# --------------------------------------------------
# 6. Undo structural operation
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("A3").value == "Before insertion"

print("Undo structural operation: PASS")


# --------------------------------------------------
# 7. Undo column dimension
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_column_width("C") != 25

print("Undo column dimension: PASS")


# --------------------------------------------------
# 8. Undo row dimension
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_row_height(3) != 35

print("Undo row dimension: PASS")


# --------------------------------------------------
# 9. Undo formatting
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("A1").format.font_size != 18
assert sheet.get_cell("A1").format.bold is not True

print("Undo formatting: PASS")


# --------------------------------------------------
# 10. Undo cell edit
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("A1").value == "Original"

print("Undo cell edit: PASS")


# --------------------------------------------------
# 11. Nothing left to undo
# --------------------------------------------------

assert history.undo() is False

print("Empty undo stack: PASS")


# --------------------------------------------------
# 12. Redo everything
# --------------------------------------------------

assert history.redo() is True
assert sheet.get_cell("A1").value == "Edited"

assert history.redo() is True
assert sheet.get_cell("A1").format.font_size == 18

assert history.redo() is True
assert sheet.get_row_height(3) == 35

assert history.redo() is True
assert sheet.get_column_width("C") == 25

assert history.redo() is True
assert sheet.get_cell("A4").value == "Before insertion"

print("Full redo sequence: PASS")


# --------------------------------------------------
# 13. Nothing left to redo
# --------------------------------------------------

assert history.redo() is False

print("Empty redo stack: PASS")


# --------------------------------------------------
# 14. New command invalidates redo
# --------------------------------------------------

assert history.undo() is True

history.execute(
    EditCellCommand(sheet, "B1", "New command")
)

assert history.can_redo() is False

print("Redo invalidation: PASS")


# --------------------------------------------------
# FINAL
# --------------------------------------------------

print("PHASE 11 INTEGRATION: PASS")