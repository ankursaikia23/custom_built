from core.cell import Cell

cell=Cell("A1","Hello")
print("Reference:",cell.reference)
print("Value:",cell.value)
print("Bold:",cell.format.bold)
print("Font size:",cell.format.font_size)
cell.format.bold=True
cell.format.font_size=14
cell.format.background_color="#FFFF00"
print("Updated bold:",cell.format.bold)
print("Updated font size:",cell.format.font_size)
print("Updated background:",cell.format.background_color)
copied=cell.format.copy()
copied.bold=False
copied.font_size=20
print("Original bold:",cell.format.bold)
print("Original font size:",cell.format.font_size)
print("Copied bold:",copied.bold)
print("Copied font size:",copied.font_size)
assert cell.format.bold is True
assert cell.format.font_size==14
assert cell.format.background_color=="#FFFF00"
assert copied.bold is False
assert copied.font_size==20
assert cell.format.bold is not copied.bold