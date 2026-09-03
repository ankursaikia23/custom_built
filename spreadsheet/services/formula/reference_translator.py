import re

class ReferenceTranslator:
    CELL_REFERENCE_PATTERN = re.compile(
        r"(?P<sheet>'[^']+'!|[A-Za-z_][A-Za-z0-9_ ]*!|)"
        r"(?P<column>\$?[A-Za-z]+)"
        r"(?P<row>\$?\d+)"
    )

    def translate(
        self,
        formula,
        row_offset,
        column_offset
    ):
        if not isinstance(formula, str):
            return formula
        if not formula.startswith("="):
            return formula

        def replace_reference(match):
            sheet = match.group("sheet")
            column = match.group("column")
            row = match.group("row")

            # COLUMN
            if column.startswith("$"):
                new_column = column
            else:
                column_name = column.upper()
                column_number = self.column_number(
                    column_name
                )
                column_number += column_offset
                if column_number < 1:
                    column_number = 1
                new_column = self.column_name(
                    column_number
                )

            # ROW
            if row.startswith("$"):
                new_row = row
            else:
                row_number = int(row)
                row_number += row_offset
                if row_number < 1:
                    row_number = 1
                new_row = str(row_number)
            return (
                f"{sheet}"
                f"{new_column}"
                f"{new_row}"
            )
        return self.CELL_REFERENCE_PATTERN.sub(
            replace_reference,
            formula
        )

    def column_number(self, column):
        result = 0
        for letter in column.upper():
            result = (
                result * 26
                + (ord(letter) - 64)
            )
        return result

    def column_name(self, column):
        result = ""
        while column:
            column, remainder = divmod(
                column - 1,
                26
            )
            result = (
                chr(65 + remainder)
                + result
            )
        return result