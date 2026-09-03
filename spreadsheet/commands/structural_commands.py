from copy import deepcopy

class InsertRowsCommand:
    def __init__(self, sheet, row, count=1):
        self.sheet = sheet
        self.row = row
        self.count = count
        self.before = None

    def execute(self):
        if self.before is None:
            self.before = deepcopy(self.sheet.cells)
        self.sheet.insert_rows(self.row, self.count)

    def undo(self):
        self.sheet.cells = deepcopy(self.before)

class DeleteRowsCommand:
    def __init__(self, sheet, row, count=1):
        self.sheet = sheet
        self.row = row
        self.count = count
        self.before = None

    def execute(self):
        if self.before is None:
            self.before = deepcopy(self.sheet.cells)
        self.sheet.delete_rows(self.row, self.count)

    def undo(self):
        self.sheet.cells = deepcopy(self.before)

class InsertColumnsCommand:
    def __init__(self, sheet, column, count=1):
        self.sheet = sheet
        self.column = column
        self.count = count
        self.before = None

    def execute(self):
        if self.before is None:
            self.before = deepcopy(self.sheet.cells)
        self.sheet.insert_columns(self.column, self.count)

    def undo(self):
        self.sheet.cells = deepcopy(self.before)

class DeleteColumnsCommand:
    def __init__(self, sheet, column, count=1):
        self.sheet = sheet
        self.column = column
        self.count = count
        self.before = None

    def execute(self):
        if self.before is None:
            self.before = deepcopy(self.sheet.cells)
        self.sheet.delete_columns(self.column, self.count)

    def undo(self):
        self.sheet.cells = deepcopy(self.before)