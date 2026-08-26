from core.workbook import Workbook
from commands.history import History
from commands.structural_commands import (
    InsertRowsCommand,
    DeleteRowsCommand,
    InsertColumnsCommand,
    DeleteColumnsCommand,
)


workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")
history = History()


# --------------------------------------------------
# 1. Insert rows
# --------------------------------------------------

sheet.set_cell("A1", "One")
sheet.set_cell("A2", "Two")
sheet.set_cell("A3", "Three")

history.execute(
    InsertRowsCommand(sheet, 2, 1)
)

assert sheet.get_cell("A1").value == "One"
assert sheet.get_cell("A3").value == "Two"
assert sheet.get_cell("A4").value == "Three"

print("Insert rows: PASS")


# --------------------------------------------------
# 2. Undo row insertion
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("A1").value == "One"
assert sheet.get_cell("A2").value == "Two"
assert sheet.get_cell("A3").value == "Three"

print("Undo row insertion: PASS")


# --------------------------------------------------
# 3. Redo row insertion
# --------------------------------------------------

assert history.redo() is True

assert sheet.get_cell("A3").value == "Two"
assert sheet.get_cell("A4").value == "Three"

print("Redo row insertion: PASS")


# --------------------------------------------------
# 4. Insert columns
# --------------------------------------------------

sheet.set_cell("B1", "B")
sheet.set_cell("C1", "C")

history.execute(
    InsertColumnsCommand(sheet, 2, 1)
)

assert sheet.get_cell("A1").value == "One"
assert sheet.get_cell("C1").value == "B"
assert sheet.get_cell("D1").value == "C"

print("Insert columns: PASS")


# --------------------------------------------------
# 5. Undo column insertion
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("B1").value == "B"
assert sheet.get_cell("C1").value == "C"

print("Undo column insertion: PASS")


# --------------------------------------------------
# 6. Redo column insertion
# --------------------------------------------------

assert history.redo() is True

assert sheet.get_cell("C1").value == "B"
assert sheet.get_cell("D1").value == "C"

print("Redo column insertion: PASS")


# --------------------------------------------------
# 7. Delete rows
# --------------------------------------------------

sheet.set_cell("A5", "Delete me")
sheet.set_cell("A6", "Keep me")

history.execute(
    DeleteRowsCommand(sheet, 5, 1)
)

assert sheet.get_cell("A5").value == "Keep me"

print("Delete rows: PASS")


# --------------------------------------------------
# 8. Undo row deletion
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("A5").value == "Delete me"
assert sheet.get_cell("A6").value == "Keep me"

print("Undo row deletion: PASS")


# --------------------------------------------------
# 9. Redo row deletion
# --------------------------------------------------

assert history.redo() is True

assert sheet.get_cell("A5").value == "Keep me"
assert sheet.get_cell("A6") is None

print("Redo row deletion: PASS")


# --------------------------------------------------
# 10. Delete columns
# --------------------------------------------------

history.execute(
    DeleteColumnsCommand(sheet, 3, 1)
)

assert sheet.get_cell("C1").value == "C"

print("Delete columns: PASS")


# --------------------------------------------------
# 11. Undo column deletion
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("C1").value == "B"
assert sheet.get_cell("D1").value == "C"

print("Undo column deletion: PASS")


# --------------------------------------------------
# 12. Redo column deletion
# --------------------------------------------------

assert history.redo() is True

assert sheet.get_cell("C1").value == "C"

print("Redo column deletion: PASS")


print("STRUCTURAL UNDO/REDO: PASS")