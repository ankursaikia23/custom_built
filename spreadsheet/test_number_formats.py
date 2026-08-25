from core.cell import Cell

cell=Cell("A1",1234.56)
formats=["general","number","integer","currency","percentage","date"]
for number_format in formats:
    cell.format.set_number_format(number_format)
    print("Number format:",cell.format.number_format)
    assert cell.format.number_format==number_format
invalid_formats=["money","decimal","percent","",None]
for number_format in invalid_formats:
    try:
        cell.format.set_number_format(number_format)
    except ValueError:
        print("Invalid number format rejected:",number_format)
    else:
        raise AssertionError(f"Invalid number format accepted: {number_format}")