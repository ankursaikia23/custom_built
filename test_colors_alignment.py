from core.cell import Cell

cell=Cell("A1","Hello")
cell.format.set_colors(
    text_color="#ff0000",
    background_color="#00ff00"
)
cell.format.set_alignment(
    horizontal="center",
    vertical="bottom"
)
print("Text color:",cell.format.text_color)
print("Background color:",cell.format.background_color)
print("Horizontal:",cell.format.horizontal_alignment)
print("Vertical:",cell.format.vertical_alignment)
assert cell.format.text_color=="#FF0000"
assert cell.format.background_color=="#00FF00"
assert cell.format.horizontal_alignment=="center"
assert cell.format.vertical_alignment=="bottom"
invalid_colors=["red","#fff","#GGGGGG","123456"]
for color in invalid_colors:
    try:
        cell.format.set_colors(text_color=color)
    except ValueError:
        print("Invalid color rejected:",color)
    else:
        raise AssertionError(f"Invalid color accepted: {color}")
invalid_horizontal=["middle","justify",""]
invalid_vertical=["middle","justify",""]
for alignment in invalid_horizontal:
    try:
        cell.format.set_alignment(horizontal=alignment)
    except ValueError:
        print("Invalid horizontal alignment rejected:",alignment)
    else:
        raise AssertionError(f"Invalid horizontal alignment accepted: {alignment}")
for alignment in invalid_vertical:
    try:
        cell.format.set_alignment(vertical=alignment)
    except ValueError:
        print("Invalid vertical alignment rejected:",alignment)
    else:
        raise AssertionError(f"Invalid vertical alignment accepted: {alignment}")