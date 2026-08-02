from PyQt6.QtGui import QFont

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
            font=item.font()
            if enabled is None:
                font.setBold(not font.bold())
            else:
                font.setBold(enabled)
            item.setFont(font)

    def set_italic(self,enabled=None):
        for item in self.selected_items():
            font=item.font()
            if enabled is None:
                font.setItalic(not font.italic())
            else:
                font.setItalic(enabled)
            item.setFont(font)

    def set_underline(self,enabled=None):
        for item in self.selected_items():
            font=item.font()
            if enabled is None:
                font.setUnderline(not font.underline())
            else:
                font.setUnderline(enabled)
            item.setFont(font)
            
    def set_strike(self,enabled=None):
        for item in self.selected_items():
            font=item.font()
            if enabled is None:
                font.setStrikeOut(not font.strikeOut())
            else:
                font.setStrikeOut(enabled)
            item.setFont(font)
            
    def toggle_wrap_text(self):
        rows=set()
        for item in self.selected_items():
            item.setText(item.text())
            rows.add(item.row())
        for row in rows:
            self.table.resizeRowToContents(row)