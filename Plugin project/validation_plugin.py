from PyQt6.QtWidgets import QMessageBox

class ValidationPlugin:
    def __init__(self,window):
        self.window=window

    def validate_number(self,row,column):
        item=self.window.table.item(row,column)
        if item:
            try:
                float(item.text())
                return True
            except:
                QMessageBox.warning(self.window,"Validation","Only numbers allowed")
                item.setText("")
                return False

    def validate_text(self,row,column):
        item=self.window.table.item(row,column)
        if item and item.text().isdigit():
            QMessageBox.warning(self.window,"Validation","Only text allowed")
            item.setText("")
            return False
        return True

    def validate_dropdown(self,row,column,values):
        item=self.window.table.item(row,column)
        if item and item.text() not in values:
            QMessageBox.warning(self.window,"Validation","Invalid value")
            item.setText("")
            return False
        return True