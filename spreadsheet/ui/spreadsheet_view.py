from PyQt6.QtWidgets import QTableWidget

class SpreadsheetView(QTableWidget):
    def __init__(self):
        super().__init__(50,26)
        self.setHorizontalHeaderLabels([chr(65+i) for i in range(26)])
        self.verticalHeader().setDefaultSectionSize(24)
        self.horizontalHeader().setDefaultSectionSize(90)