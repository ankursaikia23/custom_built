from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt

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
                "text":item.text(),
                "formula":item.data(Qt.ItemDataRole.UserRole)
            }
        return{
            "row":row,
            "col":col,
            "text":None,
            "formula":None
        }
    
    def create_row_snapshot(self,row):
        snapshots=[]
        for col in range(self.table.columnCount()):
            snapshots.append(self.create_cell_snapshot(row,col))
        return snapshots
    
    def create_column_snapshot(self,col):
        snapshots=[]
        for row in range(self.table.rowCount()):
            snapshots.append(self.create_cell_snapshot(row,col))
        return snapshots
    
    def apply_snapshot(self,snapshot):
        row=snapshot["row"]
        col=snapshot["col"]
        text=snapshot["text"]
        formula=snapshot["formula"]
        self.table.blockSignals(True)
        if text is None:
            self.table.takeItem(row,col)
        else:
            item=QTableWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole,formula)
            self.table.setItem(row,col,item)
        self.table.blockSignals(False)
        if hasattr(self.spreadsheet,"formula_plugin"):
            self.spreadsheet.formula_plugin.recalculate()
        
    def push_operation(self,before,after,operation_type="cells",operation_data=None):
        self.undo_stack.append({
            "before":before,
            "after":after,
            "type":operation_type,
            "data":operation_data
        })
        self.redo_stack.clear()
        
    def undo(self):
        if not self.undo_stack:
            return
        operation=self.undo_stack.pop()
        self.table.blockSignals(True)
        if operation["type"]=="cells":
            for snapshot in operation["before"]:
                self.apply_snapshot(snapshot)
        elif operation["type"]=="insert_rows":
            row=operation["data"]["row"]
            count=operation["data"]["count"]
            for _ in range(count):
                self.table.removeRow(row)
        elif operation["type"]=="delete_rows":
            row=operation["data"]["row"]
            snapshots=operation["data"]["snapshots"]
            for index,rowdata in enumerate(snapshots):
                self.table.insertRow(row+index)
                for snapshot in rowdata:
                    snapshot["row"]=row+index
                    self.apply_snapshot(snapshot)
        elif operation["type"]=="insert_columns":
            col=operation["data"]["col"]
            count=operation["data"]["count"]
            for _ in range(count):
                self.table.removeColumn(col)
        elif operation["type"]=="delete_columns":
            col=operation["data"]["col"]
            snapshots=operation["data"]["snapshots"]
            for index,coldata in enumerate(snapshots):
                self.table.insertColumn(col+index)
                for snapshot in coldata:
                    snapshot["col"]=col+index
                    self.apply_snapshot(snapshot)
        self.table.blockSignals(False)
        self.redo_stack.append(operation)
    
    def redo(self):
        if not self.redo_stack:
            return
        operation=self.redo_stack.pop()
        self.table.blockSignals(True)
        if operation["type"]=="cells":
            for snapshot in operation["after"]:
                self.apply_snapshot(snapshot)
        elif operation["type"]=="insert_rows":
            row=operation["data"]["row"]
            count=operation["data"]["count"]
            for _ in range(count):
                self.table.insertRow(row)
        elif operation["type"]=="delete_rows":
            row=operation["data"]["row"]
            count=operation["data"]["count"]
            for _ in range(count):
                self.table.removeRow(row)
        elif operation["type"]=="insert_columns":
            col=operation["data"]["col"]
            count=operation["data"]["count"]
            for _ in range(count):
                self.table.insertColumn(col)
        elif operation["type"]=="delete_columns":
            col=operation["data"]["col"]
            count=operation["data"]["count"]
            for _ in range(count):
                self.table.removeColumn(col)
        self.table.blockSignals(False)
        self.undo_stack.append(operation)