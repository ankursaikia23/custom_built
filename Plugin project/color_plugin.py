from PyQt6.QtWidgets import QColorDialog
from PyQt6.QtGui import QColor

class ColorPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def selected_items(self):
        return self.table.selectedItems()

    def set_font_color(self,color=None):
        if not isinstance(color,QColor):
            color=QColorDialog.getColor(parent=self.spreadsheet)

        if not color.isValid():
            return

        indexes=self.table.selectedIndexes()

        for index in indexes:
            item=self.table.item(index.row(),index.column())

            if item is None:
                from PyQt6.QtWidgets import QTableWidgetItem
                item=QTableWidgetItem("")
                self.table.setItem(index.row(),index.column(),item)

            item.setForeground(color)

    def set_background_color(self,color=None):
        if not isinstance(color,QColor):
            color=QColorDialog.getColor(parent=self.spreadsheet)

        if not color.isValid():
            return

        indexes=self.table.selectedIndexes()

        for index in indexes:
            item=self.table.item(index.row(),index.column())

            if item is None:
                from PyQt6.QtWidgets import QTableWidgetItem
                item=QTableWidgetItem("")
                self.table.setItem(index.row(),index.column(),item)

            item.setBackground(color)

    def clear_font_color(self):
        for item in self.selected_items():
            item.setForeground(QColor("black"))

    def clear_background_color(self):
        for item in self.selected_items():
            item.setBackground(QColor("white"))