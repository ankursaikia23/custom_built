from PyQt6.QtWidgets import QLabel

class StatusBarPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.statusbar=spreadsheet.statusBar()
        self.position_label=QLabel("Row: 1 | Column: A")
        self.operation_label=QLabel("Ready")
        self.statusbar.addPermanentWidget(self.position_label)
        self.statusbar.addWidget(self.operation_label,1)
        self.table.currentCellChanged.connect(self.update_position)

    def update_position(self,currentRow,currentColumn,previousRow,previousColumn):
        if currentRow<0 or currentColumn<0:
            self.position_label.setText("Row: - | Column: -")
            return
        column=""
        n=currentColumn+1
        while n:
            n,rem=divmod(n-1,26)
            column=chr(65+rem)+column
        self.position_label.setText(f"Row: {currentRow+1} | Column: {column}")
        
    def show_operation(self,text):
        self.operation_label.setText(text)