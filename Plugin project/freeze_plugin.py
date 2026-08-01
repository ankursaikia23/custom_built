from PyQt6.QtWidgets import QTableView
class FreezePlugin:
    def __init__(self,window):
        self.window=window
        self.table=window.table
    def freeze_row(self,row=0):
        self.table.verticalHeader().setSectionsMovable(False)
        self.table.setFrozenRows(row)
    def freeze_column(self,column=0):
        self.table.horizontalHeader().setSectionsMovable(False)
        self.table.setFrozenColumns(column)