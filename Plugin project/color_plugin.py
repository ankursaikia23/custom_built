from PyQt6.QtWidgets import QColorDialog
from PyQt6.QtGui import QColor

class ColorPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def selected_items(self):
        return self.table.selectedItems()

    def set_font_color(self,color=None):
        if color is None:
            color=QColorDialog.getColor(parent=self.spreadsheet)
        if not isinstance(color,QColor) or not color.isValid():
            return
        for item in self.selected_items():
            item.setForeground(color)

    def set_background_color(self,color=None):
        if color is None:
            color=QColorDialog.getColor(parent=self.spreadsheet)
        if not isinstance(color,QColor) or not color.isValid():
            return
        for item in self.selected_items():
            item.setBackground(color)

    def clear_font_color(self):
        for item in self.selected_items():
            item.setForeground(QColor("black"))

    def clear_background_color(self):
        for item in self.selected_items():
            item.setBackground(QColor("white"))