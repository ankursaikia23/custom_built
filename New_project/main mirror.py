import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QFileDialog, QLabel, QTableWidgetItem, QMenu
from PyQt6.QtGui import QAction, QPixmap, QTextDocument
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter
import json

class Spreadsheet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Spreadsheet")
        self.resize(1200, 700)
        self.table=QTableWidget(30,10)
        self.table.setUpdatesEnabled(True)
        self.table.setSortingEnabled(False)
        self.setCentralWidget(self.table)
        self.table.setStyleSheet("""
        QTableWidget::item:selected{
        background-color:#4CAF50;
        color:white;
        }
        QHeaderView::section{
        background:#f0f0f0;
        }
        QHeaderView::section:checked{
        background:#4CAF50;
        color:white;
        }
        """)
        self.table.setCornerButtonEnabled(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table.itemDoubleClicked.connect(self.start_edit)
        self.table.itemChanged.connect(self.finish_edit)
        self.table.verticalHeader().setSectionsClickable(True)
        self.table.horizontalHeader().setSectionsClickable(True)
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        self.insert_image_action = QAction("Insert Image", self)
        file_menu.addAction(self.insert_image_action)
        self.insert_pdf_action=QAction("Insert PDF",self)
        file_menu.addAction(self.insert_pdf_action)
        self.export_pdf_action = QAction("Export PDF", self)
        file_menu.addAction(self.export_pdf_action)
        self.save_action = QAction("Save Project", self)
        file_menu.addAction(self.save_action)        
        self.open_action = QAction("Open Project", self)
        file_menu.addAction(self.open_action)
        self.new_action=QAction("New",self)
        file_menu.addAction(self.new_action)
        self.insert_image_action.triggered.connect(self.insert_image)
        self.insert_pdf_action.triggered.connect(self.insert_pdf)
        self.export_pdf_action.triggered.connect(self.export_pdf)
        self.save_action.triggered.connect(self.save_project)
        self.open_action.triggered.connect(self.open_project)
        self.new_action.triggered.connect(self.new_project)
        self.images = {}
        self.pdfs = {}
        self.clipboard_data=[]
        self.undo_stack=[]
        self.redo_stack=[]
        self.edit_before=""
        self.save_state()
        
    def insert_image(self):
        row=self.table.currentRow()
        col=self.table.currentColumn()
        if row<0 or col<0:
            return
        file,_=QFileDialog.getOpenFileName(self,"Select Image","","Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if not file:
            return
        self.table.takeItem(row,col)
        pixmap=QPixmap(file)
        label=QLabel()
        label.setPixmap(pixmap.scaled(150,150,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row,col,label)
        self.table.setCurrentCell(row,col)
        self.table.setFocus()
        self.table.viewport().update()
        self.table.viewport().update()
        self.table.setRowHeight(row,160)
        self.table.setColumnWidth(col,160)
        self.images[(row,col)]=file
        self.pdfs.pop((row,col),None)
        self.save_state()
        
    def insert_pdf(self):
        row=self.table.currentRow()
        col=self.table.currentColumn()
        if row<0 or col<0:
            return
        file,_=QFileDialog.getOpenFileName(self,"Select PDF","","PDF Files (*.pdf)")
        if not file:
            return
        self.table.takeItem(row,col)
        label=QLabel("📄\n"+os.path.basename(file))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row,col,label)
        self.table.setCurrentCell(row,col)
        self.table.setFocus()
        self.table.viewport().update()
        self.table.viewport().update()
        self.table.setRowHeight(row,80)
        self.table.setColumnWidth(col,180)
        self.pdfs[(row,col)]=file
        self.images.pop((row,col),None)
        self.save_state()
        
    def export_pdf(self):
        file_name,_=QFileDialog.getSaveFileName(self,"Save PDF","","PDF Files (*.pdf)")
        if not file_name:
            return
        if not file_name.lower().endswith(".pdf"):
            file_name+=".pdf"
        used_rows=[]
        used_cols=[]
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item=self.table.item(r,c)
                if item and item.text().strip():
                    if r not in used_rows:
                        used_rows.append(r)
                    if c not in used_cols:
                        used_cols.append(c)
                elif (r,c) in self.images or (r,c) in self.pdfs:
                    if r not in used_rows:
                        used_rows.append(r)
                    if c not in used_cols:
                        used_cols.append(c)
        html="<html><body><table style='border-collapse:collapse;'>"
        for r in used_rows:
            html+="<tr>"
            for c in used_cols:
                html+="<td style='padding:6px;vertical-align:middle;'>"
                item=self.table.item(r,c)
                if item:
                    html+=item.text().replace("\n","<br>")
                if (r,c) in self.images and os.path.exists(self.images[(r,c)]):
                    path=self.images[(r,c)].replace("\\","/")
                    html+=f'<br><img src="file:///{path}" style="max-width:140px;max-height:140px;">'
                elif (r,c) in self.pdfs:
                    html+=f"<br>📄 {os.path.basename(self.pdfs[(r,c)])}"
                html+="</td>"
            html+="</tr>"
        html+="</table></body></html>"
        printer=QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_name)
        document=QTextDocument()
        document.setHtml(html)
        document.print(printer)
        print("PDF exported successfully!")
        
    def contextMenuEvent(self,event):
        pos=self.table.viewport().mapFromGlobal(event.globalPos())
        headerPos=self.table.verticalHeader().mapFromGlobal(event.globalPos())
        hheaderPos=self.table.horizontalHeader().mapFromGlobal(event.globalPos())
        if self.table.verticalHeader().rect().contains(headerPos):
            menu=QMenu(self)
            copy=menu.addAction("Copy")
            cut=menu.addAction("Cut")
            paste=menu.addAction("Paste")
            menu.addSeparator()
            rowd=menu.addAction("Delete Row")
            rowi=menu.addAction("Insert Row")
            action=menu.exec(event.globalPos())
            self.table.setFocus()
            if action==copy:
                self.copy_selection()
            elif action==cut:
                self.cut_selection()
            elif action==paste:
                self.paste_selection()
            elif action==rowd:
                rows=sorted(set(i.row() for i in self.table.selectionModel().selectedRows()),reverse=True)
                for row in rows:
                    if row>0:
                        self.table.removeRow(row)
                        self.images={(r-1 if r>row else r,c):p for (r,c),p in self.images.items() if r!=row}
                        self.pdfs={(r-1 if r>row else r,c):p for (r,c),p in self.pdfs.items() if r!=row}
                self.save_state()
            elif action==rowi:
                self.table.insertRow(max(1,self.table.currentRow()))
            return
        if self.table.horizontalHeader().rect().contains(hheaderPos):
            menu=QMenu(self)
            copy=menu.addAction("Copy")
            cut=menu.addAction("Cut")
            paste=menu.addAction("Paste")
            menu.addSeparator()
            cold=menu.addAction("Delete Column")
            coli=menu.addAction("Insert Column")
            action=menu.exec(event.globalPos())
            self.table.setFocus()
            if action==copy:
                self.copy_selection()
            elif action==cut:
                self.cut_selection()
            elif action==paste:
                self.paste_selection()
            elif action==cold:
                cols=sorted(set(i.column() for i in self.table.selectionModel().selectedColumns()),reverse=True)
                for col in cols:
                    if col>0:
                        self.table.removeColumn(col)
                        self.images={(r,c-1 if c>col else c):p for (r,c),p in self.images.items() if c!=col}
                        self.pdfs={(r,c-1 if c>col else c):p for (r,c),p in self.pdfs.items() if c!=col}
                self.save_state()
            elif action==coli:
                self.table.insertColumn(max(1,self.table.currentColumn()))
            return
        index=self.table.indexAt(pos)
        if not index.isValid():
            return
        self.table.setCurrentIndex(index)
        menu=QMenu(self)
        copy=menu.addAction("Copy")
        cut=menu.addAction("Cut")
        paste=menu.addAction("Paste")
        menu.addSeparator()
        img=menu.addAction("Insert Image")
        pdf=menu.addAction("Insert PDF")
        rem=menu.addAction("Remove Item")
        action=menu.exec(event.globalPos())
        self.table.setFocus()
        if action==copy:
            self.copy_selection()
        elif action==cut:
            self.cut_selection()
        elif action==paste:
            self.paste_selection()
        elif action==img:
            self.insert_image()
        elif action==pdf:
            self.insert_pdf()
        elif action==rem:
            r=self.table.currentRow()
            c=self.table.currentColumn()
            self.table.removeCellWidget(r,c)
            self.table.takeItem(r,c)
            self.images.pop((r,c),None)
            self.pdfs.pop((r,c),None)
            self.save_state()
        
    def save_project(self):
        file_name,_=QFileDialog.getSaveFileName(self,"Save Project","","JSON Files (*.json)")
        if not file_name:
            return
        data={"rows":self.table.rowCount(),"cols":self.table.columnCount(),"cells":[],"images":[],"pdfs":[]}
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item=self.table.item(row,col)
                if item:
                    data["cells"].append({"row":row,"col":col,"text":item.text()})
        for (row,col),path in self.images.items():
            data["images"].append({"row":row,"col":col,"path":path})
        for (row,col),path in self.pdfs.items():
            data["pdfs"].append({"row":row,"col":col,"path":path})
        with open(file_name,"w") as f:
            json.dump(data,f,indent=4)
        print("Project Saved!")
    
    def open_project(self):
        file_name,_=QFileDialog.getOpenFileName(self,"Open Project","","JSON Files (*.json)")
        if not file_name:
            return
        with open(file_name,"r") as f:
            data=json.load(f)
        self.table.clearContents()
        self.images={}
        self.pdfs={}
        self.clipboard_data=[]
        for cell in data["cells"]:
            self.table.setItem(cell["row"],cell["col"],QTableWidgetItem(cell["text"]))
        for image in data.get("images",[]):
            row=image["row"]
            col=image["col"]
            path=image["path"]
            if os.path.exists(path):
                label=QLabel()
                pixmap=QPixmap(path)
                label.setPixmap(pixmap.scaled(150,150,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(row,col,label)
                self.table.setRowHeight(row,160)
                self.table.setColumnWidth(col,160)
                self.images[(row,col)]=path
        for pdf in data.get("pdfs",[]):
            row=pdf["row"]
            col=pdf["col"]
            path=pdf["path"]
            if os.path.exists(path):
                label=QLabel("📄\n"+os.path.basename(path))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(row,col,label)
                self.table.setRowHeight(row,80)
                self.table.setColumnWidth(col,180)
                self.pdfs[(row,col)]=path
        self.save_state()
        self.table.setFocus()
        self.table.setCurrentCell(0,0)
        self.table.viewport().update()
                
    def new_project(self):
        self.table.clearContents()
        self.table.setRowCount(30)
        self.table.setColumnCount(10)
        self.images={}
        self.pdfs={}
        self.save_state()
        
    def copy_selection(self):
        self.clipboard_data=[]
        rows=[i.row() for i in self.table.selectedIndexes()]
        cols=[i.column() for i in self.table.selectedIndexes()]
        if not rows or not cols:
            return
        r0=min(rows)
        c0=min(cols)
        for index in self.table.selectedIndexes():
            r=index.row()
            c=index.column()
            cell={"r":r-r0,"c":c-c0,"text":"","image":None,"pdf":None,"rh":self.table.rowHeight(r),"cw":self.table.columnWidth(c)}
            item=self.table.item(r,c)
            if item:
                cell["text"]=item.text()
            if (r,c) in self.images:
                cell["image"]=self.images[(r,c)]
            if (r,c) in self.pdfs:
                cell["pdf"]=self.pdfs[(r,c)]
            self.clipboard_data.append(cell)
    
    def cut_selection(self):
        self.copy_selection()
        for index in self.table.selectedIndexes():
            r=index.row()
            c=index.column()
            self.table.takeItem(r,c)
            self.table.removeCellWidget(r,c)
            self.images.pop((r,c),None)
            self.pdfs.pop((r,c),None)
        self.save_state()
    
    def paste_selection(self):
        if not self.clipboard_data:
            return
        sr=self.table.currentRow()
        sc=self.table.currentColumn()
        for cell in self.clipboard_data:
            r=sr+cell["r"]
            c=sc+cell["c"]
            self.table.setRowHeight(r,cell["rh"])
            self.table.setColumnWidth(c,cell["cw"])
            if cell["text"]:
                self.table.setItem(r,c,QTableWidgetItem(cell["text"]))
            if cell["image"] and os.path.exists(cell["image"]):
                pixmap=QPixmap(cell["image"])
                label=QLabel()
                label.setPixmap(pixmap.scaled(150,150,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(r,c,label)
                self.table.setRowHeight(r,160)
                self.table.setColumnWidth(c,160)
                self.images[(r,c)]=cell["image"]
            if cell["pdf"] and os.path.exists(cell["pdf"]):
                label=QLabel("📄\n"+os.path.basename(cell["pdf"]))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(r,c,label)
                self.table.setRowHeight(r,80)
                self.table.setColumnWidth(c,180)
                self.pdfs[(r,c)]=cell["pdf"]
        self.table.viewport().update()
        self.table.setFocus()
        self.save_state()
                
    def save_state(self):
        state={"cells":[],"images":dict(self.images),"pdfs":dict(self.pdfs),"rows":self.table.rowCount(),"cols":self.table.columnCount()}
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item=self.table.item(r,c)
                if item:
                    state["cells"].append((r,c,item.text()))
        self.undo_stack.append(state)
        self.redo_stack.clear()
    
    def load_state(self,state):
        self.table.clearContents()
        self.table.setRowCount(state["rows"])
        self.table.setColumnCount(state["cols"])
        self.images={}
        self.pdfs={}
        for r,c,text in state["cells"]:
            self.table.setItem(r,c,QTableWidgetItem(text))
        for (r,c),path in state["images"].items():
            if os.path.exists(path):
                pixmap=QPixmap(path)
                label=QLabel()
                label.setPixmap(pixmap.scaled(150,150,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(r,c,label)
                self.images[(r,c)]=path
        for (r,c),path in state["pdfs"].items():
            if os.path.exists(path):
                label=QLabel("📄\n"+os.path.basename(path))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(r,c,label)
                self.pdfs[(r,c)]=path
    
    def undo(self):
        if len(self.undo_stack)<2:
            return
        self.redo_stack.append(self.undo_stack.pop())
        self.load_state(self.undo_stack[-1])
    
    def redo(self):
        if not self.redo_stack:
            return
        state=self.redo_stack.pop()
        self.undo_stack.append(state)
        self.load_state(state)
        
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
        if item.text()!=self.edit_before:
            self.save_state()
        
    def keyPressEvent(self,event):
        if event.modifiers()==Qt.KeyboardModifier.ControlModifier:
            if event.key()==Qt.Key.Key_C:
                self.copy_selection()
                return
            elif event.key()==Qt.Key.Key_X:
                self.cut_selection()
                return
            elif event.key()==Qt.Key.Key_V:
                self.paste_selection()
                return
            elif event.key()==Qt.Key.Key_Z:
                self.undo()
                return
            elif event.key()==Qt.Key.Key_Y:
                self.redo()
                return
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):
            if self.table.state()==self.table.State.EditingState:
                self.table.closePersistentEditor(self.table.currentItem())
                self.table.clearFocus()
                r=self.table.currentRow()
                c=self.table.currentColumn()
                if r<self.table.rowCount()-1:
                    self.table.setCurrentCell(r+1,c)
                return
            row=self.table.currentRow()
            col=self.table.currentColumn()
            item=self.table.item(row,col)
            if item is None:
                item=QTableWidgetItem("")
                self.table.setItem(row,col,item)
            self.start_edit(item)
            return
        super().keyPressEvent(event)

app = QApplication(sys.argv)
window = Spreadsheet()
window.show()
sys.exit(app.exec())