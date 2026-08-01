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

    def cut_selection(self):
        self.copy_selection()
        for index in self.table.selectedIndexes():
            r=index.row()
            c=index.column()
            self.table.takeItem(r,c)
            self.table.removeCellWidget(r,c)
            if hasattr(self.spreadsheet,"image_plugin"):
                self.spreadsheet.image_plugin.images.pop((r,c),None)
            if hasattr(self.spreadsheet,"pdf_plugin"):
                self.spreadsheet.pdf_plugin.pdfs.pop((r,c),None)

    def paste_selection(self):
        if not self.clipboard:
            return
        sr=self.table.currentRow()
        sc=self.table.currentColumn()
        for cell in self.clipboard:
            r=sr+cell["r"]
            c=sc+cell["c"]
            self.table.takeItem(r,c)
            self.table.removeCellWidget(r,c)
            if cell["text"]:
                self.table.setItem(r,c,QTableWidgetItem(cell["text"]))
            if cell["image"] and os.path.exists(cell["image"]):
                label=QLabel()
                pixmap=QPixmap(cell["image"])
                label.setPixmap(pixmap.scaled(150,150,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(r,c,label)
                if hasattr(self.spreadsheet,"image_plugin"):
                    self.spreadsheet.image_plugin.images[(r,c)]=cell["image"]
            if cell["pdf"] and os.path.exists(cell["pdf"]):
                label=QLabel("📄\n"+os.path.basename(cell["pdf"]))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(r,c,label)
                if hasattr(self.spreadsheet,"pdf_plugin"):
                    self.spreadsheet.pdf_plugin.pdfs[(r,c)]=cell["pdf"]