from .base import Command

class EditCellCommand(Command):
    def __init__(self,sheet,reference,new_value):
        self.sheet=sheet
        self.reference=reference
        self.new_value=new_value
        cell=sheet.get_cell(reference)
        self.old_value=cell.value if cell else None

    def execute(self):
        self.sheet.set_cell(self.reference,self.new_value)

    def undo(self):
        if self.old_value is None:
            self.sheet.cells.pop(self.reference,None)
        else:
            self.sheet.set_cell(self.reference,self.old_value)