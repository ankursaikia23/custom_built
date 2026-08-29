from core.sheet import Sheet
from services.formula.recalculation import RecalculationManager

class Workbook:
    def __init__(self):
        self.sheets = []
        self.active_sheet_index = 0
        self.recalculation_manager = RecalculationManager(
            workbook=self
        )

    def add_sheet(self,name):
        self.validate_sheet_name(name)
        if self.get_sheet(name) is not None:
            raise ValueError("Sheet name already exists")
        sheet = Sheet(name, workbook=self)
        self.sheets.append(sheet)
        if len(self.sheets)==1:
            self.active_sheet_index=0
        return sheet

    def get_sheet(self,name):
        for sheet in self.sheets:
            if sheet.name==name:
                return sheet
        return None

    def get_active_sheet(self):
        if not self.sheets:
            return None
        return self.sheets[self.active_sheet_index]
    
    def set_cell_value(self, sheet_name, reference, value):
        sheet = self.get_sheet(sheet_name)
        if sheet is None:
            raise ValueError(
                f"Sheet not found: {sheet_name}"
            )    
        cell = sheet.set_cell(
            reference,
            value
        )
        self.recalculation_manager.recalculate(
            f"{sheet_name}!{reference}"
        )
        return cell

    def set_active_sheet(self,name):
        for index,sheet in enumerate(self.sheets):
            if sheet.name==name:
                self.active_sheet_index=index
                return sheet
        raise ValueError(f"Sheet not found: {name}")

    def delete_sheet(self,name):
        if len(self.sheets)<=1:
            raise ValueError("Workbook must contain at least one sheet")
        index=None
        for i,sheet in enumerate(self.sheets):
            if sheet.name==name:
                index=i
                break
        if index is None:
            raise ValueError(f"Sheet not found: {name}")
        self.sheets.pop(index)
        if index==self.active_sheet_index:
            self.active_sheet_index=max(0,index-1)
        elif index<self.active_sheet_index:
            self.active_sheet_index-=1
        if self.active_sheet_index>=len(self.sheets):
            self.active_sheet_index=len(self.sheets)-1

    def rename_sheet(self,old_name,new_name):
        self.validate_sheet_name(new_name)
        sheet=self.get_sheet(old_name)
        if sheet is None:
            raise ValueError(f"Sheet not found: {old_name}")
        existing=self.get_sheet(new_name)
        if existing is not None and existing is not sheet:
            raise ValueError("Sheet name already exists")
        sheet.name=new_name
        return sheet

    def move_sheet(self,name,new_index):
        if not isinstance(new_index,int):
            raise ValueError("Sheet index must be an integer")
        sheet_index=None
        for index,sheet in enumerate(self.sheets):
            if sheet.name==name:
                sheet_index=index
                break
        if sheet_index is None:
            raise ValueError(f"Sheet not found: {name}")
        if new_index<0 or new_index>=len(self.sheets):
            raise ValueError("Sheet index out of range")
        if sheet_index==new_index:
            return
        active_sheet=self.get_active_sheet()
        sheet=self.sheets.pop(sheet_index)
        self.sheets.insert(new_index,sheet)
        self.active_sheet_index=self.sheets.index(active_sheet)

    def move_sheet_left(self,name):
        sheet_index=self.get_sheet_index(name)
        if sheet_index==0:
            return
        self.move_sheet(name,sheet_index-1)

    def move_sheet_right(self,name):
        sheet_index=self.get_sheet_index(name)
        if sheet_index==len(self.sheets)-1:
            return
        self.move_sheet(name,sheet_index+1)

    def get_sheet_index(self,name):
        for index,sheet in enumerate(self.sheets):
            if sheet.name==name:
                return index
        raise ValueError(f"Sheet not found: {name}")

    def sheet_names(self):
        return [sheet.name for sheet in self.sheets]

    def validate_sheet_name(self,name):
        if not isinstance(name,str) or not name.strip():
            raise ValueError("Sheet name must be a non-empty string")
        if len(name)>31:
            raise ValueError("Sheet name cannot exceed 31 characters")
        invalid_characters=[':', '\\', '/', '?', '*', '[', ']']
        if any(character in name for character in invalid_characters):
            raise ValueError("Sheet name contains invalid characters")