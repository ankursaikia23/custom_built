import os
import tempfile
from core.workbook import Workbook
from services.storage.json_storage import JSONStorage

workbook = Workbook()
sheet = workbook.add_sheet("Sheet1")

cell = sheet.set_cell("A1", "Formatted")

cell = sheet.get_cell("A1")

cell.format.set_font(
    family="Calibri",
    size=16,
    bold=True,
    italic=True,
    underline=True,
)

cell.format.set_colors(
    text_color="#FF0000",
    background_color="#FFFF00",
)

cell.format.set_alignment(
    horizontal="center",
    vertical="bottom",
)

cell.format.set_wrap_text(True)

cell.format.set_number_format("currency")

cell.format.set_border(
    "top",
    style="solid",
    width=2,
    color="#0000FF",
)

cell.format.set_border(
    "bottom",
    style="double",
    width=3,
    color="#00FF00",
)


print("Original formatting: PASS")


# --------------------------------------------------
# Save and reload
# --------------------------------------------------

with tempfile.TemporaryDirectory() as temp_dir:

    path = os.path.join(
        temp_dir,
        "format_test.json"
    )

    JSONStorage.save(workbook, path)

    restored = JSONStorage.load(path)

    restored_cell = (
        restored
        .get_sheet("Sheet1")
        .get_cell("A1")
    )


# --------------------------------------------------
# Font
# --------------------------------------------------

assert restored_cell.format.font_family == "Calibri"
assert restored_cell.format.font_size == 16
assert restored_cell.format.bold is True
assert restored_cell.format.italic is True
assert restored_cell.format.underline is True

print("Font persistence: PASS")


# --------------------------------------------------
# Colors
# --------------------------------------------------

assert restored_cell.format.text_color == "#FF0000"
assert restored_cell.format.background_color == "#FFFF00"

print("Color persistence: PASS")


# --------------------------------------------------
# Alignment
# --------------------------------------------------

assert restored_cell.format.horizontal_alignment == "center"
assert restored_cell.format.vertical_alignment == "bottom"

print("Alignment persistence: PASS")


# --------------------------------------------------
# Wrap
# --------------------------------------------------

assert restored_cell.format.wrap_text is True

print("Wrap persistence: PASS")


# --------------------------------------------------
# Number format
# --------------------------------------------------

assert restored_cell.format.number_format == "currency"

print("Number format persistence: PASS")


# --------------------------------------------------
# Borders
# --------------------------------------------------

assert restored_cell.format.borders["top"] == {
    "style": "solid",
    "width": 2,
    "color": "#0000FF",
}

assert restored_cell.format.borders["bottom"] == {
    "style": "double",
    "width": 3,
    "color": "#00FF00",
}

print("Border persistence: PASS")


# --------------------------------------------------
# Independent restored formatting
# --------------------------------------------------

restored_cell.format.set_font(
    size=30
)

assert restored_cell.format.font_size == 30
assert sheet.get_cell("A1").format.font_size == 16

print("Independent formatting: PASS")


print("FORMAT PERSISTENCE: PASS")