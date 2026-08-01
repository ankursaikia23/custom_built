from PyQt6.QtWidgets import QInputDialog,QMessageBox
class SearchPlugin:
    def __init__(self,window):
        self.window=window
    def find(self):
        text,ok=QInputDialog.getText(self.window,"Find","Text:")
        if ok and text:
            for row in range(self.window.table.rowCount()):
                for col in range(self.window.table.columnCount()):
                    item=self.window.table.item(row,col)
                    if item and text.lower() in item.text().lower():
                        self.window.table.setCurrentCell(row,col)
                        return
            QMessageBox.information(self.window,"Find","Not found")
    def replace(self):
        old,ok=QInputDialog.getText(self.window,"Replace","Find:")
        if not ok:
            return
        new,ok=QInputDialog.getText(self.window,"Replace","Replace with:")
        if not ok:
            return
        for row in range(self.window.table.rowCount()):
            for col in range(self.window.table.columnCount()):
                item=self.window.table.item(row,col)
                if item and old in item.text():
                    item.setText(item.text().replace(old,new))