from core.cell import Cell

cell=Cell("A1","Long text that should wrap")
cell.format.set_border("top","solid",2,"#FF0000")
cell.format.set_border("bottom","double",3,"#0000FF")
cell.format.set_border("left","dashed",1,"#00FF00")
cell.format.set_border("right","dotted",1,"#000000")
cell.format.set_wrap_text(True)
print("Borders:",cell.format.borders)
print("Wrap:",cell.format.wrap_text)
assert cell.format.borders["top"]["style"]=="solid"
assert cell.format.borders["top"]["width"]==2
assert cell.format.borders["top"]["color"]=="#FF0000"
assert cell.format.borders["bottom"]["style"]=="double"
assert cell.format.borders["left"]["style"]=="dashed"
assert cell.format.borders["right"]["style"]=="dotted"
assert cell.format.wrap_text is True
cell.format.remove_border("left")
assert "left" not in cell.format.borders
print("Left border removed: PASS")
for side in ["invalid","middle"]:
    try:
        cell.format.set_border(side)
    except ValueError:
        print("Invalid border side rejected:",side)
    else:
        raise AssertionError(f"Invalid border side accepted: {side}")
try:
    cell.format.set_wrap_text("yes")
except ValueError:
    print("Invalid wrap value rejected: PASS")
else:
    raise AssertionError("Invalid wrap value accepted")