from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem

class KeyboardPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def handle_key_press(self,event):
        if event.modifiers()==Qt.KeyboardModifier.ControlModifier:
            if event.key()==Qt.Key.Key_C:
                if hasattr(self.spreadsheet,"clipboard_plugin"):
                    self.spreadsheet.clipboard_plugin.copy_selection()
                return True
            elif event.key()==Qt.Key.Key_X:
                if hasattr(self.spreadsheet,"clipboard_plugin"):
                    self.spreadsheet.clipboard_plugin.cut_selection()
                return True
            elif event.key()==Qt.Key.Key_V:
                if hasattr(self.spreadsheet,"clipboard_plugin"):
                    self.spreadsheet.clipboard_plugin.paste_selection()
                return True
            elif event.key()==Qt.Key.Key_Z:
                if hasattr(self.spreadsheet,"history_plugin"):
                    self.spreadsheet.history_plugin.undo()
                return True
            elif event.key()==Qt.Key.Key_Y:
                if hasattr(self.spreadsheet,"history_plugin"):
                    self.spreadsheet.history_plugin.redo()
                return True
        if event.key() in(Qt.Key.Key_Return,Qt.Key.Key_Enter):
            if self.table.state()==self.table.State.EditingState:
                self.table.closePersistentEditor(self.table.currentItem())
                self.table.clearFocus()
                r=self.table.currentRow()
                c=self.table.currentColumn()
                if r<self.table.rowCount()-1:
                    self.table.setCurrentCell(r+1,c)
                return True
            row=self.table.currentRow()
            col=self.table.currentColumn()
            item=self.table.item(row,col)
            if item is None:
                item=QTableWidgetItem("")
                self.table.setItem(row,col,item)
            if hasattr(self.spreadsheet,"cell_plugin"):
                self.spreadsheet.cell_plugin.start_edit(item)
            return True
        return False