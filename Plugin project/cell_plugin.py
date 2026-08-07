from PyQt6.QtWidgets import QTableWidgetItem

class CellPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.edit_before=""
        self.edit_snapshot=None
        self.table.itemDoubleClicked.connect(self.start_edit)
        self.table.itemChanged.connect(self.finish_edit)

    def start_edit(self,item):
        self.edit_before=""
        self.edit_snapshot=None
        if item:
            self.edit_before=item.text()
            self.edit_snapshot=self.spreadsheet.history_plugin.create_cell_snapshot(item.row(),item.column())
        self.table.editItem(item)
        if hasattr(self.spreadsheet,"formulabar_plugin"):
            self.spreadsheet.formulabar_plugin.selecting_formula=False
        editor=self.table.focusWidget()
        if editor and hasattr(editor,"selectAll"):
            editor.selectAll()

    def finish_edit(self,item):
        if not item:
            return
        if hasattr(self.spreadsheet,"formulabar_plugin"):
            self.spreadsheet.formulabar_plugin.selecting_formula=False
        lines=max(1,item.text().count("\n")+1)
        fm=self.table.fontMetrics()
        self.table.setRowHeight(item.row(),max(30,lines*fm.lineSpacing()+10))
        if item.text()==self.edit_before:
            return
        after=self.spreadsheet.history_plugin.create_cell_snapshot(item.row(),item.column())
        self.spreadsheet.history_plugin.push_operation([self.edit_snapshot],[after])
        if hasattr(self.spreadsheet,"formula_plugin"):
            self.spreadsheet.formula_plugin.recalculate()

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