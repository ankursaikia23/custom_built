from .base import Command

class DeleteCellsCommand(Command):
    def __init__(self,sheet,references):
        self.sheet=sheet
        self.references=references
        self.old_values={}
        for reference in references:
            cell=sheet.get_cell(reference)
            self.old_values[reference]=cell.value if cell else None

    def execute(self):
        for reference in self.references:
            self.sheet.cells.pop(reference,None)

    def undo(self):
        for reference,value in self.old_values.items():
            if value is not None:
                self.sheet.set_cell(reference,value)