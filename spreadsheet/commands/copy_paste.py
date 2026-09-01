from copy import deepcopy


class Clipboard:

    def __init__(self):
        self.cells = {}
        self.source_start = None
        self.source_end = None
        self.cut_mode = False

    def clear(self):
        self.cells = {}
        self.source_start = None
        self.source_end = None
        self.cut_mode = False

    def copy(
        self,
        sheet,
        start_reference,
        end_reference
    ):
        self._capture(
            sheet,
            start_reference,
            end_reference,
            False
        )

    def cut(
        self,
        sheet,
        start_reference,
        end_reference
    ):
        self._capture(
            sheet,
            start_reference,
            end_reference,
            True
        )

    def _capture(
        self,
        sheet,
        start_reference,
        end_reference,
        cut_mode
    ):

        start_column, start_row = (
            sheet.split_reference(start_reference)
        )

        end_column, end_row = (
            sheet.split_reference(end_reference)
        )

        start_column_number = (
            sheet.column_number(start_column)
        )

        end_column_number = (
            sheet.column_number(end_column)
        )

        if (
            start_row > end_row
            or start_column_number > end_column_number
        ):
            raise ValueError(
                "Invalid copy range"
            )

        self.clear()

        self.source_start = (
            start_column_number,
            start_row
        )

        self.source_end = (
            end_column_number,
            end_row
        )

        self.cut_mode = cut_mode

        for row in range(
            start_row,
            end_row + 1
        ):

            for column_number in range(
                start_column_number,
                end_column_number + 1
            ):

                column = sheet.column_name(
                    column_number
                )

                reference = (
                    f"{column}{row}"
                )

                cell = sheet.get_cell(
                    reference
                )

                if cell is not None:

                    self.cells[
                        (
                            column_number
                            - start_column_number,
                            row - start_row
                        )
                    ] = deepcopy(cell)

    def paste(
        self,
        sheet,
        destination_reference,
        mode="all"
    ):

        if not self.cells:
            raise ValueError(
                "Clipboard is empty"
            )

        if mode not in (
            "all",
            "values",
            "formulas",
            "formatting"
        ):
            raise ValueError(
                "Invalid paste mode"
            )

        destination_column, destination_row = (
            sheet.split_reference(
                destination_reference
            )
        )

        destination_column_number = (
            sheet.column_number(
                destination_column
            )
        )

        for (
            column_offset,
            row_offset
        ), source_cell in self.cells.items():

            new_column_number = (
                destination_column_number
                + column_offset
            )

            new_row = (
                destination_row
                + row_offset
            )

            new_reference = (
                f"{sheet.column_name(new_column_number)}"
                f"{new_row}"
            )

            destination_cell = (
                sheet.get_cell(new_reference)
            )

            if mode == "all":

                copied_cell = deepcopy(
                    source_cell
                )

                copied_cell.reference = (
                    new_reference
                )

                sheet.cells[
                    new_reference
                ] = copied_cell

            elif mode == "values":

                if destination_cell is None:

                    copied_cell = deepcopy(
                        source_cell
                    )

                    copied_cell.value = (
                        source_cell.value
                    )

                    copied_cell.reference = (
                        new_reference
                    )

                    sheet.cells[
                        new_reference
                    ] = copied_cell

                else:

                    destination_cell.value = (
                        source_cell.value
                    )

            elif mode == "formulas":

                if not (
                    isinstance(
                        source_cell.value,
                        str
                    )
                    and source_cell.value.startswith("=")
                ):
                    continue

                if destination_cell is None:

                    copied_cell = deepcopy(
                        source_cell
                    )

                    copied_cell.value = (
                        source_cell.value
                    )

                    copied_cell.reference = (
                        new_reference
                    )

                    sheet.cells[
                        new_reference
                    ] = copied_cell

                else:

                    destination_cell.value = (
                        source_cell.value
                    )

            elif mode == "formatting":

                if destination_cell is None:

                    copied_cell = deepcopy(
                        source_cell
                    )

                    copied_cell.value = None

                    copied_cell.reference = (
                        new_reference
                    )

                    sheet.cells[
                        new_reference
                    ] = copied_cell

                else:

                    destination_cell.format = (
                        deepcopy(
                            source_cell.format
                        )
                    )

        if self.cut_mode and mode == "all":

            (
                source_start_column,
                source_start_row
            ) = self.source_start

            (
                source_end_column,
                source_end_row
            ) = self.source_end

            for row in range(
                source_start_row,
                source_end_row + 1
            ):

                for column_number in range(
                    source_start_column,
                    source_end_column + 1
                ):

                    reference = (
                        f"{sheet.column_name(column_number)}"
                        f"{row}"
                    )

                    sheet.delete_cell(
                        reference
                    )

            self.clear()