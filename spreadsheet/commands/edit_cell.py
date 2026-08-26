class EditCellCommand:
    
    def __init__(self, sheet, reference, value):
        self.sheet = sheet
        self.reference = reference
        self.value = value
        self.old_value = None
        self.had_old_cell = False

    def execute(self):
        cell = self.sheet.get_cell(self.reference)

        if cell is None:
            self.had_old_cell = False
            self.old_value = None
        else:
            self.had_old_cell = True
            self.old_value = cell.value

        self.sheet.set_cell(self.reference, self.value)

    def undo(self):
        if self.had_old_cell:
            self.sheet.set_cell(self.reference, self.old_value)
        else:
            self.sheet.delete_cell(self.reference)