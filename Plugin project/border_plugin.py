from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen
from PyQt6.QtWidgets import QStyledItemDelegate

class BorderDelegate(QStyledItemDelegate):
    def __init__(self,border_plugin,parent=None):
        super().__init__(parent)
        self.border_plugin=border_plugin

    def paint(self,painter,option,index):
        super().paint(painter,option,index)

        key=(index.row(),index.column())

        if key not in self.border_plugin.border_data:
            return

        border=self.border_plugin.border_data[key]

        painter.save()

        pen=QPen(Qt.GlobalColor.black)
        pen.setWidth(1)

        painter.setPen(pen)

        rect=option.rect

        if border["top"]:
            painter.drawLine(
                rect.left(),
                rect.top()+1,
                rect.right(),
                rect.top()+1
            )

        if border["bottom"]:
            painter.drawLine(
                rect.left(),
                rect.bottom()-1,
                rect.right(),
                rect.bottom()-1
            )

        if border["left"]:
            painter.drawLine(
                rect.left()+1,
                rect.top(),
                rect.left()+1,
                rect.bottom()
            )

        if border["right"]:
            painter.drawLine(
                rect.right()-1,
                rect.top(),
                rect.right()-1,
                rect.bottom()
            )

        painter.restore()

class BorderPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.border_data={}
        self.delegate=BorderDelegate(self,self.table)
        self.table.setItemDelegate(self.delegate)
        
    def refresh(self):
        self.table.viewport().update()
        self.table.viewport().repaint()
        
    def shift_rows(self,start_row,offset):
        updated={}
        for (row,col),border in self.border_data.items():
            if row>=start_row:
                updated[(row+offset,col)]=border.copy()
            else:
                updated[(row,col)]=border.copy()
        self.border_data=updated
        self.refresh()
    
    def shift_columns(self,start_col,offset):
        updated={}
        for (row,col),border in self.border_data.items():
            if col>=start_col:
                updated[(row,col+offset)]=border.copy()
            else:
                updated[(row,col)]=border.copy()
        self.border_data=updated
        self.refresh()
    
    def remove_rows(self,start_row,count):
        updated={}
        for (row,col),border in self.border_data.items():
            if row<start_row:
                updated[(row,col)]=border.copy()
            elif row>=start_row+count:
                updated[(row-count,col)]=border.copy()
        self.border_data=updated
        self.refresh()
    
    def remove_columns(self,start_col,count):
        updated={}
        for (row,col),border in self.border_data.items():
            if col<start_col:
                updated[(row,col)]=border.copy()
            elif col>=start_col+count:
                updated[(row,col-count)]=border.copy()
        self.border_data=updated
        self.refresh()
        
    def apply_border(self,border_type):
        ranges=self.table.selectedRanges()
    
        if not ranges:
            return
    
        selection=ranges[0]
    
        top=selection.topRow()
        bottom=selection.bottomRow()
        left=selection.leftColumn()
        right=selection.rightColumn()
    
        for row in range(top,bottom+1):
    
            for col in range(left,right+1):
    
                key=(row,col)
    
                border=self.border_data.setdefault(
                    key,
                    {
                        "top":False,
                        "bottom":False,
                        "left":False,
                        "right":False
                    }
                )
    
                if border_type=="none":
                    border["top"]=False
                    border["bottom"]=False
                    border["left"]=False
                    border["right"]=False
    
                elif border_type=="all":
                    border["top"]=True
                    border["bottom"]=True
                    border["left"]=True
                    border["right"]=True
    
                elif border_type=="top":
                    border["top"]=True
    
                elif border_type=="bottom":
                    border["bottom"]=True
    
                elif border_type=="left":
                    border["left"]=True
    
                elif border_type=="right":
                    border["right"]=True
    
                elif border_type=="outer":
    
                    if row==top:
                        border["top"]=True
    
                    if row==bottom:
                        border["bottom"]=True
    
                    if col==left:
                        border["left"]=True
    
                    if col==right:
                        border["right"]=True
    
                elif border_type=="inner":
    
                    if row<bottom:
                        border["bottom"]=True
    
                    if col<right:
                        border["right"]=True
        self.table.clearSelection()
        self.table.viewport().update()
        self.table.viewport().repaint()
        self.refresh()
        
    
    
   
    
   
    
   
    
    
    