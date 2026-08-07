import os
from PyQt6.QtWidgets import QFileDialog,QLabel
from PyQt6.QtCore import Qt

class PDFPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.pdfs={}
        self.pdfs_map={self.table:self.pdfs}

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
        self.pdfs=self.pdfs_map.setdefault(self.table,{})
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
            
    def shift_rows(self,start_row,offset):
        self.pdfs=self.pdfs_map.setdefault(self.table,{})
        updated={}
        for (row,col),path in sorted(self.pdfs.items()):
            if row>=start_row:
                updated[(row+offset,col)]=path
            else:
                updated[(row,col)]=path
        self.pdfs=updated
        self.refresh_pdfs()
    
    def shift_columns(self,start_col,offset):
        self.pdfs=self.pdfs_map.setdefault(self.table,{})
        updated={}
        for (row,col),path in sorted(self.pdfs.items()):
            if col>=start_col:
                updated[(row,col+offset)]=path
            else:
                updated[(row,col)]=path
        self.pdfs=updated
        self.refresh_pdfs()
    
    def refresh_pdfs(self):
        self.pdfs=self.pdfs_map.setdefault(self.table,{})
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                widget=self.table.cellWidget(row,col)
                if isinstance(widget,QLabel) and (row,col) not in getattr(self.spreadsheet.image_plugin,"images",{}):
                    self.table.removeCellWidget(row,col)
        for (row,col),path in self.pdfs.items():
            if os.path.exists(path):
                label=QLabel("📄\n"+os.path.basename(path))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(row,col,label)
                self.table.setRowHeight(row,80)
                self.table.setColumnWidth(col,180)

    def remove_pdf(self,row,col):
        self.pdfs=self.pdfs_map.setdefault(self.table,{})
        self.pdfs.pop((row,col),None)
        if isinstance(self.table.cellWidget(row,col),QLabel):
            self.table.removeCellWidget(row,col)

    def has_pdf(self,row,col):
        self.pdfs=self.pdfs_map.setdefault(self.table,{})
        return (row,col) in self.pdfs

    def pdf_path(self,row,col):
        self.pdfs=self.pdfs_map.setdefault(self.table,{})
        return self.pdfs.get((row,col))

    def clear(self):
        self.pdfs=self.pdfs_map.setdefault(self.table,{})
        for row,col in list(self.pdfs.keys()):
            self.table.removeCellWidget(row,col)
        self.pdfs.clear()