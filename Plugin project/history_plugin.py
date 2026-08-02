from PyQt6.QtWidgets import QTableWidgetItem

class HistoryPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.undo_stack=[]
        self.redo_stack=[]
        
    def create_cell_snapshot(self,row,col):
        item=self.table.item(row,col)
        if item:
            return{
                "row":row,
                "col":col,
                "text":item.text()
            }
        return{
            "row":row,
            "col":col,
            "text":None
        }
    
    def apply_snapshot(self,snapshot):
        row=snapshot["row"]
        col=snapshot["col"]
        text=snapshot["text"]
        self.table.blockSignals(True)
        if text is None:
            self.table.takeItem(row,col)
        else:
            self.table.setItem(row,col,QTableWidgetItem(text))
        self.table.blockSignals(False)
        
    def push_operation(self,before,after):
        self.undo_stack.append({
            "before":before,
            "after":after
        })
        self.redo_stack.clear()
        
    def undo(self):
        if not self.undo_stack:
            return
        operation=self.undo_stack.pop()
        self.table.blockSignals(True)
        for snapshot in operation["before"]:
            self.apply_snapshot(snapshot)
        self.table.blockSignals(False)
        self.redo_stack.append(operation)
    
    def redo(self):
        if not self.redo_stack:
            return
        operation=self.redo_stack.pop()
        self.table.blockSignals(True)
        for snapshot in operation["after"]:
            self.apply_snapshot(snapshot)
        self.table.blockSignals(False)
        self.undo_stack.append(operation)