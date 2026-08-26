from copy import deepcopy

class FormatCellCommand:
    def __init__(self, sheet, reference, changes):
        self.sheet = sheet
        self.reference = reference
        self.changes = changes
        self.before = None
        self.after = None

    def execute(self):
        cell = self.sheet.get_cell(self.reference)

        if cell is None:
            raise ValueError(
                f"Cell does not exist: {self.reference}"
            )

        if self.before is None:
            self.before = deepcopy(cell.format)

        for key, value in self.changes.items():
            setattr(cell.format, key, value)

        self.after = deepcopy(cell.format)

    def undo(self):
        cell = self.sheet.get_cell(self.reference)

        if cell is None:
            raise ValueError(
                f"Cell does not exist: {self.reference}"
            )

        cell.format = deepcopy(self.before)


class RowHeightCommand:
    def __init__(self, sheet, row, height):
        self.sheet = sheet
        self.row = row
        self.height = height
        self.before = None

    def execute(self):
        if self.before is None:
            self.before = self.sheet.get_row_height(self.row)

        self.sheet.set_row_height(self.row, self.height)

    def undo(self):
        self.sheet.set_row_height(self.row, self.before)


class ColumnWidthCommand:
    def __init__(self, sheet, column, width):
        self.sheet = sheet
        self.column = column
        self.width = width
        self.before = None

    def execute(self):
        if self.before is None:
            self.before = self.sheet.get_column_width(self.column)

        self.sheet.set_column_width(self.column, self.width)

    def undo(self):
        self.sheet.set_column_width(self.column, self.before)