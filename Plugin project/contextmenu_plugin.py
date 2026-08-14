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
        insert_menu=menu.addMenu("Insert Rows")
        insert_action=insert_menu.addAction("Insert Rows...")
        delete_action=menu.addAction("Delete Selected Rows")
        action=menu.exec(self.table.verticalHeader().viewport().mapToGlobal(pos))
        if action==insert_action:
            count,ok=QInputDialog.getInt(self.table,"Insert Rows","Number of rows:",1,1,1000,1)
            if not ok:
                return
            direction_menu=QMenu(self.table)
            up_action=direction_menu.addAction("Insert Above")
            down_action=direction_menu.addAction("Insert Below")
            direction=direction_menu.exec(self.table.verticalHeader().viewport().mapToGlobal(pos))
            if direction==up_action:
                self.insert_rows(row,"up",count)
            elif direction==down_action:
                self.insert_rows(row,"down",count)
        elif action==delete_action:
            self.delete_selected_rows()
    
    def show_column_menu(self,pos):
        col=self.table.horizontalHeader().logicalIndexAt(pos)
        if col<0:
            return
        if not self.table.selectionModel().isColumnSelected(col,self.table.rootIndex()):
            self.table.selectColumn(col)
        menu=QMenu(self.table)
        insert_menu=menu.addMenu("Insert Columns")
        insert_action=insert_menu.addAction("Insert Columns...")
        delete_action=menu.addAction("Delete Selected Columns")
        action=menu.exec(self.table.horizontalHeader().viewport().mapToGlobal(pos))
        if action==insert_action:
            count,ok=QInputDialog.getInt(self.table,"Insert Columns","Number of columns:",1,1,1000,1)
            if not ok:
                return
            direction_menu=QMenu(self.table)
            left_action=direction_menu.addAction("Insert Left")
            right_action=direction_menu.addAction("Insert Right")
            direction=direction_menu.exec(self.table.horizontalHeader().viewport().mapToGlobal(pos))
            if direction==left_action:
                self.insert_columns(col,"left",count)
            elif direction==right_action:
                self.insert_columns(col,"right",count)
        elif action==delete_action:
            self.delete_selected_columns()
            
    def insert_rows(self,row,direction="up",count=1):
        selected_rows=sorted(set(index.row() for index in self.table.selectionModel().selectedRows()))
        if not selected_rows:
            selected_rows=[row]
        first_row=min(selected_rows)
        last_row=max(selected_rows)
        insert_at=first_row if direction=="up" else last_row+1
        for _ in range(count):
            self.table.insertRow(insert_at)
            if insert_at>0:
                self.table.setRowHeight(insert_at,self.table.rowHeight(insert_at-1))
            elif self.table.rowCount()>1:
                self.table.setRowHeight(insert_at,self.table.rowHeight(insert_at+1))
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.shift_rows(insert_at,count)
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.shift_rows(insert_at,count)
        if hasattr(self.spreadsheet,"border_plugin"):
            self.spreadsheet.border_plugin.shift_rows(insert_at,count)
        self.spreadsheet.history_plugin.push_operation(
            [],
            [],
            "insert_rows",
            {"row":insert_at,"count":count}
        )
        self.spreadsheet.is_modified=True
        if hasattr(self.spreadsheet,"grid_plugin"):
            self.spreadsheet.grid_plugin.refresh_headers()
    
    def delete_selected_rows(self):
        rows=sorted(set(index.row() for index in self.table.selectionModel().selectedRows()),reverse=True)
        if not rows:
            return
        deleted=[]
        for row in sorted(rows):
            deleted.append(self.spreadsheet.history_plugin.create_row_snapshot(row))
        if hasattr(self.spreadsheet,"image_plugin"):
            images=self.spreadsheet.image_plugin.images
            updated={}
            deleted_set=set(rows)
            for (r,c),path in images.items():
                if r in deleted_set:
                    continue
                shift=sum(1 for deleted_row in rows if deleted_row<r)
                updated[(r-shift,c)]=path
            self.spreadsheet.image_plugin.images=updated
            self.spreadsheet.image_plugin.images_map[self.table]=updated
        for row in rows:
            self.table.removeRow(row)
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.refresh_images()
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.refresh_pdfs()
        if hasattr(self.spreadsheet,"border_plugin"):
            for row in rows:
                self.spreadsheet.border_plugin.remove_rows(row,1)
        self.spreadsheet.history_plugin.push_operation(
            [],
            [],
            "delete_rows",
            {"row":min(rows),"count":len(rows),"snapshots":deleted}
        )
        self.spreadsheet.is_modified=True
        if hasattr(self.spreadsheet,"grid_plugin"):
            self.spreadsheet.grid_plugin.refresh_headers()
    
    def insert_columns(self,col,direction="left",count=1):
        selected_columns=sorted(set(index.column() for index in self.table.selectionModel().selectedColumns()))
        if not selected_columns:
            selected_columns=[col]
        first_col=min(selected_columns)
        last_col=max(selected_columns)
        insert_at=first_col if direction=="left" else last_col+1
        for _ in range(count):
            self.table.insertColumn(insert_at)
            if insert_at>0:
                self.table.setColumnWidth(insert_at,self.table.columnWidth(insert_at-1))
            elif self.table.columnCount()>1:
                self.table.setColumnWidth(insert_at,self.table.columnWidth(insert_at+1))
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.shift_columns(insert_at,count)
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.shift_columns(insert_at,count)
        if hasattr(self.spreadsheet,"border_plugin"):
            self.spreadsheet.border_plugin.shift_columns(insert_at,count)
        self.spreadsheet.history_plugin.push_operation(
            [],
            [],
            "insert_columns",
            {"col":insert_at,"count":count}
        )
        self.spreadsheet.is_modified=True
        if hasattr(self.spreadsheet,"grid_plugin"):
            self.spreadsheet.grid_plugin.refresh_headers()
    
    def delete_selected_columns(self):
        cols=sorted(set(index.column() for index in self.table.selectionModel().selectedColumns()),reverse=True)
        if not cols:
            return
        deleted=[]
        for col in sorted(cols):
            deleted.append(self.spreadsheet.history_plugin.create_column_snapshot(col))
        if hasattr(self.spreadsheet,"image_plugin"):
            images=self.spreadsheet.image_plugin.images
            updated={}
            deleted_set=set(cols)
            for (r,c),path in images.items():
                if c in deleted_set:
                    continue
                shift=sum(1 for deleted_col in cols if deleted_col<c)
                updated[(r,c-shift)]=path
            self.spreadsheet.image_plugin.images=updated
            self.spreadsheet.image_plugin.images_map[self.table]=updated
        if hasattr(self.spreadsheet,"pdf_plugin"):
            pdfs=self.spreadsheet.pdf_plugin.pdfs
            updated={}
            deleted_set=set(cols)
            for (r,c),path in pdfs.items():
                if c in deleted_set:
                    continue
                shift=sum(1 for deleted_col in cols if deleted_col<c)
                updated[(r,c-shift)]=path
            self.spreadsheet.pdf_plugin.pdfs=updated
            self.spreadsheet.pdf_plugin.pdfs_map[self.table]=updated
        for col in cols:
            self.table.removeColumn(col)
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.refresh_images()
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.refresh_pdfs()
        if hasattr(self.spreadsheet,"border_plugin"):
            for col in cols:
                self.spreadsheet.border_plugin.remove_columns(col,1)
        self.spreadsheet.history_plugin.push_operation(
            [],
            [],
            "delete_columns",
            {"col":min(cols),"count":len(cols),"snapshots":deleted}
        )
        self.spreadsheet.is_modified=True
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