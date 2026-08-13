import os
from PyQt6.QtWidgets import QFileDialog,QTableWidgetItem

class ImagePlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.images={}
        self.images_map={self.table:self.images}

    def insert_image(self):
        row=self.table.currentRow()
        col=self.table.currentColumn()
        if row<0 or col<0:
            return
        file,_=QFileDialog.getOpenFileName(
            self.spreadsheet,"Select Image","","Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
            )
        if not file:
            return
        self.set_image(row,col,file)

    def set_image(self,row,col,path):
        self.images=self.images_map.setdefault(self.table,{})
        self.table.removeCellWidget(row,col)
        item=self.table.item(row,col)
        if item is None:
            item=QTableWidgetItem()
            self.table.setItem(row,col,item)
        item.setText(os.path.basename(path))
        self.images[(row,col)]=path
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.pdfs.pop((row,col),None)

    def shift_rows(self,start_row,offset):
        self.images=self.images_map.setdefault(self.table,{})
        updated={}
        for (row,col),path in sorted(self.images.items()):
            if row>=start_row:
                updated[(row+offset,col)]=path
            else:
                updated[(row,col)]=path
        self.images=updated
        self.images_map[self.table]=self.images
        self.refresh_images()

    def shift_columns(self,start_col,offset):
        self.images=self.images_map.setdefault(self.table,{})
        updated={}
        for (row,col),path in sorted(self.images.items()):
            if col>=start_col:
                updated[(row,col+offset)]=path
            else:
                updated[(row,col)]=path
        self.images=updated
        self.images_map[self.table]=self.images
        self.refresh_images()

    def refresh_images(self):
        self.images=self.images_map.setdefault(self.table,{})
        for (row,col),path in self.images.items():
            if not os.path.exists(path):
                continue
            item=self.table.item(row,col)
            if item is None:
                item=QTableWidgetItem()
                self.table.setItem(row,col,item)
            item.setText(os.path.basename(path))
            self.table.removeCellWidget(row,col)

    def remove_image(self,row,col):
        self.images=self.images_map.setdefault(self.table,{})
        self.images.pop((row,col),None)
        self.table.removeCellWidget(row,col)

    def has_image(self,row,col):
        self.images=self.images_map.setdefault(self.table,{})
        return (row,col) in self.images

    def image_path(self,row,col):
        self.images=self.images_map.setdefault(self.table,{})
        return self.images.get((row,col))

    def clear(self):
        self.images=self.images_map.setdefault(self.table,{})
        for row,col in list(self.images.keys()):
            self.table.removeCellWidget(row,col)
        self.images.clear()