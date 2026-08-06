from PyQt6.QtWidgets import QMenu
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtCore import Qt

class ContextMenuPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_menu)
        self.table.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.verticalHeader().customContextMenuRequested.connect(self.show_row_menu)
        self.table.horizontalHeader().customContextMenuRequested.connect(self.show_column_menu)
        
    def show_row_menu(self,pos):
        row=self.table.verticalHeader().logicalIndexAt(pos)
        if row<0:
            return
        if not self.table.selectionModel().isRowSelected(row,self.table.rootIndex()):
            self.table.selectRow(row)
        menu=QMenu(self.table)
        insert_action=menu.addAction("Insert Row")
        delete_action=menu.addAction("Delete Selected Rows")
        action=menu.exec(self.table.verticalHeader().viewport().mapToGlobal(pos))
        if action==insert_action:
            self.insert_rows(row)
        elif action==delete_action:
            self.delete_selected_rows()
    
    def show_column_menu(self,pos):
        col=self.table.horizontalHeader().logicalIndexAt(pos)
        if col<0:
            return
        if not self.table.selectionModel().isColumnSelected(col,self.table.rootIndex()):
            self.table.selectColumn(col)
        menu=QMenu(self.table)
        insert_action=menu.addAction("Insert Column")
        delete_action=menu.addAction("Delete Selected Columns")
        action=menu.exec(self.table.horizontalHeader().viewport().mapToGlobal(pos))
        if action==insert_action:
            self.insert_columns(col)
        elif action==delete_action:
            self.delete_selected_columns()
            
    def insert_rows(self,row):
        count,ok=QInputDialog.getInt(
            self.table,
            "Insert Rows",
            "Number of rows:",
            1,
            1,
            1000
        )
        if not ok:
            return
        for _ in range(count):
            self.table.insertRow(row)
            if row>0:
                self.table.setRowHeight(row,self.table.rowHeight(row-1))
            elif self.table.rowCount()>1:
                self.table.setRowHeight(row,self.table.rowHeight(1))
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.shift_rows(row,count)
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.shift_rows(row,count)
        if hasattr(self.spreadsheet,"border_plugin"):
            self.spreadsheet.border_plugin.shift_rows(row,count)
        self.spreadsheet.history_plugin.push_operation(
            [],
            [],
            "insert_rows",
            {"row":row,"count":count}
        )
        if hasattr(self.spreadsheet,"grid_plugin"):
            self.spreadsheet.grid_plugin.refresh_headers()
    
    def delete_selected_rows(self):
        rows=sorted(set(index.row() for index in self.table.selectionModel().selectedRows()),reverse=True)
        if not rows:
            return
        deleted=[]
        for row in sorted(rows):
            deleted.append(self.spreadsheet.history_plugin.create_row_snapshot(row))
        for row in rows:
            self.table.removeRow(row)
        if hasattr(self.spreadsheet,"border_plugin"):
            self.spreadsheet.border_plugin.remove_rows(min(rows),len(rows))
        self.spreadsheet.history_plugin.push_operation(
            [],
            [],
            "delete_rows",
            {"row":min(rows),"count":len(rows),"snapshots":deleted}
        )
        if hasattr(self.spreadsheet,"grid_plugin"):
            self.spreadsheet.grid_plugin.refresh_headers()
    
    def insert_columns(self,col):
        count,ok=QInputDialog.getInt(
            self.table,
            "Insert Columns",
            "Number of columns:",
            1,
            1,
            1000
        )
        if not ok:
            return
        for _ in range(count):
            self.table.insertColumn(col)
            if col>0:
                self.table.setColumnWidth(col,self.table.columnWidth(col-1))
            elif self.table.columnCount()>1:
                self.table.setColumnWidth(col,self.table.columnWidth(1))
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.shift_columns(col,count)
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.shift_columns(col,count)
        if hasattr(self.spreadsheet,"border_plugin"):
            self.spreadsheet.border_plugin.shift_columns(col,count)
        self.spreadsheet.history_plugin.push_operation(
            [],
            [],
            "insert_columns",
            {"col":col,"count":count}
        )
        if hasattr(self.spreadsheet,"grid_plugin"):
            self.spreadsheet.grid_plugin.refresh_headers()
    
    def delete_selected_columns(self):
        cols=sorted(set(index.column() for index in self.table.selectionModel().selectedColumns()),reverse=True)
        if not cols:
            return
        deleted=[]
        for col in sorted(cols):
            deleted.append(self.spreadsheet.history_plugin.create_column_snapshot(col))
        for col in cols:
            self.table.removeColumn(col)
        if hasattr(self.spreadsheet,"border_plugin"):
            self.spreadsheet.border_plugin.remove_columns(min(cols),len(cols))
        self.spreadsheet.history_plugin.push_operation(
            [],
            [],
            "delete_columns",
            {"col":min(cols),"count":len(cols),"snapshots":deleted}
        )
        if hasattr(self.spreadsheet,"grid_plugin"):
            self.spreadsheet.grid_plugin.refresh_headers()

    def show_menu(self,pos):
        menu=QMenu(self.table)
        copy_action=menu.addAction("Copy")
        cut_action=menu.addAction("Cut")
        paste_action=menu.addAction("Paste")
        menu.addSeparator()
        menu.addSeparator()
        image_action=menu.addAction("Insert Image")
        pdf_action=menu.addAction("Insert PDF")
        remove_action=menu.addAction("Remove Item")
        action=menu.exec(self.table.viewport().mapToGlobal(pos))
        if action==copy_action and hasattr(self.spreadsheet,"clipboard_plugin"):
            self.spreadsheet.clipboard_plugin.copy_selection()
        elif action==cut_action and hasattr(self.spreadsheet,"clipboard_plugin"):
            self.spreadsheet.clipboard_plugin.cut_selection()
        elif action==paste_action and hasattr(self.spreadsheet,"clipboard_plugin"):
            self.spreadsheet.clipboard_plugin.paste_selection()
        elif action==image_action and hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.insert_image()
        elif action==pdf_action and hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.insert_pdf()
        elif action==remove_action:
            r=self.table.currentRow()
            c=self.table.currentColumn()
            self.table.takeItem(r,c)
            self.table.removeCellWidget(r,c)
            if hasattr(self.spreadsheet,"image_plugin"):
                self.spreadsheet.image_plugin.images.pop((r,c),None)
            if hasattr(self.spreadsheet,"pdf_plugin"):
                self.spreadsheet.pdf_plugin.pdfs.pop((r,c),None)