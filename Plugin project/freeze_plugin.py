from PyQt6.QtWidgets import QTableWidget

class FreezePlugin:
    def __init__(self,window):
        self.window=window
        self.table=window.table
        self.frozen_rows=0
        self.frozen_columns=0

    def freeze_row(self,row=0):
        if row<0:
            row=0
        self.frozen_rows=min(row,self.table.rowCount())
        for index in range(self.table.rowCount()):
            self.table.setRowHidden(index,index>=self.frozen_rows and False)
        self.table.viewport().update()

    def freeze_column(self,column=0):
        if column<0:
            column=0
        self.frozen_columns=min(column,self.table.columnCount())
        for index in range(self.table.columnCount()):
            self.table.setColumnHidden(index,False)
        self.table.viewport().update()