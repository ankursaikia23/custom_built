from core.cell import Cell

cell=Cell("A1","Hello")
cell.format.set_font(
    family="Calibri",
    size=14,
    bold=True,
    italic=True,
    underline=True
)
print("Font family:",cell.format.font_family)
print("Font size:",cell.format.font_size)
print("Bold:",cell.format.bold)
print("Italic:",cell.format.italic)
print("Underline:",cell.format.underline)
assert cell.format.font_family=="Calibri"
assert cell.format.font_size==14
assert cell.format.bold is True
assert cell.format.italic is True
assert cell.format.underline is True
for invalid in [
    {"size":0},
    {"size":-5},
    {"family":""},
    {"bold":"yes"},
    {"italic":1},
    {"underline":0}
]:
    try:
        cell.format.set_font(**invalid)
    except ValueError:
        print("Invalid value rejected:",invalid)
    else:
        raise AssertionError(f"Invalid value accepted: {invalid}")