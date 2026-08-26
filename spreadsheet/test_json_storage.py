import os
import tempfile
from core.workbook import Workbook
from services.storage.json_storage import JSONStorage


# --------------------------------------------------
# 1. Create workbook
# --------------------------------------------------

workbook = Workbook()

sheet1 = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Sheet2")

sheet1.set_cell("A1", "Hello")
sheet1.set_cell("B1", 123)
sheet1.set_cell("C1", "=A1+B1")

sheet2.set_cell("A1", "Second sheet")

print("Create workbook: PASS")


# --------------------------------------------------
# 2. Save JSON
# --------------------------------------------------

with tempfile.TemporaryDirectory() as temp_dir:
    path = os.path.join(
        temp_dir,
        "test_workbook.json"
    )

    JSONStorage.save(workbook, path)

    assert os.path.exists(path)

    print("Save JSON: PASS")


    # --------------------------------------------------
    # 3. Load JSON
    # --------------------------------------------------

    restored = JSONStorage.load(path)

    assert restored is not None

    print("Load JSON: PASS")


    # --------------------------------------------------
    # 4. Verify sheet structure
    # --------------------------------------------------

    assert restored.get_sheet("Sheet1") is not None
    assert restored.get_sheet("Sheet2") is not None

    print("Sheet structure: PASS")


    # --------------------------------------------------
    # 5. Verify values
    # --------------------------------------------------

    restored_sheet1 = restored.get_sheet("Sheet1")
    restored_sheet2 = restored.get_sheet("Sheet2")

    assert restored_sheet1.get_cell("A1").value == "Hello"
    assert restored_sheet1.get_cell("B1").value == 123
    assert restored_sheet2.get_cell("A1").value == "Second sheet"

    print("Cell values: PASS")


    # --------------------------------------------------
    # 6. Verify formulas
    # --------------------------------------------------

    assert restored_sheet1.get_cell("C1").value == "=A1+B1"

    print("Formula preservation: PASS")


    # --------------------------------------------------
    # 7. Verify independent workbook
    # --------------------------------------------------

    restored_sheet1.set_cell("A1", "Changed")

    assert sheet1.get_cell("A1").value == "Hello"
    assert restored_sheet1.get_cell("A1").value == "Changed"

    print("Independent workbook: PASS")


# --------------------------------------------------
# 8. Missing file
# --------------------------------------------------

try:
    JSONStorage.load("definitely_missing_workbook.json")
    raise AssertionError("Missing file was accepted")

except FileNotFoundError:
    print("Missing file rejected: PASS")


print("JSON STORAGE: PASS")