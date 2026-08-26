import csv
from pathlib import Path

class CSVStorage:

    @staticmethod
    def save(sheet, path):
        path = Path(path)

        max_row = 0
        max_column = 0

        for reference in sheet.cells:
            letters = ""
            numbers = ""

            for character in reference:
                if character.isalpha():
                    letters += character
                elif character.isdigit():
                    numbers += character

            if numbers:
                max_row = max(
                    max_row,
                    int(numbers)
                )

            if letters:
                column = 0

                for character in letters.upper():
                    column = (
                        column * 26
                        + ord(character) - ord("A") + 1
                    )

                max_column = max(
                    max_column,
                    column
                )

        with path.open(
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            for row in range(1, max_row + 1):
                values = []

                for column in range(
                    1,
                    max_column + 1
                ):
                    reference = CSVStorage._column_name(
                        column
                    ) + str(row)

                    cell = sheet.get_cell(reference)

                    if cell is None:
                        values.append("")
                    else:
                        values.append(
                            cell.value
                        )

                writer.writerow(values)

    @staticmethod
    def load(sheet, path):
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {path}"
            )

        with path.open(
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.reader(file)

            for row_number, row in enumerate(
                reader,
                start=1
            ):
                for column_number, value in enumerate(
                    row,
                    start=1
                ):
                    if value == "":
                        continue

                    reference = (
                        CSVStorage._column_name(
                            column_number
                        )
                        + str(row_number)
                    )

                    sheet.set_cell(
                        reference,
                        CSVStorage._convert_value(value)
                    )

    @staticmethod
    def _column_name(number):
        result = ""

        while number > 0:
            number, remainder = divmod(
                number - 1,
                26
            )

            result = (
                chr(ord("A") + remainder)
                + result
            )

        return result

    @staticmethod
    def _convert_value(value):
        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        return value