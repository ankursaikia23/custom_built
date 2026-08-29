from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTabWidget, QLabel, QTableWidgetItem
from PyQt6.QtCore import QSignalBlocker
#from PyQt6.QtGui import QAction
from core.workbook import Workbook
from services.formula.evaluator import Evaluator
from commands.history import History
from commands.edit_cell import EditCellCommand
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
        self.history=History()
        self.toolbar=SpreadsheetToolbar()
        self.addToolBar(self.toolbar)
        self.formula_bar=FormulaBar()
        self.sheet_tabs=QTabWidget()
        self.views=[]
        for sheet in self.workbook.sheets:
            view=SpreadsheetView()
            view.cellChanged.connect(self.handle_cell_changed)
            view.currentCellChanged.connect(self.handle_cell_selected)
            self.views.append(view)
            self.sheet_tabs.addTab(view,sheet.name)
        self.sheet_tabs.currentChanged.connect(self.handle_sheet_changed)
        self.formula_bar.returnPressed.connect(self.handle_formula_bar)
        self.status_label=QLabel("Ready")
        self.statusBar().addPermanentWidget(self.status_label)
        self.toolbar.actions()[2].triggered.connect(self.undo)
        self.toolbar.actions()[3].triggered.connect(self.redo)
        container=QWidget()
        layout=QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.addWidget(self.formula_bar)
        layout.addWidget(self.sheet_tabs)
        self.setCentralWidget(container)
    
    def handle_cell_changed(self, row, column):
        index = self.sheet_tabs.currentIndex()
        sheet = self.workbook.sheets[index]
        reference = f"{chr(65 + column)}{row + 1}"    
        item = self.views[index].item(row, column)
        value = item.text() if item else ""
        command = EditCellCommand(
            sheet,
            reference,
            value
        )
        self.history.execute(command)
        if (
            isinstance(value, str)
            and value.startswith("=")
        ):
            evaluator = self.workbook.recalculation_manager.evaluator
            evaluator.sheet = sheet
            evaluator.workbook = self.workbook
            cell = sheet.get_cell(reference)
            if cell is not None:
                cell.calculated_value = evaluator.evaluate_cell(
                    reference
                )
        self.workbook.recalculation_manager.recalculate_from(
            reference,
            sheet=sheet
        )
        self.refresh_current_view()
        self.formula_bar.setText(value)
        self.status_label.setText(
            f"{reference} = {value}"
        )
    
    def handle_cell_selected(
        self,
        current_row,
        current_column,
        previous_row,
        previous_column
    ):
        if current_row < 0 or current_column < 0:
            self.formula_bar.clear()
            return
        sheet = self.workbook.sheets[
            self.sheet_tabs.currentIndex()
        ]    
        reference = (
            f"{chr(65 + current_column)}"
            f"{current_row + 1}"
        )
        cell = sheet.get_cell(reference)
        value = cell.value if cell else ""
        self.formula_bar.setText(
            str(value)
        )
        self.status_label.setText(
            f"{reference} = {value}"
        )
    
    def handle_sheet_changed(self,index):
        view=self.views[index]
        current=view.currentItem()
        if current is None:
            self.formula_bar.clear()
            self.status_label.setText(f"Ready - {self.workbook.sheets[index].name}")
            return
        self.handle_cell_selected(current.row(),current.column(),-1,-1)
    
    def handle_formula_bar(self):
        index = self.sheet_tabs.currentIndex()
        view = self.views[index]
        current = view.currentItem()    
        if current is None:
            row = view.currentRow()
            column = view.currentColumn()
            if row < 0 or column < 0:
                return
            current = QTableWidgetItem()
            with QSignalBlocker(view):
                view.setItem(
                    row,
                    column,
                    current
                )
        value = self.formula_bar.text()
        row = current.row()
        column = current.column()
        reference = (
            f"{chr(65 + column)}"
            f"{row + 1}"
        )
        sheet = self.workbook.sheets[index]
        command = EditCellCommand(
            sheet,
            reference,
            value
        )
        self.history.execute(command)
        if (
            isinstance(value, str)
            and value.startswith("=")
        ):
            evaluator = Evaluator(
                sheet=sheet,
                workbook=self.workbook
            )    
            cell = sheet.get_cell(reference)
            if cell is not None:
                cell.calculated_value = (
                    evaluator.evaluate_cell(
                        reference
                    )
                )
        self.workbook.recalculation_manager.recalculate_from(
            reference,
            sheet=sheet
        )
        self.refresh_current_view()
        self.status_label.setText(
            f"{reference} = {value}"
        )
        
    def refresh_cell_display(self, sheet, view, reference):
        cell = sheet.get_cell(reference)
        if cell is None:
            return    
        column, row = sheet.split_reference(reference)
        column_index = sheet.column_number(column) - 1
        row_index = row - 1
        item = view.item(row_index, column_index)
        if item is None:
            item = QTableWidgetItem()
            with QSignalBlocker(view):
                view.setItem(
                    row_index,
                    column_index,
                    item
                )
        if (
            isinstance(cell.value, str)
            and cell.value.startswith("=")
            and cell.calculated_value is not None
        ):
            item.setText(
                str(cell.calculated_value)
            )
        else:
            item.setText(
                str(cell.value)
            )
    
    def undo(self):
        self.history.undo()
        self.refresh_current_view()
    
    def redo(self):
        self.history.redo()
        self.refresh_current_view()
    
    def refresh_current_view(self):
        index = self.sheet_tabs.currentIndex()
        view = self.views[index]
        sheet = self.workbook.sheets[index]
        with QSignalBlocker(view):
            for row in range(view.rowCount()):
                for column in range(view.columnCount()):
                    reference = f"{chr(65 + column)}{row + 1}"
                    cell = sheet.get_cell(reference)    
                    if cell is None:
                        view.takeItem(row, column)
                        continue
                    item = view.item(row, column)
                    if item is None:
                        item = QTableWidgetItem()
                        view.setItem(row, column, item)
                    if (
                        isinstance(cell.value, str)
                        and cell.value.startswith("=")
                    ):
                        if cell.calculated_value is not None:
                            item.setText(
                                str(cell.calculated_value)
                            )
                        else:
                            item.setText("")
                    else:
                        item.setText(
                            str(cell.value)
                        )
        current = view.currentItem()
        if current is not None:
            self.handle_cell_selected(
                current.row(),
                current.column(),
                -1,
                -1
            )