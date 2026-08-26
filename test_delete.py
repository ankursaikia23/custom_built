from core.workbook import Workbook
from commands.delete import DeleteCellsCommand
from commands.history import History

workbook=Workbook()
sheet=workbook.add_sheet("Sheet1")
sheet.set_cell("A1","Hello")
sheet.set_cell("B1","World")
sheet.set_cell("C1","123")
history=History()
command=DeleteCellsCommand(sheet,["A1","B1","C1"])
history.execute(command)
print("After delete:",sheet.get_cell("A1"),sheet.get_cell("B1"),sheet.get_cell("C1"))
history.undo()
print("After undo:",sheet.get_cell("A1").value,sheet.get_cell("B1").value,sheet.get_cell("C1").value)
history.redo()
print("After redo:",sheet.get_cell("A1"),sheet.get_cell("B1"),sheet.get_cell("C1"))