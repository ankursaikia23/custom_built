import os
import tempfile
from core.workbook import Workbook
from services.storage.json_storage import JSONStorage


# --------------------------------------------------
# 1. Create workbook
# --------------------------------------------------

workbook = Workbook()

sheet1 = workbook.add_sheet("Sheet1")
sheet2 = workbook.add_sheet("Data")
sheet3 = workbook.add_sheet("Summary")

sheet1.set_cell("A1", "Main")
sheet2.set_cell("A1", 100)
sheet3.set_cell("A1", "=Data!A1")

print("Multiple sheets: PASS")


# --------------------------------------------------
# 2. Set dimensions
# --------------------------------------------------

sheet1.set_row_height(3, 35)
sheet1.set_row_height(7, 50)

sheet1.set_column_width("B", 25)
sheet1.set_column_width("D", 40)

sheet2.set_row_height(2, 30)
sheet2.set_column_width("C", 20)

print("Dimensions set: PASS")


# --------------------------------------------------
# 3. Set active sheet
# --------------------------------------------------

workbook.set_active_sheet("Summary")

assert workbook.get_active_sheet().name == "Summary"

print("Active sheet set: PASS")


# --------------------------------------------------
# 4. Save and reload
# --------------------------------------------------

with tempfile.TemporaryDirectory() as temp_dir:

    path = os.path.join(
        temp_dir,
        "structure_test.json"
    )

    JSONStorage.save(workbook, path)

    restored = JSONStorage.load(path)


# --------------------------------------------------
# 5. Verify sheets
# --------------------------------------------------

assert len(restored.sheets) == 3

assert restored.get_sheet("Sheet1") is not None
assert restored.get_sheet("Data") is not None
assert restored.get_sheet("Summary") is not None

print("Sheet structure persistence: PASS")


# --------------------------------------------------
# 6. Verify values
# --------------------------------------------------

assert restored.get_sheet("Sheet1").get_cell("A1").value == "Main"
assert restored.get_sheet("Data").get_cell("A1").value == 100
assert (
    restored
    .get_sheet("Summary")
    .get_cell("A1")
    .value
    == "=Data!A1"
)

print("Sheet data persistence: PASS")


# --------------------------------------------------
# 7. Verify row dimensions
# --------------------------------------------------

restored_sheet1 = restored.get_sheet("Sheet1")

assert restored_sheet1.get_row_height(3) == 35
assert restored_sheet1.get_row_height(7) == 50

print("Row dimension persistence: PASS")


# --------------------------------------------------
# 8. Verify column dimensions
# --------------------------------------------------

assert restored_sheet1.get_column_width("B") == 25
assert restored_sheet1.get_column_width("D") == 40

print("Column dimension persistence: PASS")


# --------------------------------------------------
# 9. Verify second sheet dimensions
# --------------------------------------------------

restored_data = restored.get_sheet("Data")

assert restored_data.get_row_height(2) == 30
assert restored_data.get_column_width("C") == 20

print("Multiple sheet dimensions: PASS")


# --------------------------------------------------
# 10. Verify active sheet
# --------------------------------------------------

assert restored.get_active_sheet().name == "Summary"

print("Active sheet persistence: PASS")


print("STRUCTURE PERSISTENCE: PASS")