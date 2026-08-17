from PyQt6.QtGui import QFont, QBrush 
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem

class FormatPlugin:
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

    def get_selected_cell_format(self):
        indexes=self.table.selectedIndexes()
        if len(indexes)!=1:
            return None
        item=self.table.item(indexes[0].row(),indexes[0].column())
        if item is None:
            font=QFont()
            return{
                "bold":font.bold(),
                "italic":font.italic(),
                "underline":font.underline(),
                "strike":font.strikeOut()
            }
        font=item.font()
        return{
            "bold":font.bold(),
            "italic":font.italic(),
            "underline":font.underline(),
            "strike":font.strikeOut()
        }

    def set_bold(self,enabled=None):
        for item in self.selected_items():
            font=QFont(item.font())
            font.setBold(not font.bold() if enabled is None else enabled)
            item.setFont(font)
        self.spreadsheet.is_modified=True

    def set_italic(self,enabled=None):
        for item in self.selected_items():
            font=QFont(item.font())
            font.setItalic(not font.italic() if enabled is None else enabled)
            item.setFont(font)
        self.spreadsheet.is_modified=True

    def set_underline(self,enabled=None):
        for item in self.selected_items():
            font=QFont(item.font())
            font.setUnderline(not font.underline() if enabled is None else enabled)
            item.setFont(font)
        self.spreadsheet.is_modified=True

    def set_strike(self,enabled=None):
        for item in self.selected_items():
            font=QFont(item.font())
            font.setStrikeOut(not font.strikeOut() if enabled is None else enabled)
            item.setFont(font)
        self.spreadsheet.is_modified=True

    def toggle_wrap_text(self):
        table=self.table
        items=self.selected_items()
        for item in items:
            current=item.data(Qt.ItemDataRole.UserRole+1)
            item.setData(Qt.ItemDataRole.UserRole+1,not bool(current))
        rows=set(item.row() for item in items)
        cols=set(item.column() for item in items)
        for row in rows:
            table.resizeRowToContents(row)
        for col in cols:
            table.resizeColumnToContents(col)
        self.spreadsheet.is_modified=True
        table.viewport().update()

    def set_font_color(self,color):
        for item in self.selected_items():
            item.setForeground(QBrush(color))

    def set_fill_color(self,color):
        for item in self.selected_items():
            item.setBackground(QBrush(color))