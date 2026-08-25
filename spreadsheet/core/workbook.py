class Workbook:
    def __init__(self):
        self.sheets=[]
        
    def add_sheet(self,name):
        from .sheet import Sheet
        sheet=Sheet(name)
        self.sheets.append(sheet)
        return sheet
    
    def get_sheet(self,name):
        for sheet in self.sheets:
            if sheet.name==name:
                return sheet
        return None
    
    def remove_sheet(self,name):
        self.sheets=[sheet for sheet in self.sheets if sheet.name!=name]