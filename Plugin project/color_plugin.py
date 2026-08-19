from PyQt6.QtWidgets import QColorDialog, QTableWidgetItem
from PyQt6.QtGui import QColor

class ColorPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def selected_items(self):
        items=[]
        for index in self.table.selectedIndexes():
            item=self.table.item(index.row(),index.column())
            if item is None:
                item=QTableWidgetItem("")
                self.table.setItem(index.row(),index.column(),item)
            items.append(item)
        return items

    def _apply_color(self,attribute,color):
        if not isinstance(color,QColor):
            color=QColorDialog.getColor(parent=self.spreadsheet)
        if not color.isValid():
            return
        before=[]
        after=[]
        for index in self.table.selectedIndexes():
            row=index.row()
            col=index.column()
            item=self.table.item(row,col)
            if item is None:
                item=QTableWidgetItem("")
                self.table.setItem(row,col,item)
            before.append(self.spreadsheet.history_plugin.create_cell_snapshot(row,col))
            if attribute=="font":
                item.setForeground(color)
            else:
                item.setBackground(color)
            after.append(self.spreadsheet.history_plugin.create_cell_snapshot(row,col))
        if before:
            self.spreadsheet.history_plugin.push_operation(before,after)
            self.spreadsheet.is_modified=True

    def set_font_color(self,color=None):
        self._apply_color("font",color)

    def set_background_color(self,color=None):
        self._apply_color("background",color)

    def clear_font_color(self):
        self._apply_color("font",QColor("black"))

    def clear_background_color(self):
        self._apply_color("background",QColor("white"))