import os
from PyQt6.QtWidgets import QFileDialog,QLabel
from PyQt6.QtCore import Qt

class PDFPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.pdfs={}

    def insert_pdf(self):
        row=self.table.currentRow()
        col=self.table.currentColumn()
        if row<0 or col<0:
            return
        file,_=QFileDialog.getOpenFileName(self.spreadsheet,"Select PDF","","PDF Files (*.pdf)")
        if not file:
            return
        self.set_pdf(row,col,file)

    def set_pdf(self,row,col,path):
        self.table.takeItem(row,col)
        self.table.removeCellWidget(row,col)
        label=QLabel("📄\n"+os.path.basename(path))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row,col,label)
        self.table.setRowHeight(row,80)
        self.table.setColumnWidth(col,180)
        self.pdfs[(row,col)]=path
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.images.pop((row,col),None)

    def remove_pdf(self,row,col):
        self.pdfs.pop((row,col),None)
        if isinstance(self.table.cellWidget(row,col),QLabel):
            self.table.removeCellWidget(row,col)

    def has_pdf(self,row,col):
        return (row,col) in self.pdfs

    def pdf_path(self,row,col):
        return self.pdfs.get((row,col))

    def clear(self):
        for row,col in list(self.pdfs.keys()):
            self.table.removeCellWidget(row,col)
        self.pdfs.clear()