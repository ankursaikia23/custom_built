from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTabWidget, QLabel
from PyQt6.QtCore import QSignalBlocker
from core.workbook import Workbook
from .spreadsheet_view import SpreadsheetView
from .formula_bar import FormulaBar
from .toolbar import SpreadsheetToolbar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spreadsheet")
        self.resize(1200,800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6f8;
            }
        """)
        self.workbook=Workbook()
        self.workbook.add_sheet("Sheet1")
        self.workbook.add_sheet("Sheet2")
        self.workbook.add_sheet("Sheet3")
        self.toolbar=SpreadsheetToolbar()
        self.addToolBar(self.toolbar)
        self.formula_bar=FormulaBar()
        self.sheet_tabs=QTabWidget()
        self.views=[]
        for sheet in self.workbook.sheets:
            view=SpreadsheetView()
            view.cellChanged.connect(self.handle_cell_changed)
            self.views.append(view)
            self.sheet_tabs.addTab(view,sheet.name)
        self.sheet_tabs.currentChanged.connect(self.handle_sheet_changed)
        self.formula_bar.returnPressed.connect(self.handle_formula_bar)
        self.status_label=QLabel("Ready")
        self.statusBar().addPermanentWidget(self.status_label)
        container=QWidget()
        layout=QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.addWidget(self.formula_bar)
        layout.addWidget(self.sheet_tabs)
        self.setCentralWidget(container)
    
    def handle_cell_changed(self,row,column):
        sheet=self.workbook.sheets[self.sheet_tabs.currentIndex()]
        reference=f"{chr(65+column)}{row+1}"
        item=self.views[self.sheet_tabs.currentIndex()].item(row,column)
        value=item.text() if item else ""
        sheet.set_cell(reference,value)
        self.formula_bar.setText(value)
        self.status_label.setText(f"{reference} = {value}")
    
    def handle_sheet_changed(self,index):
        self.formula_bar.clear()
        self.status_label.setText(f"Ready - {self.workbook.sheets[index].name}")
    
    def handle_formula_bar(self):
        index=self.sheet_tabs.currentIndex()
        view=self.views[index]
        current=view.currentItem()
        if current is None:
            return
        value=self.formula_bar.text()
        row=current.row()
        column=current.column()
        with QSignalBlocker(view):
            current.setText(value)
        sheet=self.workbook.sheets[index]
        reference=f"{chr(65+column)}{row+1}"
        sheet.set_cell(reference,value)
        self.status_label.setText(f"{reference} = {value}")