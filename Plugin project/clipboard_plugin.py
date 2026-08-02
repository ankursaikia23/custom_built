from PyQt6.QtWidgets import QLabel,QTableWidgetItem
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os

class ClipboardPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.clipboard=[]

    def copy_selection(self):
        self.clipboard=[]
        indexes=self.table.selectedIndexes()
        if not indexes:
            return
        r0=min(i.row() for i in indexes)
        c0=min(i.column() for i in indexes)
        for index in indexes:
            r=index.row()
            c=index.column()
            data={"r":r-r0,"c":c-c0,"text":"","image":None,"pdf":None}
            item=self.table.item(r,c)
            if item:
                data["text"]=item.text()
            if hasattr(self.spreadsheet,"image_plugin"):
                data["image"]=self.spreadsheet.image_plugin.images.get((r,c))
            if hasattr(self.spreadsheet,"pdf_plugin"):
                data["pdf"]=self.spreadsheet.pdf_plugin.pdfs.get((r,c))
            self.clipboard.append(data)
            self.spreadsheet.statusbar_plugin.show_operation("Copied")

    def cut_selection(self):
        indexes=self.table.selectedIndexes()
        if not indexes:
            return
        before=[]
        after=[]
        self.copy_selection()
        for index in indexes:
            r=index.row()
            c=index.column()
            before.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
            self.table.takeItem(r,c)
            self.table.removeCellWidget(r,c)
            if hasattr(self.spreadsheet,"image_plugin"):
                self.spreadsheet.image_plugin.images.pop((r,c),None)
            if hasattr(self.spreadsheet,"pdf_plugin"):
                self.spreadsheet.pdf_plugin.pdfs.pop((r,c),None)
            after.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
        self.spreadsheet.history_plugin.push_operation(before,after)

    def paste_selection(self):
        if not self.clipboard:
            return
        before=[]
        after=[]
        indexes=self.table.selectedIndexes()
        if indexes:
            start_row=min(i.row() for i in indexes)
            start_col=min(i.column() for i in indexes)
        else:
            start_row=self.table.currentRow()
            start_col=self.table.currentColumn()
        if len(self.clipboard)==1 and len(indexes)>1:
            targets=[(i.row(),i.column()) for i in indexes]
        else:
            targets=[]
            for cell in self.clipboard:
                targets.append((start_row+cell["r"],start_col+cell["c"]))
        for i,(r,c) in enumerate(targets):
            before.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
            if len(self.clipboard)==1:
                cell=self.clipboard[0]
            else:
                cell=self.clipboard[i]
            self.table.takeItem(r,c)
            self.table.removeCellWidget(r,c)
            if cell["text"]:
                self.table.setItem(r,c,QTableWidgetItem(cell["text"]))
            after.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
        self.spreadsheet.history_plugin.push_operation(before,after)