import re
def adjust_reference(reference,row_offset,column_offset):
    match=re.fullmatch(r"(\$?)([A-Za-z]+)(\$?)(\d+)",reference)
    if not match:
        raise ValueError(f"Invalid cell reference: {reference}")
    column_absolute,column,row_absolute,row=match.groups()
    row=int(row)
    if column_absolute:
        new_column=column.upper()
    else:
        new_column=column_name(column_number(column)+column_offset)
    if row_absolute:
        new_row=row
    else:
        new_row=row+row_offset
        if new_row<1:
            raise ValueError("Adjusted row is invalid")
    return f"{column_absolute}{new_column}{row_absolute}{new_row}"
def adjust_formula(formula,row_offset,column_offset):
    if not isinstance(formula,str) or not formula.startswith("="):
        return formula
    pattern=r"(\$?[A-Za-z]+\$?\d+)"
    return re.sub(pattern,lambda match:adjust_reference(match.group(1),row_offset,column_offset),formula)
def column_number(column):
    result=0
    for letter in column.upper():
        result=result*26+(ord(letter)-64)
    return result
def column_name(column):
    result=""
    while column:
        column,remaining=divmod(column-1,26)
        result=chr(65+remaining)+result
    return result