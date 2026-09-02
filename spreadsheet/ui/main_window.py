from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QLabel,
    QTableWidgetItem,
    QColorDialog
)
from PyQt6.QtCore import QSignalBlocker, Qt
#from PyQt6.QtGui import QAction
from core.workbook import Workbook
#from services.formula.evaluator import Evaluator
from commands.history import History
from commands.edit_cell import EditCellCommand
from .spreadsheet_view import SpreadsheetView
from .formula_bar import FormulaBar
from .toolbar import SpreadsheetToolbar
from commands.copy_paste import Clipboard
from commands.paste_cells import PasteCellsCommand
from PyQt6.QtGui import QShortcut, QKeySequence, QColor
from commands.format_cells import FormatCellsCommand

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
        self.undo_shortcut = QShortcut(
            QKeySequence("Ctrl+Z"),
            self
        )
        
        self.undo_shortcut.activated.connect(
            self.undo
        )
        
        self.redo_shortcut = QShortcut(
            QKeySequence("Ctrl+Y"),
            self
        )
        
        self.redo_shortcut.activated.connect(
            self.redo
        )
        self.clipboard=Clipboard()
        self.toolbar=SpreadsheetToolbar()
        self.addToolBar(self.toolbar)
        self.formula_bar=FormulaBar()
        self.sheet_tabs=QTabWidget()
        self.views=[]
        for sheet in self.workbook.sheets:
            view=SpreadsheetView()
            view.cellChanged.connect(self.handle_cell_changed)
            view.currentCellChanged.connect(self.handle_cell_selected)
            view.deleteRequested.connect(
                self.handle_delete_requested
            )
            view.copyRequested.connect(
                self.handle_copy_requested
            )
            view.pasteRequested.connect(
                self.handle_paste_requested
            )
            self.views.append(view)
            self.sheet_tabs.addTab(view,sheet.name)
        self.sheet_tabs.currentChanged.connect(self.handle_sheet_changed)
        self.formula_bar.returnPressed.connect(self.handle_formula_bar)
        self.status_label=QLabel("Ready")
        self.statusBar().addPermanentWidget(self.status_label)
        self.toolbar.actions()[2].triggered.connect(self.undo)
        self.toolbar.actions()[3].triggered.connect(self.redo)
        self.toolbar.bold_action.triggered.connect(
            self.handle_bold
        )
        
        self.toolbar.italic_action.triggered.connect(
            self.handle_italic
        )
        
        self.toolbar.underline_action.triggered.connect(
            self.handle_underline
        )
        self.toolbar.font_family_combo.currentTextChanged.connect(
            self.handle_font_family
        )        
        self.toolbar.font_size_combo.currentTextChanged.connect(
            self.handle_font_size
        )
        self.toolbar.text_color_action.triggered.connect(
            self.handle_text_color
        )
        self.toolbar.background_color_action.triggered.connect(
            self.handle_background_color
        )
        self.toolbar.horizontal_alignment_combo.currentTextChanged.connect(
            self.handle_horizontal_alignment
        )
        
        self.toolbar.vertical_alignment_combo.currentTextChanged.connect(
            self.handle_vertical_alignment
        )
        self.toolbar.number_format_combo.currentTextChanged.connect(
            self.handle_number_format
        )
        self.copy_shortcut = QShortcut(
            QKeySequence("Ctrl+C"),
            self
        )
        
        self.copy_shortcut.activated.connect(
            self.handle_copy
        )
        self.cut_shortcut = QShortcut(
            QKeySequence("Ctrl+X"),
            self
        )
        
        self.cut_shortcut.activated.connect(
            self.handle_cut
        )
        self.paste_shortcut = QShortcut(
            QKeySequence("Ctrl+V"),
            self
        )
        
        self.paste_shortcut.activated.connect(
            self.handle_paste
        )
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
    
        reference = (
            f"{chr(65 + column)}"
            f"{row + 1}"
        )
    
        item = self.views[index].item(
            row,
            column
        )
    
        value = (
            item.text()
            if item
            else ""
        )
    
        command = EditCellCommand(
            sheet,
            reference,
            value
        )
    
        self.history.execute(
            command
        )
    
        # ==============================================
        # Refresh affected sheets
        # ==============================================
    
        results = (
            self.workbook
            .recalculation_manager
            .recalculate_from(
                reference,
                sheet=sheet
            )
        )
    
        affected_sheets = {
            sheet
        }
    
        for qualified_reference in results:
    
            if "!" not in qualified_reference:
                continue
    
            sheet_name = (
                qualified_reference
                .rsplit("!", 1)[0]
                .strip("'")
            )
    
            target_sheet = (
                self.workbook.get_sheet(
                    sheet_name
                )
            )
    
            if target_sheet is not None:
                affected_sheets.add(
                    target_sheet
                )
    
        for affected_sheet in affected_sheets:
    
            affected_index = (
                self.workbook.sheets.index(
                    affected_sheet
                )
            )
    
            self.refresh_view(
                affected_index
            )
    
        # ==============================================
        # Restore formula bar
        # ==============================================
    
        self.formula_bar.setText(
            value
        )
    
        self.status_label.setText(
            f"{reference} = {value}"
        )
        
    def format_display_value(
        self,
        value,
        number_format
    ):

        if value is None:
            return ""

        if number_format == "general":
            return str(value)

        if number_format == "date":
            from datetime import (
                date,
                datetime
            )

            if isinstance(
                value,
                datetime
            ):
                return value.strftime(
                    "%d/%m/%Y"
                )

            if isinstance(
                value,
                date
            ):
                return value.strftime(
                    "%d/%m/%Y"
                )

            if isinstance(
                value,
                str
            ):
                date_formats = [
                    "%Y-%m-%d",
                    "%d/%m/%Y",
                    "%d-%m-%Y",
                    "%m/%d/%Y",
                ]

                for date_format in date_formats:
                    try:
                        parsed_date = (
                            datetime.strptime(
                                value,
                                date_format
                            )
                        )

                        return parsed_date.strftime(
                            "%d/%m/%Y"
                        )

                    except ValueError:
                        continue

            return str(value)

        try:
            numeric_value = float(value)
        except (
            TypeError,
            ValueError
        ):
            return str(value)

        if number_format == "number":
            return f"{numeric_value:,.2f}"

        if number_format == "integer":
            return f"{numeric_value:,.0f}"

        if number_format == "currency":
            return f"${numeric_value:,.2f}"

        if number_format == "percentage":
            return f"{numeric_value * 100:.2f}%"

        return str(value)
    
    def refresh_view(self, index):
        view = self.views[index]
        sheet = self.workbook.sheets[index]
    
        with QSignalBlocker(view):
    
            for row in range(
                view.rowCount()
            ):
    
                for column in range(
                    view.columnCount()
                ):
    
                    reference = (
                        f"{chr(65 + column)}"
                        f"{row + 1}"
                    )
    
                    cell = sheet.get_cell(
                        reference
                    )
    
                    if cell is None:
    
                        view.takeItem(
                            row,
                            column
                        )
    
                        continue
    
                    item = view.item(
                        row,
                        column
                    )
    
                    if item is None:
    
                        item = QTableWidgetItem()
    
                        view.setItem(
                            row,
                            column,
                            item
                        )
    
                    if (
                        isinstance(
                            cell.value,
                            str
                        )
                        and cell.value.startswith("=")
                    ):
    
                        if (
                            cell.calculated_value
                            is not None
                        ):
    
                            display_value = (
                                cell.calculated_value
                            )
    
                            item.setText(
                                self.format_display_value(
                                    display_value,
                                    cell.format.number_format
                                )
                            )
    
                        else:
    
                            item.setText("")
    
                    else:
    
                        display_value = cell.value
    
                        item.setText(
                            self.format_display_value(
                                display_value,
                                cell.format.number_format
                            )
                        )
    
                    self.apply_cell_format(
                        cell,
                        item
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
        self.refresh_current_view()
        self.status_label.setText(
            f"{reference} = {value}"
        )
        
    def refresh_cell_display(
        self,
        sheet,
        view,
        reference
    ):
    
        cell = sheet.get_cell(
            reference
        )
    
        if cell is None:
            return
    
        column, row = (
            sheet.split_reference(
                reference
            )
        )
    
        column_index = (
            sheet.column_number(
                column
            ) - 1
        )
    
        row_index = row - 1
    
        item = view.item(
            row_index,
            column_index
        )
    
        if item is None:
    
            item = QTableWidgetItem()
    
            with QSignalBlocker(view):
    
                view.setItem(
                    row_index,
                    column_index,
                    item
                )
    
        if (
            isinstance(
                cell.value,
                str
            )
            and cell.value.startswith("=")
            and cell.calculated_value is not None
        ):
    
            item.setText(
                str(
                    cell.calculated_value
                )
            )
    
        else:
    
            item.setText(
                str(
                    cell.value
                )
            )
    
        self.apply_cell_format(
            cell,
            item
        )
    
    def undo(self):
        command = self.history.undo()
    
        if command is None:
            return
    
        self.refresh_current_view()
    
    
    def redo(self):
        command = self.history.redo()
    
        if command is None:
            return
    
        self.refresh_current_view()
    
    def refresh_current_view(self):
    
        index = (
            self.sheet_tabs.currentIndex()
        )
    
        view = self.views[index]
        sheet = self.workbook.sheets[index]
    
        with QSignalBlocker(view):
    
            for row in range(
                view.rowCount()
            ):
    
                for column in range(
                    view.columnCount()
                ):
    
                    reference = (
                        f"{chr(65 + column)}"
                        f"{row + 1}"
                    )
    
                    cell = sheet.get_cell(
                        reference
                    )
    
                    if cell is None:
    
                        view.takeItem(
                            row,
                            column
                        )
    
                        continue
    
                    item = view.item(
                        row,
                        column
                    )
    
                    if item is None:
    
                        item = QTableWidgetItem()
    
                        view.setItem(
                            row,
                            column,
                            item
                        )
    
                    if (
                        isinstance(
                            cell.value,
                            str
                        )
                        and cell.value.startswith("=")
                    ):
    
                        if (
                            cell.calculated_value
                            is not None
                        ):
    
                            display_value = (
                                cell.calculated_value
                            )
    
                            item.setText(
                                self.format_display_value(
                                    display_value,
                                    cell.format.number_format
                                )
                            )
    
                        else:
    
                            item.setText("")
    
                    else:
    
                        display_value = cell.value
    
                        item.setText(
                            self.format_display_value(
                                display_value,
                                cell.format.number_format
                            )
                        )
    
                    self.apply_cell_format(
                        cell,
                        item
                    )
    
        current = view.currentItem()
    
        if current is not None:
    
            self.handle_cell_selected(
                current.row(),
                current.column(),
                -1,
                -1
            )
            
    def handle_copy_requested(self):

        index = self.sheet_tabs.currentIndex()
        view = self.views[index]
        sheet = self.workbook.sheets[index]

        ranges = view.selectedRanges()

        if not ranges:
            return

        selected_range = ranges[0]

        start_reference = (
            f"{chr(65 + selected_range.leftColumn())}"
            f"{selected_range.topRow() + 1}"
        )

        end_reference = (
            f"{chr(65 + selected_range.rightColumn())}"
            f"{selected_range.bottomRow() + 1}"
        )

        self.clipboard.copy(
            sheet,
            start_reference,
            end_reference
        )

        self.status_label.setText(
            f"Copied {start_reference}:{end_reference}"
        )
        
    def handle_paste_requested(self):

        index = self.sheet_tabs.currentIndex()
        view = self.views[index]
        sheet = self.workbook.sheets[index]

        row = view.currentRow()
        column = view.currentColumn()

        if row < 0 or column < 0:
            return

        if not self.clipboard.cells:
            return

        destination_reference = (
            f"{chr(65 + column)}"
            f"{row + 1}"
        )

        command = PasteCellsCommand(
            self.clipboard,
            sheet,
            destination_reference
        )

        self.history.execute(
            command
        )

        self.refresh_current_view()

        self.status_label.setText(
            f"Pasted at {destination_reference}"
        )
        
    def handle_copy(self):
        index = self.sheet_tabs.currentIndex()
        view = self.views[index]
        sheet = self.workbook.sheets[index]
    
        ranges = view.selectedRanges()
    
        if not ranges:
            return
    
        selected_range = ranges[0]
    
        start_row = selected_range.topRow()
        end_row = selected_range.bottomRow()
        start_column = selected_range.leftColumn()
        end_column = selected_range.rightColumn()
    
        start_reference = (
            f"{chr(65 + start_column)}"
            f"{start_row + 1}"
        )
    
        end_reference = (
            f"{chr(65 + end_column)}"
            f"{end_row + 1}"
        )
    
        self.clipboard.copy(
            sheet,
            start_reference,
            end_reference
        )
    
        self.status_label.setText(
            f"Copied {start_reference}:{end_reference}"
        )
        
    def handle_cut(self):
        index = self.sheet_tabs.currentIndex()
        view = self.views[index]
        sheet = self.workbook.sheets[index]
    
        ranges = view.selectedRanges()
    
        if not ranges:
            return
    
        selected_range = ranges[0]
    
        start_row = selected_range.topRow()
        end_row = selected_range.bottomRow()
        start_column = selected_range.leftColumn()
        end_column = selected_range.rightColumn()
    
        start_reference = (
            f"{chr(65 + start_column)}"
            f"{start_row + 1}"
        )
    
        end_reference = (
            f"{chr(65 + end_column)}"
            f"{end_row + 1}"
        )
    
        # Store the selected cells in the clipboard.
        self.clipboard.cut(
            sheet,
            start_reference,
            end_reference
        )
    
        self.status_label.setText(
            f"Cut {start_reference}:{end_reference}"
        )
    
    
    def handle_paste(self):
        index = self.sheet_tabs.currentIndex()
        view = self.views[index]
        sheet = self.workbook.sheets[index]
    
        row = view.currentRow()
        column = view.currentColumn()
    
        if row < 0 or column < 0:
            return
    
        destination_reference = (
            f"{chr(65 + column)}"
            f"{row + 1}"
        )
    
        if not self.clipboard.cells:
            self.status_label.setText(
                "Clipboard is empty"
            )
            return
    
        from commands.paste_cells import PasteCellsCommand
    
        command = PasteCellsCommand(
            self.clipboard,
            sheet,
            destination_reference
        )
    
        self.history.execute(command)
    
        self.workbook.recalculation_manager.recalculate_from(
            destination_reference,
            sheet=sheet
        )
    
        self.refresh_current_view()
    
        self.status_label.setText(
            f"Pasted at {destination_reference}"
        )
            
    def handle_delete_requested(self, references):

        index = self.sheet_tabs.currentIndex()
        #view = self.views[index]
        sheet = self.workbook.sheets[index]

        if not references:
            return

        from commands.delete import DeleteCellsCommand

        command = DeleteCellsCommand(
            sheet,
            references
        )

        self.history.execute(command)

        for reference in references:
            self.workbook.recalculation_manager.recalculate_from(
                reference,
                sheet=sheet
            )

        self.refresh_current_view()

        self.formula_bar.clear()

        self.status_label.setText(
            f"{len(references)} cell(s) cleared"
        )
        
    def get_selected_references(self):
    
        index = self.sheet_tabs.currentIndex()
        view = self.views[index]
    
        ranges = view.selectedRanges()
    
        if not ranges:
            row = view.currentRow()
            column = view.currentColumn()
    
            if row < 0 or column < 0:
                return []
    
            return [
                f"{chr(65 + column)}{row + 1}"
            ]
    
        selected_range = ranges[0]
    
        references = []
    
        for row in range(
            selected_range.topRow(),
            selected_range.bottomRow() + 1
        ):
    
            for column in range(
                selected_range.leftColumn(),
                selected_range.rightColumn() + 1
            ):
    
                references.append(
                    f"{chr(65 + column)}{row + 1}"
                )
    
        return references
    
    
    def handle_bold(self, checked):
    
        self.apply_formatting(
            bold=checked
        )
    
    
    def handle_italic(self, checked):
    
        self.apply_formatting(
            italic=checked
        )
    
    
    def handle_underline(self, checked):
    
        self.apply_formatting(
            underline=checked
        )
        
    def handle_horizontal_alignment(
        self,
        alignment
    ):
    
        alignment_map = {
            "Left": "left",
            "Center": "center",
            "Right": "right",
        }
    
        value = alignment_map.get(
            alignment
        )
    
        if value is None:
            return
    
        self.apply_formatting(
            horizontal_alignment=value
        )
    
    
    def handle_vertical_alignment(
        self,
        alignment
    ):
    
        alignment_map = {
            "Top": "top",
            "Center": "center",
            "Bottom": "bottom",
        }
    
        value = alignment_map.get(
            alignment
        )
    
        if value is None:
            return
    
        self.apply_formatting(
            vertical_alignment=value
        )
        
    def handle_number_format(self):
        format_map = {
            "General": "general",
            "Number": "number",
            "Integer": "integer",
            "Currency": "currency",
            "Percentage": "percentage",
            "Date": "date",
        }

        selected_format = (
            self.toolbar.number_format_combo.currentText()
        )

        number_format = format_map.get(
            selected_format
        )

        if number_format is None:
            return

        self.apply_formatting(
            number_format=number_format
        )
        
    def apply_cell_format(
        self,
        cell,
        item
    ):
    
        if cell is None or item is None:
            return
    
        cell_format = cell.format
    
        # ==========================================
        # Font
        # ==========================================
    
        font = item.font()
    
        font.setFamily(
            cell_format.font_family
        )
    
        font.setPointSize(
            int(cell_format.font_size)
        )
    
        font.setBold(
            cell_format.bold
        )
    
        font.setItalic(
            cell_format.italic
        )
    
        font.setUnderline(
            cell_format.underline
        )
    
        item.setFont(
            font
        )
    
        # ==========================================
        # Text color
        # ==========================================
    
        item.setForeground(
            QColor(
                cell_format.text_color
            )
        )
 
        # ==========================================
        # Background color
        # ==========================================
        
        item.setBackground(
            QColor(
                cell_format.background_color
            )
        )
    
        # ==========================================
        # Horizontal alignment
        # ==========================================
    
        horizontal_alignment = (
            cell_format.horizontal_alignment
        )
    
        if horizontal_alignment == "left":
    
            horizontal_flag = (
                Qt.AlignmentFlag.AlignLeft
            )
    
        elif horizontal_alignment == "center":
    
            horizontal_flag = (
                Qt.AlignmentFlag.AlignHCenter
            )
    
        else:
    
            horizontal_flag = (
                Qt.AlignmentFlag.AlignRight
            )
    
        # ==========================================
        # Vertical alignment
        # ==========================================
    
        vertical_alignment = (
            cell_format.vertical_alignment
        )
    
        if vertical_alignment == "top":
    
            vertical_flag = (
                Qt.AlignmentFlag.AlignTop
            )
    
        elif vertical_alignment == "center":
    
            vertical_flag = (
                Qt.AlignmentFlag.AlignVCenter
            )
    
        else:
    
            vertical_flag = (
                Qt.AlignmentFlag.AlignBottom
            )
    
        item.setTextAlignment(
            horizontal_flag
            | vertical_flag
        )
        
    def handle_font_family(self, family):
        if not family:
            return
    
        self.apply_formatting(
            font_family=family
        )
    
    def handle_font_size(self, size):
        if not size:
            return
    
        try:
            size = float(size)
        except ValueError:
            return
    
        self.apply_formatting(
            font_size=size
        )
        
    def handle_text_color(self):
        color = QColorDialog.getColor(
            parent=self
        )
    
        if not color.isValid():
            return
    
        self.apply_formatting(
            text_color=color.name().upper()
        )
        
    def handle_background_color(self):
    
        color = QColorDialog.getColor(
            parent=self
        )
    
        if not color.isValid():
            return
    
        self.apply_formatting(
            background_color=color.name().upper()
        )
        
    def apply_formatting(
        self,
        bold=None,
        italic=None,
        underline=None,
        font_family=None,
        font_size=None,
        text_color=None,
        background_color=None,
        horizontal_alignment=None,
        vertical_alignment=None,
        number_format=None
    ):
    
        index = self.sheet_tabs.currentIndex()
        sheet = self.workbook.sheets[index]
    
        references = self.get_selected_references()
    
        if not references:
            return
    
        command = FormatCellsCommand(
            sheet,
            references,
            bold=bold,
            italic=italic,
            underline=underline,
            font_family=font_family,
            font_size=font_size,
            text_color=text_color,
            background_color=background_color,
            horizontal_alignment=horizontal_alignment,
            vertical_alignment=vertical_alignment,
            number_format=number_format
        )
    
        self.history.execute(command)
    
        self.refresh_current_view()
    
        self.status_label.setText(
            f"Formatted {len(references)} cell(s)"
        )