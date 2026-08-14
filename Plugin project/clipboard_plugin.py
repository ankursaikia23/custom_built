from PyQt6.QtWidgets import QTableWidgetItem

class ClipboardPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.clipboard=[]

    def copy_selection(self):
        self.clipboard=[]
        ranges=self.table.selectedRanges()
        if not ranges:
            row=self.table.currentRow()
            col=self.table.currentColumn()
            if row<0 or col<0:
                return
            ranges=[]
            from PyQt6.QtCore import QRect
            selection=QRect(col,row,1,1)
        else:
            selection=ranges[0]
        r0=selection.topRow()
        c0=selection.leftColumn()
        for r in range(selection.topRow(),selection.bottomRow()+1):
            for c in range(selection.leftColumn(),selection.rightColumn()+1):
                data={"r":r-r0,"c":c-c0,"text":"","image":None,"pdf":None}
                item=self.table.item(r,c)
                if item:
                    data["text"]=item.text()
                if hasattr(self.spreadsheet,"image_plugin"):
                    data["image"]=self.spreadsheet.image_plugin.images.get((r,c))
                if hasattr(self.spreadsheet,"pdf_plugin"):
                    data["pdf"]=self.spreadsheet.pdf_plugin.pdfs.get((r,c))
                self.clipboard.append(data)
        if hasattr(self.spreadsheet,"statusbar_plugin"):
            self.spreadsheet.statusbar_plugin.show_operation("Copied")

    def cut_selection(self):
        ranges=self.table.selectedRanges()
        if not ranges:
            row=self.table.currentRow()
            col=self.table.currentColumn()
            if row<0 or col<0:
                return
            ranges=[]
            from PyQt6.QtCore import QRect
            selection=QRect(col,row,1,1)
        else:
            selection=ranges[0]
        self.copy_selection()
        before=[]
        after=[]
        for r in range(selection.topRow(),selection.bottomRow()+1):
            for c in range(selection.leftColumn(),selection.rightColumn()+1):
                before.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
                self.table.takeItem(r,c)
                self.table.removeCellWidget(r,c)
                if hasattr(self.spreadsheet,"image_plugin"):
                    self.spreadsheet.image_plugin.images.pop((r,c),None)
                if hasattr(self.spreadsheet,"pdf_plugin"):
                    self.spreadsheet.pdf_plugin.pdfs.pop((r,c),None)
                after.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
        self.spreadsheet.history_plugin.push_operation(before,after)
        self.spreadsheet.is_modified=True

    def paste_selection(self):
        if not self.clipboard:
            return
        indexes=self.table.selectedIndexes()
        if indexes:
            start_row=min(i.row() for i in indexes)
            start_col=min(i.column() for i in indexes)
        else:
            start_row=self.table.currentRow()
            start_col=self.table.currentColumn()
        if start_row<0 or start_col<0:
            return
        targets=[]
        if len(self.clipboard)==1 and len(indexes)>1:
            targets=[(i.row(),i.column()) for i in indexes]
        else:
            for cell in self.clipboard:
                targets.append((start_row+cell["r"],start_col+cell["c"]))
        before=[]
        after=[]
        for i,(r,c) in enumerate(targets):
            if r>=self.table.rowCount() or c>=self.table.columnCount():
                continue
            before.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
            cell=self.clipboard[0] if len(self.clipboard)==1 else self.clipboard[i]
            self.table.takeItem(r,c)
            self.table.removeCellWidget(r,c)
            if hasattr(self.spreadsheet,"image_plugin"):
                self.spreadsheet.image_plugin.images.pop((r,c),None)
            if hasattr(self.spreadsheet,"pdf_plugin"):
                self.spreadsheet.pdf_plugin.pdfs.pop((r,c),None)
            if cell["image"] and hasattr(self.spreadsheet,"image_plugin"):
                self.spreadsheet.image_plugin.set_image(r,c,cell["image"])
            elif cell["pdf"] and hasattr(self.spreadsheet,"pdf_plugin"):
                self.spreadsheet.pdf_plugin.set_pdf(r,c,cell["pdf"])
            elif cell["text"]:
                self.table.setItem(r,c,QTableWidgetItem(cell["text"]))
            after.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
        if before:
            self.spreadsheet.history_plugin.push_operation(before,after)
            self.spreadsheet.is_modified=True