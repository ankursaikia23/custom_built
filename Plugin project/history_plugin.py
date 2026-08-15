from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt

class HistoryPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.undo_stacks={}
        self.redo_stacks={}
        
    def create_cell_snapshot(self,row,col):
        item=self.table.item(row,col)
        if item:
            return{
                "row":row,
                "col":col,
                "text":item.text(),
                "formula":item.data(Qt.ItemDataRole.UserRole),
                "font":item.font(),
                "foreground":item.foreground(),
                "background":item.background(),
                "alignment":item.textAlignment()
            }
        return{
            "row":row,
            "col":col,
            "text":None,
            "formula":None,
            "font":None,
            "foreground":None,
            "background":None,
            "alignment":None
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
        try:
            if text is None:
                self.table.takeItem(row,col)
            else:
                item=QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole,formula)
                if snapshot.get("font") is not None:
                    item.setFont(snapshot["font"])
                if snapshot.get("foreground") is not None:
                    item.setForeground(snapshot["foreground"])
                if snapshot.get("background") is not None:
                    item.setBackground(snapshot["background"])
                if snapshot.get("alignment") is not None:
                    item.setTextAlignment(snapshot["alignment"])
                self.table.setItem(row,col,item)
        finally:
            self.table.blockSignals(False)
        if hasattr(self.spreadsheet,"formula_plugin"):
            self.spreadsheet.formula_plugin.recalculate()
        
    def push_operation(self,before,after,operation_type="cells",operation_data=None):
        table=self.table
        self.undo_stacks.setdefault(table,[])
        self.redo_stacks.setdefault(table,[])
        self.undo_stacks[table].append({
            "before":before,
            "after":after,
            "type":operation_type,
            "data":operation_data
        })
        self.redo_stacks[table].clear()
        
    def undo(self):
        table=self.table
        self.undo_stacks.setdefault(table,[])
        self.redo_stacks.setdefault(table,[])
        if not self.undo_stacks[table]:
            return
        operation=self.undo_stacks[table].pop()
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
                    restored=dict(snapshot)
                    restored["row"]=row+index
                    self.apply_snapshot(restored)
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
                    restored=dict(snapshot)
                    restored["col"]=col+index
                    self.apply_snapshot(restored)
        self.table.blockSignals(False)
        self.redo_stacks[table].append(operation)
        self.spreadsheet.is_modified=True
    
    def redo(self):
        table=self.table
        self.undo_stacks.setdefault(table,[])
        self.redo_stacks.setdefault(table,[])
        if not self.redo_stacks[table]:
            return
        operation=self.redo_stacks[table].pop()
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
        self.undo_stacks[table].append(operation)
        self.spreadsheet.is_modified=True