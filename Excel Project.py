import sys
import base64
from datetime import datetime
from PyQt5.QtCore import Qt, QPoint, QItemSelection, QItemSelectionModel, pyqtSignal, QEvent
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QLabel, QToolButton, QMenu, QFileDialog, QInputDialog, QColorDialog,
    QMessageBox, QTabWidget, QHeaderView, QAbstractItemView, QComboBox, QFrame, QDialog, QSpinBox,
    QRadioButton, QDialogButtonBox, QStyledItemDelegate, QAbstractItemDelegate, QTextEdit,
    QTableWidgetSelectionRange
)

class SpreadsheetHeader(QHeaderView):
    rightClicked = pyqtSignal(int, QPoint)
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setHighlightSections(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.logicalIndexAt(
                event.pos().y()
                if self.orientation() == Qt.Vertical
                else event.pos().x()
            )
            if index >= 0:
                self.rightClicked.emit(
                    index,
                    event.pos()
                )
            event.accept()
            return
        super().mousePressEvent(event)
        
class SpreadsheetDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if editor is not None:
            editor.installEventFilter(self)
        return editor

    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.commitData.emit(editor)
                self.closeEditor.emit(
                    editor,
                    QAbstractItemDelegate.NoHint
                )
                return True
        return super().eventFilter(editor, event)

class SpreadsheetTable(QTableWidget):
    def __init__(self, rows=0, columns=0, parent=None):
        super().__init__(rows, columns, parent)
        self.header_drag_mode = None
        self.header_drag_start = -1
        self.header_anchor = -1
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.installEventFilter(self)
        self._editing = False
        self._history_editing = False
        self._edit_history_saved = False
    
    def select_entire_row(self, row, command):
        if row < 0 or row >= self.rowCount():
            return
        selection_model = self.selectionModel()
        top_left = self.model().index(row, 0)
        bottom_right = self.model().index(row, self.columnCount() - 1)
        selection = QItemSelection(top_left, bottom_right)
        selection_model.select(selection, command)
    
    def select_entire_column(self, column, command):
        if column < 0 or column >= self.columnCount():
            return
        selection_model = self.selectionModel()
        top_left = self.model().index(0, column)
        bottom_right = self.model().index(self.rowCount() - 1, column)
        selection = QItemSelection(top_left, bottom_right)
        selection_model.select(selection, command)
    
    def mousePressEvent(self, event):
        pos = event.pos()
        if event.button() == Qt.LeftButton:
            if self.verticalHeader().geometry().contains(pos):
                row = self.verticalHeader().logicalIndexAt(pos.y())
                if row >= 0:
                    modifiers = event.modifiers()
                    if modifiers & Qt.ShiftModifier:
                        if self.header_anchor < 0:
                            self.header_anchor = row
                        start = min(self.header_anchor, row)
                        end = max(self.header_anchor, row)
                        self.selectionModel().clearSelection()
                        for r in range(start, end + 1):
                            self.select_entire_row(r, QItemSelectionModel.Select)
                    elif modifiers & Qt.ControlModifier:
                        self.select_entire_row(row, QItemSelectionModel.Toggle)
                        self.header_anchor = row
                    else:
                        self.selectionModel().clearSelection()
                        self.select_entire_row(row, QItemSelectionModel.Select)
                        self.header_anchor = row
                    self.header_drag_mode = "row"
                    self.header_drag_start = row
                    event.accept()
                    return
            if self.horizontalHeader().geometry().contains(pos):
                column = self.horizontalHeader().logicalIndexAt(pos.x())
                if column >= 0:
                    modifiers = event.modifiers()
                    if modifiers & Qt.ShiftModifier:
                        if self.header_anchor < 0:
                            self.header_anchor = column
                        start = min(self.header_anchor, column)
                        end = max(self.header_anchor, column)
                        self.selectionModel().clearSelection()
                        for c in range(start, end + 1):
                            self.select_entire_column(c, QItemSelectionModel.Select)
                    elif modifiers & Qt.ControlModifier:
                        self.select_entire_column(column, QItemSelectionModel.Toggle)
                        self.header_anchor = column
                    else:
                        self.selectionModel().clearSelection()
                        self.select_entire_column(column, QItemSelectionModel.Select)
                        self.header_anchor = column
                    self.header_drag_mode = "column"
                    self.header_drag_start = column
                    event.accept()
                    return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.header_drag_mode == "row":
            current = self.verticalHeader().logicalIndexAt(event.pos().y())
            if current >= 0:
                start = min(self.header_drag_start, current)
                end = max(self.header_drag_start, current)
                self.selectionModel().clearSelection()
                for row in range(start, end + 1):
                    self.select_entire_row(row, QItemSelectionModel.Select)
                event.accept()
                return
        elif self.header_drag_mode == "column":
            current = self.horizontalHeader().logicalIndexAt(event.pos().x())
            if current >= 0:
                start = min(self.header_drag_start, current)
                end = max(self.header_drag_start, current)
                self.selectionModel().clearSelection()
                for column in range(start, end + 1):
                    self.select_entire_column(column, QItemSelectionModel.Select)
                event.accept()
                return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.header_drag_mode in ("row", "column"):
            self.header_drag_mode = None
            self.header_drag_start = -1
            event.accept()
            return
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        window = self.window()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                window.undo()
                event.accept()
                return
            if event.key() == Qt.Key_Y:
                window.redo()
                event.accept()
                return
            if event.key() == Qt.Key_C:
                window.copy_cells()
                event.accept()
                return
            if event.key() == Qt.Key_X:
                window.cut_cells()
                event.accept()
                return
            if event.key() == Qt.Key_V:
                window.paste_cells()
                event.accept()
                return
        if event.key() == Qt.Key_Backspace:
            if self.state() == QAbstractItemView.EditingState:
                super().keyPressEvent(event)
                return
            if self.selectedItems():
                window.save_history_state()
                for item in self.selectedItems():
                    item.setText("")
            elif self.currentItem():
                window.save_history_state()
                self.currentItem().setText("")
            event.accept()
            return
        if event.key() == Qt.Key_Delete:
            if self.state() == QAbstractItemView.EditingState:
                super().keyPressEvent(event)
                return
            if self.selectedItems():
                window.save_history_state()
                for item in self.selectedItems():
                    item.setText("")
            elif self.currentItem():
                window.save_history_state()
                self.currentItem().setText("")
            event.accept()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current = self.currentIndex()
            if not current.isValid():
                event.accept()
                return
            if self.state() == QAbstractItemView.EditingState:
                event.accept()
                return
            if not self._edit_history_saved:
                window.save_history_state()
                self._edit_history_saved = True
            self.edit(current)
            event.accept()
            return
        if self.state() != QAbstractItemView.EditingState:
            if not modifiers and (
                event.text()
                or event.key() in (
                    Qt.Key_Space,
                    Qt.Key_Backspace,
                    Qt.Key_Delete
                )
            ):
                current = self.currentIndex()
                if current.isValid() and not self._edit_history_saved:
                    window.save_history_state()
                    self._edit_history_saved = True
        super().keyPressEvent(event)
        if self.state() == QAbstractItemView.EditingState:
            self._edit_history_saved = True
    
    def eventFilter(self, watched, event):
        if event.type() == QEvent.FocusIn:
            if watched is self:
                self._edit_history_saved = False
        if event.type() == QEvent.FocusOut:
            self._edit_history_saved = False
        return super().eventFilter(watched, event)

class AddRowsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Rows")
        self.setFixedSize(300, 170)
        layout = QVBoxLayout(self)
        self.number_label = QLabel("Number of rows:")
        layout.addWidget(self.number_label)
        self.number_input = QSpinBox()
        self.number_input.setRange(1, 1000)
        self.number_input.setValue(1)
        layout.addWidget(self.number_input)
        direction_layout = QHBoxLayout()
        self.above_button = QRadioButton("Above")
        self.below_button = QRadioButton("Below")
        self.above_button.setChecked(True)
        direction_layout.addWidget(self.above_button)
        direction_layout.addWidget(self.below_button)
        layout.addLayout(direction_layout)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        direction = "above" if self.above_button.isChecked() else "below"
        return self.number_input.value(), direction

class AddColumnsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Columns")
        self.setFixedSize(300, 170)
        layout = QVBoxLayout(self)
        self.number_label = QLabel("Number of columns:")
        layout.addWidget(self.number_label)
        self.number_input = QSpinBox()
        self.number_input.setRange(1, 1000)
        self.number_input.setValue(1)
        layout.addWidget(self.number_input)
        direction_layout = QHBoxLayout()
        self.left_button = QRadioButton("Left")
        self.right_button = QRadioButton("Right")
        self.left_button.setChecked(True)
        direction_layout.addWidget(self.left_button)
        direction_layout.addWidget(self.right_button)
        layout.addLayout(direction_layout)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        direction = "left" if self.left_button.isChecked() else "right"
        return self.number_input.value(), direction

class Spreadsheet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spreadsheet")
        self.resize(1700, 900)
        self.current_file = None
        self.clipboard_data = None
        self.clipboard_source = None
        self.clipboard_cut = False
        self.sidebar_visible = True
        self.sheet_histories = {}
        self.history_replaying = False
        self.setup_ui()

    def setup_ui(self):
        self.status = QLabel("Ready")
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_status)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setMovable(True)
        self.create_sheet()
        self.update_cell_editor()
        self.tabs.tabBarDoubleClicked.connect(self.rename_tab)
        menu = QMenu(self)
        self.file_menu = menu.addMenu("File Operations")
        self.add_action(
            self.file_menu,
            "New File",
            self.new_file
        )
        self.add_action(
            self.file_menu,
            "Open File",
            self.open_file
        )
        self.add_action(
            self.file_menu,
            "Save As",
            self.save_as
        )
        self.add_action(
            self.file_menu,
            "New Tab",
            self.new_tab
        )
        self.insert_menu = menu.addMenu("Insert Operations")
        self.add_action(
            self.insert_menu,
            "Insert Image",
            self.insert_image
        )
        self.add_action(
            self.insert_menu,
            "Insert Date",
            self.insert_date
        )
        self.add_action(
            menu,
            "Undo",
            self.undo
        )
        self.add_action(
            menu,
            "Redo",
            self.redo
        )
        self.add_action(
            menu,
            "Refresh",
            self.refresh
        )
        self.add_action(
            menu,
            "Copy",
            self.copy_cells
        )
        self.add_action(
            menu,
            "Cut",
            self.cut_cells
        )
        self.add_action(
            menu,
            "Paste",
            self.paste_cells
        )
        self.add_action(
            menu,
            "Bold",
            self.bold
        )
        self.add_action(
            menu,
            "Italic",
            self.italic
        )
        self.add_action(
            menu,
            "Underline",
            self.underline
        )
        self.add_action(
            menu,
            "Strikethrough",
            self.strikethrough
        )
        self.add_action(
            menu,
            "Wrap Text",
            self.wrap_text
        )
        self.add_action(
            menu,
            "Merge Cells",
            self.merge_cells
        )
        self.add_action(
            menu,
            "Unmerge Cells",
            self.unmerge_cells
        )
        self.add_action(
            menu,
            "Font Color",
            self.font_color
        )
        self.add_action(
            menu,
            "Fill Color",
            self.fill_color
        )
        align_menu = menu.addMenu("Horizontal Alignment")
        self.add_action(
            align_menu,
            "Left",
            lambda: self.horizontal_alignment(Qt.AlignLeft)
        )
        self.add_action(
            align_menu,
            "Center",
            lambda: self.horizontal_alignment(Qt.AlignCenter)
        )
        self.add_action(
            align_menu,
            "Right",
            lambda: self.horizontal_alignment(Qt.AlignRight)
        )
        valign_menu = menu.addMenu("Vertical Alignment")
        self.add_action(
            valign_menu,
            "Top",
            lambda: self.vertical_alignment(Qt.AlignTop)
        )
        self.add_action(
            valign_menu,
            "Middle",
            lambda: self.vertical_alignment(Qt.AlignVCenter)
        )
        self.add_action(
            valign_menu,
            "Bottom",
            lambda: self.vertical_alignment(Qt.AlignBottom)
        )
        self.add_action(
            menu,
            "Borders",
            self.borders
        )
        self.add_action(
            menu,
            "Formulas",
            self.formulas
        )
        self.add_action(
            menu,
            "Export HTML",
            self.export_html
        )
        self.add_action(
            menu,
            "Export CSV",
            self.export_csv
        )
        self.menu_button = QToolButton()
        self.menu_button.setText("☰")
        self.menu_button.setFixedSize(38, 38)
        self.menu_button.clicked.connect(self.toggle_sidebar)
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(175)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(4, 4, 4, 4)
        side_layout.setSpacing(2)
        side_layout.setAlignment(Qt.AlignTop)
        side_layout.addWidget(self.menu_button)
        self.sidebar_content = QFrame()
        sidebar_content_layout = QVBoxLayout(
            self.sidebar_content
        )
        sidebar_content_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        sidebar_content_layout.setSpacing(2)
        side_layout.addWidget(self.sidebar_content)
        sidebar_content_layout.addWidget(
            self.side_button(
                "▣ File Operations",
                self.show_file_menu
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "⊕ Insert Operations",
                self.show_insert_menu
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "↶ Undo",
                self.undo
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "↷ Redo",
                self.redo
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "⤢ Scale Up / Down",
                self.scale
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "⟳ Refresh",
                self.refresh
            )
        )
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        sidebar_content_layout.addWidget(line)
        sidebar_content_layout.addWidget(
            self.side_button(
                "▣ Copy",
                self.copy_cells
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "✂ Cut",
                self.cut_cells
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "▣ Paste",
                self.paste_cells
            )
        )
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        sidebar_content_layout.addWidget(line)
        sidebar_content_layout.addWidget(
            self.side_button(
                "B Bold",
                self.bold
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "I Italic",
                self.italic
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "U Underline",
                self.underline
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "S Strikethrough",
                self.strikethrough
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "↕ Wrap Text",
                self.wrap_text
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "⊞ Merge",
                self.merge_cells
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "⊟ Unmerge",
                self.unmerge_cells
            )
        )
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        sidebar_content_layout.addWidget(line)
        sidebar_content_layout.addWidget(
            self.side_button(
                "A Font Color",
                self.font_color
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "◆ Fill Color",
                self.fill_color
            )
        )
        self.horizontal_combo = QComboBox()
        self.horizontal_combo.addItems(
            ["Left", "Centre", "Right"]
        )
        self.horizontal_combo.currentTextChanged.connect(
            self.change_horizontal
        )
        sidebar_content_layout.addWidget(
            self.horizontal_combo
        )
        self.vertical_combo = QComboBox()
        self.vertical_combo.addItems(
            ["Top", "Middle", "Bottom"]
        )
        self.vertical_combo.currentTextChanged.connect(
            self.change_vertical
        )
        sidebar_content_layout.addWidget(
            self.vertical_combo
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "▱ Borders",
                self.borders
            )
        )
        sidebar_content_layout.addWidget(
            self.side_button(
                "Σ Formulas",
                self.formulas
            )
        )
        sidebar_content_layout.addStretch()
        self.statusBar().addWidget(self.status)
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        self.cell_editor = QTextEdit()
        self.cell_editor.setFixedHeight(128)
        self.cell_editor.setPlaceholderText("Selected cell")
        self.cell_editor.setAcceptRichText(False)
        self.cell_editor.textChanged.connect(self.update_selected_cell)
        content.addWidget(self.cell_editor)
        content.addWidget(self.tabs)
        layout.addLayout(content)
        self.setCentralWidget(central)

    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar_content.setVisible(
            self.sidebar_visible
        )
        if self.sidebar_visible:
            self.sidebar.setFixedWidth(175)
        else:
            self.sidebar.setFixedWidth(46)

    def show_file_menu(self):
        position = self.menu_button.mapToGlobal(
            QPoint(self.menu_button.width(), 0)
        )
        self.file_menu.exec_(position)

    def show_insert_menu(self):
        position = self.menu_button.mapToGlobal(
            QPoint(self.menu_button.width(), 0)
        )
        self.insert_menu.exec_(position)

    def add_action(self, menu, text, slot):
        action = menu.addAction(text)
        action.triggered.connect(slot)

    def side_button(self, text, slot):
        button = QPushButton(text)
        button.setFlat(True)
        button.setStyleSheet(
            "QPushButton{"
            "text-align:left;"
            "padding:7px 8px;"
            "font-size:14px;"
            "}"
            "QPushButton:hover{"
            "background:#e8e8e8;"
            "}"
        )
        button.clicked.connect(slot)
        return button

    def create_sheet(self, name="Sheet1"):
        table = SpreadsheetTable(50, 26)
        table.setItemDelegate(
            SpreadsheetDelegate(table)
        )
        table.setObjectName("sheet")
        table.setHorizontalHeaderLabels(
            [
                self.column_name(i)
                for i in range(table.columnCount())
            ]
        )
        table.setVerticalHeaderLabels(
            [
                str(i + 1)
                for i in range(table.rowCount())
            ]
        )
        table.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectItems
        )
        table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.EditKeyPressed |
            QAbstractItemView.AnyKeyPressed
        )
        table.setWordWrap(True)
        vertical_header = SpreadsheetHeader(
            Qt.Vertical,
            table
        )
        horizontal_header = SpreadsheetHeader(
            Qt.Horizontal,
            table
        )
        table.setVerticalHeader(
            vertical_header
        )
        table.setHorizontalHeader(
            horizontal_header
        )
        table.horizontalHeader().setDefaultSectionSize(
            100
        )
        table.verticalHeader().setDefaultSectionSize(
            32
        )
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        table.verticalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        table.setAlternatingRowColors(False)
        table.setStyleSheet(
            "QTableWidget{"
            "gridline-color:#d5d5d5;"
            "font-size:14px;"
            "}"
            "QHeaderView::section{"
            "background:#eef0f2;"
            "border:1px solid #d5d5d5;"
            "padding:4px;"
            "}"
        )
        table.itemSelectionChanged.connect(
            self.update_status
        )
        table.itemSelectionChanged.connect(
            self.update_cell_editor
        )
        table.currentCellChanged.connect(
            lambda row, column, previous_row, previous_column:
            self.update_cell_editor()
        )
        vertical_header.rightClicked.connect(
            lambda index, pos:
            self.row_header_menu(
                table,
                index,
                pos
            )
        )    
        horizontal_header.rightClicked.connect(
            lambda index, pos:
            self.column_header_menu(
                table,
                index,
                pos
            )
        )
        self.tabs.addTab(
            table,
            name
        )
        self.sheet_histories[id(table)] = {
            "undo": [],
            "redo": []
        }
        self.tabs.setCurrentWidget(
            table
        )

    def current_table(self):
        return self.tabs.currentWidget()

    def selected_items(self):
        table = self.current_table()
        if not table:
            return []
        return table.selectedItems()

    def selected_ranges(self):
        table = self.current_table()
        return table.selectedRanges() if table else []
    
    def update_cell_editor(self):
        table = self.current_table()
        if not table:
            return
        index = table.currentIndex()
        if not index.isValid():
            return
        item = table.item(index.row(), index.column())
        text = item.text() if item else ""
        self.cell_editor.blockSignals(True)
        self.cell_editor.setPlainText(text)
        self.cell_editor.blockSignals(False)
    
    def update_selected_cell(self):
        table = self.current_table()
        if not table:
            return
        index = table.currentIndex()
        if not index.isValid():
            return
        item = table.item(index.row(), index.column())
        if not item:
            item = QTableWidgetItem()
            table.setItem(index.row(), index.column(), item)
        item.setText(self.cell_editor.toPlainText())
        table.resizeColumnToContents(index.column())
        table.resizeRowToContents(index.row())

    def column_name(self, n):
        result = ""
        while n >= 0:
            result = chr(n % 26 + 65) + result
            n = n // 26 - 1
        return result

    def update_status(self):
        table = self.current_table()
        if table:
            ranges = table.selectedRanges()
            if ranges:
                r = ranges[0]
                self.status.setText(
                    f"Row: {r.topRow() + 1} | "
                    f"Column: {self.column_name(r.leftColumn())}"
                )
            else:
                self.status.setText("Ready")

    def rename_tab(self, index):
        if index < 0:
            return
        current_name = self.tabs.tabText(index)
        name, ok = QInputDialog.getText(
            self,
            "Rename Tab",
            "Tab name:",
            text=current_name
        )
        if ok and name.strip():
            self.tabs.setTabText(
                index,
                name.strip()
            )

    def row_header_menu(self, table, row, pos):
        if row < 0:
            return
        selected_rows = table.selectionModel().selectedRows()    
        selected_indexes = [
            index.row()
            for index in selected_rows
        ]
        if row not in selected_indexes:    
            table.clearSelection()
            table.selectionModel().select(
                table.model().index(
                    row,
                    0
                ),
                table.selectionModel().Select
                |
                table.selectionModel().Rows
            )
        menu = QMenu(self)    
        add_menu = menu.addMenu(
            "Add Rows"
        )
        above_action = add_menu.addAction(
            "Add Rows Above"
        )
        below_action = add_menu.addAction(
            "Add Rows Below"
        )
        menu.addSeparator()
        delete_action = menu.addAction(
            "Delete Selected Rows"
        )
        global_pos = table.verticalHeader().mapToGlobal(
            pos
        )    
        action = menu.exec_(
            global_pos
        )
        if action == above_action:    
            self.add_rows(
                table,
                "above"
            )
        elif action == below_action:
            self.add_rows(
                table,
                "below"
            )
        elif action == delete_action:
            self.delete_selected_rows(
                table
            )

    def column_header_menu(self, table, column, pos):
        if column < 0:
            return
        selected_columns = (
            table.selectionModel().selectedColumns()
        )    
        selected_indexes = [
            index.column()
            for index in selected_columns
        ]
        if column not in selected_indexes:    
            table.clearSelection()
            table.selectionModel().select(
                table.model().index(
                    0,
                    column
                ),
                table.selectionModel().Select
                |
                table.selectionModel().Columns
            )
        menu = QMenu(self)    
        add_menu = menu.addMenu(
            "Add Columns"
        )
        left_action = add_menu.addAction(
            "Add Columns Left"
        )
        right_action = add_menu.addAction(
            "Add Columns Right"
        )
        menu.addSeparator()
        delete_action = menu.addAction(
            "Delete Selected Columns"
        )
        global_pos = table.horizontalHeader().mapToGlobal(
            pos
        )    
        action = menu.exec_(
            global_pos
        )
        if action == left_action:
            self.add_columns(
                table,
                "left"
            )    
        elif action == right_action:
            self.add_columns(
                table,
                "right"
            )
        elif action == delete_action:
            self.delete_selected_columns(
                table
            )

    def add_rows(self, table, direction):
        rows = table.selectionModel().selectedRows()
        if not rows:
            return
        selected = sorted(
            index.row()
            for index in rows
        )
#        count = len(selected)
        dialog = AddRowsDialog(self)
        dialog.above_button.setChecked(
            direction == "above"
        )
        dialog.below_button.setChecked(
            direction == "below"
        )
        if dialog.exec_() != QDialog.Accepted:
            return
        number, direction = dialog.values()
        if direction == "above":
            position = selected[0]
        else:
            position = selected[-1] + 1
        for _ in range(number):
            table.insertRow(position)
        self.refresh_headers(table)

    def add_columns(self, table, direction):
        columns = table.selectionModel().selectedColumns()
        if not columns:
            return
        selected = sorted(
            index.column()
            for index in columns
        )
        dialog = AddColumnsDialog(self)
        dialog.left_button.setChecked(
            direction == "left"
        )
        dialog.right_button.setChecked(
            direction == "right"
        )
        if dialog.exec_() != QDialog.Accepted:
            return
        number, direction = dialog.values()
        if direction == "left":
            position = selected[0]
        else:
            position = selected[-1] + 1
        for _ in range(number):
            table.insertColumn(position)
        self.refresh_headers(table)
        
    def delete_selected_rows(self, table):
        selected_rows = (
            table.selectionModel().selectedRows()
        )    
        if not selected_rows:
            return
        rows = sorted(
            [
                index.row()
                for index in selected_rows
            ],
            reverse=True
        )
        for row in rows:
            table.removeRow(row)
        self.refresh_headers(table)
        table.clearSelection()
        if table.rowCount() > 0:
            table.setCurrentCell(
                min(rows[-1], table.rowCount() - 1),
                0
            )
            
    def delete_selected_columns(self, table):
        selected_columns = (
            table.selectionModel().selectedColumns()
        )
        if not selected_columns:
            return
        columns = sorted(
            [
                index.column()
                for index in selected_columns
            ],
            reverse=True
        )
        for column in columns:
            table.removeColumn(column)
        self.refresh_headers(table)
        table.clearSelection()
        if table.columnCount() > 0:
            table.setCurrentCell(
                0,
                min(columns[-1], table.columnCount() - 1)
            )

    def delete_row(self):
        table = self.current_table()    
        if not table:
            return
        selected_rows = (
            table.selectionModel().selectedRows()
        )
        if selected_rows:
            self.delete_selected_rows(
                table
            )
            return
        row = table.currentRow()
        if row >= 0:
            table.removeRow(
                row
            )
            self.refresh_headers(
                table
            )

    def delete_column(self):
        table = self.current_table()
        if not table:
            return
        selected_columns = (
            table.selectionModel().selectedColumns()
        )
        if selected_columns:
            self.delete_selected_columns(
                table
            )
            return
        column = table.currentColumn()
        if column >= 0:
            table.removeColumn(
                column
            )
            self.refresh_headers(
                table
            )

    def refresh_headers(self, table=None):
        if table is None:
            table = self.current_table()
        if not table:
            return
        table.setHorizontalHeaderLabels(
            [
                self.column_name(i)
                for i in range(table.columnCount())
            ]
        )
        table.setVerticalHeaderLabels(
            [
                str(i + 1)
                for i in range(table.rowCount())
            ]
        )

    def new_file(self):
        self.tabs.clear()
        self.current_file = None
        self.create_sheet("Sheet1")

    def new_tab(self):
        number = self.tabs.count() + 1
        self.create_sheet(
            f"Sheet{number}"
        )

    def close_tab(self, index):
        if self.tabs.count() == 1:
            return
        table = self.tabs.widget(index)
        if table:
            self.sheet_histories.pop(
                id(table),
                None
            )
        self.tabs.removeTab(index)

    def close_current_tab(self):
        if self.tabs.count() > 1:
            self.close_tab(
                self.tabs.currentIndex()
            )

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Spreadsheet Files (*.csv *.html);;"
            "CSV Files (*.csv);;"
            "HTML Files (*.html)"
        )
        if not path:
            return
        if path.lower().endswith(".csv"):
            self.load_csv(path)
        elif path.lower().endswith(".html"):
            QMessageBox.information(
                self,
                "Open HTML",
                "HTML files are currently export-only. "
                "CSV files can be reopened."
            )

    def load_csv(self, path):
        import csv
        self.new_file()
        table = self.current_table()
        with open(
            path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:
            rows = list(csv.reader(f))
        table.setRowCount(
            max(50, len(rows))
        )
        table.setColumnCount(
            max(
                26,
                max(
                    [
                        len(r)
                        for r in rows
                    ],
                    default=26
                )
            )
        )
        self.refresh_headers(table)
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                table.setItem(
                    r,
                    c,
                    QTableWidgetItem(value)
                )
        self.current_file = path

    def save_file(self):
        if not self.current_file:
            return self.save_as()
        if self.current_file.lower().endswith(".csv"):
            self.export_csv_to(
                self.current_file
            )
        else:
            self.save_as()

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "CSV Files (*.csv);;HTML Files (*.html)"
        )
        if not path:
            return
        if path.lower().endswith(".html"):
            self.export_html_to(path)
        else:
            self.export_csv_to(path)
        self.current_file = path

    def copy_cells(self):
        table = self.current_table()
        if not table:
            return
        ranges = table.selectedRanges()
        if not ranges:
            return
        selection = ranges[0]
        data = []
        for r in range(selection.topRow(), selection.bottomRow() + 1):
            row_data = []
            for c in range(selection.leftColumn(), selection.rightColumn() + 1):
                item = table.item(r, c)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        self.clipboard_data = data
        self.clipboard_source = (
            selection.topRow(),
            selection.leftColumn(),
            selection.bottomRow(),
            selection.rightColumn()
        )
        self.clipboard_cut = False
        QApplication.clipboard().setText(
            "\n".join(
                "\t".join(row)
                for row in data
            )
        )

    def cut_cells(self):
        table = self.current_table()
        if not table:
            return
        self.copy_cells()
        if self.clipboard_data is None:
            return
        self.save_history_state()
        self.clipboard_cut = True
        for item in table.selectedItems():
            item.setText("")
        table.viewport().update()
    
    def paste_cells(self):
        table = self.current_table()
        if not table or not self.clipboard_data:
            return
        ranges = table.selectedRanges()
        if ranges:
            selection = ranges[0]
            start_row = selection.topRow()
            start_column = selection.leftColumn()
            destination_rows = selection.rowCount()
            destination_columns = selection.columnCount()
        else:
            current = table.currentIndex()
            if not current.isValid():
                return
            start_row = current.row()
            start_column = current.column()
            destination_rows = 1
            destination_columns = 1
        source = self.clipboard_data
        source_rows = len(source)
        source_columns = max(
            len(row)
            for row in source
        )
        self.save_history_state()
        if source_rows == 1 and source_columns == 1:
            target_rows = destination_rows
            target_columns = destination_columns
        elif destination_rows == 1 and destination_columns == 1:
            target_rows = source_rows
            target_columns = source_columns
        else:
            target_rows = destination_rows
            target_columns = destination_columns
        for row_offset in range(target_rows):
            for column_offset in range(target_columns):
                source_row = row_offset % source_rows
                source_column = column_offset % len(source[source_row])
                value = source[source_row][source_column]
                row = start_row + row_offset
                column = start_column + column_offset
                while row >= table.rowCount():
                    table.insertRow(table.rowCount())
                while column >= table.columnCount():
                    table.insertColumn(table.columnCount())
                item = table.item(row, column)
                if not item:
                    item = QTableWidgetItem()
                    table.setItem(row, column, item)
                item.setText(value)
        self.refresh_headers(table)
        table.viewport().update()
        if self.clipboard_cut:
            self.clipboard_cut = False
            self.clipboard_source = None
            
    def save_history_state(self):
        table = self.current_table()
        if not table or self.history_replaying:
            return
        history = self.sheet_histories.setdefault(
            id(table),
            {"undo": [], "redo": []}
        )
        state = self.capture_table_state(table)
        if history["undo"] and self.states_equal(history["undo"][-1], state):
            return
        history["undo"].append(state)
        if len(history["undo"]) > 100:
            history["undo"].pop(0)
        history["redo"].clear()
    
    def capture_table_state(self, table):
        state = {
            "rows": table.rowCount(),
            "columns": table.columnCount(),
            "cells": [],
            "spans": [],
            "row_heights": [
                table.rowHeight(r)
                for r in range(table.rowCount())
            ],
            "column_widths": [
                table.columnWidth(c)
                for c in range(table.columnCount())
            ]
        }
        for r in range(table.rowCount()):
            row = []
            for c in range(table.columnCount()):
                item = table.item(r, c)
                if item:
                    row.append({
                        "text": item.text(),
                        "font": item.font(),
                        "foreground": item.foreground(),
                        "background": item.background(),
                        "alignment": item.textAlignment(),
                        "flags": item.flags(),
                        "data1": item.data(Qt.UserRole + 1),
                        "data2": item.data(Qt.UserRole + 2)
                    })
                else:
                    row.append(None)
            state["cells"].append(row)
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                rowspan = table.rowSpan(r, c)
                colspan = table.columnSpan(r, c)
                if rowspan > 1 or colspan > 1:
                    state["spans"].append(
                        (r, c, rowspan, colspan)
                    )
        return state
    
    def states_equal(self, first, second):
        if first["rows"] != second["rows"]:
            return False
        if first["columns"] != second["columns"]:
            return False
        if first["spans"] != second["spans"]:
            return False
        if first["row_heights"] != second["row_heights"]:
            return False
        if first["column_widths"] != second["column_widths"]:
            return False
        for r in range(first["rows"]):
            for c in range(first["columns"]):
                a = first["cells"][r][c]
                b = second["cells"][r][c]
                if a is None and b is None:
                    continue
                if a is None or b is None:
                    return False
                if a["text"] != b["text"]:
                    return False
                if a["font"] != b["font"]:
                    return False
                if a["foreground"] != b["foreground"]:
                    return False
                if a["background"] != b["background"]:
                    return False
                if a["alignment"] != b["alignment"]:
                    return False
                if a["flags"] != b["flags"]:
                    return False
                if a["data1"] != b["data1"]:
                    return False
                if a["data2"] != b["data2"]:
                    return False
        return True
    
    def restore_table_state(self, table, state):
        self.history_replaying = True
        table.setUpdatesEnabled(False)
        table.clearSpans()
        table.setRowCount(state["rows"])
        table.setColumnCount(state["columns"])
        for r in range(state["rows"]):
            for c in range(state["columns"]):
                data = state["cells"][r][c]
                if data is None:
                    table.setItem(r, c, None)
                    continue
                item = QTableWidgetItem(data["text"])
                item.setFont(data["font"])
                item.setForeground(data["foreground"])
                item.setBackground(data["background"])
                item.setTextAlignment(data["alignment"])
                item.setFlags(data["flags"])
                item.setData(Qt.UserRole + 1, data["data1"])
                item.setData(Qt.UserRole + 2, data["data2"])
                table.setItem(r, c, item)
        for r, height in enumerate(state["row_heights"]):
            if r < table.rowCount():
                table.setRowHeight(r, height)
        for c, width in enumerate(state["column_widths"]):
            if c < table.columnCount():
                table.setColumnWidth(c, width)
        for r, c, rowspan, colspan in state["spans"]:
            if (
                r < table.rowCount()
                and c < table.columnCount()
            ):
                table.setSpan(
                    r,
                    c,
                    rowspan,
                    colspan
                )
        self.refresh_headers(table)
        table.setUpdatesEnabled(True)
        table.viewport().update()
        self.history_replaying = False
        table._edit_history_saved = False

    def undo(self):
        table = self.current_table()
        if not table:
            return
        history = self.sheet_histories.setdefault(
            id(table),
            {"undo": [], "redo": []}
        )
        if not history["undo"]:
            return
        current_state = self.capture_table_state(table)
        previous_state = history["undo"].pop()
        history["redo"].append(current_state)
        self.restore_table_state(
            table,
            previous_state
        )
        self.status.setText("Undo")
    
    def redo(self):
        table = self.current_table()
        if not table:
            return
        history = self.sheet_histories.setdefault(
            id(table),
            {"undo": [], "redo": []}
        )
        if not history["redo"]:
            return
        current_state = self.capture_table_state(table)
        next_state = history["redo"].pop()
        history["undo"].append(current_state)
        self.restore_table_state(
            table,
            next_state
        )
        self.status.setText("Redo")

    def refresh(self):
        table = self.current_table()
        if not table:
            return
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        for column in range(table.columnCount()):
            width = table.columnWidth(column)
            table.setColumnWidth(column, max(100, width))
        for row in range(table.rowCount()):
            height = table.rowHeight(row)
            table.setRowHeight(row, max(32, height))
        table.viewport().update()

    def scale(self):
        table = self.current_table()
        if not table:
            return
        value, ok = QInputDialog.getInt(
            self,
            "Scale",
            "Spreadsheet scale (%):",
            100,
            50,
            200
        )
        if not ok:
            return
        factor = value / 100
        table.setStyleSheet(
            "QTableWidget{"
            f"gridline-color:#d5d5d5;"
            f"font-size:{14 * factor}px;"
            "}"
            "QHeaderView::section{"
            "background:#eef0f2;"
            "border:1px solid #d5d5d5;"
            f"padding:{4 * factor}px;"
            "}"
        )
        table.horizontalHeader().setDefaultSectionSize(
            int(100 * factor)
        )
        table.verticalHeader().setDefaultSectionSize(
            int(32 * factor)
        )
        table.resizeRowsToContents()

    def bold(self):
        self.set_font_property("bold")

    def italic(self):
        self.set_font_property("italic")

    def underline(self):
        self.set_font_property("underline")

    def strikethrough(self):
        self.set_font_property("strike")

    def set_font_property(self, prop):
        items = self.selected_items()
        if not items:
            return
        self.save_history_state()
        for item in items:
            font = item.font()
            if prop == "bold":
                font.setBold(not font.bold())
            elif prop == "italic":
                font.setItalic(not font.italic())
            elif prop == "underline":
                font.setUnderline(not font.underline())
            elif prop == "strike":
                font.setStrikeOut(not font.strikeOut())
            item.setFont(font)

    def wrap_text(self):
        items = self.selected_items()
        if not items:
            return
        self.save_history_state()
        for item in items:
            alignment = item.textAlignment()
            item.setData(
                Qt.UserRole + 1,
                True
            )
            item.setTextAlignment(
                alignment
            )
        table = self.current_table()
        if table:
            table.resizeRowsToContents()

    def merge_cells(self):
        table = self.current_table()
        if not table:
            return
        ranges = table.selectedRanges()
        if not ranges:
            return
        top = min(r.topRow() for r in ranges)
        left = min(r.leftColumn() for r in ranges)
        bottom = max(r.bottomRow() for r in ranges)
        right = max(r.rightColumn() for r in ranges)
        if top == bottom and left == right:
            span_row = table.rowSpan(top, left)
            span_column = table.columnSpan(top, left)
            if span_row > 1 or span_column > 1:
                bottom = top + span_row - 1
                right = left + span_column - 1
            else:
                QMessageBox.information(
                    self,
                    "Merge Cells",
                    "Select multiple cells first."
                )
                return
        existing_ranges = []
        processed = set()
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                span_row = table.rowSpan(row, column)
                span_column = table.columnSpan(row, column)
                if span_row <= 1 and span_column <= 1:
                    continue
                merged_top = row
                merged_left = column
                for r in range(row, -1, -1):
                    for c in range(column, -1, -1):
                        if table.rowSpan(r, c) == span_row and table.columnSpan(r, c) == span_column:
                            merged_top = r
                            merged_left = c
                            break
                    else:
                        continue
                    break
                merged_bottom = merged_top + span_row - 1
                merged_right = merged_left + span_column - 1
                key = (
                    merged_top,
                    merged_left,
                    merged_bottom,
                    merged_right
                )
                if key in processed:
                    continue
                processed.add(key)
                existing_ranges.append(key)
        for merged_top, merged_left, merged_bottom, merged_right in existing_ranges:
            if (
                merged_top < top or
                merged_left < left or
                merged_bottom > bottom or
                merged_right > right
            ):
                QMessageBox.warning(
                    self,
                    "Merge Cells",
                    "The selection partially overlaps an existing merged range."
                )
                return
        texts = []
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                item = table.item(row, column)
                if item and item.text():
                    texts.append(item.text())
        for merged_top, merged_left, merged_bottom, merged_right in existing_ranges:
            table.setSpan(
                merged_top,
                merged_left,
                1,
                1
            )
        table.setSpan(
            top,
            left,
            bottom - top + 1,
            right - left + 1
        )
        item = table.item(top, left)
        if not item:
            item = QTableWidgetItem()
            table.setItem(
                top,
                left,
                item
            )
        item.setText(" ".join(texts))
        table.setCurrentCell(
            top,
            left
        )
        table.viewport().update()

    def unmerge_cells(self):
        table = self.current_table()
        ranges = self.selected_ranges()
        if not table or not ranges:
            return
        self.save_history_state()
        table.clearSpans()
        table.viewport().update()

    def font_color(self):
        color = QColorDialog.getColor(
            Qt.black,
            self,
            "Font Color"
        )
        if not color.isValid():
            return
        items = self.selected_items()
        if not items:
            return
        self.save_history_state()
        for item in items:
            item.setForeground(color)

    def fill_color(self):
        color = QColorDialog.getColor(
            Qt.white,
            self,
            "Fill Color"
        )
        if not color.isValid():
            return
        items = self.selected_items()
        if not items:
            return
        self.save_history_state()
        for item in items:
            item.setBackground(color)

    def horizontal_alignment(self, alignment):
        items = self.selected_items()
        if not items:
            return
        self.save_history_state()
        for item in items:
            item.setTextAlignment(
                alignment | Qt.AlignVCenter
            )

    def vertical_alignment(self, alignment):
        items = self.selected_items()
        if not items:
            return
        self.save_history_state()
        for item in items:
            current = item.textAlignment()
            horizontal = (
                current &
                Qt.AlignHorizontal_Mask
            )
            item.setTextAlignment(
                horizontal | alignment
            )

    def change_horizontal(self, value):
        if value == "Left":
            self.horizontal_alignment(
                Qt.AlignLeft
            )
        elif value == "Centre":
            self.horizontal_alignment(
                Qt.AlignCenter
            )
        else:
            self.horizontal_alignment(
                Qt.AlignRight
            )

    def change_vertical(self, value):
        if value == "Top":
            self.vertical_alignment(
                Qt.AlignTop
            )
        elif value == "Middle":
            self.vertical_alignment(
                Qt.AlignVCenter
            )
        else:
            self.vertical_alignment(
                Qt.AlignBottom
            )

    def borders(self):
        table = self.current_table()
        if not table:
            return
        menu = QMenu(self)
        all_action = menu.addAction("All Borders")
        inner_action = menu.addAction("Inner Borders")
        outer_action = menu.addAction("Outer Borders")
        left_action = menu.addAction("Left Borders")
        right_action = menu.addAction("Right Borders")
        top_action = menu.addAction("Top Borders")
        bottom_action = menu.addAction("Bottom Borders")
        no_action = menu.addAction("No Borders")
        menu.addSeparator()
        color_action = menu.addAction("Border Color")
        action = menu.exec_(self.cursor().pos())
        if action == color_action:
            color = QColorDialog.getColor(Qt.black, self, "Border Color")
            if not color.isValid():
                return
            table._border_color = color.name()
            return
        if action is None:
            return
        selected = table.selectedRanges()
        if not selected:
            current = table.currentIndex()
            if not current.isValid():
                return
            selected = [QTableWidgetSelectionRange(
                current.row(),
                current.column(),
                current.row(),
                current.column()
            )]
        color = getattr(table, "_border_color", "#000000")
        border_map = getattr(table, "_cell_borders", {})
        for selection in selected:
            top = selection.topRow()
            bottom = selection.bottomRow()
            left = selection.leftColumn()
            right = selection.rightColumn()
            for row in range(top, bottom + 1):
                for column in range(left, right + 1):
                    key = (row, column)
                    borders = border_map.setdefault(key, set())
                    if action == no_action:
                        borders.clear()
                    elif action == all_action:
                        borders.update(["top", "bottom", "left", "right"])
                    elif action == inner_action:
                        if row > top:
                            borders.add("top")
                        if row < bottom:
                            borders.add("bottom")
                        if column > left:
                            borders.add("left")
                        if column < right:
                            borders.add("right")
                    elif action == outer_action:
                        if row == top:
                            borders.add("top")
                        if row == bottom:
                            borders.add("bottom")
                        if column == left:
                            borders.add("left")
                        if column == right:
                            borders.add("right")
                    elif action == left_action:
                        if column == left:
                            borders.add("left")
                    elif action == right_action:
                        if column == right:
                            borders.add("right")
                    elif action == top_action:
                        if row == top:
                            borders.add("top")
                    elif action == bottom_action:
                        if row == bottom:
                            borders.add("bottom")
                    border_map[key] = borders
        table._cell_borders = border_map
        table.viewport().update()


    def insert_date(self):
        table = self.current_table()
        if not table:
            return
        items = self.selected_items()
        if not items:
            return
        self.save_history_state()
        date = datetime.now().strftime("%d/%m/%Y")
        for item in items:
            item.setText(date)

    def insert_image(self):
        table = self.current_table()
        if not table:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Insert Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not path:
            return
        item = table.currentItem()
        if not item:
            item = QTableWidgetItem()
            table.setItem(
                table.currentRow(),
                table.currentColumn(),
                item
            )
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
        label = QLabel()
        label.setPixmap(
            pixmap.scaled(
                150,
                150,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
        label.setAlignment(
            Qt.AlignCenter
        )
        table.setCellWidget(
            item.row(),
            item.column(),
            label
        )
        table.setRowHeight(
            item.row(),
            160
        )

    def formulas(self):
        table = self.current_table()
        if not table:
            return
        formula, ok = QInputDialog.getText(
            self,
            "Formula",
            "Enter formula, e.g. =SUM(A1:A5):"
        )
        if not ok or not formula:
            return
        self.save_history_state()
        item = table.currentItem()
        if not item:
            item = QTableWidgetItem()
            table.setItem(
                table.currentRow(),
                table.currentColumn(),
                item
            )
        if formula.startswith("="):
            result = self.calculate_formula(formula)
            item.setText(str(result))
        else:
            item.setText(formula)


    def calculate_formula(self, formula):
        import re
        table = self.current_table()
        expression = formula[1:].upper()
        match = re.fullmatch(
            r"SUM\(([A-Z]+)(\d+):([A-Z]+)(\d+)\)",
            expression
        )
        if match:
            c1, r1, c2, r2 = match.groups()
            total = 0
            for r in range(
                int(r1) - 1,
                int(r2)
            ):
                for c in range(
                    self.column_number(c1),
                    self.column_number(c2) + 1
                ):
                    item = table.item(r, c)
                    if item:
                        try:
                            total += float(
                                item.text()
                            )
                        except:
                            pass
            return (
                int(total)
                if total.is_integer()
                else total
            )
        return formula

    def column_number(self, name):
        number = 0
        for char in name:
            number = (
                number * 26 +
                ord(char) -
                64
            )
        return number - 1
    
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "",
            "CSV Files (*.csv)"
        )
        if path:
            self.export_csv_to(path)


    def export_csv_to(self, path):
        import csv
        table = self.current_table()
        with open(
            path,
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as f:
            writer = csv.writer(f)
            for r in range(
                table.rowCount()
            ):
                row = []
                for c in range(
                    table.columnCount()
                ):
                    item = table.item(r, c)
                    row.append(
                        item.text()
                        if item
                        else ""
                    )
                writer.writerow(row)

    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export HTML",
            "",
            "HTML Files (*.html)"
        )
        if path:
            self.export_html_to(path)

    def export_html_to(self, path):
        table = self.current_table()
        rows = []
        rows.append(
            "<!DOCTYPE html>"
            "<html>"
            "<head>"
            "<meta charset='UTF-8'>"
            "<title>Spreadsheet</title>"
            "<style>"
            "body{font-family:Arial,sans-serif;"
            "margin:20px;background:white}"
            "table{border-collapse:collapse;"
            "table-layout:fixed}"
            "th,td{border:1px solid #ccc;"
            "padding:5px;min-width:80px;"
            "height:30px;vertical-align:middle;"
            "white-space:normal}"
            "th{background:#eef0f2;"
            "font-weight:bold;text-align:center}"
            "img{max-width:100%;height:auto}"
            "</style>"
            "</head>"
            "<body>"
            "<table>"
        )
        rows.append("<tr><th></th>")
        for c in range(
            table.columnCount()
        ):
            rows.append(
                f"<th>{self.column_name(c)}</th>"
            )
        rows.append("</tr>")
        for r in range(
            table.rowCount()
        ):
            rows.append(
                f"<tr><th>{r + 1}</th>"
            )
            for c in range(
                table.columnCount()
            ):
                item = table.item(r, c)
                widget = table.cellWidget(r, c)
                attrs = ""
                content = ""
                if item:
                    font = item.font()
                    if font.bold():
                        attrs += "font-weight:bold;"
                    if font.italic():
                        attrs += "font-style:italic;"
                    decorations = []
                    if font.underline():
                        decorations.append(
                            "underline"
                        )
                    if font.strikeOut():
                        decorations.append(
                            "line-through"
                        )
                    if decorations:
                        attrs += (
                            "text-decoration:"
                            f"{' '.join(decorations)};"
                        )
                    attrs += (
                        "color:"
                        f"{item.foreground().color().name()};"
                    )
                    attrs += (
                        "background-color:"
                        f"{item.background().color().name()};"
                    )
                    align = item.textAlignment()
                    if align & Qt.AlignLeft:
                        attrs += "text-align:left;"
                    elif align & Qt.AlignRight:
                        attrs += "text-align:right;"
                    else:
                        attrs += "text-align:center;"
                    if align & Qt.AlignTop:
                        attrs += "vertical-align:top;"
                    elif align & Qt.AlignBottom:
                        attrs += "vertical-align:bottom;"
                    else:
                        attrs += "vertical-align:middle;"
                    content = (
                        item.text()
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace("\n", "<br>")
                    )
                if (
                    widget and
                    isinstance(widget, QLabel) and
                    widget.pixmap()
                ):
                    image = widget.pixmap().toImage()
                    from PyQt5.QtCore import (
                        QBuffer,
                        QIODevice
                    )
                    qbuffer = QBuffer()
                    qbuffer.open(
                        QIODevice.WriteOnly
                    )
                    image.save(
                        qbuffer,
                        "PNG"
                    )
                    encoded = base64.b64encode(
                        bytes(qbuffer.data())
                    ).decode()
                    content = (
                        "<img src='data:image/png;"
                        f"base64,{encoded}'>"
                    )
                rowspan = table.rowSpan(r, c)
                colspan = table.columnSpan(r, c)
                span = ""
                if rowspan > 1:
                    span += (
                        f" rowspan='{rowspan}'"
                    )
                if colspan > 1:
                    span += (
                        f" colspan='{colspan}'"
                    )
                rows.append(
                    f"<td style='{attrs}'"
                    f"{span}>{content}</td>"
                )
            rows.append("</tr>")
        rows.append(
            "</table>"
            "</body>"
            "</html>"
        )
        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(
                "".join(rows)
            )

app = QApplication(sys.argv)
window = Spreadsheet()
window.show()
sys.exit(app.exec_())