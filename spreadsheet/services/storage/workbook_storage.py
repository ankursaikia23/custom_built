from pathlib import Path
from services.storage.csv_storage import CSVStorage
from services.storage.json_storage import JSONStorage

class WorkbookStorage:

    @staticmethod
    def save(workbook, path):
        path = Path(path)
        #csv_path = path.with_suffix(".csv")
        json_path = path.with_suffix(".json")

        # SAVE WORKBOOK METADATA AND FORMATTING
        JSONStorage.save(
            workbook,
            json_path
        )

        # SAVE EACH SHEET's CELL VALUES
        for sheet in workbook.sheets:
            sheet_csv_path = (
                path.parent
                / f"{path.stem}_{sheet.name}.csv"
            )
            CSVStorage.save(
                sheet,
                sheet_csv_path
            )

    @staticmethod
    def load(path):
        path = Path(path)
        json_path = path.with_suffix(".json")
        workbook = JSONStorage.load(
            json_path
        )

        # LOAD CELL VALUES FROM CSV FILES
        for sheet in workbook.sheets:
            sheet_csv_path = (
                path.parent
                / f"{path.stem}_{sheet.name}.csv"
            )
            if sheet_csv_path.exists():
                CSVStorage.load(
                    sheet,
                    sheet_csv_path
                )
        return workbook