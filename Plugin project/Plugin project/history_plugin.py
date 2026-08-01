from PyQt6.QtWidgets import QTableWidgetItem,QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os
import copy

class HistoryPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.undo_stack=[]
        self.redo_stack=[]

    def save_state(self):
        state={"rows":self.table.rowCount(),"cols":self.table.columnCount(),"cells":[],"images":{},"pdfs":{}}
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item=self.table.item(r,c)
                if item:
                    state["cells"].append((r,c,item.text()))
        if hasattr(self.spreadsheet,"image_plugin"):
            state["images"]=copy.deepcopy(self.spreadsheet.image_plugin.images)
        if hasattr(self.spreadsheet,"pdf_plugin"):
            state["pdfs"]=copy.deepcopy(self.spreadsheet.pdf_plugin.pdfs)
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def load_state(self,state):
        self.table.clearContents()
        self.table.setRowCount(state["rows"])
        self.table.setColumnCount(state["cols"])
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.images.clear()
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.pdfs.clear()
        for r,c,text in state["cells"]:
            self.table.setItem(r,c,QTableWidgetItem(text))
        for (r,c),path in state["images"].items():
            if os.path.exists(path):
                label=QLabel()
                pixmap=QPixmap(path)
                label.setPixmap(pixmap.scaled(150,150,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(r,c,label)
                self.spreadsheet.image_plugin.images[(r,c)]=path
        for (r,c),path in state["pdfs"].items():
            if os.path.exists(path):
                label=QLabel("📄\n"+os.path.basename(path))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(r,c,label)
                self.spreadsheet.pdf_plugin.pdfs[(r,c)]=path

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