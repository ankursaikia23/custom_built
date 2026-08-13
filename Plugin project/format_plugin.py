from PyQt6.QtGui import QFont,QBrush,QColor
from PyQt6.QtCore import Qt

class FormatPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def selected_items(self):
        return self.table.selectedItems()

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

    def set_italic(self,enabled=None):
        for item in self.selected_items():
            font=QFont(item.font())
            font.setItalic(not font.italic() if enabled is None else enabled)
            item.setFont(font)

    def set_underline(self,enabled=None):
        for item in self.selected_items():
            font=QFont(item.font())
            font.setUnderline(not font.underline() if enabled is None else enabled)
            item.setFont(font)

    def set_strike(self,enabled=None):
        for item in self.selected_items():
            font=QFont(item.font())
            font.setStrikeOut(not font.strikeOut() if enabled is None else enabled)
            item.setFont(font)

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
        table.viewport().update()

    def set_font_color(self,color):
        for item in self.selected_items():
            item.setForeground(QBrush(color))

    def set_fill_color(self,color):
        for item in self.selected_items():
            item.setBackground(QBrush(color))