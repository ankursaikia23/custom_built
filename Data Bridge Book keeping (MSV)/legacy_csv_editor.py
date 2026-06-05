import sys
import re
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog,
    QTextEdit, QAbstractItemView, QInputDialog, QLabel, QMessageBox,
    QPlainTextEdit, QSizePolicy, QDialog, QSpinBox, QDialogButtonBox,
    QComboBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from PyPDF2 import PdfReader
import uuid

class SmartTextEdit(QPlainTextEdit):
    navigateUp = pyqtSignal()
    navigateDown = pyqtSignal()

    def keyPressEvent(self, event):
        key = event.key()
        cursor = self.textCursor()
        doc = self.document()
        line_count = doc.blockCount()
        has_shift = bool(event.modifiers() & Qt.ShiftModifier)
        if key == Qt.Key_Up:
            if line_count == 1:
                if has_shift:
                    cursor.movePosition(QTextCursor.Start, QTextCursor.KeepAnchor)
                else:
                    cursor.movePosition(QTextCursor.Start)
                self.setTextCursor(cursor)
                return
            else:
                super().keyPressEvent(event)
                return
        elif key == Qt.Key_Down:
            if line_count == 1:
                if has_shift:
                    cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                else:
                    cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)
                return
            else:
                super().keyPressEvent(event)
                return
        super().keyPressEvent(event)

class PDFLoaderThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        text_parts = []
        try:
            reader = PdfReader(self.filepath)
            for page in reader.pages:
                if self._stop_requested:
                    self.finished.emit("__CANCELLED__")
                    return
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        except Exception as e:
            self.finished.emit(f"__ERROR__{e}")
            return
        if self._stop_requested:
            self.finished.emit("__CANCELLED__")
            return
        self.finished.emit("\n".join(text_parts))

def shift_expand_selection(editor, key):
    if isinstance(editor, QLineEdit):
        cur_pos = editor.cursorPosition()
        text_len = len(editor.text())
        if key == Qt.Key_Up:
            editor.setSelection(0, cur_pos)
        elif key == Qt.Key_Down:
            editor.setSelection(cur_pos, text_len - cur_pos)
    elif isinstance(editor, (QTextEdit, QPlainTextEdit)):
        cursor = editor.textCursor()
        anchor = cursor.anchor()
        if key == Qt.Key_Up:
            cursor.setPosition(0, QTextCursor.KeepAnchor)
            if anchor != cursor.position():
                cursor.setPosition(anchor, QTextCursor.KeepAnchor)
            editor.setTextCursor(cursor)
        elif key == Qt.Key_Down:
            cursor.setPosition(len(editor.toPlainText()), QTextCursor.KeepAnchor)
            if anchor != cursor.position():
                cursor.setPosition(anchor, QTextCursor.KeepAnchor)
            editor.setTextCursor(cursor)

class ExcelTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_font_size = 12
        self.update_font()
        self.setWordWrap(True)
        self.setTextElideMode(Qt.ElideNone)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.undo_stack = []
        self.redo_stack = []
        self._internal_clipboards = {}

    def update_font(self):
        font = self.font()
        font.setPointSize(self.base_font_size)
        self.setFont(font)
        QTimer.singleShot(0, self._deferred_resize)
        
    def _deferred_resize(self):
        try:
            if self.rowCount() <= 500:
                self.resizeRowsToContents()
                self.resizeColumnsToContents()
            else:
                self.resizeColumnsToContents()
        except Exception:
            pass

    def keyPressEvent(self, event):
        ctrl = bool(event.modifiers() & Qt.ControlModifier)
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        if ctrl:
            if event.key() in (Qt.Key_Plus, Qt.Key_Equal):
                self.base_font_size += 1
                self.update_font()
                return
            elif event.key() == Qt.Key_Minus:
                if self.base_font_size > 6:
                    self.base_font_size -= 1
                    self.update_font()
                return
            elif event.key() == Qt.Key_Z:
                self.perform_undo()
                return
            elif event.key() == Qt.Key_Y:
                self.perform_redo()
                return
            elif event.key() == Qt.Key_C:
                self.copy_selection()
                return
            elif event.key() == Qt.Key_V:
                self.paste_selection()
                return
            elif event.key() == Qt.Key_X:
                self.cut_selection()
                return
            elif event.key() == Qt.Key_Backspace:
                self.delete_selection()
                return    
        if self.state() == QAbstractItemView.EditingState and self.focusWidget():
            editor = self.focusWidget()
            if shift and event.key() in (Qt.Key_Up, Qt.Key_Down):
                shift_expand_selection(editor, event.key())
                return
            if event.key() == Qt.Key_Up:
                try:
                    editor.setCursorPosition(0)
                except Exception:
                    pass
                return
            elif event.key() == Qt.Key_Down:
                try:
                    editor.setCursorPosition(len(editor.text()))
                except Exception:
                    pass
                return
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key_Backspace:
            selected = self.selectedIndexes()
            if selected:
                for idx in selected:
                    item = self.item(idx.row(), idx.column())
                    if item:
                        self.undo_stack.append((idx.row(), idx.column(), item.text()))
                        item.setText("")
                self.redo_stack.clear()
            return    
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cur = self.currentItem()
            if cur is not None:
                self.editItem(cur)
            return
        super().keyPressEvent(event)

    def perform_undo(self):
        if not self.undo_stack:
            return
        entry = self.undo_stack.pop()
        entries = entry if isinstance(entry, list) else [entry]
        reverse_changes = []
        for ch in entries:
            if len(ch) >= 3:
                r, c, old = ch[0], ch[1], ch[2]
            else:
                continue
            item = self.item(r, c)
            current_val = item.text() if item else ""
            reverse_changes.append((r, c, current_val, old))
            if item:
                item.setText(old)
            else:
                self.setItem(r, c, QTableWidgetItem(old))
        if reverse_changes:
            self.redo_stack.append(reverse_changes)
    
    def delete_selection(self):
        selected = self.selectedIndexes()
        if not selected:
            return
        positions = []
        seen = set()
        for idx in selected:
            pos = (idx.row(), idx.column())
            if pos not in seen:
                seen.add(pos)
                positions.append(pos)
        changes = []
        for r, c in positions:
            item = self.item(r, c)
            old_val = item.text() if item else ""
            if old_val != "":
                changes.append((r, c, old_val, ""))
                if item:
                    item.setText("")
                else:
                    self.setItem(r, c, QTableWidgetItem(""))
        if changes:
            self.undo_stack.append(changes)
            self.redo_stack.clear()
        parent = self.parent()
        if parent and hasattr(parent, "notify"):
            parent.notify(f"🧹 Cleared {len(positions)} cell(s)")
    
    def cut_selection(self):
        self.copy_selection()
        selected = self.selectedIndexes()
        if not selected:
            return
        selected = sorted(selected, key=lambda x: (x.row(), x.column()))
        changes = []
        seen = set()
        for idx in selected:
            pos = (idx.row(), idx.column())
            if pos in seen:
                continue
            seen.add(pos)
            item = self.item(idx.row(), idx.column())
            old_val = item.text() if item else ""
            if old_val != "":
                changes.append((idx.row(), idx.column(), old_val, ""))
                if item:
                    item.setText("")
                else:
                    self.setItem(idx.row(), idx.column(), QTableWidgetItem(""))
        if changes:
            self.undo_stack.append(changes)
            self.redo_stack.clear()

    def perform_redo(self):
        if not self.redo_stack:
            return
        entry = self.redo_stack.pop()
        entries = entry if isinstance(entry, list) else [entry]
        reverse_changes = []
        for ch in entries:
            if len(ch) >= 4:
                r, c, _, new = ch[0], ch[1], ch[2], ch[3]
            elif len(ch) == 3:
                r, c, new = ch[0], ch[1], ""
            else:
                continue
            item = self.item(r, c)
            current_val = item.text() if item else ""
            reverse_changes.append((r, c, current_val, new))
            if item:
                item.setText(new)
            else:
                self.setItem(r, c, QTableWidgetItem(new))
        if reverse_changes:
            self.undo_stack.append(reverse_changes)

    def copy_selection(self):
        selected = self.selectedRanges()
        if not selected:
            return
        text = ""
        for rng in selected:
            for r in range(rng.topRow(), rng.bottomRow() + 1):
                row_text = []
                for c in range(rng.leftColumn(), rng.rightColumn() + 1):
                    item = self.item(r, c)
                    cell_text = item.text() if item else ""
                    cell_text = cell_text.replace("\n", "\\n")
                    row_text.append(cell_text)
                text += "\t".join(row_text) + "\n"
        text = text.strip()
        if len(text) > 1_000_000:
            key = str(uuid.uuid4())
            self._internal_clipboards[key] = text
            if len(self._internal_clipboards) > 20:
                self._internal_clipboards.pop(next(iter(self._internal_clipboards)))
            QApplication.clipboard().setText(f"__INTERNAL_CLIPBOARD__:{key}")
        else:
            QApplication.clipboard().setText(text)

    def paste_selection(self):
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return
        if clipboard_text.startswith("__INTERNAL_CLIPBOARD__:"):
            key = clipboard_text.split(":", 1)[1]
            text = self._internal_clipboards.get(key, "")
        else:
            text = clipboard_text
        if not text:
            return
        rows = text.split("\n")
        selected = self.selectedIndexes()
        if not selected:
            return
        selected = sorted(selected, key=lambda x: (x.row(), x.column()))
        matrix = [r.split("\t") for r in rows]
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                matrix[i][j] = matrix[i][j].replace("\\n", "\n")
        changes = []
        max_rows = self.rowCount()
        max_cols = self.columnCount()
        if len(matrix) == 1 and len(matrix[0]) == 1:
            val = matrix[0][0]
            seen = set()
            positions = []
            for idx in selected:
                pos = (idx.row(), idx.column())
                if pos not in seen:
                    seen.add(pos)
                    positions.append(pos)
            for r_idx, c_idx in positions:
                if r_idx < max_rows and c_idx < max_cols:
                    item = self.item(r_idx, c_idx)
                    old_val = item.text() if item else ""
                    if old_val != val:
                        changes.append((r_idx, c_idx, old_val, val))
                        if item:
                            item.setText(val)
                        else:
                            self.setItem(r_idx, c_idx, QTableWidgetItem(val))
        else:
            start_row = selected[0].row()
            start_col = selected[0].column()
            truncated = False
            for i, row_vals in enumerate(matrix):
                for j, val in enumerate(row_vals):
                    r_idx = start_row + i
                    c_idx = start_col + j
                    if r_idx < max_rows and c_idx < max_cols:
                        item = self.item(r_idx, c_idx)
                        old_val = item.text() if item else ""
                        if old_val != val:
                            changes.append((r_idx, c_idx, old_val, val))
                            if item:
                                item.setText(val)
                            else:
                                self.setItem(r_idx, c_idx, QTableWidgetItem(val))
                    else:
                        truncated = True
            if truncated:
                parent = self.parent()
                if parent and hasattr(parent, "notify"):
                    parent.notify("⚠️ Paste truncated to fit table")
        if changes:
            self.undo_stack.append(changes)
            self.redo_stack.clear()
        parent = self.parent()
        if parent and hasattr(parent, "notify"):
            parent.notify("📋 Data pasted into table")
            
class CellEditor(QTextEdit):
    def keyPressEvent(self, event):
        cursor = self.textCursor()
        shift_pressed = bool(event.modifiers() & Qt.ShiftModifier)
        if event.key() == Qt.Key_Up:
            if shift_pressed:
                cursor.setPosition(0, QTextCursor.KeepAnchor)
            else:
                cursor.setPosition(0)
            self.setTextCursor(cursor)
            return
        elif event.key() == Qt.Key_Down:
            end_pos = len(self.toPlainText())
            if shift_pressed:
                cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
            else:
                cursor.setPosition(end_pos)
            self.setTextCursor(cursor)
            return    
        super().keyPressEvent(event)
        
class CollapsibleMenu(QWidget):
    def __init__(self, side="left"):
        super().__init__()
        self.side = side
        self.expanded = True
        self.buttons = []
        self.full_width = 180
        self.collapsed_width = 36
        self.setFixedWidth(self.full_width)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setFixedSize(32,32)
        self.toggle_btn.clicked.connect(self.toggle_menu)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(2,2,2,2)
        if side == "left":
            top_layout.addWidget(self.toggle_btn)
            top_layout.addStretch()
        else:
            top_layout.addStretch()
            top_layout.addWidget(self.toggle_btn)
        self.main_layout.addLayout(top_layout)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(2,2,2,2)
        self.container_layout.setSpacing(2)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(self.container)
        self.main_layout.addStretch()

    def add_button(self, button):
        button.setStyleSheet("text-align:left; padding-left:8px;")
        button.setMinimumHeight(28)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.buttons.append(button)
        self.container_layout.addWidget(button)
        
    def finalize_buttons(self):
        if not self.buttons:
            return
        fm = self.buttons[0].fontMetrics()
        longest = max(self.buttons, key=lambda b: len(b.text())).text()
        width = fm.horizontalAdvance(longest) + 30
        for btn in self.buttons:
            btn.setFixedWidth(width)
        self.full_width = width + 10
        self.setFixedWidth(self.full_width)

    def toggle_menu(self):
        if self.expanded:
            self.container.hide()
            self.setFixedWidth(self.collapsed_width)
        else:
            self.container.show()
            self.setFixedWidth(self.full_width)
        self.expanded = not self.expanded

class CSVEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.debug_enabled = False
        self.setWindowTitle("DataBridge Studio")
        self.resize(1400, 820)
        self.df = None
        self.filtered_df = None
        self.pdf_text = ""
        self.pdf_matches = []
        self.current_match_index = -1
        self.csv_filename = ""
        self.pdf_filename = ""
        self.unsaved_changes = False
        self.original_df = None
        self.last_state_df = None
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)
        left_sidebar = CollapsibleMenu("left")
        self.load_pdf_btn = QPushButton("Load PDF")
        self.cancel_pdf_btn = QPushButton("Cancel PDF")
        self.prev_match_btn = QPushButton("Previous")
        self.next_match_btn = QPushButton("Next")
        left_sidebar.add_button(self.load_pdf_btn)
        left_sidebar.add_button(self.cancel_pdf_btn)
        left_sidebar.finalize_buttons()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0,0,0,0)
        pdf_search_layout = QHBoxLayout()
        self.pdf_search = QLineEdit()
        self.pdf_search.setPlaceholderText("Search PDF... (press Enter)")
        self.pdf_clear = QPushButton("Clear Search")
        pdf_search_layout.addWidget(self.pdf_search)
        pdf_search_layout.addWidget(self.pdf_clear)
        left_layout.addLayout(pdf_search_layout)
        nav_btn_layout = QHBoxLayout()
        nav_btn_layout.setContentsMargins(0, 0, 0, 0)
        nav_btn_layout.setSpacing(0)
        self.prev_match_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.next_match_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        nav_btn_layout.addWidget(self.prev_match_btn)
        nav_btn_layout.addWidget(self.next_match_btn)
        left_layout.addLayout(nav_btn_layout)
        self.prev_match_btn.setStyleSheet("border-right: 1px solid gray;")
        self.next_match_btn.setStyleSheet("")
        self.pdf_viewer = QTextEdit()
        self.pdf_viewer.setStyleSheet("""
        QTextEdit {
            selection-background-color: orange;
        }
        """)
        self.pdf_viewer.setReadOnly(True)
        left_layout.addWidget(self.pdf_viewer)
        right_layout = QVBoxLayout()
        csv_search_layout = QHBoxLayout()
        self.csv_search = QLineEdit()
        self.csv_search.setPlaceholderText("Search CSV...")
        self.csv_clear = QPushButton("Clear")
        csv_search_layout.addWidget(self.csv_search)
        csv_search_layout.addWidget(self.csv_clear)
        right_layout.addLayout(csv_search_layout)
        self.csv_status_label = QLabel("")
        self.csv_status_label.setTextFormat(Qt.RichText)
        self.csv_status_label.setStyleSheet("""
            padding: 4px;
            font-weight: bold;
        """)
        right_layout.addWidget(self.csv_status_label)
        self.file_info_label = QLabel("PDF: - | CSV: - | Questions: -")
        self.file_info_label.setStyleSheet("color: darkgreen; font-weight: bold;")
        right_layout.addWidget(self.file_info_label)
        self.row_info_label = QLabel("Row: -")
        self.row_info_label.setStyleSheet("""
            color: #1976D2;
            font-weight: bold;
            padding: 2px;
        """)
        right_layout.addWidget(self.row_info_label)
        self.cell_editor = SmartTextEdit()
        self.cell_editor.setPlaceholderText("Edit cell content here...")
        self.cell_editor.setFixedHeight(100)
        self.cell_editor.setStyleSheet("font-family: Consolas; font-size: 12px;")
        right_layout.addWidget(self.cell_editor)
        self.cell_editor.textChanged.connect(self.update_cell_from_editor)
        self.cell_editor.navigateUp.connect(self.focus_previous_cell)
        self.cell_editor.navigateDown.connect(self.focus_next_cell)
        self.table = ExcelTable()
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.edit_column_header)
    
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.EditKeyPressed
        )
    
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        right_layout.addWidget(self.table)
        self.table.itemChanged.connect(self.on_table_item_changed)
        right_sidebar = CollapsibleMenu("right")
        self._btn = QPushButton("Load CSV")
        self.create_csv_btn = QPushButton("Create CSV")
        self.save_csv_btn = QPushButton("Save CSV")
        self.rename_csv_btn = QPushButton("Rename CSV")
        self.validate_btn = QPushButton("Validate Answers")
        self.structure_validate_btn = QPushButton("Validate Structure")
        self.clean_multiline_btn = QPushButton("Clean Multilines")
        self.add_rows_btn = QPushButton("Add Row(s)")
        self.delete_row_btn = QPushButton("Delete Selected Row(s)")
        self.remove_duplicates_btn = QPushButton("Remove Duplicates")
        self.missing_only_btn = QPushButton("Missing Only")
        self.show_all_btn = QPushButton("Show All")
        self.undo_all_btn = QPushButton("Undo All")
        self.redo_all_btn = QPushButton("Redo All")
        self.scale_btn = QPushButton("Scale Up / Down")
        self.insert_cols_btn = QPushButton("Insert Column(s)")
        self.del_col_btn = QPushButton("Delete Selected Column(s)")
        right_sidebar.add_button(self._btn)
        right_sidebar.add_button(self.create_csv_btn)
        right_sidebar.add_button(self.save_csv_btn)
        right_sidebar.add_button(self.rename_csv_btn)
        right_sidebar.add_button(self.add_rows_btn)
        right_sidebar.add_button(self.insert_cols_btn)
        right_sidebar.add_button(self.delete_row_btn)
        right_sidebar.add_button(self.del_col_btn)
        right_sidebar.add_button(self.missing_only_btn)
        right_sidebar.add_button(self.remove_duplicates_btn)
        right_sidebar.add_button(self.clean_multiline_btn)
        right_sidebar.add_button(self.validate_btn)
        right_sidebar.add_button(self.structure_validate_btn)
        right_sidebar.add_button(self.scale_btn)
        right_sidebar.add_button(self.show_all_btn)
        right_sidebar.add_button(self.undo_all_btn)
        right_sidebar.add_button(self.redo_all_btn)
        right_sidebar.finalize_buttons()
        left_panel = QHBoxLayout()
        left_panel.addWidget(left_sidebar)
        left_panel.addLayout(left_layout)
        main_layout.addLayout(left_panel,1)
        main_layout.addLayout(right_layout,4)
        main_layout.addWidget(right_sidebar)
        self.load_pdf_btn.clicked.connect(self.load_pdf)
        self.cancel_pdf_btn.clicked.connect(self.cancel_pdf)
        self.pdf_search.returnPressed.connect(self.search_pdf)
        self.pdf_clear.clicked.connect(self.clear_pdf_search)
        self.prev_match_btn.clicked.connect(lambda: self.navigate_match(-1))
        self.next_match_btn.clicked.connect(lambda: self.navigate_match(1))
        self._btn.clicked.connect(self.load_csv)
        self.save_csv_btn.clicked.connect(self.save_csv)
        self.create_csv_btn.clicked.connect(self.create_csv)
        self.rename_csv_btn.clicked.connect(self.rename_csv)
        self.validate_btn.clicked.connect(self.validate_answers)
        self.structure_validate_btn.clicked.connect(self.validate_structure)
        self.clean_multiline_btn.clicked.connect(self.clean_multiline_cells)
        self.csv_search.returnPressed.connect(self.search_csv)
        self.csv_clear.clicked.connect(self.clear_search)
        self.add_rows_btn.clicked.connect(self.open_add_rows_dialog)
        self.delete_row_btn.clicked.connect(self.delete_selected_rows)
        self.insert_cols_btn.clicked.connect(self.open_insert_columns_dialog)
        self.del_col_btn.clicked.connect(self.delete_selected_columns)
        self.remove_duplicates_btn.clicked.connect(self.remove_duplicates)
        self.missing_only_btn.clicked.connect(self.show_missing_only)
        self.show_all_btn.clicked.connect(self.show_all_data)
        self.undo_all_btn.clicked.connect(self.undo_all_changes)
        self.redo_all_btn.clicked.connect(self.redo_all_changes)
        self.scale_btn.clicked.connect(self.open_scale_dialog)
        self.table.currentItemChanged.connect(self.update_editor_from_cell)
        self.table.currentItemChanged.connect(self.update_row_info)
        self.table.currentItemChanged.connect(lambda: self.notify("🔎 Cell selected"))
        self.table.currentItemChanged.connect(self.sync_pdf_with_selected_cell)
        self.table.currentItemChanged.connect(self.sync_pdf_with_csv)
        self.csv_search.keyPressEvent = lambda e, w=self.csv_search: self.search_bar_keypress(w, e)
        self.pdf_search.keyPressEvent = lambda e, w=self.pdf_search: self.search_bar_keypress(w, e)
        self._original_setText = self.csv_status_label.setText
        self.csv_status_label.setText = self.notify

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            self.save_csv()
            return
        super().keyPressEvent(event)
        
    def confirm_discard_or_save(self):
        if self.df is None:
            return True
        if self.unsaved_changes or not getattr(self, "current_csv_path", ""):
            msg = QMessageBox(self)
            msg.setWindowTitle("Unsaved Changes")
            msg.setText("You have an open CSV. Save before proceeding?")
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Save)
            result = msg.exec_()
            if result == QMessageBox.Save:
                self.save_csv()
                return True
            elif result == QMessageBox.Discard:
                return True
            else:
                return False
        return True
        
    def update_row_info(self, current, previous):
        if current:
            row = current.row() + 1
            col = current.column()
    
            if self.df is not None and col < len(self.df.columns):
                col_name = self.df.columns[col]
            else:
                col_name = f"Col {col+1}"
    
            self.row_info_label.setText(f"Row - {row} | Column - {col_name}")
        else:
            self.row_info_label.setText("Row - - | Column - -")

    def search_bar_keypress(self, widget, event):
        ctrl = bool(event.modifiers() & Qt.ControlModifier)
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        if ctrl or shift:
            if event.key() == Qt.Key_Up:
                widget.setSelection(0, widget.cursorPosition())
                return
            elif event.key() == Qt.Key_Down:
                widget.setSelection(widget.cursorPosition(), len(widget.text()) - widget.cursorPosition())
                return    
        if event.key() == Qt.Key_Up:
            widget.setCursorPosition(0)
            return
        elif event.key() == Qt.Key_Down:
            widget.setCursorPosition(len(widget.text()))
            return
        QLineEdit.keyPressEvent(widget, event)

    def load_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return
        self.pdf_viewer.setPlainText("Loading PDF...")
        self.pdf_text = ""
        self.pdf_thread = PDFLoaderThread(file_path)
        self.pdf_thread.finished.connect(self.display_pdf)
        self.pdf_thread.start()

    def display_pdf(self, text):
        if text == "__CANCELLED__":
            return
        if text.startswith("__ERROR__"):
            self.pdf_text = ""
            self.pdf_viewer.clear()
            return
        self.pdf_text = text
        self.pdf_viewer.setPlainText(self.pdf_text)
        self.pdf_filename = getattr(self.pdf_thread, "filepath", "").split("/")[-1]
        self.update_file_info_label()
        self.pdf_matches = []
        self.current_match_index = -1
        self.clear_all_highlights()
        
    def _build_ws_insensitive_pattern(self, s):
        s = s.strip()
        if not s:
            return None
        parts = re.split(r"\s+", s)
        escaped = [re.escape(p) for p in parts if p]
        if not escaped:
            return None
        pattern = r"\s+".join(escaped)
        return pattern

    def search_pdf(self):
        query = self.pdf_search.text().strip()
        if not query or not self.pdf_text:
            self.pdf_matches = []
            self.current_match_index = -1
            self.clear_all_highlights()
            return
        pattern = self._build_ws_insensitive_pattern(query)
        if not pattern:
            self.pdf_matches = []
            self.current_match_index = -1
            self.clear_all_highlights()
            return
        try:
            self.pdf_matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE | re.DOTALL))
        except re.error:
            self.pdf_matches = list(re.finditer(re.escape(query), self.pdf_text, re.IGNORECASE))
        if not self.pdf_matches:
            self.current_match_index = -1
            self.clear_all_highlights()
            return
        self.current_match_index = 0
        self.highlight_current_match()

    def highlight_current_match(self):
        self.pdf_viewer.setExtraSelections([])
        if not self.pdf_matches or self.current_match_index < 0:
            return
        prev_focus = QApplication.focusWidget()
        current = self.pdf_matches[self.current_match_index]
        selection = QTextEdit.ExtraSelection()
        cursor = self.pdf_viewer.textCursor()
        cursor.setPosition(current.start())
        cursor.setPosition(current.end(), QTextCursor.KeepAnchor)
        selection.cursor = cursor
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("orange"))
        selection.format = fmt
        self.pdf_viewer.setTextCursor(cursor)
        self.pdf_viewer.setExtraSelections([selection])
        self.pdf_viewer.ensureCursorVisible()
        self.pdf_viewer.repaint()
        QApplication.processEvents()
        self.pdf_viewer.setFocus()
        self.pdf_viewer.ensureCursorVisible()
    
        if prev_focus:
            prev_focus.setFocus()

    def navigate_match(self, direction):
        if not self.pdf_matches:
            return
        self.current_match_index = (self.current_match_index + direction) % len(self.pdf_matches)
        self.highlight_current_match()

    def clear_all_highlights(self):
        self.pdf_viewer.setExtraSelections([])

    def clear_pdf_search(self):
        self.pdf_search.clear()
        self.clear_all_highlights()
        self.pdf_matches = []
        self.current_match_index = -1
        
    def sync_pdf_with_csv(self, current, previous):
        if not self.pdf_text:
            return
        if current is None:
            return
        term = current.text().strip()
        if not term:
            self.clear_all_highlights()
            return
        self.pdf_search.setText(term)
        pattern = self._build_ws_insensitive_pattern(term)
        if not pattern:
            self.clear_all_highlights()
            self.pdf_matches = []
            self.current_match_index = -1
            return
        try:
            self.pdf_matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE | re.DOTALL))
        except re.error:
            self.pdf_matches = list(re.finditer(re.escape(term), self.pdf_text, re.IGNORECASE))
        if not self.pdf_matches:
            self.clear_all_highlights()
            self.current_match_index = -1
            return
        self.current_match_index = 0
        self.highlight_current_match()
        cursor = self.pdf_viewer.textCursor()
        cursor.setPosition(self.pdf_matches[0].start())
        self.pdf_viewer.setTextCursor(cursor)
        self.pdf_viewer.ensureCursorVisible()

    def cancel_pdf(self):
        try:
            if hasattr(self, "pdf_thread") and self.pdf_thread.isRunning():
                self.pdf_thread.stop()
        except Exception:
            pass
        self.pdf_text = ""
        self.pdf_viewer.clear()
        self.pdf_search.clear()
        self.pdf_matches = []
        self.current_match_index = -1

    def load_csv(self):
        if not self.confirm_discard_or_save():
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Data Files (*.csv *.xlsx *.xls *.ods);;All Files (*)"
        )
        if not file_path:
            return
        temp_csv_path = None
        try:
            if file_path.lower().endswith((".xlsx", ".xls", ".ods")):
                excel_df = pd.read_excel(
                    file_path,
                    engine="openpyxl" if file_path.lower().endswith((".xlsx", ".xls")) else None
                )
                temp_csv_path = file_path.rsplit(".", 1)[0] + "_converted.csv"
                excel_df.to_csv(temp_csv_path, index=False)
                self.df = pd.read_csv(temp_csv_path)
                self.current_csv_path = temp_csv_path
                self.csv_status_label.setText(f"✅ Converted {file_path.split('/')[-1]} to CSV and loaded.")
            else:
                self.df = pd.read_csv(file_path)
                self.current_csv_path = file_path
                self.csv_status_label.setText(f"✅ Loaded CSV: {file_path.split('/')[-1]}")
            self.df = self.df.loc[:, ~self.df.columns.duplicated()].copy()
        except Exception as e:
            self.csv_status_label.setText(f"Error loading file: {e}")
            self.df = None
            return
        finally:
            if temp_csv_path and os.path.exists(temp_csv_path):
                try:
                    os.remove(temp_csv_path)
                except Exception:
                    pass
        if self.df is None or self.df.empty:
            self.csv_status_label.setText("CSV is empty or invalid.")
            return
        self.df = self.df.drop(columns=["Q#"], errors="ignore")
        self.df.insert(0, "Q#", range(1, len(self.df) + 1))
        self.csv_status_label.setText(f"Loaded CSV with {len(self.df.columns)} columns.")
        self.normalize_missing()
        self.filtered_df = None
        self.populate_table(self.df)
        self.csv_status_label.setText(f"Loaded CSV: {file_path}")
        self.csv_filename = file_path.split("/")[-1]
        self.current_csv_path = file_path
        self.update_file_info_label()
        self.unsaved_changes = False
        self.original_df = self.df.copy(deep=True)
        self.last_state_df = None
        
    def create_csv(self):
        if not self.confirm_discard_or_save():
            return
        self.df = pd.DataFrame([[""]], columns=["Column_1"])
        self.df.insert(0, "Q#", [1])
        self.current_csv_path = ""
        self.csv_filename = "untitled.csv"
        self.filtered_df = None
        self.populate_table(self.df)
        QTimer.singleShot(50, self.auto_fit_new_csv_grid)
        self.csv_status_label.setText("🆕 Created new CSV (auto-fitted grid)")
        self.update_file_info_label()
        self.unsaved_changes = True
        self.original_df = self.df.copy(deep=True)
        self.last_state_df = None

    def validate_answers(self):
        if self.df is None or self.df.empty:
            self.csv_status_label.setText("No CSV loaded.")
            return
        self.update_dataframe_from_table()
        self.normalize_missing()    
        if "Answer" not in self.df.columns:
            QMessageBox.warning(self, "Missing Column", "Column 'Answer' not found in CSV.")
            return    
        option_cols = self.get_option_columns()
        if not option_cols:
            QMessageBox.warning(self, "Missing Columns", "No option columns found.")
            return
        invalid_rows = []
        for i, row in self.df.iterrows():
            ans_val = row["Answer"]
            if pd.isna(ans_val) or str(ans_val).strip() == "":
                invalid_rows.append(i + 1)
                continue
            ans = str(ans_val).strip().casefold()
            options = []
            for c in option_cols:
                val = row[c]
                if not pd.isna(val) and str(val).strip() != "":
                    options.append(str(val).strip().casefold())
            if ans not in options:
                invalid_rows.append(i + 1)
        if invalid_rows:
            msg = f"⚠️ {len(invalid_rows)} invalid row(s): " + ", ".join(map(str, invalid_rows))
            self.csv_status_label.setText(msg)
        else:
            self.csv_status_label.setText("✅ All answers match one of the options!")
            
    def validate_structure(self):
        if self.df is None or self.df.empty:
            return
        self.update_dataframe_from_table()
        self.normalize_missing()    
        dialog = QDialog(self)
        dialog.setWindowTitle("Validate Structure")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Select Question Column:"))
        q_combo = QComboBox()
        q_combo.addItems(self.df.columns.tolist())
        layout.addWidget(q_combo)
        layout.addWidget(QLabel("Select Answer Column:"))
        a_combo = QComboBox()
        a_combo.addItems(self.df.columns.tolist())
        layout.addWidget(a_combo)
        layout.addWidget(QLabel("Select Option Columns:"))
        opt_list = QListWidget()
        opt_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(opt_list)
    
        def refresh_options():
            opt_list.clear()
            q_col = q_combo.currentText()
            a_col = a_combo.currentText()
            for col in self.df.columns:
                if col not in [q_col, a_col]:
                    item = QListWidgetItem(col)
                    item.setSelected(True)
                    opt_list.addItem(item)
    
        refresh_options()
        q_combo.currentTextChanged.connect(refresh_options)
        a_combo.currentTextChanged.connect(refresh_options)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if not dialog.exec_():
            return
        q_col = q_combo.currentText()
        a_col = a_combo.currentText()
        opt_cols = [item.text() for item in opt_list.selectedItems()]
        missing_cols = [col for col in [q_col, a_col] if col not in self.df.columns]
        if missing_cols:
            QMessageBox.warning(self, "Missing Columns", f"Columns not found: {', '.join(missing_cols)}")
            return
        if not opt_cols:
            QMessageBox.warning(self, "Invalid Selection", "Please select at least one option column.")
            return
        total = len(self.df)
        valid = 0
        invalid = 0
        error_details = []
        for idx, row in self.df.iterrows():
            row_num = idx + 1
            question = row.get(q_col)
            answer = row.get(a_col)
            options = []
            for col in opt_cols:
                val = row.get(col)
                if not pd.isna(val) and str(val).strip() != "":
                    options.append(str(val).strip())
            missing_fields = []
            if pd.isna(question) or str(question).strip() == "":
                missing_fields.append(q_col)
            if pd.isna(answer) or str(answer).strip() == "":
                missing_fields.append(a_col)
            if missing_fields:
                invalid += 1
                error_details.append(f"Row {row_num} - Missing: {', '.join(missing_fields)}")
                continue
            if len(options) < 2:
                invalid += 1
                error_details.append(f"Row {row_num} - Less than 2 options")
                continue
            if str(answer).strip().casefold() not in [opt.casefold() for opt in options]:
                invalid += 1
                error_details.append(f"Row {row_num} - Answer does not match options")
                continue
            valid += 1
        msg_text = (
            f"Total Rows: {total}\n"
            f"Valid Rows: {valid}\n"
            f"Invalid Rows: {invalid}\n\n"
        )
        if error_details:
            msg_text += "Errors:\n" + "\n".join(error_details[:50])
            if len(error_details) > 50:
                msg_text += f"\n...and {len(error_details) - 50} more"
        msg = QMessageBox(self)
        msg.setWindowTitle("Validation Result")
        msg.setText(msg_text)
        msg.exec_()
            
    def clean_multiline_cells(self):
        if not self.df_is_loaded():
            return
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            rows = range(self.table.rowCount())
            cols = range(self.table.columnCount())
        else:
            rows = []
            cols = []
            for r in selected_ranges:
                rows.extend(range(r.topRow(), r.bottomRow() + 1))
                cols.extend(range(r.leftColumn(), r.rightColumn() + 1))
            rows = list(set(rows))
            cols = list(set(cols))
        cleaned_count = 0
        for row in rows:
            for col in cols:
                item = self.table.item(row, col)
                if item:
                    old_text = item.text()
                    new_text = re.sub(r"\s+", " ", old_text).strip()
                    if new_text != old_text:
                        item.setText(new_text)
                        cleaned_count += 1
        self.update_dataframe_from_table()
        self.notify(f"🧹 Cleaned {cleaned_count} cell(s)")

    def update_dataframe_from_table(self):
        if self.df is None:
            return
        rows = self.table.rowCount()
        cols = self.table.columnCount()    
        data = []
        for r in range(rows):
            row_data = []
            for c in range(cols):
                item = self.table.item(r, c)
                if item is None:
                    row_data.append(pd.NA)
                else:
                    text = item.text().strip()
                    if text == "" or text.lower() in ["nan", "none"]:
                        row_data.append(pd.NA)
                    else:
                        row_data.append(text)
            data.append(row_data)
        self.df = pd.DataFrame(data, columns=self.df.columns)

    def commit_editor_changes(self):
        current = self.table.currentItem()
        if current is None:
            return
        text = self.cell_editor.toPlainText()
        current.setText(text)
        row = current.row()
        col = current.column()
        if self.df is not None and 0 <= row < len(self.df.index) and 0 <= col < len(self.df.columns):
            self.df.iat[row, col] = text
        if self.df is not None and 0 <= row < len(self.df.index) and 0 <= col < len(self.df.columns):
            try:
                print(f"[DEBUG] Committing cell ({row},{col}) = {text}")
            except Exception:
                pass
        else:
            print("[DEBUG] commit_editor_changes skipped invalid row/col.")

    def save_csv(self):
        if self.df is None or self.df.empty:
            self.csv_status_label.setText("❌ No data to save.")
            return
        try:
            self.update_dataframe_from_table()    
            if not hasattr(self, "current_csv_path") or not self.current_csv_path:
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save CSV",
                    "",
                    "CSV Files (*.csv)"
                )
                if not file_path:
                    return
                self.current_csv_path = file_path
            self.df = self.df.map(lambda x: x.strip() if isinstance(x, str) else x)
            self.df.to_csv(self.current_csv_path, index=False)
            self.csv_filename = self.current_csv_path.split("/")[-1]
            self.update_file_info_label()
            self.csv_status_label.setText(f"✅ Saved: {self.csv_filename}")
            self.unsaved_changes = False
        except Exception as e:
            self.csv_status_label.setText(f"❌ Save failed: {e}")
        
    def rename_csv(self):
        if not hasattr(self, "current_csv_path") or not self.current_csv_path:
            self.csv_status_label.setText("❌ No CSV file loaded.")
            return
        current_name = self.csv_filename
        new_name, ok = QInputDialog.getText(
            self,
            "Rename CSV",
            "Enter new name (or leave blank for auto-update):",
            text=current_name
        )
        if not ok:
            return    
        if new_name.strip() == "":
            base_name = f"questions_{len(self.df)}.csv"
            new_path = os.path.join(os.path.dirname(self.current_csv_path), base_name)
        else:
            name = new_name.strip()
            if not name.lower().endswith(".csv"):
                name += ".csv"
            new_path = os.path.join(os.path.dirname(self.current_csv_path), name)
        try:
            os.rename(self.current_csv_path, new_path)
            self.current_csv_path = new_path
            self.csv_filename = os.path.basename(new_path)
            self.update_file_info_label()
            self.csv_status_label.setText(f"✅ Renamed to {self.csv_filename}")
        except Exception as e:
            self.csv_status_label.setText(f"❌ Rename failed: {e}")
                
    def df_is_loaded(self):
        if self.df is None or self.df.empty:
            self.csv_status_label.setText("No CSV loaded.")
            return False
        return True

    def search_csv(self):
        if self.df is None:
            return
        self.update_dataframe_from_table()
        query = self.csv_search.text().strip()
        if not query:
            self.populate_table(self.df)
            return
        self.filtered_df = self.df[self.df.apply(
            lambda r: r.astype(str).str.contains(query, case=False).any(), axis=1
        )]
        self.populate_table(self.filtered_df)

    def clear_search(self):
        self.csv_search.clear()
        self.show_all_data()

    def update_editor_from_cell(self, current, previous):
        if current:
            self.cell_editor.blockSignals(True)
            self.cell_editor.setPlainText(current.text())
            self.cell_editor.blockSignals(False)
        else:
            self.cell_editor.clear()

    def update_cell_from_editor(self):
        current = self.table.currentItem()
        if current is None or self.df is None:
            return
        text = self.cell_editor.toPlainText()
        row, col = current.row(), current.column()
        if row >= len(self.df.index) or col >= len(self.df.columns):
            return
        col_name = self.df.columns[col]
        self.table.blockSignals(True)
        current.setText(text)
        self.table.blockSignals(False)
        try:
            self.df.at[row, col_name] = text
            self.unsaved_changes = True
        except Exception:
            pass
                
    def on_table_item_changed(self, item):
        if getattr(self, "_loading_table", False):
            return
        if self.df is None:
            return
        row, col = item.row(), item.column()
        if col >= len(self.df.columns):
            return
        text = item.text()
        try:
            col_name = self.df.columns[col]
            if text.strip() == "":
                self.df.at[row, col_name] = pd.NA
                self.unsaved_changes = True
            else:
                orig_dtype = str(self.df[col_name].dtype)
                if "int" in orig_dtype or "Int" in orig_dtype:
                    try:
                        self.df.at[row, col_name] = int(float(text))
                    except Exception:
                        self.df[col_name] = self.df[col_name].astype("object")
                        self.df.at[row, col_name] = text
                elif "float" in orig_dtype:
                    try:
                        self.df.at[row, col_name] = float(text)
                    except Exception:
                        self.df[col_name] = self.df[col_name].astype("object")
                        self.df.at[row, col_name] = text
                else:
                    self.df.at[row, col_name] = text
                self.unsaved_changes = True
        except Exception:
            if col < len(self.df.columns):
                self.df.at[row, self.df.columns[col]] = text
                self.unsaved_changes = True
    
        def col_to_letter(c):
            result = ""
            while c >= 0:
                result = chr(c % 26 + 65) + result
                c = c // 26 - 1
            return result
    
        cell_name = f"{col_to_letter(col)}{row+1}"
        self.notify(f"✏️ Updated Cell {cell_name}")

    def focus_previous_cell(self):
        current = self.table.currentIndex()
        if current.row() > 0:
            new_index = self.table.model().index(current.row() - 1, current.column())
            self.table.setCurrentIndex(new_index)
            self.table.scrollTo(new_index)
    
    def focus_next_cell(self):
        current = self.table.currentIndex()
        if current.row() < self.table.rowCount() - 1:
            new_index = self.table.model().index(current.row() + 1, current.column())
            self.table.setCurrentIndex(new_index)
            self.table.scrollTo(new_index)
    
    def sync_pdf_with_selected_cell(self, current, previous):
        if not current or not self.pdf_text:
            return
        text = current.text().strip()
        if not text:
            return
        pattern = self._build_ws_insensitive_pattern(text)
        if not pattern:
            self.pdf_viewer.setExtraSelections([])
            return
        try:
            matches = list(re.finditer(pattern, self.pdf_text, re.IGNORECASE | re.DOTALL))
        except re.error:
            matches = list(re.finditer(re.escape(text), self.pdf_text, re.IGNORECASE))
        if not matches:
            self.pdf_viewer.setExtraSelections([])
            return
        first = matches[0]
        cursor = self.pdf_viewer.textCursor()
        cursor.setPosition(first.start())
        cursor.setPosition(first.end(), QTextCursor.KeepAnchor)
        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("yellow"))
        selection.format = fmt
        self.pdf_viewer.setExtraSelections([selection])
        self.pdf_viewer.setTextCursor(cursor)
        self.pdf_viewer.ensureCursorVisible()

    def populate_table(self, df):
        if df is self.df:
            self.filtered_df = None
        self._loading_table = True
        self.table.clear()
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns.tolist())
        for i in range(len(df)):
            for j in range(len(df.columns)):
                value = "" if pd.isna(df.iat[i, j]) else str(df.iat[i, j])
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self._loading_table = False
        
    def auto_fit_new_csv_grid(self):
        if self.table.viewport().width() == 0 or self.table.viewport().height() == 0:
            return
        viewport_width = self.table.viewport().width()
        viewport_height = self.table.viewport().height()
        col_width = 120
        row_height = 28
        col_count = max(1, viewport_width // col_width)
        row_count = max(1, viewport_height // row_height)
        cols = ["Q#"] + [f"Column_{i+1}" for i in range(col_count - 1)]
        data = [["" for _ in cols] for _ in range(row_count)]
        self.df = pd.DataFrame(data, columns=cols)
        self.df["Q#"] = range(1, len(self.df) + 1)
        self.populate_table(self.df)
        actual_col_width = max(80, viewport_width // len(cols))
        for c in range(len(cols)):
            self.table.setColumnWidth(c, actual_col_width)
        for r in range(row_count):
            self.table.setRowHeight(r, row_height)
        
    def edit_column_header(self, index):
        if index < 0 or index >= self.table.columnCount():
            return
        header = self.table.horizontalHeader()
        header.blockSignals(True)
        old_name = self.table.horizontalHeaderItem(index).text()
        new_name, ok = QInputDialog.getText(
            self,
            "Edit Column Name",
            f"Enter new name for column '{old_name}':",
            text=old_name
        )
        if ok and new_name.strip():
            self.table.setHorizontalHeaderItem(index, QTableWidgetItem(new_name.strip()))
            if self.df is not None and index < len(self.df.columns):
                self.df.columns.values[index] = new_name.strip()
        header.blockSignals(False)

    def delete_selected_rows(self):
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not selected_rows:
            self.csv_status_label.setText("No rows selected for deletion.")
            return
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_rows)} selected row(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            self.csv_status_label.setText("Deletion cancelled.")
            return
        for row in selected_rows:
            self.df.drop(self.df.index[row], inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        if "Q#" in self.df.columns:
            self.df["Q#"] = range(1, len(self.df) + 1)
        self.populate_table(self.df)
        self.notify(f"🗑️ Deleted {len(selected_rows)} row(s)")
        self.update_file_info_label()
        
    def open_insert_columns_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Insert Column(s)")
        layout = QVBoxLayout(dialog)
        label = QLabel("Number of columns:")
        layout.addWidget(label)    
        spin = QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(100)
        spin.setValue(1)
        layout.addWidget(spin)
        pos_label = QLabel("Insert columns:")
        layout.addWidget(pos_label)
        btn_layout = QHBoxLayout()
        left_btn = QPushButton("Left")
        right_btn = QPushButton("Right")
        left_btn.setCheckable(True)
        right_btn.setCheckable(True)
    
        def select_left():
            left_btn.setChecked(True)
            right_btn.setChecked(False)
            left_btn.setStyleSheet("background-color: lightgreen")
            right_btn.setStyleSheet("")
    
        def select_right():
            right_btn.setChecked(True)
            left_btn.setChecked(False)
            right_btn.setStyleSheet("background-color: lightgreen")
            left_btn.setStyleSheet("")
    
        left_btn.clicked.connect(select_left)
        right_btn.clicked.connect(select_right)
        select_right()
        btn_layout.addWidget(left_btn)
        btn_layout.addWidget(right_btn)
        layout.addLayout(btn_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
    
        if dialog.exec_():
            n = spin.value()
            if left_btn.isChecked():
                self._insert_columns(position="left", n=n)
            elif right_btn.isChecked():
                self._insert_columns(position="right", n=n)

    def _insert_columns(self, position="right", n=1):
        if self.df is None or self.df.empty:
            self.csv_status_label.setText("No CSV loaded.")
            return
        selected_cols = sorted(set(idx.column() for idx in self.table.selectedIndexes()))
        if not selected_cols:
            insert_pos = len(self.df.columns)
        else:
            first_col = selected_cols[0]
            last_col = selected_cols[-1]
            insert_pos = first_col if position == "left" else last_col + 1
        existing = set(self.df.columns)
        for i in range(n):
            base = "NewColumn"
            k = 1
            while f"{base}_{k}" in existing:
                k += 1
            col_name = f"{base}_{k}"
            existing.add(col_name)
            self.df.insert(insert_pos + i, col_name, "")
        self.populate_table(self.df)
        self.normalize_column_names()
        self.csv_status_label.setText(f"Inserted {n} column(s) to the {position}.")
        self.update_file_info_label()
        self.notify(f"➕ Added {n} column(s)")
        
    def delete_selected_columns(self):
        if self.df is None or self.df.empty:
            self.csv_status_label.setText("No CSV loaded.")
            return
        selected_cols = sorted(set(idx.column() for idx in self.table.selectedIndexes()), reverse=True)
        if not selected_cols:
            self.csv_status_label.setText("No columns selected for deletion.")
            return
        reply = QMessageBox.question(
            self,
            "Confirm Column Deletion",
            f"Are you sure you want to delete {len(selected_cols)} selected column(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        for col in selected_cols:
            if col < len(self.df.columns):
                self.df.drop(self.df.columns[col], axis=1, inplace=True)
                self.normalize_column_names()
        self.populate_table(self.df)
        self.notify(f"🗑️ Deleted {len(selected_cols)} column(s)")
        self.update_file_info_label()
        
    def open_add_rows_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Row(s)")
        layout = QVBoxLayout(dialog)
        label = QLabel("Number of rows:")
        layout.addWidget(label)
        spin = QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(1000)
        spin.setValue(1)
        layout.addWidget(spin)
        label2 = QLabel("Insert rows:")
        layout.addWidget(label2)
        btn_layout = QHBoxLayout()
        above_btn = QPushButton("Above")
        below_btn = QPushButton("Below")
        above_btn.setCheckable(True)
        below_btn.setCheckable(True)
        btn_layout.addWidget(above_btn)
        btn_layout.addWidget(below_btn)
        layout.addLayout(btn_layout)
        below_btn.setChecked(True)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec_():
            n = spin.value()
            if above_btn.isChecked():
                self.insert_row(relative_position="above", n=n)
            else:
                self.insert_row(relative_position="below", n=n)

    def insert_row(self, relative_position="below", n=1):
        if self.df is None or self.df.empty:
            return
        self.update_dataframe_from_table()
        selected = self.table.currentRow()
        if selected < 0:
            self.csv_status_label.setText("Select a row first.")
            return
        new_rows = []
        for _ in range(n):
            new_row = {col: pd.NA for col in self.df.columns}
            new_rows.append(new_row)
        new_df = pd.DataFrame(new_rows, columns=self.df.columns)
        insert_index = selected if relative_position == "above" else selected + 1
        self.df = pd.concat(
            [self.df.iloc[:insert_index], new_df, self.df.iloc[insert_index:]],
            ignore_index=True
        )
        if "Q#" in self.df.columns:
            self.df["Q#"] = range(1, len(self.df) + 1)
        self.populate_table(self.df)
        self.table.selectRow(insert_index)
        self.update_file_info_label()
        self.notify(f"➕ Added {n} row(s)")

    def remove_duplicates(self):
        if self.df is None or self.df.empty:
            return
        if "Question" not in self.df.columns:
            self.csv_status_label.setText("❌ 'Question' column not found.")
            return
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=["Question"]).reset_index(drop=True)
        if "Q#" in self.df.columns:
            self.df["Q#"] = range(1, len(self.df) + 1)
        self.populate_table(self.df)
        removed = before - len(self.df)
        self.notify(f"🧹 Removed {removed} duplicate(s)")
        self.update_file_info_label()

    def normalize_missing(self):
        if self.df is None:
            return    
        self.df = self.df.replace(
            to_replace=[None, "", " ", "nan", "NaN", "None"],
            value=pd.NA
        )
        self.df = self.df.map(
            lambda x: pd.NA if pd.isna(x) else str(x).strip()
        )
        
    def get_option_columns(self):
        if self.df is None:
            return []
        return [
            col for col in self.df.columns
            if "option" in col.lower() or "choice" in col.lower()
        ]

    def normalize_column_names(self):
        if self.df is None:
            return
        new_cols = []
        col_counter = 1
        for col in self.df.columns:
            if col == "Q#":
                new_cols.append(col)
            elif col.startswith("Column_"):
                new_cols.append(f"Column_{col_counter}")
                col_counter += 1
            else:
                new_cols.append(col)
        self.df.columns = new_cols

    def show_missing_only(self):
        if self.df is None:
            return
        self.update_dataframe_from_table()
        self.normalize_missing()
        cols_to_check = [c for c in self.df.columns if c != "Q#"]
        self.filtered_df = self.df[self.df[cols_to_check].isna().any(axis=1)]
        if self.filtered_df.empty:
            self.csv_status_label.setText("No missing values found.")
        else:
            self.populate_table(self.filtered_df)
            self.csv_status_label.setText(f"{len(self.filtered_df)} row(s) with missing values shown.")
        self.update_file_info_label()

    def show_all_data(self):
        if self.df is None:
            return
        self.filtered_df = None
        self.populate_table(self.df.copy())
        self.csv_search.clear()
        self.csv_status_label.setText("Showing all data.")
        self.update_file_info_label()
        
    def open_scale_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Scale CSV View")
        layout = QVBoxLayout(dialog)
        percent_layout = QHBoxLayout()
        percent_label = QLabel("Scale %:")
        spin = QSpinBox()
        spin.setRange(1, 100)
        spin.setValue(50)
        percent_layout.addWidget(percent_label)
        percent_layout.addWidget(spin)
        layout.addLayout(percent_layout)
        preset_layout = QHBoxLayout()
        min_btn = QPushButton("Min")
        mid_btn = QPushButton("50%")
        max_btn = QPushButton("Max")
        preset_layout.addWidget(min_btn)
        preset_layout.addWidget(mid_btn)
        preset_layout.addWidget(max_btn)
        layout.addLayout(preset_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        min_btn.clicked.connect(lambda: spin.setValue(spin.minimum()))
        mid_btn.clicked.connect(lambda: spin.setValue(50))
        max_btn.clicked.connect(lambda: spin.setValue(spin.maximum()))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec_():
            scale_percent = spin.value()
            base_size = 10
            new_size = max(6, min(40, base_size * scale_percent / 50))
            font = self.table.font()
            font.setPointSizeF(new_size)
            self.table.setFont(font)
            
    def undo_all_changes(self):
        if self.original_df is None:
            self.csv_status_label.setText("No original state available.")
            return
        if self.df is None:
            return
        self.last_state_df = self.df.copy(deep=True)
        self.df = self.original_df.copy(deep=True)
        self.filtered_df = None
        self.populate_table(self.df)
        self.csv_status_label.setText("↩️ Reverted to original CSV state.")
        self.update_file_info_label()
    
    def redo_all_changes(self):
        if self.last_state_df is None:
            self.csv_status_label.setText("No redo state available.")
            return
        temp = self.df.copy(deep=True)
        self.df = self.last_state_df.copy(deep=True)
        self.last_state_df = temp
        self.filtered_df = None
        self.populate_table(self.df)
        self.csv_status_label.setText("↪️ Restored last changes.")
        self.update_file_info_label()

    def update_file_info_label(self):
        pdf_name = self.pdf_filename if self.pdf_filename else "-"
        csv_name = self.csv_filename if self.csv_filename else "-"
        count = len(self.df) if self.df is not None else 0
        self.file_info_label.setText(f"PDF: {pdf_name} | CSV: {csv_name} | Questions: {count}")

    def notify(self, message):
        msg = str(message).lower()
        color = "#2196F3"
        if any(k in msg for k in ["saved", "success", "loaded", "created"]):
            color = "#4CAF50"
        elif any(k in msg for k in ["error", "failed", "invalid"]):
            color = "#F44336"
        elif any(k in msg for k in ["missing", "warning", "cancel"]):
            color = "#FF9800"
        elif any(k in msg for k in ["deleted", "removed", "cleared"]):
            color = "#9C27B0"
        elif any(k in msg for k in ["added", "insert"]):
            color = "#009688"
        styled = f'<span style="color:{color}; font-weight:bold;">{message}</span>'
        try:
            self._original_setText(styled)
        except Exception:
            pass

    def closeEvent(self, event):
        if not self.unsaved_changes:
            event.accept()
            return
        msg = QMessageBox(self)
        msg.setWindowTitle("Exit Confirmation")
        msg.setText("Do you want to save the CSV before exiting?")
        msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Save)
        result = msg.exec_()
        if result == QMessageBox.Save:
            self.save_csv()
            if getattr(self, "current_csv_path", ""):
                event.accept()
            else:
                event.ignore()
        elif result == QMessageBox.Discard:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVEditor()
    window.show()
    sys.exit(app.exec_())