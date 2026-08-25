from core.cell import Cell

cell=Cell("A1","Hello")
cell.format.set_font("Calibri",14,True,True,True)
cell.format.set_colors("#FF0000","#FFFF00")
cell.format.set_alignment("center","bottom")
cell.format.set_wrap_text(True)
cell.format.set_number_format("currency")
cell.format.set_border("top","solid",2,"#0000FF")
cell.format.set_border("bottom","double",3,"#00FF00")
print("Font:",cell.format.font_family,cell.format.font_size)
print("Font styles:",cell.format.bold,cell.format.italic,cell.format.underline)
print("Colors:",cell.format.text_color,cell.format.background_color)
print("Alignment:",cell.format.horizontal_alignment,cell.format.vertical_alignment)
print("Wrap:",cell.format.wrap_text)
print("Number format:",cell.format.number_format)
print("Borders:",cell.format.borders)
copied=cell.format.copy()
copied.bold=False
copied.background_color="#FFFFFF"
copied.borders["top"]["color"]="#000000"
assert cell.format.bold is True
assert cell.format.background_color=="#FFFF00"
assert cell.format.borders["top"]["color"]=="#0000FF"
assert copied.bold is False
assert copied.background_color=="#FFFFFF"
assert copied.borders["top"]["color"]=="#000000"
print("Independent copy: PASS")