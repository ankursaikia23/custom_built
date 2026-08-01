import os
from PyQt6.QtWidgets import QFileDialog,QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class ImagePlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.images={}

    def insert_image(self):
        row=self.table.currentRow()
        col=self.table.currentColumn()
        if row<0 or col<0:
            return
        file,_=QFileDialog.getOpenFileName(self.spreadsheet,"Select Image","","Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if not file:
            return
        self.set_image(row,col,file)

    def set_image(self,row,col,path):
        self.table.takeItem(row,col)
        self.table.removeCellWidget(row,col)
        pixmap=QPixmap(path)
        label=QLabel()
        label.setPixmap(pixmap.scaled(150,150,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row,col,label)
        self.table.setRowHeight(row,160)
        self.table.setColumnWidth(col,160)
        self.images[(row,col)]=path
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.pdfs.pop((row,col),None)

    def remove_image(self,row,col):
        self.images.pop((row,col),None)
        if isinstance(self.table.cellWidget(row,col),QLabel):
            self.table.removeCellWidget(row,col)

    def has_image(self,row,col):
        return (row,col) in self.images

    def image_path(self,row,col):
        return self.images.get((row,col))

    def clear(self):
        for row,col in list(self.images.keys()):
            self.table.removeCellWidget(row,col)
        self.images.clear()