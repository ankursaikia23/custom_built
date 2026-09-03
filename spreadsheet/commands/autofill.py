from copy import deepcopy
from services.formula.reference import adjust_formula

class Autofill:
    def fill(self,sheet,start_reference,end_reference):
        start_column,start_row=sheet.split_reference(start_reference)
        end_column,end_row=sheet.split_reference(end_reference)
        start_column_number=sheet.column_number(start_column)
        end_column_number=sheet.column_number(end_column)
        if start_row>end_row or start_column_number>end_column_number:
            raise ValueError("Invalid autofill range")
        width=end_column_number-start_column_number+1
        height=end_row-start_row+1
        if width==1 and height>1:
            self.fill_vertical(sheet,start_column_number,start_row,end_row)
        elif height==1 and width>1:
            self.fill_horizontal(sheet,start_column_number,end_column_number,start_row)
        else:
            raise ValueError("Autofill requires a single row or single column")
    
    def fill_vertical(self,sheet,column_number,start_row,end_row):
        source_cells=[]
        for row in range(start_row,end_row+1):
            cell=sheet.get_cell(f"{sheet.column_name(column_number)}{row}")
            if cell is not None:
                source_cells.append((row,cell))
        if not source_cells:
            raise ValueError("Autofill source is empty")
        if len(source_cells)==1:
            source_row,source_cell=source_cells[0]
            for row in range(start_row+1,end_row+1):
                self._place(sheet,source_cell,source_row,row,column_number)
            return
        first_row,first_cell=source_cells[0]
        second_row,second_cell=source_cells[1]
        if isinstance(first_cell.value,(int,float)) and isinstance(second_cell.value,(int,float)):
            step=second_cell.value-first_cell.value
            for row in range(second_row+1,end_row+1):
                value=second_cell.value+step*(row-second_row)
                self._place_value(sheet,second_cell,row,column_number,value)
        elif isinstance(first_cell.value,str) and first_cell.value.startswith("="):
            for row in range(second_row+1,end_row+1):
                offset=row-first_row
                formula=adjust_formula(first_cell.value,offset,0)
                self._place_value(sheet,first_cell,row,column_number,formula)
        else:
            for row in range(second_row+1,end_row+1):
                self._place_value(sheet,second_cell,row,column_number,second_cell.value)
    
    def fill_horizontal(self,sheet,start_column_number,end_column_number,row):
        source_cells=[]
        for column_number in range(start_column_number,end_column_number+1):
            cell=sheet.get_cell(f"{sheet.column_name(column_number)}{row}")
            if cell is not None:
                source_cells.append((column_number,cell))    
        if not source_cells:
            raise ValueError("Autofill source is empty")
        first_column,first_cell=source_cells[0]
        if isinstance(first_cell.value,str) and first_cell.value.startswith("="):
            for column_number in range(first_column+1,end_column_number+1):
                offset=column_number-first_column
                formula=adjust_formula(first_cell.value,0,offset)
                self._place_value(
                    sheet,
                    first_cell,
                    row,
                    column_number,
                    formula
                )
            return
        if len(source_cells)==1:
            source_column,source_cell=source_cells[0]
            for column_number in range(source_column+1,end_column_number+1):
                self._place_value(
                    sheet,
                    source_cell,
                    row,
                    column_number,
                    source_cell.value
                )
            return
        second_column,second_cell=source_cells[1]
        if (
            isinstance(first_cell.value,(int,float))
            and isinstance(second_cell.value,(int,float))
        ):
            step=second_cell.value-first_cell.value
            for column_number in range(second_column+1,end_column_number+1):
                value=second_cell.value+step*(column_number-second_column)    
                self._place_value(
                    sheet,
                    second_cell,
                    row,
                    column_number,
                    value
                )
        else:
            for column_number in range(second_column+1,end_column_number+1):
                self._place_value(
                    sheet,
                    second_cell,
                    row,
                    column_number,
                    second_cell.value
                )
    
    def _place(self,sheet,source_cell,source_row,target_row,source_column_number):
        copied=deepcopy(source_cell)
        if isinstance(copied.value,str) and copied.value.startswith("="):
            copied.value=adjust_formula(copied.value,target_row-source_row,0)
        copied.reference=f"{sheet.column_name(source_column_number)}{target_row}"
        sheet.cells[copied.reference]=copied
    
    def _place_value(self,sheet,source_cell,row,column_number,value):
        copied=deepcopy(source_cell)
        copied.value=value
        copied.reference=f"{sheet.column_name(column_number)}{row}"
        sheet.cells[copied.reference]=copied