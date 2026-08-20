from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen
from PyQt6.QtWidgets import QStyledItemDelegate

class BorderDelegate(QStyledItemDelegate):
    def __init__(self,border_plugin,parent=None):
        super().__init__(parent)
        self.border_plugin=border_plugin

    def paint(self,painter,option,index):
        super().paint(painter,option,index)
        row=index.row()
        col=index.column()
        current=self.border_plugin.border_data.get((row,col),{})
        above=self.border_plugin.border_data.get((row-1,col),{}) if row>0 else {}
        left=self.border_plugin.border_data.get((row,col-1),{}) if col>0 else {}
        below=self.border_plugin.border_data.get((row+1,col),{})
        right=self.border_plugin.border_data.get((row,col+1),{})
        if not current and not above and not left and not below and not right:
            return
        painter.save()
        pen=QPen(Qt.GlobalColor.black)
        pen.setWidth(1)
        painter.setPen(pen)
        rect=option.rect
        top_y=rect.top()
        bottom_y=rect.bottom()-1
        left_x=rect.left()
        right_x=rect.right()-1
        if current.get("top",False) or above.get("bottom",False):
            painter.drawLine(left_x,top_y,right_x,top_y)
        if current.get("bottom",False) or below.get("top",False):
            painter.drawLine(left_x,bottom_y,right_x,bottom_y)
        if current.get("left",False) or left.get("right",False):
            painter.drawLine(left_x,top_y,left_x,bottom_y)
        if current.get("right",False) or right.get("left",False):
            painter.drawLine(right_x,top_y,right_x,bottom_y)
        painter.restore()

class BorderPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.border_data={}
        self.border_data_map={self.table:self.border_data}
        self.delegate=BorderDelegate(self,self.table)
        self.table.setItemDelegate(self.delegate)

    def refresh(self):
        self.border_data=self.border_data_map.setdefault(self.table,self.border_data)
        self.table.viewport().update()
        self.table.viewport().repaint()

    def shift_rows(self,start_row,offset):
        self.border_data=self.border_data_map.setdefault(self.table,{})
        updated={}
        for (row,col),border in self.border_data.items():
            if row>=start_row:
                updated[(row+offset,col)]=border.copy()
            else:
                updated[(row,col)]=border.copy()
        self.border_data=updated
        self.border_data_map[self.table]=updated
        self.refresh()

    def shift_columns(self,start_col,offset):
        self.border_data=self.border_data_map.setdefault(self.table,{})
        updated={}
        for (row,col),border in self.border_data.items():
            if col>=start_col:
                updated[(row,col+offset)]=border.copy()
            else:
                updated[(row,col)]=border.copy()
        self.border_data=updated
        self.border_data_map[self.table]=updated
        self.refresh()

    def remove_rows(self,start_row,count):
        self.border_data=self.border_data_map.setdefault(self.table,{})
        updated={}
        for (row,col),border in self.border_data.items():
            if row<start_row:
                updated[(row,col)]=border.copy()
            elif row>=start_row+count:
                updated[(row-count,col)]=border.copy()
        self.border_data=updated
        self.border_data_map[self.table]=updated
        self.refresh()

    def remove_columns(self,start_col,count):
        self.border_data=self.border_data_map.setdefault(self.table,{})
        updated={}
        for (row,col),border in self.border_data.items():
            if col<start_col:
                updated[(row,col)]=border.copy()
            elif col>=start_col+count:
                updated[(row,col-count)]=border.copy()
        self.border_data=updated
        self.border_data_map[self.table]=updated
        self.refresh()

    def apply_border(self,border_type):
        self.border_data=self.border_data_map.setdefault(self.table,{})
        ranges=self.table.selectedRanges()
        if not ranges:
            return
        for selection in ranges:
            top=selection.topRow()
            bottom=selection.bottomRow()
            left=selection.leftColumn()
            right=selection.rightColumn()
            for row in range(top,bottom+1):
                for col in range(left,right+1):
                    key=(row,col)
                    if border_type=="none":
                        if key in self.border_data:
                            border=self.border_data[key]
                            border["top"]=False
                            border["bottom"]=False
                            border["left"]=False
                            border["right"]=False
                            if not any(border.values()):
                                del self.border_data[key]
                        continue
                    border=self.border_data.setdefault(key,{"top":False,"bottom":False,"left":False,"right":False})
                    if border_type=="all":
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
        self.border_data_map[self.table]=self.border_data
        self.table.clearSelection()
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=True
        self.table.viewport().update()
        self.table.viewport().repaint()
        self.refresh()