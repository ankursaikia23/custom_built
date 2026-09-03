from copy import deepcopy

class PasteCommand:
    def __init__(self, clipboard, sheet, destination_reference, mode="all"):
        self.clipboard = clipboard
        self.sheet = sheet
        self.destination_reference = destination_reference
        self.mode = mode
        self.source_cells = None
        self.source_start = None
        self.source_end = None
        self.cut_mode = False
        self.before_destination = None

    def execute(self):
        # CAPTURE THE CLIPBOARD OPERATION ONLY INCE
        if self.source_cells is None:
            if not self.clipboard.cells:
                raise ValueError("Clipboard is empty")
            self.source_cells = deepcopy(self.clipboard.cells)
            self.source_start = self.clipboard.source_start
            self.source_end = self.clipboard.source_end
            self.cut_mode = self.clipboard.cut_mode
            self.before_destination = self._capture_destination()
        self._perform_paste()

    def undo(self):
        self._clear_destination()
        self._restore_destination(self.before_destination)
        if self.cut_mode:
            self._restore_source()

    def _perform_paste(self):
        destination_column, destination_row = self.sheet.split_reference(
            self.destination_reference
        )
        destination_column_number = self.sheet.column_number(
            destination_column
        )
        for (column_offset, row_offset), source_cell in self.source_cells.items():
            column_number = (
                destination_column_number + column_offset
            )
            row = destination_row + row_offset
            reference = (
                f"{self.sheet.column_name(column_number)}{row}"
            )
            if self.mode == "all":
                copied_cell = deepcopy(source_cell)
                copied_cell.reference = reference
                self.sheet.cells[reference] = copied_cell
            elif self.mode == "values":
                destination_cell = self.sheet.get_cell(reference)
                if destination_cell is None:
                    copied_cell = deepcopy(source_cell)
                    copied_cell.value = source_cell.value
                    copied_cell.reference = reference
                    self.sheet.cells[reference] = copied_cell
                else:
                    destination_cell.value = source_cell.value
            elif self.mode == "formulas":
                if (
                    isinstance(source_cell.value, str)
                    and source_cell.value.startswith("=")
                ):
                    destination_cell = self.sheet.get_cell(reference)
                    if destination_cell is None:
                        copied_cell = deepcopy(source_cell)
                        copied_cell.reference = reference
                        self.sheet.cells[reference] = copied_cell
                    else:
                        destination_cell.value = source_cell.value
            elif self.mode == "formatting":
                destination_cell = self.sheet.get_cell(reference)
                if destination_cell is None:
                    copied_cell = deepcopy(source_cell)
                    copied_cell.value = None
                    copied_cell.reference = reference
                    self.sheet.cells[reference] = copied_cell
                else:
                    destination_cell.format = deepcopy(
                        source_cell.format
                    )
            else:
                raise ValueError("Invalid paste mode")
        if self.cut_mode:
            self._clear_source()

    def _capture_destination(self):
        destination_column, destination_row = self.sheet.split_reference(
            self.destination_reference
        )
        destination_column_number = self.sheet.column_number(
            destination_column
        )
        snapshot = {}
        for (column_offset, row_offset) in self.source_cells:
            column_number = (
                destination_column_number + column_offset
            )
            row = destination_row + row_offset
            reference = (
                f"{self.sheet.column_name(column_number)}{row}"
            )
            cell = self.sheet.get_cell(reference)
            if cell is not None:
                snapshot[reference] = deepcopy(cell)
        return snapshot

    def _clear_destination(self):
        destination_column, destination_row = self.sheet.split_reference(
            self.destination_reference
        )
        destination_column_number = self.sheet.column_number(
            destination_column
        )
        for (column_offset, row_offset) in self.source_cells:
            column_number = (
                destination_column_number + column_offset
            )
            row = destination_row + row_offset
            reference = (
                f"{self.sheet.column_name(column_number)}{row}"
            )
            self.sheet.delete_cell(reference)

    def _restore_destination(self, snapshot):
        for reference, cell in snapshot.items():
            self.sheet.cells[reference] = deepcopy(cell)

    def _capture_source(self):
        snapshot = {}
        start_column, start_row = self.source_start
        end_column, end_row = self.source_end
        for row in range(start_row, end_row + 1):
            for column_number in range(
                start_column,
                end_column + 1
            ):
                reference = (
                    f"{self.sheet.column_name(column_number)}{row}"
                )
                cell = self.sheet.get_cell(reference)
                if cell is not None:
                    snapshot[reference] = deepcopy(cell)
        return snapshot

    def _restore_source(self):
        # SOURCE CELLS ARE ALREADY CONTAINED IN SOURCE_CELLS
        # BUT WE NEED THEIR ORIGINAL REFERENCES
        start_column, start_row = self.source_start
        for (column_offset, row_offset), cell in self.source_cells.items():
            column_number = start_column + column_offset
            row = start_row + row_offset
            reference = (
                f"{self.sheet.column_name(column_number)}{row}"
            )
            restored_cell = deepcopy(cell)
            restored_cell.reference = reference
            self.sheet.cells[reference] = restored_cell

    def _clear_source(self):
        start_column, start_row = self.source_start
        end_column, end_row = self.source_end
        for row in range(start_row, end_row + 1):
            for column_number in range(
                start_column,
                end_column + 1
            ):
                reference = (
                    f"{self.sheet.column_name(column_number)}{row}"
                )
                self.sheet.delete_cell(reference)