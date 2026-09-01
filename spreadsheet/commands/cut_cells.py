from .base import Command
from copy import deepcopy


class CutCellsCommand(Command):

    def __init__(
        self,
        clipboard,
        sheet,
        destination_reference
    ):
        self.clipboard = clipboard
        self.sheet = sheet
        self.destination_reference = destination_reference
        self.old_cells = {}
        self.source_cells = {}

    def execute(self):

        self.old_cells = {}
        self.source_cells = {}

        destination_column, destination_row = (
            self.sheet.split_reference(
                self.destination_reference
            )
        )

        destination_column_number = (
            self.sheet.column_number(
                destination_column
            )
        )

        # Save destination cells
        for (
            column_offset,
            row_offset
        ), source_cell in self.clipboard.cells.items():

            new_column_number = (
                destination_column_number
                + column_offset
            )

            new_row = (
                destination_row
                + row_offset
            )

            reference = (
                f"{self.sheet.column_name(new_column_number)}"
                f"{new_row}"
            )

            existing_cell = self.sheet.get_cell(
                reference
            )

            self.old_cells[reference] = (
                deepcopy(existing_cell)
                if existing_cell is not None
                else None
            )

            copied_cell = deepcopy(source_cell)
            copied_cell.reference = reference

            self.sheet.cells[reference] = copied_cell

        # Save and remove source cells
        source_start_column, source_start_row = (
            self.clipboard.source_start
        )

        source_end_column, source_end_row = (
            self.clipboard.source_end
        )

        for row in range(
            source_start_row,
            source_end_row + 1
        ):
            for column_number in range(
                source_start_column,
                source_end_column + 1
            ):

                reference = (
                    f"{self.sheet.column_name(column_number)}"
                    f"{row}"
                )

                cell = self.sheet.get_cell(
                    reference
                )

                self.source_cells[reference] = (
                    deepcopy(cell)
                    if cell is not None
                    else None
                )

                self.sheet.delete_cell(
                    reference
                )

    def undo(self):

        # Remove pasted cells
        for reference in self.old_cells:

            old_cell = self.old_cells[reference]

            if old_cell is None:
                self.sheet.delete_cell(
                    reference
                )
            else:
                self.sheet.cells[reference] = (
                    deepcopy(old_cell)
                )

        # Restore source cells
        for reference, cell in self.source_cells.items():

            if cell is not None:
                self.sheet.cells[reference] = (
                    deepcopy(cell)
                )