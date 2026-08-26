from core.workbook import Workbook
from commands.edit_cell import EditCellCommand
from commands.history import History


workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")
history = History()


# --------------------------------------------------
# 1. Edit existing cell
# --------------------------------------------------

sheet.set_cell("A1", "Original")

history.execute(
    EditCellCommand(sheet, "A1", "Changed")
)

assert sheet.get_cell("A1").value == "Changed"
print("Edit existing cell: PASS")


# --------------------------------------------------
# 2. Undo existing cell edit
# --------------------------------------------------

assert history.undo() is True
assert sheet.get_cell("A1").value == "Original"
print("Undo existing cell edit: PASS")


# --------------------------------------------------
# 3. Redo existing cell edit
# --------------------------------------------------

assert history.redo() is True
assert sheet.get_cell("A1").value == "Changed"
print("Redo existing cell edit: PASS")


# --------------------------------------------------
# 4. Edit empty cell
# --------------------------------------------------

history.execute(
    EditCellCommand(sheet, "B1", "New cell")
)

assert sheet.get_cell("B1").value == "New cell"
print("Edit empty cell: PASS")


# --------------------------------------------------
# 5. Undo creation of new cell
# --------------------------------------------------

assert history.undo() is True
assert sheet.get_cell("B1") is None
print("Undo new cell creation: PASS")


# --------------------------------------------------
# 6. Redo creation of new cell
# --------------------------------------------------

assert history.redo() is True
assert sheet.get_cell("B1").value == "New cell"
print("Redo new cell creation: PASS")


# --------------------------------------------------
# 7. Multiple edits
# --------------------------------------------------

history.execute(
    EditCellCommand(sheet, "A1", "Second")
)

history.execute(
    EditCellCommand(sheet, "A1", "Third")
)

assert sheet.get_cell("A1").value == "Third"

assert history.undo() is True
assert sheet.get_cell("A1").value == "Second"

assert history.undo() is True
assert sheet.get_cell("A1").value == "Changed"

print("Multiple undo operations: PASS")


# --------------------------------------------------
# 8. Multiple redo operations
# --------------------------------------------------

assert history.redo() is True
assert sheet.get_cell("A1").value == "Second"

assert history.redo() is True
assert sheet.get_cell("A1").value == "Third"

print("Multiple redo operations: PASS")


print("CELL EDIT UNDO/REDO: PASS")