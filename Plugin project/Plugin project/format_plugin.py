from PyQt6.QtGui import QFont

class FormatPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def selected_items(self):
        return self.table.selectedItems()

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