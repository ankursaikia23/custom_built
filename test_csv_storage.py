import os
import tempfile

from core.workbook import Workbook
from services.storage.csv_storage import CSVStorage


# --------------------------------------------------
# 1. Create workbook
# --------------------------------------------------

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

sheet.set_cell("A1", "Hello")
sheet.set_cell("B1", 123)
sheet.set_cell("C1", 45.5)

sheet.set_cell("A2", "World")
sheet.set_cell("B2", 999)

print("Create sheet: PASS")


# --------------------------------------------------
# 2. Save CSV
# --------------------------------------------------

with tempfile.TemporaryDirectory() as temp_dir:

    path = os.path.join(
        temp_dir,
        "test.csv"
    )

    CSVStorage.save(sheet, path)

    assert os.path.exists(path)

    print("Save CSV: PASS")


    # --------------------------------------------------
    # 3. Load CSV
    # --------------------------------------------------

    restored_workbook = Workbook()
    restored_sheet = restored_workbook.add_sheet(
        "Sheet1"
    )

    CSVStorage.load(
        restored_sheet,
        path
    )

    print("Load CSV: PASS")


    # --------------------------------------------------
    # 4. Verify values
    # --------------------------------------------------

    assert (
        restored_sheet
        .get_cell("A1")
        .value
        == "Hello"
    )

    assert (
        restored_sheet
        .get_cell("B1")
        .value
        == 123
    )

    assert (
        restored_sheet
        .get_cell("C1")
        .value
        == 45.5
    )

    assert (
        restored_sheet
        .get_cell("A2")
        .value
        == "World"
    )

    assert (
        restored_sheet
        .get_cell("B2")
        .value
        == 999
    )

    print("CSV values: PASS")


    # --------------------------------------------------
    # 5. Empty cells
    # --------------------------------------------------

    assert (
        restored_sheet
        .get_cell("D1")
        is None
    )

    print("Empty cells: PASS")


    # --------------------------------------------------
    # 6. Independent sheet
    # --------------------------------------------------

    restored_sheet.set_cell(
        "A1",
        "Changed"
    )

    assert (
        sheet
        .get_cell("A1")
        .value
        == "Hello"
    )

    print("Independent CSV load: PASS")


# --------------------------------------------------
# 7. Missing file
# --------------------------------------------------

try:
    CSVStorage.load(
        Workbook().add_sheet("Test"),
        "missing_file.csv"
    )

    raise AssertionError(
        "Missing CSV file was accepted"
    )

except FileNotFoundError:
    print("Missing CSV rejected: PASS")


print("CSV STORAGE: PASS")