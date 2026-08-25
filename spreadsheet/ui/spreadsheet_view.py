from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

class SpreadsheetView(QTableWidget):
    def __init__(self):
        super().__init__(50,26)
        self.setHorizontalHeaderLabels([chr(65+i) for i in range(26)])
        self.verticalHeader().setDefaultSectionSize(24)
        self.horizontalHeader().setDefaultSectionSize(90)

    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            row=self.currentRow()
            column=self.currentColumn()
            if row>0:
                self.setCurrentCell(row-1,column)
            return
        super().keyPressEvent(event)