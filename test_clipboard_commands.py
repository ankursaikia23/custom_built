from core.workbook import Workbook
from commands.copy_paste import Clipboard
from commands.clipboard_commands import PasteCommand
from commands.history import History


workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

clipboard = Clipboard()
history = History()


# --------------------------------------------------
# 1. Copy and paste
# --------------------------------------------------

sheet.set_cell("A1", "Hello")
sheet.set_cell("B1", 123)

clipboard.copy(sheet, "A1", "B1")

command = PasteCommand(
    clipboard,
    sheet,
    "D1"
)

history.execute(command)

assert sheet.get_cell("D1").value == "Hello"
assert sheet.get_cell("E1").value == 123

print("Paste command: PASS")


# --------------------------------------------------
# 2. Undo paste
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("D1") is None
assert sheet.get_cell("E1") is None

print("Undo paste: PASS")


# --------------------------------------------------
# 3. Redo paste
# --------------------------------------------------

assert history.redo() is True

assert sheet.get_cell("D1").value == "Hello"
assert sheet.get_cell("E1").value == 123

print("Redo paste: PASS")


# --------------------------------------------------
# 4. Existing destination restoration
# --------------------------------------------------

sheet.set_cell("F1", "Original")

clipboard.copy(sheet, "A1", "A1")

command = PasteCommand(
    clipboard,
    sheet,
    "F1"
)

history.execute(command)

assert sheet.get_cell("F1").value == "Hello"

assert history.undo() is True

assert sheet.get_cell("F1").value == "Original"

print("Destination restoration: PASS")


# --------------------------------------------------
# 5. Cut/paste
# --------------------------------------------------

sheet.set_cell("A3", "Move me")
sheet.set_cell("B3", "Also move")

clipboard.cut(sheet, "A3", "B3")

command = PasteCommand(
    clipboard,
    sheet,
    "D3"
)

history.execute(command)

assert sheet.get_cell("D3").value == "Move me"
assert sheet.get_cell("E3").value == "Also move"

print("Cut/paste command: PASS")


# --------------------------------------------------
# 6. Undo cut/paste
# --------------------------------------------------

assert history.undo() is True

assert sheet.get_cell("D3") is None
assert sheet.get_cell("E3") is None

print("Undo cut/paste: PASS")


# --------------------------------------------------
# 7. Redo cut/paste
# --------------------------------------------------

assert history.redo() is True

assert sheet.get_cell("D3").value == "Move me"
assert sheet.get_cell("E3").value == "Also move"

print("Redo cut/paste: PASS")


print("CLIPBOARD UNDO/REDO: PASS")