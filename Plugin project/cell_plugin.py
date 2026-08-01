from PyQt6.QtWidgets import QTableWidgetItem

class CellPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.edit_before=""
        self.table.itemDoubleClicked.connect(self.start_edit)
        self.table.itemChanged.connect(self.finish_edit)

    def start_edit(self,item):
        self.edit_before=""
        if item:
            self.edit_before=item.text()
        self.table.editItem(item)
        editor=self.table.focusWidget()
        if editor and hasattr(editor,"selectAll"):
            editor.selectAll()

    def finish_edit(self,item):
        if not item:
            return
        lines=max(1,item.text().count("\n")+1)
        fm=self.table.fontMetrics()
        self.table.setRowHeight(item.row(),max(30,lines*fm.lineSpacing()+10))
        if item.text()!=self.edit_before and hasattr(self.spreadsheet,"history_plugin"):
            self.spreadsheet.history_plugin.save_state()

    def current_item(self):
        return self.table.currentItem()

    def current_text(self):
        item=self.table.currentItem()
        if item:
            return item.text()
        return ""

    def set_text(self,row,col,text):
        item=self.table.item(row,col)
        if item is None:
            item=QTableWidgetItem()
            self.table.setItem(row,col,item)
        item.setText(text)

    def clear_cell(self,row,col):
        self.table.takeItem(row,col)
        self.table.removeCellWidget(row,col)