# csv_editor(v22) #

import sys
import re
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog,
    QTextEdit, QAbstractItemView, QInputDialog, QLabel, QMessageBox, QPlainTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QKeyEvent
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
    elif isinstance(editor, QTextEdit):
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
        ctrl = event.modifiers() == Qt.ControlModifier
        shift = event.modifiers() == Qt.ShiftModifier

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
            if len(ch) == 4:
                r, c, old, new = ch
            elif len(ch) == 3:
                r, c, old = ch
                new = ""
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
    
    def cut_selection(self):
        self.copy_selection()
        selected = self.selectedIndexes()
        for idx in selected:
            item = self.item(idx.row(), idx.column())
            if item:
                self.undo_stack.append((idx.row(), idx.column(), item.text()))
                item.setText("")
        self.redo_stack.clear()

    def perform_redo(self):
        if not self.redo_stack:
            return
        entry = self.redo_stack.pop()
        entries = entry if isinstance(entry, list) else [entry]
        reverse_changes = []
        for ch in entries:
            if len(ch) == 4:
                r, c, old, new = ch
            elif len(ch) == 3:
                r, c, old = ch
                new = ""
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
        matrix = [r.split("\t") for r in rows]
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                matrix[i][j] = matrix[i][j].replace("\\n", "\n")
        changes = []
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
                if r_idx < self.rowCount() and c_idx < self.columnCount():
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
            for i, row_vals in enumerate(matrix):
                for j, val in enumerate(row_vals):
                    r_idx = start_row + i
                    c_idx = start_col + j
                    if r_idx < self.rowCount() and c_idx < self.columnCount():
                        item = self.item(r_idx, c_idx)
                        old_val = item.text() if item else ""
                        if old_val != val:
                            changes.append((r_idx, c_idx, old_val, val))
                            if item:
                                item.setText(val)
                            else:
                                self.setItem(r_idx, c_idx, QTableWidgetItem(val))
        if changes:
            self.undo_stack.append(changes)
            self.redo_stack.clear()
            
class CellEditor(QTextEdit):
    def keyPressEvent(self, event):
        cursor = self.textCursor()
        shift_pressed = event.modifiers() & Qt.ShiftModifier

        if event.key() == Qt.Key_Up:
            if shift_pressed:
                cursor.setPosition(0, QTextCursor.KeepAnchor)
            else:
                cursor.setPosition(0)
            self.setTextCursor(cursor)
            return

        elif event.key() == Qt.Key_Down:
            if shift_pressed:
                cursor.setPosition(len(self.toPlainText()), QTextCursor.KeepAnchor)
            else:
                cursor.setPosition(len(self.toPlainText()))
            self.setTextCursor(cursor)
            return

        super().keyPressEvent(event)

class CSVEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.debug_enabled = False
        self.setWindowTitle("CSV Editor")
        self.resize(1400, 820)
        self.df = None
        self.filtered_df = None
        self.pdf_text = ""
        self.pdf_matches = []
        self.current_match_index = -1
        self.csv_filename = ""
        self.pdf_filename = ""
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        pdf_controls = QHBoxLayout()
        self.load_pdf_btn = QPushButton("Load PDF")
        self.cancel_pdf_btn = QPushButton("Cancel PDF")
        pdf_controls.addWidget(self.load_pdf_btn)
        pdf_controls.addWidget(self.cancel_pdf_btn)
        left_layout.addLayout(pdf_controls)

        pdf_search_layout = QHBoxLayout()
        self.pdf_search = QLineEdit()
        self.pdf_search.setPlaceholderText("Search PDF... (press Enter)")
        self.pdf_clear = QPushButton("Clear Search")
        self.prev_match_btn = QPushButton("Previous")
        self.next_match_btn = QPushButton("Next")
        pdf_search_layout.addWidget(self.pdf_search)
        pdf_search_layout.addWidget(self.pdf_clear)
        pdf_search_layout.addWidget(self.prev_match_btn)
        pdf_search_layout.addWidget(self.next_match_btn)
        left_layout.addLayout(pdf_search_layout)

        self.pdf_viewer = QTextEdit()
        self.pdf_viewer.setReadOnly(True)
        left_layout.addWidget(self.pdf_viewer)

        right_layout = QVBoxLayout()
        csv_top_layout = QHBoxLayout()
        self._btn = QPushButton("Load CSV")
        self.save_csv_btn = QPushButton("Save CSV")
        csv_top_layout.addWidget(self._btn)
        csv_top_layout.addWidget(self.save_csv_btn)
        self.rename_csv_btn = QPushButton("Rename CSV")
        csv_top_layout.addWidget(self.rename_csv_btn)
        self.rename_csv_btn.clicked.connect(self.rename_csv)
        right_layout.addLayout(csv_top_layout)
        self.validate_btn = QPushButton("Validate Answers")
        csv_top_layout.addWidget(self.validate_btn)
        self.structure_validate_btn = QPushButton("Validate Structure")
        csv_top_layout.addWidget(self.structure_validate_btn)
        self.clean_multiline_btn = QPushButton("Clean Multilines")
        csv_top_layout.addWidget(self.clean_multiline_btn)

        csv_search_layout = QHBoxLayout()
        self.csv_search = QLineEdit()
        self.csv_search.setPlaceholderText("Search CSV...")
        self.csv_clear = QPushButton("Clear")
        csv_search_layout.addWidget(self.csv_search)
        csv_search_layout.addWidget(self.csv_clear)
        right_layout.addLayout(csv_search_layout)

        self.csv_status_label = QLabel("")
        self.csv_status_label.setStyleSheet("color: green;")
        right_layout.addWidget(self.csv_status_label)
        
        self.file_info_label = QLabel("PDF: - | CSV: - | Questions: -")
        self.file_info_label.setStyleSheet("color: darkgreen; font-weight: bold;")
        right_layout.addWidget(self.file_info_label)

        self.row_info_label = QLabel("Row: -")
        self.row_info_label.setStyleSheet("color: blue; font-weight: bold;")
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
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        right_layout.addWidget(self.table)
        
        self.table.itemChanged.connect(self.on_table_item_changed)

        row_ops = QHBoxLayout()
        self._above_btn = QPushButton("Add Row Above")
        self._below_btn = QPushButton("Add Row Below")
        self.delete_row_btn = QPushButton("Delete Selected Row(s)")
        self.remove_duplicates_btn = QPushButton("Remove Duplicates")
        self.missing_only_btn = QPushButton("Missing Only")
        self.show_all_btn = QPushButton("Show All")
        row_ops.addWidget(self._above_btn)
        row_ops.addWidget(self._below_btn)
        row_ops.addWidget(self.delete_row_btn)
        row_ops.addWidget(self.remove_duplicates_btn)
        row_ops.addWidget(self.missing_only_btn)
        row_ops.addWidget(self.show_all_btn)
        right_layout.addLayout(row_ops)
        
        col_ops = QHBoxLayout()
        self.add_col_left_btn = QPushButton("Insert Column(s) Left")
        self.add_col_right_btn = QPushButton("Insert Column(s) Right")
        self.del_col_btn = QPushButton("Delete Selected Column(s)")
        col_ops.addWidget(self.add_col_left_btn)
        col_ops.addWidget(self.add_col_right_btn)
        col_ops.addWidget(self.del_col_btn)
        right_layout.addLayout(col_ops)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)

        self.load_pdf_btn.clicked.connect(self.load_pdf)
        self.cancel_pdf_btn.clicked.connect(self.cancel_pdf)
        self.pdf_search.returnPressed.connect(self.search_pdf)
        self.pdf_clear.clicked.connect(self.clear_pdf_search)
        self.prev_match_btn.clicked.connect(lambda: self.navigate_match(-1))
        self.next_match_btn.clicked.connect(lambda: self.navigate_match(1))

        self._btn.clicked.connect(self.load_csv)
        self.save_csv_btn.clicked.connect(self.save_csv)
        self.validate_btn.clicked.connect(self.validate_answers)
        self.structure_validate_btn.clicked.connect(self.validate_structure)
        self.clean_multiline_btn.clicked.connect(self.clean_multiline_cells)
        self.csv_search.returnPressed.connect(self.search_csv)
        self.csv_clear.clicked.connect(self.clear_search)

        self._above_btn.clicked.connect(lambda: self.insert_row(relative_position="above"))
        self._below_btn.clicked.connect(lambda: self.insert_row(relative_position="below"))
        self.delete_row_btn.clicked.connect(self.delete_selected_rows)
        self.add_col_left_btn.clicked.connect(self.add_columns_left)
        self.add_col_right_btn.clicked.connect(self.add_columns_right)
        self.del_col_btn.clicked.connect(self.delete_selected_columns)
        self.remove_duplicates_btn.clicked.connect(self.remove_duplicates)
        self.missing_only_btn.clicked.connect(self.show_missing_only)
        self.show_all_btn.clicked.connect(self.show_all_data)
        
        self.table.currentItemChanged.connect(self.update_editor_from_cell)
        self.table.currentItemChanged.connect(self.update_row_info)
        self.table.currentItemChanged.connect(self.sync_pdf_with_selected_cell)

        self.csv_search.keyPressEvent = lambda e, w=self.csv_search: self.search_bar_keypress(w, e)
        self.pdf_search.keyPressEvent = lambda e, w=self.pdf_search: self.search_bar_keypress(w, e)
        self.table.currentItemChanged.connect(self.sync_pdf_with_csv)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            self.save_csv()
            return
        super().keyPressEvent(event)
        
    def update_row_info(self, current, previous):
        if current:
            self.row_info_label.setText(f"Row: {current.row() + 1}")
        else:
            self.row_info_label.setText("Row: -")

    def search_bar_keypress(self, widget, event):
        ctrl = event.modifiers() == Qt.ControlModifier
        shift = event.modifiers() == Qt.ShiftModifier
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
        current = self.pdf_matches[self.current_match_index]
        selection = QTextEdit.ExtraSelection()
        cursor = self.pdf_viewer.textCursor()
        cursor.setPosition(current.start())
        cursor.setPosition(current.end(), QTextCursor.KeepAnchor)
        selection.cursor = cursor
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("orange"))
        selection.format = fmt
        self.pdf_viewer.setExtraSelections([selection])
        self.pdf_viewer.setTextCursor(cursor)

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
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Data Files (*.csv *.xlsx *.xls *.ods);;All Files (*)"
        )
        if not file_path:
            return
        
        try:
            if file_path.lower().endswith((".xlsx", ".xls", ".ods")):
                excel_df = pd.read_excel(file_path, engine="openpyxl" if file_path.lower().endswith((".xlsx", ".xls")) else None)
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

        except Exception as e:
            self.csv_status_label.setText(f"Error loading CSV: {e}")
            self.df = None
            return
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

    def validate_answers(self):
        if self.df is None or self.df.empty:
            self.csv_status_label.setText("No CSV loaded.")
            return
    
        self.update_dataframe_from_table()
    
        required_cols = ["Answer"]
        option_cols = [c for c in self.df.columns if c.lower().startswith("option")]
    
        for col in required_cols + option_cols:
            if col not in self.df.columns:
                QMessageBox.warning(self, "Missing Columns", f"Column '{col}' not found in CSV.")
                return
    
        invalid_rows = []
        for i, row in self.df.iterrows():
            ans = str(row["Answer"]).strip()
            if ans == "" or pd.isna(ans):
                continue
            options = [str(row[c]).strip() for c in option_cols if c in self.df.columns]
            if ans not in options:
                invalid_rows.append(i + 1)
    
        if invalid_rows:
            msg = f"⚠️ {len(invalid_rows)} invalid row(s): " + ", ".join(map(str, invalid_rows))
            self.csv_status_label.setText(msg)
        else:
            self.csv_status_label.setText("✅ All answers match one of the options!")
            
    def validate_structure(self):
        if self.df is None or self.df.empty:
            self.csv_status_label.setText("No CSV loaded.")
            return
    
        self.update_dataframe_from_table()
    
        issues = []
        option_cols = [c for c in self.df.columns if c.lower().startswith("option")]
        required_cols = ["Question", "Answer"]
    
        for col in required_cols + option_cols:
            if col not in self.df.columns:
                continue
            missing_rows = self.df[self.df[col].astype(str).str.strip().eq("")].index + 1
            if len(missing_rows) > 0:
                issues.append(f"{col}: Missing data in rows {', '.join(map(str, missing_rows))}")
    
        dup_rows = []
        for i, row in self.df.iterrows():
            opts = [str(row[c]).strip() for c in option_cols if c in self.df.columns]
            opts_clean = [o for o in opts if o and o.lower() != "nan"]
            if len(opts_clean) != len(set(opts_clean)):
                dup_rows.append(i + 1)
        if dup_rows:
            issues.append(f"Duplicate options found in rows {', '.join(map(str, dup_rows))}")
    
        malformed = []
        for i, ans in enumerate(self.df["Answer"]):
            text = str(ans).strip()
            if len(text.splitlines()) > 1 or len(text.split("?")) > 2 or len(text) > 200:
                malformed.append(i + 1)
        if malformed:
            issues.append(f"Suspicious 'Answer' content in rows {', '.join(map(str, malformed))}")
    
        short_q = self.df[self.df["Question"].astype(str).str.len() < 5].index + 1
        if len(short_q) > 0:
            issues.append(f"Very short questions in rows {', '.join(map(str, short_q))}")
    
        if issues:
            msg = "⚠️ Data validation issues detected: " + "; ".join(issues)
            self.csv_status_label.setText(msg)
        else:
            self.csv_status_label.setText("✅ No structural issues found.")
            
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
        self.csv_status_label.setText(f"🧹 Cleaned {cleaned_count} cell(s) (removed newlines & extra spaces).")

    def update_dataframe_from_table(self):
        if self.df is None:
            return
    
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        current_df = self.filtered_df if self.filtered_df is not None else self.df
    
        if cols != len(current_df.columns):
            self.csv_status_label.setText("Column count mismatch; cannot update dataframe.")
            return
    
        new_data = []
        for r in range(rows):
            row_vals = []
            for c in range(cols):
                item = self.table.item(r, c)
                val = item.text() if item else ""
                if isinstance(val, str) and val.strip().lower() in ["", "nan", "none", "na"]:
                    val = pd.NA
                row_vals.append(val)
            new_data.append(row_vals)
    
        try:
            unique_cols = pd.Index(current_df.columns).drop_duplicates(keep="first")
            new_df = pd.DataFrame(new_data, columns=unique_cols, index=current_df.index)
        except Exception as e:
            self.csv_status_label.setText(f"Error updating dataframe: {e}")
            return
    
        base_df = self.df
    
        if self.filtered_df is not None:
            for idx in new_df.index:
                if idx in base_df.index:
                    for col in new_df.columns:
                        new_val = new_df.at[idx, col]
                        orig_dtype = base_df[col].dtype
                        try:
                            if pd.isna(new_val):
                                base_df.at[idx, col] = pd.NA
                            elif pd.api.types.is_integer_dtype(orig_dtype):
                                base_df.at[idx, col] = int(new_val)
                            elif pd.api.types.is_float_dtype(orig_dtype):
                                base_df.at[idx, col] = float(new_val)
                            else:
                                base_df.at[idx, col] = str(new_val)
                        except Exception:
                            base_df.at[idx, col] = str(new_val)
    
            self.filtered_df = base_df.loc[new_df.index]
        else:
            self.df = new_df

    def commit_editor_changes(self):
        current = self.table.currentItem()
        if current is not None:
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
        self.update_cell_from_editor()
        self.commit_editor_changes()
    
        if not hasattr(self, "current_csv_path") or not self.current_csv_path:
            self.csv_status_label.setText("❌ No CSV file loaded.")
            return
    
        if self.df is None or self.df.empty:
            self.csv_status_label.setText("❌ Nothing to save.")
            return
    
        try:
            self.update_dataframe_from_table()
            self.df.to_csv(self.current_csv_path, index=False)
            self.csv_status_label.setText(f"✅ Saved successfully to {self.current_csv_path}")
            print(f"[DEBUG] CSV saved to: {self.current_csv_path}")
        except Exception as e:
            self.csv_status_label.setText(f"❌ Error saving: {e}")
            print("[DEBUG] Save failed:", e)
        print("[DEBUG] First few df rows before save:")
        print(self.df.head())
        
    def rename_csv(self):
        if not hasattr(self, "current_csv_path") or not self.current_csv_path:
            self.csv_status_label.setText("❌ No CSV file loaded.")
            return
    
        current_name = self.csv_filename
        new_name, ok = QInputDialog.getText(
            self, "Rename CSV",
            f"Enter new name (or leave blank for auto-update):",
            text=current_name
        )
        if not ok:
            return
    
        if new_name.strip() == "":
            base_name = f"questions_{len(self.df)}.csv"
            new_path = "/".join(self.current_csv_path.split("/")[:-1] + [base_name])
        else:
            new_path = "/".join(self.current_csv_path.split("/")[:-1] + [new_name.strip()])
    
        try:
            import os
            os.rename(self.current_csv_path, new_path)
            self.current_csv_path = new_path
            self.csv_filename = new_path.split("/")[-1]
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
        filtered = self.df[self.df.apply(lambda r: r.astype(str).str.contains(query, case=False).any(), axis=1)]
        self.populate_table(filtered)

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
        
        text = self.cell_editor.toPlainText().strip()
        row, col = current.row(), current.column()
        
        if row >= len(self.df.index) or col >= len(self.df.columns):
            print(f"[DEBUG] Skipping update_cell_from_editor → invalid (row={row}, col={col})")
            return
        
        if col >= len(self.df.columns):
            print(f"[DEBUG] Skipping on_table_item_changed → invalid column index {col}")
            return
        col_name = self.df.columns[col]
        current.setText(text)
    
        try:
            self.df.at[row, col_name] = text
            print(f"[DEBUG] update_cell_from_editor → df[{row},{col_name!r}] updated.")
        except Exception as e:
            print("[DEBUG] Failed to update df from editor:", e)
                
    def on_table_item_changed(self, item):
        if self.df is None:
            return
        row, col = item.row(), item.column()
        text = item.text()
    
        try:
            col_name = self.df.columns[col]
    
            if text.strip() == "":
                self.df.at[row, col_name] = pd.NA
                return
    
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
    
        except Exception as e:
            self.df.at[row, self.df.columns[col]] = text

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
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.edit_column_header)
        
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
        self.csv_status_label.setText(f"Deleted {len(selected_rows)} row(s).")
        self.update_file_info_label()
        
    def add_columns_left(self):
        self._insert_columns(position="left")

    def add_columns_right(self):
        self._insert_columns(position="right")

    def _insert_columns(self, position="right"):
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
    
        n, ok = QInputDialog.getInt(self, f"Insert Column(s) {position.title()}",
                                    f"Number of columns to insert to the {position}:", 1, 1, 100)
        if not ok:
            return
    
        base_name = "NewColumn"
        for i in range(n):
            col_name = f"{base_name}_{insert_pos + i + 1}"
            self.df.insert(insert_pos + i, col_name, "")
    
        self.populate_table(self.df)
        self.csv_status_label.setText(f"Inserted {n} column(s) to the {position}.")
        self.update_file_info_label()
        
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
        self.populate_table(self.df)
        self.csv_status_label.setText(f"Deleted {len(selected_cols)} column(s).")
        self.update_file_info_label()

    def insert_row(self, relative_position="below"):
        if self.df is None or self.df.empty:
            return
        self.update_dataframe_from_table()
        selected = self.table.currentRow()
        if selected < 0:
            self.csv_status_label.setText("Select a row first.")
            return
        n, ok = QInputDialog.getInt(self, "Add Rows", "Number of rows to insert:", 1, 1, 1000, 1)
        if not ok:
            return
        new_rows = []
        for _ in range(n):
            new_row = {col: "" for col in self.df.columns}
            new_rows.append(new_row)
        new_df = pd.DataFrame(new_rows, columns=self.df.columns)
        insert_index = selected if relative_position == "above" else selected + 1
        self.df = pd.concat([self.df.iloc[:insert_index], new_df, self.df.iloc[insert_index:]], ignore_index=True)
        if "Q#" in self.df.columns:
            self.df["Q#"] = range(1, len(self.df) + 1)
        self.populate_table(self.df)
        self.table.selectRow(insert_index)
        self.update_file_info_label()

    def remove_duplicates(self):
        if self.df is None:
            return
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=["Question"]).reset_index(drop=True)
        self.df["Q#"] = range(1, len(self.df)+1)
        self.populate_table(self.df)
        removed = before - len(self.df)
        self.csv_status_label.setText(f"Removed {removed} duplicate(s).")
        self.update_file_info_label()

    def normalize_missing(self):
        if self.df is None:
            return
        cols_to_check = [c for c in self.df.columns if c != "Q#"]
        self.df[cols_to_check] = self.df[cols_to_check].replace(["", " ", "nan", "NaN", "None", "NA", "na"], pd.NA)

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

    def update_file_info_label(self):
        pdf_name = self.pdf_filename if self.pdf_filename else "-"
        csv_name = self.csv_filename if self.csv_filename else "-"
        count = len(self.df) if self.df is not None else 0
        self.file_info_label.setText(f"PDF: {pdf_name} | CSV: {csv_name} | Questions: {count}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVEditor()
    window.show()
    sys.exit(app.exec_())