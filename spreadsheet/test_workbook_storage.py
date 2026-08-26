import os
import tempfile

from core.workbook import Workbook
from services.storage.workbook_storage import (
    WorkbookStorage,
)


# --------------------------------------------------
# 1. Create workbook
# --------------------------------------------------

workbook = Workbook()

sheet1 = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Data")

sheet1.set_cell("A1", "Hello")
sheet1.set_cell("B1", 123)
sheet1.set_cell("C1", "=1+2")

sheet2.set_cell("A1", 500)
sheet2.set_cell("B1", "Data")

# Formatting
cell = sheet1.get_cell("A1")

cell.format.set_font(
    family="Calibri",
    size=16,
    bold=True,
)

cell.format.set_colors(
    text_color="#FF0000",
    background_color="#FFFF00",
)

# Dimensions
sheet1.set_row_height(3, 35)
sheet1.set_column_width("B", 25)

# Active sheet
workbook.set_active_sheet("Data")

print("Create workbook: PASS")


# --------------------------------------------------
# 2. Save paired files
# --------------------------------------------------

with tempfile.TemporaryDirectory() as temp_dir:

    path = os.path.join(
        temp_dir,
        "MyWorkbook"
    )

    WorkbookStorage.save(
        workbook,
        path
    )

    assert os.path.exists(
        os.path.join(
            temp_dir,
            "MyWorkbook.json"
        )
    )

    assert os.path.exists(
        os.path.join(
            temp_dir,
            "MyWorkbook_Sheet1.csv"
        )
    )

    assert os.path.exists(
        os.path.join(
            temp_dir,
            "MyWorkbook_Data.csv"
        )
    )

    print("Paired files saved: PASS")


    # --------------------------------------------------
    # 3. Load workbook
    # --------------------------------------------------

    restored = WorkbookStorage.load(
        path
    )

    print("Workbook loaded: PASS")


    # --------------------------------------------------
    # 4. Sheet structure
    # --------------------------------------------------

    assert len(restored.sheets) == 2

    assert (
        restored.get_sheet("Sheet1")
        is not None
    )

    assert (
        restored.get_sheet("Data")
        is not None
    )

    print("Sheet structure: PASS")


    # --------------------------------------------------
    # 5. Cell values
    # --------------------------------------------------

    restored_sheet1 = (
        restored.get_sheet("Sheet1")
    )

    restored_data = (
        restored.get_sheet("Data")
    )

    assert (
        restored_sheet1
        .get_cell("A1")
        .value
        == "Hello"
    )

    assert (
        restored_sheet1
        .get_cell("B1")
        .value
        == 123
    )

    assert (
        restored_sheet1
        .get_cell("C1")
        .value
        == "=1+2"
    )

    assert (
        restored_data
        .get_cell("A1")
        .value
        == 500
    )

    assert (
        restored_data
        .get_cell("B1")
        .value
        == "Data"
    )

    print("Cell values: PASS")


    # --------------------------------------------------
    # 6. Formatting
    # --------------------------------------------------

    restored_cell = (
        restored_sheet1
        .get_cell("A1")
    )

    assert (
        restored_cell
        .format
        .font_family
        == "Calibri"
    )

    assert (
        restored_cell
        .format
        .font_size
        == 16
    )

    assert (
        restored_cell
        .format
        .bold
        is True
    )

    assert (
        restored_cell
        .format
        .text_color
        == "#FF0000"
    )

    assert (
        restored_cell
        .format
        .background_color
        == "#FFFF00"
    )

    print("Formatting: PASS")


    # --------------------------------------------------
    # 7. Dimensions
    # --------------------------------------------------

    assert (
        restored_sheet1
        .get_row_height(3)
        == 35
    )

    assert (
        restored_sheet1
        .get_column_width("B")
        == 25
    )

    print("Dimensions: PASS")


    # --------------------------------------------------
    # 8. Active sheet
    # --------------------------------------------------

    assert (
        restored
        .get_active_sheet()
        .name
        == "Data"
    )

    print("Active sheet: PASS")


    # --------------------------------------------------
    # 9. Independent workbook
    # --------------------------------------------------

    restored_sheet1.set_cell(
        "A1",
        "Changed"
    )

    assert (
        sheet1
        .get_cell("A1")
        .value
        == "Hello"
    )

    print("Independent workbook: PASS")


print("PHASE 12 INTEGRATION: PASS")