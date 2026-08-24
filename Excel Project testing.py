import json
import sys
import base64
import os
from PyQt5.QtCore import (
    Qt, QPoint, QItemSelection, QItemSelectionModel, pyqtSignal, QEvent, QDate
)
from PyQt5.QtGui import (
    QPixmap, QColor, QImageReader, QCursor
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QLabel, QToolButton, QMenu, QFileDialog, QInputDialog, QColorDialog,
    QMessageBox, QTabWidget, QHeaderView, QAbstractItemView, QComboBox, QFrame, QDialog,
    QSpinBox, QRadioButton, QDialogButtonBox, QStyledItemDelegate, QAbstractItemDelegate,
    QTextEdit, QTableWidgetSelectionRange, QScrollArea, QSizePolicy
)
try:
    from PyQt5.QtPdf import QPdfDocument
    from PyQt5.QtPdfWidgets import QPdfView
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    
class SpreadsheetHeader(QHeaderView):
    rightClicked = pyqtSignal(int, QPoint)
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setHighlightSections(True)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.logicalIndexAt(event.pos().y() if self.orientation() == Qt.Vertical else event.pos().x())
            if index >= 0:
                self.rightClicked.emit(index, event.pos())
            event.accept()
            return
        
        super().mousePressEvent(event)
class SpreadsheetDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if editor is not None:
            editor.installEventFilter(self)
            table = index.model().parent()
            if table is not None:
                window = table.window()
                if hasattr(window, "save_history_state"):
                    window.save_history_state()
                table._edit_history_saved = True
        return editor
    
    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QAbstractItemDelegate.NoHint)
                return True
        if event.type() == QEvent.FocusOut:
            table = editor.parent()
            while table is not None and not isinstance(table, SpreadsheetTable):
                table = table.parent()
            if table is not None:
                table._edit_history_saved = False
        return super().eventFilter(editor, event)
    
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        table = index.model().parent()
        if table is None:
            return
        border_map = getattr(table, "_cell_borders", {})
        borders = border_map.get((index.row(), index.column()), set())
        if not borders:
            return
        color = QColor(getattr(table, "_border_color", "#000000"))
        painter.save()
        pen = painter.pen()
        pen.setColor(color)
        pen.setWidth(1)
        painter.setPen(pen)
        rect = option.rect
        if "top" in borders:
            painter.drawLine(rect.topLeft(), rect.topRight())
        if "bottom" in borders:
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        if "left" in borders:
            painter.drawLine(rect.topLeft(), rect.bottomLeft())
        if "right" in borders:
            painter.drawLine(rect.topRight(), rect.bottomRight())
        painter.restore()
        
class MediaViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.zoom_factor = 1.0
        self.locked = False
        self.media_type = None
        self.pdf_document = None
        self.pdf_view = None
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setMinimumSize(1, 1)
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(False)
        self.image_scroll.setAlignment(Qt.AlignCenter)
        self.image_scroll.setWidget(self.image_label)
        self.header = QFrame()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(5, 5, 5, 5)
        self.lock_button = QPushButton("🔓 Unlock")
        self.lock_button.setCheckable(True)
        self.lock_button.clicked.connect(self.toggle_lock)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_zoom)
        self.name_label = QLabel("")
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout.addWidget(self.name_label)
        header_layout.addWidget(self.lock_button)
        header_layout.addWidget(self.reset_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.image_scroll)
        self.image_scroll.viewport().installEventFilter(self)
        self.setStyleSheet("QWidget{background:#fafafa;}QPushButton{padding:5px 10px;font-size:13px;}")
    
    def toggle_lock(self):
        self.locked = self.lock_button.isChecked()
        self.lock_button.setText("🔒 Locked" if self.locked else "🔓 Unlock")
    
    def reset_zoom(self):
        self.zoom_factor = 1.0
        if self.media_type == "image":
            self.update_image()
        elif self.media_type == "pdf":
            if self.pdf_view is not None:
                self.pdf_view.setZoomFactor(1.0)
    
    def clear_viewer(self):
        self.file_path = None
        self.media_type = None
        self.name_label.setText("")
        self.image_label.clear()
        if self.pdf_view is not None:
            self.pdf_view.hide()
            self.pdf_view.setDocument(None)
        self.image_scroll.setWidget(self.image_label)
        self.image_label.setText("Select an image or PDF cell")
        self.image_label.setStyleSheet("font-size:16px;color:#777;")
        self.image_label.adjustSize()
        self.zoom_factor = 1.0
    
    def show_media(self, path):
        if not path or not os.path.exists(path):
            self.clear_viewer()
            return
        self.file_path = path
        self.name_label.setText(os.path.basename(path))
        extension = os.path.splitext(path)[1].lower()
        if extension == ".pdf":
            self.show_pdf(path)
        else:
            self.show_image(path)
    
    def show_image(self, path):
        self.media_type = "image"
        self.zoom_factor = 1.0
        if self.pdf_view is not None:
            self.pdf_view.hide()
        self.image_label.setText("")
        self.image_label.setStyleSheet("")
        self.image_scroll.setWidget(self.image_label)
        reader = QImageReader(path)
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            self.image_label.setText("Unable to display image")
            self.image_label.setStyleSheet("font-size:16px;color:#c00;")
            self.image_label.adjustSize()
            return
        self._image = image
        self.update_image()
    
    def update_image(self):
        if self.media_type != "image" or not hasattr(self, "_image"):
            return
        pixmap = QPixmap.fromImage(self._image)
        if pixmap.isNull():
            return
        width = max(1, int(pixmap.width() * self.zoom_factor))
        height = max(1, int(pixmap.height() * self.zoom_factor))
        scaled = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.resize(scaled.size())
    
    def show_pdf(self, path):
        if not PDF_SUPPORT:
            self.media_type = "pdf"
            self.image_label.setText("PDF support is unavailable in this PyQt5 installation.")
            self.image_label.setStyleSheet("font-size:16px;color:#c00;")
            self.image_scroll.setWidget(self.image_label)
            self.image_label.adjustSize()
            return
        self.media_type = "pdf"
        self.pdf_document = QPdfDocument(self)
        error = self.pdf_document.load(path)
        if error != QPdfDocument.Error.None_:
            self.image_label.setText("Unable to open PDF")
            self.image_label.setStyleSheet("font-size:16px;color:#c00;")
            self.image_scroll.setWidget(self.image_label)
            self.image_label.adjustSize()
            return
        if self.pdf_view is None:
            self.pdf_view = QPdfView()
            self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setZoomFactor(1.0)
        self.image_scroll.setWidget(self.pdf_view)
    
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Wheel and self.file_path and not self.locked:
            delta = event.angleDelta().y()
            if delta == 0:
                return False
            if self.media_type == "image":
                old_zoom = self.zoom_factor
                factor = 1.15 if delta > 0 else 1 / 1.15
                new_zoom = max(0.05, min(10.0, old_zoom * factor))
                cursor_pos = event.pos()
                hbar = self.image_scroll.horizontalScrollBar()
                vbar = self.image_scroll.verticalScrollBar()
                old_x = hbar.value()
                old_y = vbar.value()
                relative_x = cursor_pos.x() + old_x
                relative_y = cursor_pos.y() + old_y
                ratio_x = relative_x / max(1, self.image_label.width())
                ratio_y = relative_y / max(1, self.image_label.height())
                self.zoom_factor = new_zoom
                self.update_image()
                new_relative_x = ratio_x * self.image_label.width()
                new_relative_y = ratio_y * self.image_label.height()
                hbar.setValue(int(new_relative_x - cursor_pos.x()))
                vbar.setValue(int(new_relative_y - cursor_pos.y()))
                return True
            if self.media_type == "pdf" and self.pdf_view is not None:
                old_zoom = self.pdf_view.zoomFactor()
                factor = 1.15 if delta > 0 else 1 / 1.15
                new_zoom = max(0.05, min(10.0, old_zoom * factor))
                self.pdf_view.setZoomFactor(new_zoom)
                return True
        return super().eventFilter(watched, event)

class SpreadsheetTable(QTableWidget):
    def __init__(self, rows=0, columns=0, parent=None):
        super().__init__(rows, columns, parent)
        self.header_drag_mode = None
        self.header_drag_start = -1
        self.header_anchor = -1
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.installEventFilter(self)
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
    
    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid() and not self.selectionModel().isSelected(index):
            self.setCurrentCell(index.row(), index.column(), QItemSelectionModel.ClearAndSelect)
        window = self.window()
        if hasattr(window, "cell_context_menu"):
            window.cell_context_menu(self, event.globalPos())
        event.accept()
    
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
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
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
            if not modifiers and (event.text() or event.key() in (Qt.Key_Space, Qt.Key_Backspace, Qt.Key_Delete)):
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
        if event.type() == QEvent.MouseButtonPress:
            self._edit_history_saved = False
        return super().eventFilter(watched, event)

class AddRowsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Rows")
        self.setFixedSize(300, 170)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Number of rows:"))
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
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def values(self):
        return self.number_input.value(), "above" if self.above_button.isChecked() else "below"

class AddColumnsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Columns")
        self.setFixedSize(300, 170)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Number of columns:"))
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
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def values(self):
        return self.number_input.value(), "left" if self.left_button.isChecked() else "right"    

class Spreadsheet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spreadsheet")
        self.resize(1700, 900)
        self.current_file = None
        self.clipboard_data = None
        self.sidebar_visible = True
        self.viewer_visible = True
        self.sheet_histories = {}
        self.history_replaying = False
        self.session_data = {"version": 1, "current_file": None, "current_tab": 0, "sheets": []}
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
        self.add_action(self.file_menu, "New File", self.new_file)
        self.add_action(self.file_menu, "Open File", self.open_file)
        self.add_action(self.file_menu, "Save As", self.save_as)
        self.add_action(self.file_menu, "New Tab", self.new_tab)
        self.insert_menu = menu.addMenu("Insert Operations")
        self.add_action(self.insert_menu, "Insert Image / PDF", self.insert_media)
        self.add_action(self.insert_menu, "Insert Date", self.insert_date)
        self.add_action(menu, "Undo", self.undo)
        self.add_action(menu, "Redo", self.redo)
        self.add_action(menu, "Refresh", self.refresh)
        self.add_action(menu, "Copy", self.copy_cells)
        self.add_action(menu, "Cut", self.cut_cells)
        self.add_action(menu, "Paste", self.paste_cells)
        self.add_action(menu, "Bold", self.bold)
        self.add_action(menu, "Italic", self.italic)
        self.add_action(menu, "Underline", self.underline)
        self.add_action(menu, "Strikethrough", self.strikethrough)
        self.add_action(menu, "Wrap Text", self.wrap_text)
        self.add_action(menu, "Merge Cells", self.merge_cells)
        self.add_action(menu, "Unmerge Cells", self.unmerge_cells)
        self.add_action(menu, "Font Color", self.font_color)
        self.add_action(menu, "Fill Color", self.fill_color)
        align_menu = menu.addMenu("Horizontal Alignment")
        self.add_action(align_menu, "Left", lambda: self.horizontal_alignment(Qt.AlignLeft))
        self.add_action(align_menu, "Center", lambda: self.horizontal_alignment(Qt.AlignCenter))
        self.add_action(align_menu, "Right", lambda: self.horizontal_alignment(Qt.AlignRight))
        valign_menu = menu.addMenu("Vertical Alignment")
        self.add_action(valign_menu, "Top", lambda: self.vertical_alignment(Qt.AlignTop))
        self.add_action(valign_menu, "Middle", lambda: self.vertical_alignment(Qt.AlignVCenter))
        self.add_action(valign_menu, "Bottom", lambda: self.vertical_alignment(Qt.AlignBottom))
        self.add_action(menu, "Borders", self.borders)
        self.add_action(menu, "Formulas", self.formulas)
        self.add_action(menu, "Export HTML", self.export_html)
        self.add_action(menu, "Export CSV", self.export_csv)
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
        sidebar_content_layout = QVBoxLayout(self.sidebar_content)
        sidebar_content_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_content_layout.setSpacing(2)
        side_layout.addWidget(self.sidebar_content)
        sidebar_content_layout.addWidget(self.side_button("▣ File Operations", self.show_file_menu))
        sidebar_content_layout.addWidget(self.side_button("⊕ Insert Operations", self.show_insert_menu))
        sidebar_content_layout.addWidget(self.side_button("↶ Undo", self.undo))
        sidebar_content_layout.addWidget(self.side_button("↷ Redo", self.redo))
        sidebar_content_layout.addWidget(self.side_button("⤢ Scale Up / Down", self.scale))
        sidebar_content_layout.addWidget(self.side_button("⟳ Refresh", self.refresh))
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        sidebar_content_layout.addWidget(line)
        sidebar_content_layout.addWidget(self.side_button("▣ Copy", self.copy_cells))
        sidebar_content_layout.addWidget(self.side_button("✂ Cut", self.cut_cells))
        sidebar_content_layout.addWidget(self.side_button("▣ Paste", self.paste_cells))
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        sidebar_content_layout.addWidget(line)
        sidebar_content_layout.addWidget(self.side_button("B Bold", self.bold))
        sidebar_content_layout.addWidget(self.side_button("I Italic", self.italic))
        sidebar_content_layout.addWidget(self.side_button("U Underline", self.underline))
        sidebar_content_layout.addWidget(self.side_button("S Strikethrough", self.strikethrough))
        sidebar_content_layout.addWidget(self.side_button("↕ Wrap Text", self.wrap_text))
        sidebar_content_layout.addWidget(self.side_button("⊞ Merge", self.merge_cells))
        sidebar_content_layout.addWidget(self.side_button("⊟ Unmerge", self.unmerge_cells))
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        sidebar_content_layout.addWidget(line)
        sidebar_content_layout.addWidget(self.side_button("A Font Color", self.font_color))
        sidebar_content_layout.addWidget(self.side_button("◆ Fill Color", self.fill_color))
        self.horizontal_combo = QComboBox()
        self.horizontal_combo.addItems(["Left", "Centre", "Right"])
        self.horizontal_combo.currentTextChanged.connect(self.change_horizontal)
        sidebar_content_layout.addWidget(self.horizontal_combo)
        self.vertical_combo = QComboBox()
        self.vertical_combo.addItems(["Top", "Middle", "Bottom"])
        self.vertical_combo.currentTextChanged.connect(self.change_vertical)
        sidebar_content_layout.addWidget(self.vertical_combo)
        sidebar_content_layout.addWidget(self.side_button("▱ Borders", self.borders))
        sidebar_content_layout.addWidget(self.side_button("Σ Formulas", self.formulas))
        sidebar_content_layout.addStretch()
        self.statusBar().addWidget(self.status)
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        self.main_content = QWidget()
        main_layout = QVBoxLayout(self.main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.cell_editor = QTextEdit()
        self.cell_editor.setFixedHeight(128)
        self.cell_editor.setPlaceholderText("Selected cell")
        self.cell_editor.setAcceptRichText(False)
        self.cell_editor.textChanged.connect(self.update_selected_cell)
        main_layout.addWidget(self.cell_editor)
        spreadsheet_view = QHBoxLayout()
        spreadsheet_view.setContentsMargins(0, 0, 0, 0)
        spreadsheet_view.setSpacing(0)        
        spreadsheet_view.addWidget(self.tabs, 1)
        self.viewer_container = QFrame()
        self.viewer_container.setMinimumWidth(300)
        self.viewer_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)        
        viewer_layout = QVBoxLayout(self.viewer_container)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)
        self.viewer = MediaViewer()
        viewer_layout.addWidget(self.viewer)
        spreadsheet_view.addWidget(self.viewer_container, 1)
        self.viewer_strip = QFrame()
        self.viewer_strip.setFixedWidth(38)        
        viewer_strip_layout = QVBoxLayout(self.viewer_strip)
        viewer_strip_layout.setContentsMargins(0, 0, 0, 0)
        viewer_strip_layout.setSpacing(0)
        self.viewer_toggle = QToolButton()
        self.viewer_toggle.setText("☰")
        self.viewer_toggle.setFixedSize(38, 38)
        self.viewer_toggle.setCursor(Qt.PointingHandCursor)
        self.viewer_toggle.setToolTip("Collapse / Expand Viewer")
        self.viewer_toggle.clicked.connect(self.toggle_viewer)
        viewer_strip_layout.addWidget(self.viewer_toggle)
        viewer_strip_layout.addStretch()
        spreadsheet_view.addWidget(self.viewer_strip)
        main_layout.addLayout(spreadsheet_view, 1)
        layout.addWidget(self.main_content, 1)
        self.setCentralWidget(central)
        self.apply_viewer_sizes()
    
    def apply_viewer_sizes(self):
        if self.viewer_visible:
            self.viewer_container.setVisible(True)
            self.viewer_strip.setVisible(True)
            self.viewer_container.setMinimumWidth(300)
            self.viewer_toggle.setToolTip("Collapse Viewer")
        else:
            self.viewer_container.setVisible(False)
            self.viewer_strip.setVisible(True)
            self.viewer_toggle.setToolTip("Expand Viewer")
    
    def toggle_viewer(self):
        self.viewer_visible = not self.viewer_visible
        self.apply_viewer_sizes()
    
    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar_content.setVisible(self.sidebar_visible)
        self.sidebar.setFixedWidth(175 if self.sidebar_visible else 46)
    
    def show_file_menu(self):
        position = self.menu_button.mapToGlobal(QPoint(self.menu_button.width(), 0))
        self.file_menu.exec_(position)
    
    def show_insert_menu(self):
        position = self.menu_button.mapToGlobal(QPoint(self.menu_button.width(), 0))
        self.insert_menu.exec_(position)
    
    def cell_context_menu(self, table, pos):
        index = table.currentIndex()
        menu = QMenu(self)
        menu.addAction("Cut", self.cut_cells)
        menu.addAction("Copy", self.copy_cells)
        menu.addAction("Paste", self.paste_cells)
        menu.addSeparator()
        menu.addAction("Bold", self.bold)
        menu.addAction("Italic", self.italic)
        menu.addAction("Underline", self.underline)
        menu.addAction("Strikethrough", self.strikethrough)
        menu.addAction("Wrap Text", self.wrap_text)
        menu.addSeparator()
        menu.addAction("Insert Date", self.insert_date)
        if index.isValid():
            item = table.item(index.row(), index.column())
            media_path = item.data(Qt.UserRole + 2) if item else None
            if media_path and os.path.exists(str(media_path)):
                menu.addAction("Remove Image / PDF", self.remove_media)
            else:
                menu.addAction("Insert Image / PDF", self.insert_media)
        menu.addAction("Font Color", self.font_color)
        menu.addAction("Fill Color", self.fill_color)
        align_menu = menu.addMenu("Horizontal Alignment")
        align_menu.addAction("Left", lambda: self.horizontal_alignment(Qt.AlignLeft))
        align_menu.addAction("Center", lambda: self.horizontal_alignment(Qt.AlignCenter))
        align_menu.addAction("Right", lambda: self.horizontal_alignment(Qt.AlignRight))
        valign_menu = menu.addMenu("Vertical Alignment")
        valign_menu.addAction("Top", lambda: self.vertical_alignment(Qt.AlignTop))
        valign_menu.addAction("Middle", lambda: self.vertical_alignment(Qt.AlignVCenter))
        valign_menu.addAction("Bottom", lambda: self.vertical_alignment(Qt.AlignBottom))
        border_menu = menu.addMenu("Borders")        
        border_menu.addAction(
            "All Borders",
            lambda: self.apply_border_action("all")
        )        
        border_menu.addAction(
            "Inner Borders",
            lambda: self.apply_border_action("inner")
        )
        border_menu.addAction(
            "Outer Borders",
            lambda: self.apply_border_action("outer")
        )
        border_menu.addSeparator()
        border_menu.addAction(
            "Left Borders",
            lambda: self.apply_border_action("left")
        )
        border_menu.addAction(
            "Right Borders",
            lambda: self.apply_border_action("right")
        )
        border_menu.addAction(
            "Top Borders",
            lambda: self.apply_border_action("top")
        )
        border_menu.addAction(
            "Bottom Borders",
            lambda: self.apply_border_action("bottom")
        )
        border_menu.addSeparator()
        border_menu.addAction(
            "No Borders",
            lambda: self.apply_border_action("none")
        )
        border_menu.addAction(
            "Border Color",
            self.border_color
        )
        menu.addAction("Formulas", self.formulas)
        has_multiple_selection = len(table.selectedIndexes()) > 1
        has_merged_selection = False
        for row in range(table.rowCount()):
            for column in range(table.columnCount()):
                rowspan = table.rowSpan(row, column)
                colspan = table.columnSpan(row, column)
                if rowspan <= 1 and colspan <= 1:
                    continue
                span_bottom = row + rowspan - 1
                span_right = column + colspan - 1
                for selection in table.selectedRanges():
                    if not (span_bottom < selection.topRow() or row > selection.bottomRow() or span_right < selection.leftColumn() or column > selection.rightColumn()):
                        has_merged_selection = True
                        break
                if has_merged_selection:
                    break
            if has_merged_selection:
                break
        if has_multiple_selection or has_merged_selection:
            menu.addSeparator()
            menu.addAction("Merge Cells", self.merge_cells)
            menu.addAction("Unmerge Cells", self.unmerge_cells)
        menu.exec_(pos)
    
    def add_action(self, menu, text, slot):
        action = menu.addAction(text)
        action.triggered.connect(slot)
    
    def side_button(self, text, slot):
        button = QPushButton(text)
        button.setFlat(True)
        button.setStyleSheet("QPushButton{text-align:left;padding:7px 8px;font-size:14px;}QPushButton:hover{background:#e8e8e8;}")
        button.clicked.connect(slot)
        return button
    
    def create_sheet(self, name="Sheet1"):
        table = SpreadsheetTable(50, 26)
        table.setItemDelegate(SpreadsheetDelegate(table))
        table.setObjectName("sheet")
        table.setHorizontalHeaderLabels([self.column_name(i) for i in range(table.columnCount())])
        table.setVerticalHeaderLabels([str(i + 1) for i in range(table.rowCount())])
        table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed)
        table.setWordWrap(True)
        vertical_header = SpreadsheetHeader(Qt.Vertical, table)
        horizontal_header = SpreadsheetHeader(Qt.Horizontal, table)
        table.setVerticalHeader(vertical_header)
        table.setHorizontalHeader(horizontal_header)
        table.horizontalHeader().setDefaultSectionSize(100)
        table.verticalHeader().setDefaultSectionSize(32)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.setAlternatingRowColors(False)
        table.setStyleSheet("QTableWidget{gridline-color:#d5d5d5;font-size:14px;}QHeaderView::section{background:#eef0f2;border:1px solid #d5d5d5;padding:4px;}")
        table.itemSelectionChanged.connect(self.update_status)
        table.itemSelectionChanged.connect(self.update_cell_editor)
        table.itemSelectionChanged.connect(self.update_viewer_from_selection)
        table.currentCellChanged.connect(lambda row, column, previous_row, previous_column: self.update_cell_editor())
        table.currentCellChanged.connect(lambda row, column, previous_row, previous_column: self.update_viewer_from_selection())
        vertical_header.rightClicked.connect(lambda index, pos: self.row_header_menu(table, index, pos))
        horizontal_header.rightClicked.connect(lambda index, pos: self.column_header_menu(table, index, pos))
        self.tabs.addTab(table, name)
        self.sheet_histories[id(table)] = {"undo": [], "redo": []}
        self.tabs.setCurrentWidget(table)
        self.update_session_state()
    
    def serialize_color(self, color):
        return {
            "name": color.name(),
            "alpha": color.alpha()
        }
    
    def deserialize_color(self, data):
        color = QColor(data.get("name", "#000000"))
        color.setAlpha(data.get("alpha", 255))
        return color
    
    def serialize_font(self, font):
        return {
            "family": font.family(),
            "pointSize": font.pointSizeF(),
            "bold": font.bold(),
            "italic": font.italic(),
            "underline": font.underline(),
            "strikeOut": font.strikeOut(),
            "weight": font.weight()
        }
    
    def deserialize_font(self, data):
        from PyQt5.QtGui import QFont
        font = QFont(data.get("family", "Arial"))
        font.setPointSizeF(float(data.get("pointSize", 14)))
        font.setBold(bool(data.get("bold", False)))
        font.setItalic(bool(data.get("italic", False)))
        font.setUnderline(bool(data.get("underline", False)))
        font.setStrikeOut(bool(data.get("strikeOut", False)))    
        if "weight" in data:
            font.setWeight(int(data["weight"]))
        return font
    
    def serialize_session_cell(self, item):
        if item is None:
            return None
        foreground = item.foreground().color()
        background = item.background().color()    
        return {
            "text": item.text(),
            "font": self.serialize_font(item.font()),
            "foreground": self.serialize_color(foreground),
            "background": self.serialize_color(background),
            "alignment": int(item.textAlignment()),
            "data1": item.data(Qt.UserRole + 1),
            "data2": item.data(Qt.UserRole + 2),
            "data3": item.data(Qt.UserRole + 3),
            "data4": item.data(Qt.UserRole + 4),
            "tooltip": item.toolTip()
        }
    
    def serialize_session_table(self, table):
        state = {
            "rows": table.rowCount(),
            "columns": table.columnCount(),
            "cells": [],
            "spans": [],
            "row_heights": [table.rowHeight(r) for r in range(table.rowCount())],
            "column_widths": [table.columnWidth(c) for c in range(table.columnCount())],
            "border_color": getattr(table, "_border_color", "#000000"),
            "cell_borders": {}
        }
        for r in range(table.rowCount()):
            row = []
            for c in range(table.columnCount()):
                row.append(self.serialize_session_cell(table.item(r, c)))
            state["cells"].append(row)    
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                rowspan = table.rowSpan(r, c)
                colspan = table.columnSpan(r, c)
                if rowspan > 1 or colspan > 1:
                    state["spans"].append([r, c, rowspan, colspan])
        for key, borders in getattr(table, "_cell_borders", {}).items():
            state["cell_borders"][f"{key[0]},{key[1]}"] = list(borders)
        current = table.currentIndex()
        state["current_cell"] = [
            current.row(),
            current.column()
        ] if current.isValid() else None
        state["selection_ranges"] = []
        for selection in table.selectedRanges():
            state["selection_ranges"].append([
                selection.topRow(),
                selection.leftColumn(),
                selection.bottomRow(),
                selection.rightColumn()
            ])
        return state
        
    def save_session_json(self):
        path = self.session_json_path()
        if not path:
            return    
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(
                    self.session_data,
                    file,
                    ensure_ascii=False,
                    indent=2
                )
        except (OSError, TypeError):
            pass
    
    def save_session(self):
        self.update_session_state()
    
    def load_session(self):
        path = self.session_json_path()
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as file:
                session = json.load(file)
            sheets = session.get("sheets", [])
            if not sheets:
                return
            self.history_replaying = True
            self.tabs.clear()
            self.sheet_histories.clear()
            for sheet_data in sheets:
                table = SpreadsheetTable(50, 26)
                table.setItemDelegate(SpreadsheetDelegate(table))
                table.setObjectName("sheet")
                table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed)
                table.setWordWrap(True)
                vertical_header = SpreadsheetHeader(Qt.Vertical, table)
                horizontal_header = SpreadsheetHeader(Qt.Horizontal, table)
                table.setVerticalHeader(vertical_header)
                table.setHorizontalHeader(horizontal_header)
                table.horizontalHeader().setDefaultSectionSize(100)
                table.verticalHeader().setDefaultSectionSize(32)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
                table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
                table.setAlternatingRowColors(False)
                table.setStyleSheet("QTableWidget{gridline-color:#d5d5d5;font-size:14px;}QHeaderView::section{background:#eef0f2;border:1px solid #d5d5d5;padding:4px;}")
                table.itemSelectionChanged.connect(self.update_status)
                table.itemSelectionChanged.connect(self.update_cell_editor)
                table.itemSelectionChanged.connect(self.update_viewer_from_selection)
                table.currentCellChanged.connect(lambda row, column, previous_row, previous_column: self.update_cell_editor())
                table.currentCellChanged.connect(lambda row, column, previous_row, previous_column: self.update_viewer_from_selection())
                vertical_header.rightClicked.connect(lambda index, pos, t=table: self.row_header_menu(t, index, pos))
                horizontal_header.rightClicked.connect(lambda index, pos, t=table: self.column_header_menu(t, index, pos))
                self.tabs.addTab(table, sheet_data.get("name", f"Sheet{self.tabs.count() + 1}"))
                self.sheet_histories[id(table)] = {"undo": [], "redo": []}
                self.restore_session_table(table, sheet_data.get("state", {}))
            current_tab = int(session.get("current_tab", 0))
            if 0 <= current_tab < self.tabs.count():
                self.tabs.setCurrentIndex(current_tab)
            self.session_data = session
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return
        finally:
            self.history_replaying = False
            self.update_cell_editor()
            self.update_viewer_from_selection()
    
    def restore_session_cell(self, table, row, column, data):
        if data is None:
            table.setItem(row, column, None)
            return
        item = QTableWidgetItem(data.get("text", ""))
        if data.get("font"):
            item.setFont(self.deserialize_font(data["font"]))
        if data.get("foreground"):
            item.setForeground(self.deserialize_color(data["foreground"]))
        if data.get("background"):
            item.setBackground(self.deserialize_color(data["background"]))
        item.setTextAlignment(int(data.get("alignment", Qt.AlignLeft | Qt.AlignVCenter)))
        item.setData(Qt.UserRole + 1, data.get("data1"))
        media_path = data.get("data2")
        if media_path and self.current_file:
            media_path = str(media_path)
            if not os.path.isabs(media_path):
                media_path = os.path.normpath(os.path.join(os.path.dirname(self.current_file), media_path))
            elif not os.path.exists(media_path):
                cache_dir = os.path.splitext(self.current_file)[0] + "_cache"
                cache_path = os.path.join(cache_dir, os.path.basename(media_path))
                if os.path.exists(cache_path):
                    media_path = cache_path
        item.setData(Qt.UserRole + 2, media_path)
        item.setData(Qt.UserRole + 3, data.get("data3"))
        item.setData(Qt.UserRole + 4, data.get("data4"))
        item.setToolTip(data.get("tooltip", ""))
        table.setItem(row, column, item)
        
    def restore_session_table(self, table, state):
        if not isinstance(state, dict):
            return
        self.history_replaying = True
        table.setUpdatesEnabled(False)    
        try:
            table.clearSpans()
            rows = int(state.get("rows", table.rowCount()))
            columns = int(state.get("columns", table.columnCount()))
            table.setRowCount(rows)
            table.setColumnCount(columns)
            table._border_color = state.get(
                "border_color",
                "#000000"
            )
            table._cell_borders = {}
            cells = state.get("cells", [])
            for r in range(min(rows, len(cells))):
                row_data = cells[r]
                for c in range(min(columns, len(row_data))):
                    self.restore_session_cell(
                        table,
                        r,
                        c,
                        row_data[c]
                    )
            for span in state.get("spans", []):
                if len(span) != 4:
                    continue
                r, c, rowspan, colspan = span
                if (
                    r >= 0 and
                    c >= 0 and
                    r + rowspan <= table.rowCount() and
                    c + colspan <= table.columnCount()
                ):
                    table.setSpan(
                        r,
                        c,
                        rowspan,
                        colspan
                    )
            for key, borders in state.get(
                "cell_borders",
                {}
            ).items():
                try:
                    row, column = [
                        int(value)
                        for value in key.split(",", 1)
                    ]
                except (ValueError, AttributeError):
                    continue
                table._cell_borders[
                    (row, column)
                ] = set(borders)
            for r, height in enumerate(
                state.get("row_heights", [])
            ):
                if r < table.rowCount():
                    table.setRowHeight(
                        r,
                        int(height)
                    )
            for c, width in enumerate(
                state.get("column_widths", [])
            ):
                if c < table.columnCount():
                    table.setColumnWidth(
                        c,
                        int(width)
                    )
            self.refresh_headers(table)
            table.clearSelection()
            selection_ranges = state.get(
                "selection_ranges",
                []
            )
            for selection in selection_ranges:
                if len(selection) != 4:
                    continue
                top, left, bottom, right = selection
                if (
                    top < 0 or
                    left < 0 or
                    bottom >= table.rowCount() or
                    right >= table.columnCount()
                ):
                    continue
                table.setRangeSelected(
                    QTableWidgetSelectionRange(
                        top,
                        left,
                        bottom,
                        right
                    ),
                    True
                )
            current_cell = state.get("current_cell")
            if (
                isinstance(current_cell, list) and
                len(current_cell) == 2
            ):
                row, column = current_cell
                if (
                    0 <= row < table.rowCount() and
                    0 <= column < table.columnCount()
                ):
                    table.setCurrentCell(
                        row,
                        column
                    )
        finally:
            table.setUpdatesEnabled(True)
            table.viewport().update()
            self.history_replaying = False
    
    def current_table(self):
        return self.tabs.currentWidget()
    
    def selected_items(self):
        table = self.current_table()
        return table.selectedItems() if table else []
    
    def selected_ranges(self):
        table = self.current_table()
        return table.selectedRanges() if table else []
    
    def update_viewer_from_selection(self):
        table = self.current_table()
        if not table:
            return
        index = table.currentIndex()
        if not index.isValid():
            self.viewer.clear_viewer()
            return
        item = table.item(index.row(), index.column())
        path = item.data(Qt.UserRole + 2) if item else None
        if path:
            path = str(path)
            if not os.path.isabs(path):
                base = os.path.dirname(self.current_file) if self.current_file else os.getcwd()
                path = os.path.join(base, path)
            if os.path.exists(path):
                self.viewer.show_media(path)
                return
        self.viewer.clear_viewer()
    
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
        if item.data(Qt.UserRole + 2):
            return
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
                self.status.setText(f"Row: {r.topRow() + 1} | Column: {self.column_name(r.leftColumn())}")
            else:
                self.status.setText("Ready")
    
    def rename_tab(self, index):
        if index < 0:
            return
        current_name = self.tabs.tabText(index)
        name, ok = QInputDialog.getText(self, "Rename Tab", "Tab name:", text=current_name)
        if ok and name.strip():
            self.tabs.setTabText(index, name.strip())
    
    def row_header_menu(self, table, row, pos):
        if row < 0:
            return
        selected_rows = table.selectionModel().selectedRows()
        selected_indexes = [index.row() for index in selected_rows]
        if row not in selected_indexes:
            table.clearSelection()
            table.selectionModel().select(table.model().index(row, 0), table.selectionModel().Select | table.selectionModel().Rows)
        menu = QMenu(self)
        add_menu = menu.addMenu("Add Rows")
        above_action = add_menu.addAction("Add Rows Above")
        below_action = add_menu.addAction("Add Rows Below")
        menu.addSeparator()
        delete_action = menu.addAction("Delete Selected Rows")
        action = menu.exec_(table.verticalHeader().mapToGlobal(pos))
        if action == above_action:
            self.add_rows(table, "above")
        elif action == below_action:
            self.add_rows(table, "below")
        elif action == delete_action:
            self.delete_selected_rows(table)
    
    def column_header_menu(self, table, column, pos):
        if column < 0:
            return
        selected_columns = table.selectionModel().selectedColumns()
        selected_indexes = [index.column() for index in selected_columns]
        if column not in selected_indexes:
            table.clearSelection()
            table.selectionModel().select(table.model().index(0, column), table.selectionModel().Select | table.selectionModel().Columns)
        menu = QMenu(self)
        add_menu = menu.addMenu("Add Columns")
        left_action = add_menu.addAction("Add Columns Left")
        right_action = add_menu.addAction("Add Columns Right")
        menu.addSeparator()
        delete_action = menu.addAction("Delete Selected Columns")
        action = menu.exec_(table.horizontalHeader().mapToGlobal(pos))
        if action == left_action:
            self.add_columns(table, "left")
        elif action == right_action:
            self.add_columns(table, "right")
        elif action == delete_action:
            self.delete_selected_columns(table)
    
    def add_rows(self, table, direction):
        rows = table.selectionModel().selectedRows()
        if not rows:
            return
        selected = sorted(index.row() for index in rows)
        dialog = AddRowsDialog(self)
        dialog.above_button.setChecked(direction == "above")
        dialog.below_button.setChecked(direction == "below")
        if dialog.exec_() != QDialog.Accepted:
            return
        number, direction = dialog.values()
        position = selected[0] if direction == "above" else selected[-1] + 1
        for _ in range(number):
            table.insertRow(position)
        self.refresh_headers(table)
    
    def add_columns(self, table, direction):
        columns = table.selectionModel().selectedColumns()
        if not columns:
            return
        selected = sorted(index.column() for index in columns)
        dialog = AddColumnsDialog(self)
        dialog.left_button.setChecked(direction == "left")
        dialog.right_button.setChecked(direction == "right")
        if dialog.exec_() != QDialog.Accepted:
            return
        number, direction = dialog.values()
        position = selected[0] if direction == "left" else selected[-1] + 1
        for _ in range(number):
            table.insertColumn(position)
        self.refresh_headers(table)
    
    def delete_selected_rows(self, table):
        selected_rows = table.selectionModel().selectedRows()
        if not selected_rows:
            return
        rows = sorted([index.row() for index in selected_rows], reverse=True)
        self.save_history_state()
        for row in rows:
            table.removeRow(row)
        self.refresh_headers(table)
        table.clearSelection()
        if table.rowCount() > 0:
            table.setCurrentCell(min(rows[-1], table.rowCount() - 1), 0)
    
    def delete_selected_columns(self, table):
        selected_columns = table.selectionModel().selectedColumns()
        if not selected_columns:
            return
        columns = sorted([index.column() for index in selected_columns], reverse=True)
        self.save_history_state()
        for column in columns:
            table.removeColumn(column)
        self.refresh_headers(table)
        table.clearSelection()
        if table.columnCount() > 0:
            table.setCurrentCell(0, min(columns[-1], table.columnCount() - 1))
    
    def refresh_headers(self, table=None):
        if table is None:
            table = self.current_table()
        if not table:
            return
        table.setHorizontalHeaderLabels([self.column_name(i) for i in range(table.columnCount())])
        table.setVerticalHeaderLabels([str(i + 1) for i in range(table.rowCount())])
    
    def new_file(self):
        self.tabs.clear()
        self.current_file = None
        self.session_data = {
            "version": 2,
            "current_file": None,
            "current_tab": 0,
            "sheets": []
        }
    
    def new_tab(self):
        number = self.tabs.count() + 1
        self.create_sheet(f"Sheet{number}")
    
    def close_tab(self, index):
        if self.tabs.count() == 1:
            return
        table = self.tabs.widget(index)
        if table:
            self.sheet_histories.pop(id(table), None)
        self.tabs.removeTab(index)
        self.viewer.clear_viewer()
    
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Spreadsheet Files (*.csv *.html);;CSV Files (*.csv);;HTML Files (*.html)")
        if not path:
            return
        if path.lower().endswith(".csv"):
            self.load_csv(path)
        elif path.lower().endswith(".html"):
            QMessageBox.information(self, "Open HTML", "HTML files are currently export-only. CSV files can be reopened.")
    
    def load_csv(self, path):
        import csv
        try:
            with open(path, "r", newline="", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))
            table = self.current_table()
            if table is None:
                self.create_sheet()
                table = self.current_table()
            table.setRowCount(max(50, len(rows)))
            table.setColumnCount(max(20, max((len(row) for row in rows), default=0)))
            table.clearContents()
            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    table.setItem(r, c, QTableWidgetItem(value))
            self.current_file = path
            self.load_session()
            self.refresh_headers(table)
            self.update_viewer_from_selection()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        
    def closeEvent(self, event):
        self.save_session()
        event.accept()
    
    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;HTML Files (*.html)")
        if not path:
            return
        if not path.lower().endswith((".csv", ".html")):
            path += ".csv"
        if path.lower().endswith(".html"):
            self.export_html_to(path)
        else:
            self.export_csv_to(path)
    
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
        QApplication.clipboard().setText("\n".join("\t".join(row) for row in data))
    
    def cut_cells(self):
        table = self.current_table()
        if not table:
            return
        self.copy_cells()
        if self.clipboard_data is None:
            return
        self.save_history_state()
        for item in table.selectedItems():
            item.setText("")
            item.setData(Qt.UserRole + 2, None)
            item.setData(Qt.UserRole + 3, None)
        self.viewer.clear_viewer()
    
    def paste_cells(self):
        table = self.current_table()
        if not table or not self.clipboard_data:
            return
        selected_indexes = table.selectedIndexes()
        if selected_indexes:
            selected_indexes = sorted(
                {(index.row(), index.column()) for index in selected_indexes}
            )
            start_row = min(row for row, column in selected_indexes)
            start_column = min(column for row, column in selected_indexes)
        else:
            current = table.currentIndex()
            if not current.isValid():
                return
            selected_indexes = [(current.row(), current.column())]
            start_row = current.row()
            start_column = current.column()    
        source = self.clipboard_data
        source_rows = len(source)
        source_columns = max((len(row) for row in source), default=0)
        if source_rows == 0 or source_columns == 0:
            return
        self.save_history_state()
        if source_rows == 1 and source_columns == 1:
            value = source[0][0]
            for row, column in selected_indexes:
                while row >= table.rowCount():
                    table.insertRow(table.rowCount())
                while column >= table.columnCount():
                    table.insertColumn(table.columnCount())
                item = table.item(row, column)
                if not item:
                    item = QTableWidgetItem()
                    table.setItem(row, column, item)
                item.setText(value)
                item.setData(Qt.UserRole + 2, None)
                item.setData(Qt.UserRole + 3, None)
        else:
            ranges = table.selectedRanges()
            if ranges:
                selection = ranges[0]
                start_row = selection.topRow()
                start_column = selection.leftColumn()
                destination_rows = selection.rowCount()
                destination_columns = selection.columnCount()
            else:
                destination_rows = 1
                destination_columns = 1
            if destination_rows == 1 and destination_columns == 1:
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
                    item.setData(Qt.UserRole + 2, None)
                    item.setData(Qt.UserRole + 3, None)
        self.refresh_headers(table)
        table.viewport().update()
    
    def insert_media(self):
        table = self.current_table()
        if not table:
            return
        index = table.currentIndex()
        if not index.isValid():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Insert Image / PDF",
            "",
            "Media Files (*.png *.jpg *.jpeg *.jpe *.jfif *.bmp *.gif *.tif *.tiff *.webp *.heic *.heif *.ico *.svg *.avif *.pdf);;All Files (*)"
        )
        if not path:
            return
        extension = os.path.splitext(path)[1].lower()
        if extension != ".pdf":
            reader = QImageReader(path)
            if not reader.canRead():
                QMessageBox.warning(self, "Insert Image / PDF", "The selected file could not be read as an image.")
                return
        if extension == ".pdf" and not PDF_SUPPORT:
            QMessageBox.warning(self, "Insert Image / PDF", "PDF support is unavailable in this PyQt5 installation.")
            return
        self.save_history_state()
        item = table.item(index.row(), index.column())
        if not item:
            item = QTableWidgetItem()
            table.setItem(index.row(), index.column(), item)
        stored_path = path
        if self.current_file and self.current_file.lower().endswith(".csv"):
            cache_dir = os.path.splitext(self.current_file)[0] + "_cache"
            os.makedirs(cache_dir, exist_ok=True)
            cache_name = os.path.basename(path)
            cache_path = os.path.join(cache_dir, cache_name)
            if os.path.abspath(path) != os.path.abspath(cache_path):
                import shutil
                shutil.copy2(path, cache_path)
            stored_path = os.path.relpath(cache_path, os.path.dirname(self.current_file))
        item.setText(os.path.basename(path))
        item.setData(Qt.UserRole + 2, stored_path)
        item.setData(Qt.UserRole + 3, "pdf" if extension == ".pdf" else "image")
        item.setToolTip(stored_path)
        table.resizeColumnToContents(index.column())
        table.resizeRowToContents(index.row())
        self.viewer.show_media(path)
        self.update_session_state()
        self.update_session_state()
        self.update_session_state()
    
    def remove_media(self):
        table = self.current_table()
        if not table:
            return
        index = table.currentIndex()
        if not index.isValid():
            return
        item = table.item(index.row(), index.column())
        if not item:
            return
        path = item.data(Qt.UserRole + 2)
        if not path:
            return
        self.save_history_state()
        item.setText("")
        item.setData(Qt.UserRole + 2, None)
        item.setData(Qt.UserRole + 3, None)
        item.setToolTip("")
        self.viewer.clear_viewer()
        self.update_session_state()
    
    def save_history_state(self):
        table = self.current_table()
        if not table or self.history_replaying:
            return
        history = self.sheet_histories.setdefault(id(table), {"undo": [], "redo": []})
        state = self.capture_table_state(table)
        if history["undo"] and self.states_equal(history["undo"][-1], state):
            return
        history["undo"].append(state)
        if len(history["undo"]) > 100:
            history["undo"].pop(0)
        history["redo"].clear()
        table._edit_history_saved = False
        self.update_session_state()
    
    def states_equal(self, first, second):
        if first["rows"] != second["rows"] or first["columns"] != second["columns"]:
            return False
        if first["spans"] != second["spans"] or first["row_heights"] != second["row_heights"] or first["column_widths"] != second["column_widths"]:
            return False
        if first["border_color"] != second["border_color"] or first["cell_borders"] != second["cell_borders"]:
            return False
        for r in range(first["rows"]):
            for c in range(first["columns"]):
                a = first["cells"][r][c]
                b = second["cells"][r][c]
                if a is None and b is None:
                    continue
                if a is None or b is None:
                    return False
                for key in ("text", "font", "foreground", "background", "alignment", "flags", "data1", "data2", "data3", "tooltip"):
                    if a[key] != b[key]:
                        return False
        return True
    
    def restore_table_state(self, table, state):
        self.history_replaying = True
        table.setUpdatesEnabled(False)
        table.clearSpans()
        table.setRowCount(state["rows"])
        table.setColumnCount(state["columns"])
        table._border_color = state.get("border_color", "#000000")
        table._cell_borders = {key: set(value) for key, value in state.get("cell_borders", {}).items()}
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
                item.setData(Qt.UserRole + 3, data["data3"])
                item.setToolTip(data.get("tooltip", ""))
                table.setItem(r, c, item)
        for r, height in enumerate(state["row_heights"]):
            if r < table.rowCount():
                table.setRowHeight(r, height)
        for c, width in enumerate(state["column_widths"]):
            if c < table.columnCount():
                table.setColumnWidth(c, width)
        for r, c, rowspan, colspan in state["spans"]:
            if r < table.rowCount() and c < table.columnCount():
                table.setSpan(r, c, rowspan, colspan)
        self.refresh_headers(table)
        table.setUpdatesEnabled(True)
        table.viewport().update()
        self.history_replaying = False
        table._edit_history_saved = False
        self.update_viewer_from_selection()
        
    def session_json_path(self, csv_path=None):
        csv_path = csv_path or self.current_file
        if not csv_path:
            return None
        return os.path.splitext(csv_path)[0] + ".json"
    
    def update_session_state(self):
        if not self.current_file or not self.current_file.lower().endswith(".csv"):
            return
        sheets = []
        for index in range(self.tabs.count()):
            table = self.tabs.widget(index)
            sheets.append({
                "name": self.tabs.tabText(index),
                "state": self.capture_table_state(table)
            })
        self.session_data = {
            "version": 2,
            "current_file": self.current_file,
            "current_tab": self.tabs.currentIndex(),
            "sheets": sheets
        }
        json_path = self.session_json_path(self.current_file)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.session_data, f, ensure_ascii=False, indent=2)
    
    def undo(self):
        table = self.current_table()
        if not table:
            return
        history = self.sheet_histories.setdefault(id(table), {"undo": [], "redo": []})
        if not history["undo"]:
            return
        current_state = self.capture_table_state(table)
        previous_state = history["undo"].pop()
        history["redo"].append(current_state)
        self.restore_table_state(table, previous_state)
        self.status.setText("Undo")
    
    def redo(self):
        table = self.current_table()
        if not table:
            return
        history = self.sheet_histories.setdefault(id(table), {"undo": [], "redo": []})
        if not history["redo"]:
            return
        current_state = self.capture_table_state(table)
        next_state = history["redo"].pop()
        history["undo"].append(current_state)
        self.restore_table_state(table, next_state)
        self.status.setText("Redo")
    
    def refresh(self):
        table = self.current_table()
        if not table:
            return
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        for column in range(table.columnCount()):
            table.setColumnWidth(column, max(100, table.columnWidth(column)))
        for row in range(table.rowCount()):
            table.setRowHeight(row, max(32, table.rowHeight(row)))
        table.viewport().update()
    
    def scale(self):
        table = self.current_table()
        if not table:
            return
        value, ok = QInputDialog.getInt(self, "Scale", "Spreadsheet scale (%):", 100, 50, 200)
        if not ok:
            return
        factor = value / 100
        table.setStyleSheet(
            "QTableWidget{"
            "gridline-color:#d5d5d5;"
            f"font-size:{14 * factor}px;"
            "}"
            "QHeaderView::section{"
            "background:#eef0f2;"
            "border:1px solid #d5d5d5;"
            f"padding:{4 * factor}px;"
            "}"
        )
        table.horizontalHeader().setDefaultSectionSize(int(100 * factor))
        table.verticalHeader().setDefaultSectionSize(int(32 * factor))
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
            item.setData(Qt.UserRole + 1, True)
            item.setTextAlignment(item.textAlignment())
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
                QMessageBox.information(self, "Merge Cells", "Select multiple cells first.")
                return
        texts = []
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                item = table.item(row, column)
                if item and item.text():
                    texts.append(item.text())
        self.save_history_state()
        table.setSpan(top, left, bottom - top + 1, right - left + 1)
        item = table.item(top, left)
        if not item:
            item = QTableWidgetItem()
            table.setItem(top, left, item)
        item.setText(" ".join(texts))
        table.setCurrentCell(top, left)
        table.viewport().update()
    
    def unmerge_cells(self):
        table = self.current_table()
        ranges = self.selected_ranges()
        if not table or not ranges:
            return
        spans = []
        for row in range(table.rowCount()):
            for column in range(table.columnCount()):
                rowspan = table.rowSpan(row, column)
                colspan = table.columnSpan(row, column)
                if rowspan <= 1 and colspan <= 1:
                    continue
                span_bottom = row + rowspan - 1
                span_right = column + colspan - 1
                for selection in ranges:
                    if not (span_bottom < selection.topRow() or row > selection.bottomRow() or span_right < selection.leftColumn() or column > selection.rightColumn()):
                        spans.append((row, column))
                        break
        if not spans:
            return
        self.save_history_state()
        for row, column in spans:
            table.setSpan(row, column, 1, 1)
        table.viewport().update()
    
    def font_color(self):
        color = QColorDialog.getColor(Qt.black, self, "Font Color")
        if not color.isValid():
            return
        items = self.selected_items()
        if not items:
            return
        self.save_history_state()
        for item in items:
            item.setForeground(color)
    
    def fill_color(self):
        color = QColorDialog.getColor(Qt.white, self, "Fill Color")
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
            item.setTextAlignment(alignment | Qt.AlignVCenter)
    
    def vertical_alignment(self, alignment):
        items = self.selected_items()
        if not items:
            return
        self.save_history_state()
        for item in items:
            current = item.textAlignment()
            horizontal = current & Qt.AlignHorizontal_Mask
            item.setTextAlignment(horizontal | alignment)
    
    def change_horizontal(self, value):
        if value == "Left":
            self.horizontal_alignment(Qt.AlignLeft)
        elif value == "Centre":
            self.horizontal_alignment(Qt.AlignCenter)
        else:
            self.horizontal_alignment(Qt.AlignRight)
    
    def change_vertical(self, value):
        if value == "Top":
            self.vertical_alignment(Qt.AlignTop)
        elif value == "Middle":
            self.vertical_alignment(Qt.AlignVCenter)
        else:
            self.vertical_alignment(Qt.AlignBottom)
            
    def apply_border_action(self, border_type):
        table = self.current_table()
        if not table:
            return    
        selected = table.selectedRanges()
        if not selected:
            current = table.currentIndex()
            if not current.isValid():
                return    
            selected = [
                QTableWidgetSelectionRange(
                    current.row(),
                    current.column(),
                    current.row(),
                    current.column()
                )
            ]
        self.save_history_state()
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
                    if border_type == "none":
                        borders.clear()
                    elif border_type == "all":
                        borders.update([
                            "top",
                            "bottom",
                            "left",
                            "right"
                        ])
                    elif border_type == "inner":
                        if row > top:
                            borders.add("top")
                        if row < bottom:
                            borders.add("bottom")
                        if column > left:
                            borders.add("left")
                        if column < right:
                            borders.add("right")
                    elif border_type == "outer":
                        if row == top:
                            borders.add("top")
                        if row == bottom:
                            borders.add("bottom")
                        if column == left:
                            borders.add("left")
                        if column == right:
                            borders.add("right")
                    elif border_type == "left":
                        borders.add("left")    
                    elif border_type == "right":
                        borders.add("right")
                    elif border_type == "top":
                        borders.add("top")
                    elif border_type == "bottom":
                        borders.add("bottom")
                    border_map[key] = borders
        table._cell_borders = border_map
        table.viewport().update()
    
    def borders(self):
        table = self.current_table()
        if not table:
            return
        menu = QMenu(self)    
        all_action = menu.addAction("All Borders")
        inner_action = menu.addAction("Inner Borders")
        outer_action = menu.addAction("Outer Borders")
        menu.addSeparator()
        left_action = menu.addAction("Left Borders")
        right_action = menu.addAction("Right Borders")
        top_action = menu.addAction("Top Borders")
        bottom_action = menu.addAction("Bottom Borders")    
        menu.addSeparator()
        no_action = menu.addAction("No Borders")
        color_action = menu.addAction("Border Color")    
        action = menu.exec_(QCursor.pos())
        actions = {
            all_action: "all",
            inner_action: "inner",
            outer_action: "outer",
            left_action: "left",
            right_action: "right",
            top_action: "top",
            bottom_action: "bottom",
            no_action: "none",
        }
        if action in actions:
            self.apply_border_action(actions[action])
        elif action == color_action:
            self.border_color()
                
    def border_color(self):
        table = self.current_table()
        if not table:
            return    
        color = QColorDialog.getColor(
            QColor(getattr(table, "_border_color", "#000000")),
            self,
            "Border Color"
        )
        if not color.isValid():
            return
        self.save_history_state()
        table._border_color = color.name()
        table.viewport().update()
    
    def insert_date(self):
        table = self.current_table()
        if not table:
            return
        indexes = table.selectedIndexes()
        if not indexes:
            current = table.currentIndex()
            if not current.isValid():
                return
            indexes = [current]
        current_date = QDate.currentDate()
        dialog = QDialog(self)
        dialog.setWindowTitle("Insert Date")
        dialog.setFixedSize(460, 150)
        layout = QVBoxLayout(dialog)
        date_layout = QHBoxLayout()
        month_combo = QComboBox()
        months = ["01 - Jan", "02 - Feb", "03 - Mar", "04 - Apr", "05 - May", "06 - Jun", "07 - Jul", "08 - Aug", "09 - Sep", "10 - Oct", "11 - Nov", "12 - Dec"]
        for month_number, month_name in enumerate(months, 1):
            month_combo.addItem(month_name, month_number)
        day_combo = QComboBox()
        year_combo = QComboBox()
        month_combo.setCurrentIndex(current_date.month() - 1)
        for year in range(1901, current_date.year() + 1):
            year_combo.addItem(str(year), year)
        year_combo.setCurrentIndex(current_date.year() - 1901)
        day_combo.setMinimumWidth(80)
        month_combo.setMinimumWidth(120)
        year_combo.setMinimumWidth(100)
        day_combo.setMinimumHeight(36)
        month_combo.setMinimumHeight(36)
        year_combo.setMinimumHeight(36)
        day_combo.setStyleSheet("QComboBox{font-size:16px;padding:4px;}")
        month_combo.setStyleSheet("QComboBox{font-size:16px;padding:4px;}")
        year_combo.setStyleSheet("QComboBox{font-size:16px;padding:4px;}")
        date_layout.addWidget(QLabel("Month"))
        date_layout.addWidget(month_combo)
        date_layout.addWidget(QLabel("Day"))
        date_layout.addWidget(day_combo)
        date_layout.addWidget(QLabel("Year"))
        date_layout.addWidget(year_combo)
        layout.addLayout(date_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        def update_days():
            year = year_combo.currentData()
            month = month_combo.currentData()
            days_in_month = QDate(year, month, 1).daysInMonth()
            max_day = days_in_month
            if year == current_date.year() and month == current_date.month():
                max_day = current_date.day()
            current_day = day_combo.currentData() or min(current_date.day(), max_day)
            day_combo.blockSignals(True)
            day_combo.clear()
            for day in range(1, max_day + 1):
                day_combo.addItem(str(day), day)
            day_combo.setCurrentIndex(min(current_day, max_day) - 1)
            day_combo.blockSignals(False)
        month_combo.currentIndexChanged.connect(update_days)
        year_combo.currentIndexChanged.connect(update_days)
        update_days()
        if dialog.exec_() != QDialog.Accepted:
            return
        year = year_combo.currentData()
        month = month_combo.currentData()
        day = day_combo.currentData()
        selected_date = QDate(year, month, day)
        if selected_date > current_date:
            QMessageBox.warning(self, "Invalid Date", "The selected date cannot be later than today.")
            return
        date = selected_date.toString("MM-dd-yyyy")
        self.save_history_state()
        for index in indexes:
            item = table.item(index.row(), index.column())
            if not item:
                item = QTableWidgetItem()
                table.setItem(index.row(), index.column(), item)
            item.setText(date)
    
    def formulas(self):
        table = self.current_table()
        if not table:
            return
        formula, ok = QInputDialog.getText(self, "Formula", "Enter formula, e.g. =SUM(A1:A5):")
        if not ok or not formula:
            return
        self.save_history_state()
        item = table.currentItem()
        if not item:
            item = QTableWidgetItem()
            table.setItem(table.currentRow(), table.currentColumn(), item)
        if formula.startswith("="):
            result = self.calculate_formula(formula)
            item.setText(str(result))
        else:
            item.setText(formula)
    
    def calculate_formula(self, formula):
        import re
        table = self.current_table()
        expression = formula[1:].upper()
        match = re.fullmatch(r"SUM\(([A-Z]+)(\d+):([A-Z]+)(\d+)\)", expression)
        if match:
            c1, r1, c2, r2 = match.groups()
            total = 0
            for r in range(int(r1) - 1, int(r2)):
                for c in range(self.column_number(c1), self.column_number(c2) + 1):
                    item = table.item(r, c)
                    if item:
                        try:
                            total += float(item.text())
                        except:
                            pass
            return int(total) if total.is_integer() else total
        return formula
    
    def column_number(self, name):
        number = 0
        for char in name:
            number = number * 26 + ord(char) - 64
        return number - 1
    
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if path:
            self.export_csv_to(path)
    
    def export_csv_to(self, path):
        import csv
        table = self.current_table()
        if not table:
            return
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            for r in range(table.rowCount()):
                row = []
                for c in range(table.columnCount()):
                    item = table.item(r, c)
                    row.append(item.text() if item else "")
                writer.writerow(row)
        self.current_file = path
        self.update_session_state()
    
    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export HTML", "", "HTML Files (*.html)")
        if path:
            self.export_html_to(path)
    
    def export_html_to(self, path):
        import html
        table = self.current_table()
        if not table:
            return
        rows = [
            "<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1.0'><title>Spreadsheet</title><style>",
            "body{font-family:Arial,sans-serif;margin:20px;background:white}",
            "table{border-collapse:collapse;table-layout:fixed}",
            "th,td{border:1px solid #ccc;padding:5px;min-width:80px;height:30px;vertical-align:middle;white-space:normal}",
            "th{background:#eef0f2;font-weight:bold;text-align:center}",
            "img{max-width:100%;height:auto}",
            "a{color:inherit;text-decoration:none}",
            "</style></head><body><table>"
        ]
        rows.append("<tr><th></th>")
        for c in range(table.columnCount()):
            rows.append(f"<th>{html.escape(self.column_name(c))}</th>")
        rows.append("</tr>")
        for r in range(table.rowCount()):
            rows.append(f"<tr><th>{r + 1}</th>")
            for c in range(table.columnCount()):
                item = table.item(r, c)
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
                        decorations.append("underline")
                    if font.strikeOut():
                        decorations.append("line-through")
                    if decorations:
                        attrs += f"text-decoration:{' '.join(decorations)};"
                    attrs += f"color:{item.foreground().color().name()};"
                    attrs += f"background-color:{item.background().color().name()};"
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
                    content = html.escape(item.text()).replace("\n", "<br>")
                    media_path = item.data(Qt.UserRole + 2)
                    media_type = item.data(Qt.UserRole + 3)
                    if media_path and os.path.exists(str(media_path)):
                        try:
                            with open(str(media_path), "rb") as media_file:
                                encoded = base64.b64encode(media_file.read()).decode("ascii")
                            if str(media_type).lower() == "pdf":
                                content = f"<a href='data:application/pdf;base64,{encoded}' target='_blank'>{html.escape(os.path.basename(str(media_path)))}</a>"
                            else:
                                extension = os.path.splitext(str(media_path))[1].lower()
                                mime_types = {
                                    ".png": "image/png",
                                    ".jpg": "image/jpeg",
                                    ".jpeg": "image/jpeg",
                                    ".gif": "image/gif",
                                    ".bmp": "image/bmp",
                                    ".webp": "image/webp",
                                    ".svg": "image/svg+xml",
                                    ".ico": "image/x-icon",
                                    ".tif": "image/tiff",
                                    ".tiff": "image/tiff"
                                }
                                mime = mime_types.get(extension, "application/octet-stream")
                                content = f"<a href='data:{mime};base64,{encoded}' target='_blank'><img src='data:{mime};base64,{encoded}'></a>"
                        except (OSError, ValueError):
                            pass
                rowspan = table.rowSpan(r, c)
                colspan = table.columnSpan(r, c)
                span = ""
                if rowspan > 1:
                    span += f" rowspan='{rowspan}'"
                if colspan > 1:
                    span += f" colspan='{colspan}'"
                rows.append(f"<td style='{attrs}'{span}>{content}</td>")
            rows.append("</tr>")
        rows.append("</table></body></html>")
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(rows))
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Spreadsheet()
    window.show()
    sys.exit(app.exec_())