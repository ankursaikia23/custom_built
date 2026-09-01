from core.cell import Cell

class Sheet:
    def __init__(self, name, workbook=None):
        self.name = name
        self.workbook = workbook
        self.cells = {}
        self.default_row_height=20
        self.default_column_width=80
        self.row_heights={}
        self.column_widths={}
        self.hidden_rows=set()
        self.hidden_columns=set()
        self.merged_ranges=[]

    def set_cell(self, reference, value):
        reference = self._normalize_reference(reference)
    
        if reference not in self.cells:
            self.cells[reference] = Cell(
                reference,
                value
            )
        else:
            cell = self.cells[reference]
            cell.value = value
            cell.calculated_value = None
    
        if self.workbook is not None:
    
            qualified_reference = (
                f"{self.name}!{reference}"
            )
    
            self.workbook.recalculation_manager.register_formula(
                qualified_reference,
                value
            )
    
            self.workbook.recalculation_manager.recalculate_from(
                reference,
                sheet=self
            )
    
        return self.cells[reference]
    
    
    def get_cell(self, reference):
        reference = self._normalize_reference(reference)
        return self.cells.get(reference)
    
    
    def delete_cell(self, reference):
        reference = self._normalize_reference(reference)
    
        cell = self.cells.pop(
            reference,
            None
        )
    
        if (
            cell is not None
            and self.workbook is not None
        ):
    
            qualified_reference = (
                f"{self.name}!{reference}"
            )
    
            self.workbook.recalculation_manager.remove_formula(
                qualified_reference
            )
    
        return cell

    def set_row_height(self,row,height):
        if row<1:
            raise ValueError("Row must be greater than zero")
        if not isinstance(height,(int,float)) or height<=0:
            raise ValueError("Row height must be greater than zero")
        self.row_heights[row]=height

    def get_row_height(self,row):
        if row<1:
            raise ValueError("Row must be greater than zero")
        return self.row_heights.get(row,self.default_row_height)

    def set_column_width(self,column,width):
        if not isinstance(column,str) or not column.strip():
            raise ValueError("Column must be a non-empty string")
        if not isinstance(width,(int,float)) or width<=0:
            raise ValueError("Column width must be greater than zero")
        column=self.column_name(self.column_number(column))
        self.column_widths[column]=width

    def get_column_width(self,column):
        if not isinstance(column,str) or not column.strip():
            raise ValueError("Column must be a non-empty string")
        column=self.column_name(self.column_number(column))
        return self.column_widths.get(column,self.default_column_width)

    def set_default_row_height(self,height):
        if not isinstance(height,(int,float)) or height<=0:
            raise ValueError("Default row height must be greater than zero")
        self.default_row_height=height

    def set_default_column_width(self,width):
        if not isinstance(width,(int,float)) or width<=0:
            raise ValueError("Default column width must be greater than zero")
        self.default_column_width=width

    def hide_row(self,row):
        if row<1:
            raise ValueError("Row must be greater than zero")
        self.hidden_rows.add(row)

    def show_row(self,row):
        if row<1:
            raise ValueError("Row must be greater than zero")
        self.hidden_rows.discard(row)

    def is_row_hidden(self,row):
        if row<1:
            raise ValueError("Row must be greater than zero")
        return row in self.hidden_rows

    def hide_column(self,column):
        if not isinstance(column,str) or not column.strip():
            raise ValueError("Column must be a non-empty string")
        column=self.column_name(self.column_number(column))
        self.hidden_columns.add(column)

    def show_column(self,column):
        if not isinstance(column,str) or not column.strip():
            raise ValueError("Column must be a non-empty string")
        column=self.column_name(self.column_number(column))
        self.hidden_columns.discard(column)

    def is_column_hidden(self,column):
        if not isinstance(column,str) or not column.strip():
            raise ValueError("Column must be a non-empty string")
        column=self.column_name(self.column_number(column))
        return column in self.hidden_columns

    def merge_cells(self,start_reference,end_reference):
        start_column,start_row=self.split_reference(start_reference)
        end_column,end_row=self.split_reference(end_reference)
        start_column_number=self.column_number(start_column)
        end_column_number=self.column_number(end_column)
        if start_row>end_row or start_column_number>end_column_number:
            raise ValueError("Invalid merge range")
        normalized_start=f"{start_column}{start_row}"
        normalized_end=f"{end_column}{end_row}"
        new_range=(normalized_start,normalized_end)
        if new_range in self.merged_ranges:
            return
        if self.range_overlaps_merge(new_range):
            raise ValueError("Merge range overlaps an existing merged range")
        self.merged_ranges.append(new_range)

    def unmerge_cells(self,start_reference,end_reference):
        start_column,start_row=self.split_reference(start_reference)
        end_column,end_row=self.split_reference(end_reference)
        normalized_range=(f"{start_column}{start_row}",f"{end_column}{end_row}")
        if normalized_range not in self.merged_ranges:
            raise ValueError("Merged range does not exist")
        self.merged_ranges.remove(normalized_range)

    def is_merged(self,reference):
        column,row=self.split_reference(reference)
        column_number=self.column_number(column)
        for start_reference,end_reference in self.merged_ranges:
            start_column,start_row=self.split_reference(start_reference)
            end_column,end_row=self.split_reference(end_reference)
            if start_row<=row<=end_row and self.column_number(start_column)<=column_number<=self.column_number(end_column):
                return True
        return False

    def get_merge_range(self,reference):
        column,row=self.split_reference(reference)
        column_number=self.column_number(column)
        for start_reference,end_reference in self.merged_ranges:
            start_column,start_row=self.split_reference(start_reference)
            end_column,end_row=self.split_reference(end_reference)
            if start_row<=row<=end_row and self.column_number(start_column)<=column_number<=self.column_number(end_column):
                return start_reference,end_reference
        return None

    def range_overlaps_merge(self,merge_range):
        start_reference,end_reference=merge_range
        start_column,start_row=self.split_reference(start_reference)
        end_column,end_row=self.split_reference(end_reference)
        start_column_number=self.column_number(start_column)
        end_column_number=self.column_number(end_column)
        for existing_start,existing_end in self.merged_ranges:
            existing_start_column,existing_start_row=self.split_reference(existing_start)
            existing_end_column,existing_end_row=self.split_reference(existing_end)
            existing_start_column_number=self.column_number(existing_start_column)
            existing_end_column_number=self.column_number(existing_end_column)
            rows_overlap=start_row<=existing_end_row and end_row>=existing_start_row
            columns_overlap=start_column_number<=existing_end_column_number and end_column_number>=existing_start_column_number
            if rows_overlap and columns_overlap:
                return True
        return False

    def insert_rows(self,index,count=1):
        if index<1 or count<1:
            raise ValueError("Row index and count must be greater than zero")
        new_cells={}
        for reference,cell in self.cells.items():
            column,row=self.split_reference(reference)
            if row>=index:
                row+=count
            new_reference=f"{column}{row}"
            cell.reference=new_reference
            new_cells[new_reference]=cell
        self.cells=new_cells
        new_heights={}
        for row,height in self.row_heights.items():
            if row>=index:
                row+=count
            new_heights[row]=height
        self.row_heights=new_heights
        self.hidden_rows={row+count if row>=index else row for row in self.hidden_rows}
        new_merges=[]
        for start_reference,end_reference in self.merged_ranges:
            start_column,start_row=self.split_reference(start_reference)
            end_column,end_row=self.split_reference(end_reference)
            if start_row>=index:
                start_row+=count
            if end_row>=index:
                end_row+=count
            new_merges.append((f"{start_column}{start_row}",f"{end_column}{end_row}"))
        self.merged_ranges=new_merges

    def delete_rows(self,index,count=1):
        if index<1 or count<1:
            raise ValueError("Row index and count must be greater than zero")
        end=index+count-1
        new_cells={}
        for reference,cell in self.cells.items():
            column,row=self.split_reference(reference)
            if index<=row<=end:
                continue
            if row>end:
                row-=count
            new_reference=f"{column}{row}"
            cell.reference=new_reference
            new_cells[new_reference]=cell
        self.cells=new_cells
        new_heights={}
        for row,height in self.row_heights.items():
            if index<=row<=end:
                continue
            if row>end:
                row-=count
            new_heights[row]=height
        self.row_heights=new_heights
        self.hidden_rows={row-count if row>end else row for row in self.hidden_rows if not index<=row<=end}
        new_merges=[]
        for start_reference,end_reference in self.merged_ranges:
            start_column,start_row=self.split_reference(start_reference)
            end_column,end_row=self.split_reference(end_reference)
            if start_row>end:
                start_row-=count
                end_row-=count
            elif start_row>=index:
                if end_row<=end:
                    continue
                start_row=index
                end_row-=count
            elif end_row>=index:
                end_row=max(index-1,end_row-count)
            if start_row<=end_row:
                new_merges.append((f"{start_column}{start_row}",f"{end_column}{end_row}"))
        self.merged_ranges=new_merges

    def insert_columns(self,index,count=1):
        if index<1 or count<1:
            raise ValueError("Column index and count must be greater than zero")
        new_cells={}
        for reference,cell in self.cells.items():
            column,row=self.split_reference(reference)
            column_number=self.column_number(column)
            if column_number>=index:
                column_number+=count
            new_column=self.column_name(column_number)
            new_reference=f"{new_column}{row}"
            cell.reference=new_reference
            new_cells[new_reference]=cell
        self.cells=new_cells
        new_widths={}
        for column,width in self.column_widths.items():
            column_number=self.column_number(column)
            if column_number>=index:
                column_number+=count
            new_column=self.column_name(column_number)
            new_widths[new_column]=width
        self.column_widths=new_widths
        self.hidden_columns={self.column_name(self.column_number(column)+count) if self.column_number(column)>=index else column for column in self.hidden_columns}
        new_merges=[]
        for start_reference,end_reference in self.merged_ranges:
            start_column,start_row=self.split_reference(start_reference)
            end_column,end_row=self.split_reference(end_reference)
            start_column_number=self.column_number(start_column)
            end_column_number=self.column_number(end_column)
            if start_column_number>=index:
                start_column_number+=count
            if end_column_number>=index:
                end_column_number+=count
            new_merges.append((f"{self.column_name(start_column_number)}{start_row}",f"{self.column_name(end_column_number)}{end_row}"))
        self.merged_ranges=new_merges

    def delete_columns(self,index,count=1):
        if index<1 or count<1:
            raise ValueError("Column index and count must be greater than zero")
        end=index+count-1
        new_cells={}
        for reference,cell in self.cells.items():
            column,row=self.split_reference(reference)
            column_number=self.column_number(column)
            if index<=column_number<=end:
                continue
            if column_number>end:
                column_number-=count
            new_column=self.column_name(column_number)
            new_reference=f"{new_column}{row}"
            cell.reference=new_reference
            new_cells[new_reference]=cell
        self.cells=new_cells
        new_widths={}
        for column,width in self.column_widths.items():
            column_number=self.column_number(column)
            if index<=column_number<=end:
                continue
            if column_number>end:
                column_number-=count
            new_column=self.column_name(column_number)
            new_widths[new_column]=width
        self.column_widths=new_widths
        self.hidden_columns={self.column_name(self.column_number(column)-count) if self.column_number(column)>end else column for column in self.hidden_columns if not index<=self.column_number(column)<=end}
        new_merges=[]
        for start_reference,end_reference in self.merged_ranges:
            start_column,start_row=self.split_reference(start_reference)
            end_column,end_row=self.split_reference(end_reference)
            start_column_number=self.column_number(start_column)
            end_column_number=self.column_number(end_column)
            if index<=start_column_number<=end:
                continue
            if start_column_number>end:
                start_column_number-=count
            if index<=end_column_number<=end:
                end_column_number=index-1
            elif end_column_number>end:
                end_column_number-=count
            if start_column_number<=end_column_number:
                new_merges.append((f"{self.column_name(start_column_number)}{start_row}",f"{self.column_name(end_column_number)}{end_row}"))
        self.merged_ranges=new_merges

    def split_reference(self, reference):
        import re
        match = re.fullmatch(
            r"\$?([A-Za-z]+)\$?(\d+)",
            reference.strip()
        )    
        if not match:
            raise ValueError(
                f"Invalid cell reference: {reference}"
            )
        return (
            match.group(1).upper(),
            int(match.group(2))
        )
    
    def _normalize_reference(self, reference):
        if not isinstance(reference, str):
            raise ValueError(
                "Cell reference must be a non-empty string"
            )
    
        reference = reference.strip()
    
        if not reference:
            raise ValueError(
                "Cell reference must be a non-empty string"
            )
    
        column, row = self.split_reference(reference)
    
        return f"{column}{row}"

    def column_number(self,column):
        result=0
        for letter in column.upper():
            result=result*26+(ord(letter)-64)
        return result

    def column_name(self,column):
        result=""
        while column:
            column,remaining=divmod(column-1,26)
            result=chr(65+remaining)+result
        return result