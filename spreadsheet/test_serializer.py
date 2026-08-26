from core.workbook import Workbook
from services.storage.serializer import WorkbookSerializer

# --------------------------------------------------
# 1. Create workbook
# --------------------------------------------------

workbook = Workbook()

sheet = workbook.add_sheet("Sheet1")

sheet.set_cell("A1", "Hello")
sheet.set_cell("B1", 123)
sheet.set_cell("C1", "=1+2")

print("Original workbook: PASS")


# --------------------------------------------------
# 2. Serialize
# --------------------------------------------------

data = WorkbookSerializer.serialize(workbook)

assert isinstance(data, dict)
assert "sheets" in data
assert len(data["sheets"]) == 1

assert data["sheets"][0]["name"] == "Sheet1"
assert data["sheets"][0]["cells"]["A1"]["value"] == "Hello"
assert data["sheets"][0]["cells"]["B1"]["value"] == 123
assert data["sheets"][0]["cells"]["C1"]["value"] == "=1+2"

print("Serialize workbook: PASS")


# --------------------------------------------------
# 3. Deserialize
# --------------------------------------------------

restored = WorkbookSerializer.deserialize(data)

restored_sheet = restored.get_sheet("Sheet1")

assert restored_sheet is not None

assert restored_sheet.get_cell("A1").value == "Hello"
assert restored_sheet.get_cell("B1").value == 123
assert restored_sheet.get_cell("C1").value == "=1+2"

print("Deserialize workbook: PASS")


# --------------------------------------------------
# 4. Independent restored workbook
# --------------------------------------------------

restored_sheet.set_cell("A1", "Changed")

assert sheet.get_cell("A1").value == "Hello"
assert restored_sheet.get_cell("A1").value == "Changed"

print("Independent restored workbook: PASS")


# --------------------------------------------------
# 5. Multiple sheets
# --------------------------------------------------

sheet2 = workbook.add_sheet("Sheet2")
sheet2.set_cell("A1", "Second sheet")

data = WorkbookSerializer.serialize(workbook)

restored = WorkbookSerializer.deserialize(data)

assert restored.get_sheet("Sheet1").get_cell("A1").value == "Hello"
assert restored.get_sheet("Sheet2").get_cell("A1").value == "Second sheet"

print("Multiple sheet serialization: PASS")


print("SERIALIZER FOUNDATION: PASS")