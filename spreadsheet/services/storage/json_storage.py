import json
from pathlib import Path
from services.storage.serializer import WorkbookSerializer

class JSONStorage:
    
    @staticmethod
    def save(workbook, path):
        path = Path(path)
        data = WorkbookSerializer.serialize(workbook)
        with path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

    @staticmethod
    def load(path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Workbook file not found: {path}"
            )
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError(
                "Invalid workbook JSON structure"
            )
        return WorkbookSerializer.deserialize(data)