from PyQt6.QtWidgets import QTabWidget,QTableWidget
class SheetPlugin:
    def __init__(self,window):
        self.window=window
        self.tabs=QTabWidget()
        self.sheets=[]
        self.add_sheet()
    def widget(self):
        return self.tabs
    def add_sheet(self,name=None):
        table=QTableWidget(100,26)
        self.sheets.append(table)
        self.tabs.addTab(table,name or f"Sheet {len(self.sheets)}")
    def rename_sheet(self,index,name):
        self.tabs.setTabText(index,name)
    def delete_sheet(self,index):
        if self.tabs.count()>1:
            self.tabs.removeTab(index)
            self.sheets.pop(index)