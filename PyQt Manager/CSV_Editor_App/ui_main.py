import sys
import os
import json
import re
import pandas as pd
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, QTextEdit, QPlainTextEdit, QMessageBox
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QKeyEvent
from PyQt5.QtCore import Qt, QEvent
from modules.table_widget import ExcelTable, SmartTextEdit
from modules.csv_manager import CSVManager
from modules.pdf_manager import PDFLoaderThread
from features.validators import Validator
from modules.row_column_ops import RowColumnOps

class SmartLineEdit(QLineEdit):
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Home, Qt.Key_End):
            cursor_pos = 0 if event.key() == Qt.Key_Home else len(self.text())
            if event.modifiers() & Qt.ControlModifier:
                self.setSelection(0, len(self.text()) if event.key() == Qt.Key_Home else len(self.text()) - cursor_pos)
            else:
                self.setCursorPosition(cursor_pos)
        else:
            super().keyPressEvent(event)

class CSVEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV + PDF Editor (Refactored Advanced)")
        self.resize(1500, 900)
        self.csv = CSVManager()
        self.pdf_thread = None
        self.pdf_path = ""
        self.validator = Validator()
        self.ops = RowColumnOps()
        self.dark_mode_enabled = False
        self.session_file = "last_session.json"
        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        right = QVBoxLayout()
        self.load_pdf_btn = QPushButton("Load PDF")
        self.pdf_search = SmartLineEdit(); self.pdf_search.setPlaceholderText("Search PDF...")
        self.prev_pdf = QPushButton("◀"); self.next_pdf = QPushButton("▶")
        search_bar = QHBoxLayout()
        search_bar.addWidget(self.pdf_search); search_bar.addWidget(self.prev_pdf); search_bar.addWidget(self.next_pdf)
        self.csv_col_search = SmartLineEdit(); self.csv_col_search.setPlaceholderText("Search CSV Column...")
        self.col_pick = SmartLineEdit(); self.col_pick.setPlaceholderText("Column name")
        col_search = QHBoxLayout()
        col_search.addWidget(self.col_pick); col_search.addWidget(self.csv_col_search)
        right.addLayout(col_search)
        self.pdf_viewer = QTextEdit(); self.pdf_viewer.setReadOnly(True)
        left.addWidget(self.load_pdf_btn); left.addLayout(search_bar); left.addWidget(self.pdf_viewer)
        top = QHBoxLayout()
        self.load_csv_btn = QPushButton("Load CSV")
        self.save_csv_btn = QPushButton("Save CSV")
        self.validate_btn = QPushButton("Validate Answers")
        self.structure_btn = QPushButton("Validate Structure")
        top.addWidget(self.load_csv_btn); top.addWidget(self.save_csv_btn)
        top.addWidget(self.validate_btn); top.addWidget(self.structure_btn)
        self.bulk_find_input = SmartLineEdit(); self.bulk_find_input.setPlaceholderText("Find")
        self.bulk_replace_input = SmartLineEdit(); self.bulk_replace_input.setPlaceholderText("Replace")
        self.bulk_apply_btn = QPushButton("Apply Replace")
        top.addWidget(self.bulk_find_input); top.addWidget(self.bulk_replace_input); top.addWidget(self.bulk_apply_btn)
        self.autofill_btn = QPushButton("Auto-fill from PDF"); top.addWidget(self.autofill_btn)
        self.export_btn = QPushButton("Export"); top.addWidget(self.export_btn)
        self.dark_mode = QPushButton("Dark Mode"); top.addWidget(self.dark_mode)
        right.addLayout(top)
        rowtools = QHBoxLayout()
        self.missing_btn = QPushButton("Missing Only"); self.show_all_btn = QPushButton("Show All")
        self.dupe_btn = QPushButton("Remove Duplicates"); self.add_row_btn = QPushButton("Add Row"); self.del_row_btn = QPushButton("Delete Row")
        rowtools.addWidget(self.missing_btn); rowtools.addWidget(self.show_all_btn)
        rowtools.addWidget(self.dupe_btn); rowtools.addWidget(self.add_row_btn); rowtools.addWidget(self.del_row_btn)
        right.addLayout(rowtools)
        coltools = QHBoxLayout()
        self.add_col_l = QPushButton("Add Col Left"); self.add_col_r = QPushButton("Add Col Right")
        self.del_col = QPushButton("Delete Col"); self.sort_up = QPushButton("Sort ↑"); self.sort_down = QPushButton("Sort ↓")
        self.freeze_col_btn = QPushButton("Freeze 1st Col")
        coltools.addWidget(self.add_col_l); coltools.addWidget(self.add_col_r); coltools.addWidget(self.del_col)
        coltools.addWidget(self.sort_up); coltools.addWidget(self.sort_down); coltools.addWidget(self.freeze_col_btn)
        right.addLayout(coltools)
        self.cell_editor = SmartTextEdit()
        self.table = ExcelTable()
        self.stats_panel = QTextEdit(); self.stats_panel.setReadOnly(True)
        right.addWidget(self.cell_editor); right.addWidget(self.table); right.addWidget(self.stats_panel)
        layout.addLayout(left, 2); layout.addLayout(right, 4)
        self.pdf_hits = []; self.pdf_pos = -1
        self.load_pdf_btn.clicked.connect(self.load_pdf)
        self.pdf_search.returnPressed.connect(self.search_pdf)
        self.prev_pdf.clicked.connect(lambda: self.move_pdf(-1)); self.next_pdf.clicked.connect(lambda: self.move_pdf(+1))
        self.load_csv_btn.clicked.connect(self.load_csv); self.save_csv_btn.clicked.connect(self.save_csv)
        self.validate_btn.clicked.connect(self.run_validate_answers); self.structure_btn.clicked.connect(self.run_structure_check)
        self.missing_btn.clicked.connect(self.show_missing_only); self.show_all_btn.clicked.connect(self.show_all_rows)
        self.dupe_btn.clicked.connect(self.remove_dupes); self.add_row_btn.clicked.connect(self.insert_row); self.del_row_btn.clicked.connect(self.delete_row)
        self.add_col_l.clicked.connect(lambda: self.insert_col(True)); self.add_col_r.clicked.connect(lambda: self.insert_col(False))
        self.del_col.clicked.connect(self.delete_col); self.sort_up.clicked.connect(lambda: self.sort_col(True)); self.sort_down.clicked.connect(lambda: self.sort_col(False))
        self.freeze_col_btn.clicked.connect(lambda: self.table.freeze_first_column())
        self.csv_col_search.returnPressed.connect(self.search_column)
        self.bulk_apply_btn.clicked.connect(self.bulk_replace); self.autofill_btn.clicked.connect(self.autofill_from_pdf)
        self.export_btn.clicked.connect(self.export_file)
        self.dark_mode.clicked.connect(self.theme)
        self.load_session()

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv *.xlsx *.xls)")
        if path and self.csv.load_csv_file(path):
            self.csv.populate_table(self.table, self.csv.df)
            self.update_stats()
            self.save_session()

    def save_csv(self):
        self.csv.update_from_table(self.table)
        self.csv.save()
        self.save_session()
        self.update_stats()

    def load_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if not path: return
        self.pdf_path = path
        self.load_pdf_path(path)
        self.save_session()

    def load_pdf_path(self, path):
        if not path or not os.path.exists(path): return
        self.pdf_path = path
        self.pdf_viewer.setText("Loading PDF...")
        self.pdf_thread = PDFLoaderThread(path)
        self.pdf_thread.finished.connect(lambda txt: self.pdf_viewer.setText(txt))
        self.pdf_thread.start()

    def search_pdf(self):
        txt = self.pdf_search.text().strip()
        body = self.pdf_viewer.toPlainText()
        if not txt or not body: self.pdf_hits = []; self.pdf_pos = -1; self.pdf_viewer.setExtraSelections([]); return
        try: self.pdf_hits = list(re.finditer(re.escape(txt), body, re.IGNORECASE))
        except re.error: self.pdf_hits = list(re.finditer(re.escape(txt), body))
        if not self.pdf_hits: self.pdf_pos = -1; self.pdf_viewer.setExtraSelections([]); return
        self.pdf_pos = 0; self.highlight_pdf()

    def move_pdf(self, step):
        if not self.pdf_hits: return
        self.pdf_pos = (self.pdf_pos + step) % len(self.pdf_hits)
        self.highlight_pdf()

    def highlight_pdf(self):
        if not self.pdf_hits or self.pdf_pos < 0: self.pdf_viewer.setExtraSelections([]); return
        match = self.pdf_hits[self.pdf_pos]; start, end = match.start(), match.end()
        cursor = self.pdf_viewer.textCursor(); cursor.setPosition(start); cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.pdf_viewer.setTextCursor(cursor); self.pdf_viewer.ensureCursorVisible()
        selection = QTextEdit.ExtraSelection(); selection.cursor = cursor
        fmt = QTextCharFormat(); fmt.setBackground(QColor("orange")); selection.format = fmt
        self.pdf_viewer.setExtraSelections([selection])

    def run_validate_answers(self):
        result = self.validator.validate_answers(self.csv.df)
        self.dialog(result)

    def run_structure_check(self):
        result = self.validator.validate_structure(self.csv.df)
        self.dialog(result)

    def show_missing_only(self):
        filtered = self.ops.missing_only(self.csv.df)
        self.csv.populate_table(self.table, filtered)
        self.update_stats()

    def show_all_rows(self):
        self.csv.populate_table(self.table, self.csv.df)
        self.update_stats()

    def remove_dupes(self):
        new_df, removed = self.ops.remove_duplicates(self.csv.df)
        self.csv.df = new_df
        self.csv.populate_table(self.table, new_df)
        self.dialog(f"{removed} duplicates removed")
        self.update_stats()

    def insert_row(self):
        row = self.table.currentRow()
        self.csv.df = self.ops.insert_rows(self.csv.df, row, 1)
        self.csv.populate_table(self.table, self.csv.df)
        self.update_stats()

    def delete_row(self):
        row = self.table.currentRow()
        self.csv.df = self.ops.delete_rows(self.csv.df, [row])
        self.csv.populate_table(self.table, self.csv.df)
        self.update_stats()

    def insert_col(self, left=True):
        col = self.table.currentColumn(); idx = col if left else col+1
        if col < 0: return
        self.csv.df = self.ops.insert_columns(self.csv.df, idx, 1)
        self.csv.populate_table(self.table, self.csv.df)
        self.update_stats()

    def delete_col(self):
        cols = list({i.column() for i in self.table.selectedIndexes()})
        if not cols: return
        self.csv.df = self.ops.delete_columns(self.csv.df, cols)
        self.csv.populate_table(self.table, self.csv.df)
        self.update_stats()

    def sort_col(self, ascending=True):
        col = self.table.currentColumn()
        if col < 0: return
        name = self.csv.df.columns[col]
        self.csv.df = self.csv.df.sort_values(by=name, ascending=ascending, na_position="last").reset_index(drop=True)
        self.csv.populate_table(self.table, self.csv.df)
        self.update_stats()

    def search_column(self):
        col = self.col_pick.text().strip(); text = self.csv_col_search.text().strip()
        if not col or col not in self.csv.df.columns: return self.dialog("Invalid column")
        filtered = self.csv.df[self.csv.df[col].astype(str).str.contains(text, case=False, na=False)]
        self.csv.populate_table(self.table, filtered)
        self.update_stats()

    def bulk_replace(self):
        cols_text = self.col_pick.text().strip()
        if not cols_text: return self.dialog("Enter column names (comma-separated)")
        cols = [c.strip() for c in cols_text.split(",")]
        find = self.bulk_find_input.text(); replace = self.bulk_replace_input.text()
        self.csv.df = self.ops.bulk_find_replace(self.csv.df, cols, find, replace)
        self.csv.populate_table(self.table, self.csv.df)
        self.update_stats()

    def autofill_from_pdf(self):
        col = self.col_pick.text().strip()
        if not col or col not in self.csv.df.columns: return self.dialog("Invalid column")
        pdf_text = self.pdf_viewer.toPlainText()
        for idx, val in self.csv.df[col].iteritems():
            if pd.isna(val) or str(val).strip() == "":
                pattern = re.escape(str(idx))
                match = re.search(pattern, pdf_text)
                if match: self.csv.df.at[idx, col] = match.group(0)
        self.csv.populate_table(self.table, self.csv.df)
        self.update_stats()

    def export_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export File", "", "Excel (*.xlsx);;JSON (*.json);;Markdown (*.md)")
        if not path: return
        ext = path.split(".")[-1].lower()
        if ext not in ("xlsx", "json", "md"): return self.dialog("Invalid file extension")
        self.csv.export(path, ext)
        self.dialog(f"File exported as {ext.upper()}")

    def theme(self):
        if not self.dark_mode_enabled:
            dark = """
            QWidget { background:#222; color:white; }
            QLineEdit, QTextEdit { background:#111; color:#0f0; }
            QPushButton { background:#333; color:white; border:1px solid #666; }
            QTableWidget { background:#111; color:white; gridline-color:#555; }
            """
            self.setStyleSheet(dark)
            self.dark_mode.setText("Light Mode")
            self.dark_mode_enabled = True
        else:
            self.setStyleSheet("")
            self.dark_mode.setText("Dark Mode")
            self.dark_mode_enabled = False

    def dialog(self, text):
        QMessageBox.information(self, "Status", str(text))

    def update_stats(self):
        if self.csv.df is None: self.stats_panel.setText(""); return
        total = self.csv.df.size
        missing = self.csv.df.isna().sum().sum()
        duplicates = self.csv.df.duplicated(subset=["Question"]).sum() if "Question" in self.csv.df.columns else 0
        avg_len = self.csv.df.astype(str).applymap(len).mean().mean()
        text = f"Total Cells: {total}\nMissing: {missing}\nDuplicates: {duplicates}\nAvg Cell Length: {avg_len:.2f}"
        self.stats_panel.setText(text)

    def save_session(self):
        data = {"last_csv": self.csv.current_csv_path if self.csv.df is not None else "", "last_pdf": self.pdf_path}
        try:
            with open(self.session_file, "w") as f: json.dump(data, f)
        except: pass

    def load_session(self):
        if not os.path.exists(self.session_file): return
        try:
            with open(self.session_file, "r") as f: data = json.load(f)
            last_csv = data.get("last_csv", ""); last_pdf = data.get("last_pdf", "")
            if last_csv and os.path.exists(last_csv):
                self.csv.load_csv_file(last_csv)
                self.csv.populate_table(self.table, self.csv.df)
            if last_pdf and os.path.exists(last_pdf):
                self.load_pdf_path(last_pdf)
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = CSVEditor()
    editor.show()
    sys.exit(app.exec_())