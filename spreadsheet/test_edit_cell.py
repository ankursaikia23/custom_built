from core.workbook import Workbook
from commands.edit_cell import EditCellCommand
from commands.history import History

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
history=History()
command=EditCellCommand(sheet,"A1","Hello")
history.execute(command)
print("After edit:",sheet.get_cell("A1").value)
history.undo()
cell=sheet.get_cell("A1")
print("After undo:",cell.value if cell else None)
history.redo()
print("After redo:",sheet.get_cell("A1").value)
command=EditCellCommand(sheet,"A1","Updated")
history.execute(command)
print("After second edit:",sheet.get_cell("A1").value)
history.undo()
print("After second undo:",sheet.get_cell("A1").value)