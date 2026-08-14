from PyQt6.QtWidgets import QCalendarWidget,QDialog,QVBoxLayout,QTableWidgetItem

class DatePlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def insert_date(self):
        dialog=QDialog(self.spreadsheet)
        dialog.setWindowTitle("Select Date")
        layout=QVBoxLayout(dialog)
        calendar=QCalendarWidget()
        layout.addWidget(calendar)
        calendar.activated.connect(lambda:self.apply_date(calendar.selectedDate().toString("yyyy-MM-dd"),dialog))
        dialog.exec()

    def apply_date(self,date_text,dialog=None):
        row=self.table.currentRow()
        col=self.table.currentColumn()
        if row<0 or col<0:
            if dialog:
                dialog.accept()
            return
        item=self.table.item(row,col)
        if item is None:
            item=QTableWidgetItem()
            self.table.setItem(row,col,item)
        item.setText(date_text)
        self.spreadsheet.is_modified=True
        if dialog:
            dialog.accept()