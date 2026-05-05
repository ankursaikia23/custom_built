import sys
import sqlite3
import pandas as pd
import re
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QTableWidget,
    QTableWidgetItem, QLabel, QHBoxLayout, QSplitter,
    QAbstractItemView, QComboBox, QCompleter, QTextEdit, QMenu, QHeaderView
)
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QTextCursor, QSyntaxHighlighter, QTextCharFormat, QColor, QFont

SQL_KEYWORDS = [
    "SELECT","FROM","WHERE","DISTINCT","ALL","AS",

    "JOIN","INNER","LEFT","RIGHT","FULL","OUTER","CROSS","NATURAL","ON","USING",

    "AND","OR","NOT","IN","EXISTS","BETWEEN","LIKE","GLOB","IS","NULL","ISNULL",

    "GROUP","BY","HAVING","ORDER","LIMIT","OFFSET",

    "ASC","DESC","NULLS","FIRST","LAST",

    "UNION","INTERSECT","EXCEPT",

    "INSERT","INTO","VALUES",
    "UPDATE","SET",
    "DELETE",

    "CREATE","TABLE","ALTER","ADD","DROP",
    "INDEX","VIEW","TRIGGER",

    "PRIMARY","KEY","FOREIGN","REFERENCES",
    "UNIQUE","CHECK","DEFAULT","CASCADE",

    "COUNT","SUM","AVG","MIN","MAX",
    "ROUND","LENGTH","UPPER","LOWER","SUBSTR",
    "COALESCE","IFNULL","CAST",

    "CASE","WHEN","THEN","ELSE","END",

    "OVER","PARTITION","ROWS","RANGE",
    "PRECEDING","FOLLOWING","CURRENT","ROW",

    "WITH","RECURSIVE",

    "BEGIN","COMMIT","ROLLBACK","TRANSACTION",

    "AUTOINCREMENT","ROWID","WITHOUT",
    "PRAGMA","VACUUM","ANALYZE",

    "COLLATE","ESCAPE"
]

class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)    
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#808080"))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"\b(" + "|".join(map(re.escape, SQL_KEYWORDS)) + r")\b"
        self.pattern = re.compile(pattern, re.IGNORECASE)

    def highlightBlock(self, text):
        for match in self.pattern.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.keyword_format)

class SQLTextEdit(QTextEdit):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.completer = None

    def setCompleter(self, completer):
        self.completer = completer
        completer.setWidget(self)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setModel(QStringListModel([]))
        completer.activated.connect(self.insertCompletion)

    def insertCompletion(self, completion):
        tc = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        tc.removeSelectedText()
        tc.insertText(completion + " ")
        self.setTextCursor(tc)

    def extract_table_context(self, text):
        tables = []
        matches = re.findall(r'\bFROM\s+(\w+)|\bJOIN\s+(\w+)', text, re.IGNORECASE)
        for m in matches:
            table = m[0] or m[1]
            if table:
                tables.append(table)
        return tables

    def last_keyword(self, text):
        tokens = re.findall(r'\b\w+\b', text.upper().split()[-1])
        for token in reversed(tokens):
            if token in SQL_KEYWORDS:
                return token
        return None

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            super().keyPressEvent(event)
            return
        if event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            super().keyPressEvent(event)
            return    
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                index = self.completer.popup().currentIndex()
                if index.isValid():
                    self.insertCompletion(index.data())
                self.completer.popup().hide()
                return
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                return
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down) and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            cursor = self.textCursor()
            doc = self.document()    
            current_block = cursor.block()
            first_block = doc.firstBlock()
            last_block = doc.lastBlock()
            if event.key() == Qt.Key.Key_Up:
                if current_block == first_block:
                    cursor.movePosition(QTextCursor.MoveOperation.Start)
                    self.setTextCursor(cursor)
                    return
            if event.key() == Qt.Key.Key_Down:
                if current_block == last_block:
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.setTextCursor(cursor)
                    return
        if event.key() == Qt.Key.Key_Tab:
            if not self.completer:
                self.insertPlainText("    ")
                return    
            tc = self.textCursor()
            tc.select(QTextCursor.SelectionType.WordUnderCursor)
            prefix = tc.selectedText()
            if len(prefix) == 0:
                self.insertPlainText("    ")
                return
            full_text = self.toPlainText()
            context_tables = self.extract_table_context(full_text)
            last_kw = self.last_keyword(full_text)
            suggestions = []
            if last_kw == "SELECT":
                for df in self.app.tables.values():
                    suggestions += df.columns.tolist()
            elif last_kw in ["FROM","JOIN","INTO","UPDATE","TABLE","DROP"]:
                suggestions += list(self.app.tables.keys())
            elif last_kw in ["WHERE","SET","ORDER","GROUP","HAVING","ON"]:
                if context_tables:
                    for table in context_tables:
                        if table in self.app.tables:
                            suggestions += self.app.tables[table].columns.tolist()
            suggestions += SQL_KEYWORDS
            suggestions += list(self.app.tables.keys())
            for df in self.app.tables.values():
                suggestions += df.columns.tolist()
            self.completer.model().setStringList(sorted(set(suggestions)))
            self.completer.setCompletionPrefix(prefix)    
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 20)
            self.completer.complete(cr)
            return
        if event.key() == Qt.Key.Key_Return:
            tc = self.textCursor()
            tc.movePosition(QTextCursor.MoveOperation.StartOfLine)
            tc.select(QTextCursor.SelectionType.LineUnderCursor)
            line = tc.selectedText()
            indent = len(line) - len(line.lstrip(" "))
            super().keyPressEvent(event)
            self.insertPlainText(" " * indent)
            return
        super().keyPressEvent(event)

class CSVSQLApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV SQL Workbench")
        self.setGeometry(100, 100, 1000, 650)
        self.conn = sqlite3.connect(":memory:")
        self.tables = {}
        self.name_map = {}
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        self.load_btn = QPushButton("LOAD CSV(s)")
        self.cancel_btn = QPushButton("CANCEL CSV(s)")
        self.run_btn = QPushButton("RUN QUERY")
        self.clear_btn = QPushButton("CLEAR")
        self.export_btn = QPushButton("EXPORT")
        self.result_info = QLabel("Rows affected: 0 | Columns: 0")
        self.source_info = QComboBox()
        self.source_info.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.source_info.setMinimumContentsLength(30)
        self.result_info.setStyleSheet("""
            QLabel {
                background-color: #2ecc71;
                color: white;
                padding: 6px 12px;
                border-radius: 10px;
                font-weight: bold;
            }
        """)
        self.source_info.setStyleSheet("""
            QComboBox {
                background-color: #27ae60;
                color: white;
                padding: 6px 12px;
                border-radius: 10px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        font = self.load_btn.font()
        font.setBold(True)
        btns = [self.load_btn, self.cancel_btn, self.run_btn, self.clear_btn, self.export_btn]
        for b in btns:
            b.setFont(font)
        max_width = max(b.sizeHint().width() for b in btns) + 30
        self.source_info.setMinimumWidth(max_width)
        for b in btns:
            b.setFixedWidth(max_width)
        self.query_box = SQLTextEdit(self)
        self.highlighter = SQLHighlighter(self.query_box.document())
        self.completer = QCompleter([])
        self.query_box.setCompleter(self.completer)
        menu = QMenu()
        menu.addAction("Export as CSV", self.export_csv)
        menu.addAction("Export as PDF", self.export_pdf)
        self.export_btn.setMenu(menu)
        self.result_table = QTableWidget()
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.horizontalHeader().setStretchLastSection(False)
        self.table_selector = QComboBox()
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Table Mode", "Detail Mode"])
        self.csv_info = QTableWidget()
        self.csv_info.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.csv_info.horizontalHeader().setStretchLastSection(True)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        top_bar.addWidget(self.load_btn)
        top_bar.addWidget(self.cancel_btn)
        top_bar.addWidget(self.run_btn)
        top_bar.addWidget(self.clear_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.source_info)
        top_bar.addWidget(self.result_info)
        top_bar.addWidget(self.export_btn)
        top_widget = QWidget()
        top_widget.setLayout(top_bar)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)
        query_layout.setContentsMargins(6, 6, 6, 6)
        query_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.query_box.setMinimumWidth(700)
        self.query_status = QTextEdit()
        self.query_status.setReadOnly(True)
        query_splitter.addWidget(self.query_box)
        query_splitter.addWidget(self.query_status)
        query_splitter.setSizes([700, 300])
        query_layout.addWidget(query_splitter)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.addWidget(self.table_selector)
        left_layout.addWidget(self.mode_selector)
        left_layout.addWidget(self.csv_info)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.addWidget(self.result_table)
        bottom_splitter.addWidget(left_panel)
        bottom_splitter.addWidget(right_panel)
        self.table_selector.currentIndexChanged.connect(self.update_table_view)
        self.mode_selector.currentIndexChanged.connect(self.update_table_view)
        self.source_info.currentIndexChanged.connect(self.update_source_tooltip)
        main_splitter.addWidget(query_widget)
        main_splitter.addWidget(bottom_splitter)
        self.layout.addWidget(top_widget)
        self.layout.addWidget(main_splitter)
        main_splitter.setSizes([300, 700])
        bottom_splitter.setSizes([250, 550])
        self.setStyleSheet("""
            QWidget { background-color: #f5f7fa; font-size: 13px; }
            QPushButton { background-color: #4a90e2; color: white; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background-color: #357abd; }
            QTextEdit { background: white; border: 1px solid #d0d7de; border-radius: 6px; padding: 6px; }
            QTableWidget { background: white; border: 1px solid #d0d7de; border-radius: 6px; gridline-color: #e5e7eb; }
            QLabel { padding: 4px; color: #333; }
        """)
        self.load_btn.clicked.connect(self.load_csv)
        self.cancel_btn.clicked.connect(self.clear_csvs)
        self.run_btn.clicked.connect(self.run_query)
        self.clear_btn.clicked.connect(self.clear_all)

    def load_csv(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select CSV files", "", "CSV Files (*.csv)")
        for file in files:
            try:
                df = pd.read_csv(file)
                original_table_name = os.path.basename(file).split(".")[0]
                clean_table_name = re.sub(r'\W+', '_', original_table_name).lower()
                original_columns = df.columns.tolist()
                clean_columns = [re.sub(r'\W+', '_', c).lower() for c in original_columns]
                df.columns = clean_columns
                df.to_sql(clean_table_name, self.conn, if_exists="replace", index=False)
                if clean_table_name not in self.tables:
                    self.table_selector.addItem(original_table_name)
                self.tables[clean_table_name] = df
                self.name_map[original_table_name] = {
                    "clean": clean_table_name,
                    "columns": dict(zip(original_columns, clean_columns)),
                    "reverse_columns": dict(zip(clean_columns, original_columns))
                }
            except Exception as e:
                self.query_status.setText(f"Error:\n{str(e)}")
        self.update_table_view()

    def clear_csvs(self):
        self.conn.close()
        self.conn = sqlite3.connect(":memory:")
        self.tables.clear()
        self.name_map.clear()
        self.table_selector.clear()
        self.csv_info.setRowCount(0)
        self.csv_info.setColumnCount(0)
        self.source_info.clear()
        self.source_info.addItem("Source: - | Max Rows: -")
        self.source_info.setItemData(0, "No source", Qt.ItemDataRole.ToolTipRole)
        self.source_info.setToolTip("No source")
        self.update_source_tooltip()
        self.query_status.clear()

    def export_csv(self):
        if self.result_table.rowCount() == 0:
            self.query_status.setText("No data to export")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        rows = self.result_table.rowCount()
        cols = self.result_table.columnCount()
        data = []
        headers = [self.result_table.horizontalHeaderItem(i).text() for i in range(cols)]
        for i in range(rows):
            row = []
            for j in range(cols):
                item = self.result_table.item(i, j)
                row.append(item.text() if item else "")
            data.append(row)
        df = pd.DataFrame(data, columns=headers)
        df.to_csv(path, index=False)

    def export_pdf(self):
        if self.result_table.rowCount() == 0:
            self.query_status.setText("No data to export")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        from reportlab.platypus import SimpleDocTemplate, Table
        rows = self.result_table.rowCount()
        cols = self.result_table.columnCount()
        data = []
        headers = [self.result_table.horizontalHeaderItem(i).text() for i in range(cols)]
        data.append(headers)
        for i in range(rows):
            row = []
            for j in range(cols):
                item = self.result_table.item(i, j)
                row.append(item.text() if item else "")
            data.append(row)
        pdf = SimpleDocTemplate(path)
        table = Table(data)
        pdf.build([table])
        
    def format_name(self, name):
        return name if len(name) <= 30 else name[:27] + "..."
    
    def update_source_tooltip(self):
        index = self.source_info.currentIndex()
        if index >= 0:
            tooltip = self.source_info.itemData(index, Qt.ItemDataRole.ToolTipRole)
            if tooltip:
                self.source_info.setToolTip(tooltip)

    def run_query(self):
        query = self.query_box.toPlainText()
        tables_in_query = re.findall(r'\bFROM\s+(\w+)|\bJOIN\s+(\w+)', query, re.IGNORECASE)
        tables_in_query = [t[0] or t[1] for t in tables_in_query if (t[0] or t[1])]
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            if cursor.description:
                headers = [desc[0] for desc in cursor.description]
            else:
                affected = cursor.rowcount if cursor.rowcount != -1 else 0
                self.result_table.setRowCount(0)
                self.result_table.setColumnCount(0)
                self.result_info.setText(f"Rows affected: {affected} | Columns: 0")
                self.source_info.clear()
                self.source_info.addItem("Source: - | Max Rows: -")
                self.source_info.setItemData(0, "No source", Qt.ItemDataRole.ToolTipRole)
                self.source_info.setToolTip("No source")
                self.query_status.setText(f"Query executed\nRows affected: {affected}")
                return
            rows = cursor.fetchall()
            self.result_table.setRowCount(len(rows))
            self.result_table.setColumnCount(len(headers))
            self.result_table.setHorizontalHeaderLabels(headers)    
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    self.result_table.setItem(i, j, QTableWidgetItem(str(val)))
            self.result_table.resizeColumnsToContents()
            self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.result_info.setText(f"Rows affected: {len(rows)} | Columns: {len(headers)}")
            self.source_info.clear()
            if tables_in_query:
                full_names = []
                for table in set(tables_in_query):
                    if table in self.tables:
                        max_rows = len(self.tables[table])
                        display_name = next((k for k,v in self.name_map.items() if v["clean"] == table), table)
                        short_name = self.format_name(display_name)
                        self.source_info.addItem(f"{short_name} | Rows: {max_rows}")
                        index = self.source_info.count() - 1
                        self.source_info.setItemData(index, display_name, Qt.ItemDataRole.ToolTipRole)
                        full_names.append(display_name)    
                self.source_info.setToolTip("\n".join(full_names))
                self.update_source_tooltip()
            else:
                self.source_info.addItem("Source: - | Max Rows: -")
                self.source_info.setItemData(0, "No source", Qt.ItemDataRole.ToolTipRole)
                self.source_info.setToolTip("No source")
                self.update_source_tooltip()
            self.query_status.setText(f"Query executed successfully\nRows returned: {len(rows)}")
        except Exception as e:
            self.query_status.setText(f"Error:\n{str(e)}")

    def clear_all(self):
        self.query_box.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.result_info.setText("Rows affected: 0 | Columns: 0")
        self.source_info.clear()
        self.source_info.addItem("Source: - | Max Rows: -")
        self.source_info.setItemData(0, "No source", Qt.ItemDataRole.ToolTipRole)
        self.source_info.setToolTip("No source")
        self.update_source_tooltip()
        self.query_status.clear()

    def update_table_view(self):
        original_name = self.table_selector.currentText()
        if original_name not in self.name_map:
            return
        clean_name = self.name_map[original_name]["clean"]
        df = self.tables[clean_name]
        if self.mode_selector.currentText() == "Table Mode":
            self.csv_info.setRowCount(len(df.columns))
            self.csv_info.setColumnCount(2)
            self.csv_info.setHorizontalHeaderLabels(["Column", "Non-Null Rows"])
            reverse_cols = self.name_map[original_name]["reverse_columns"]
            for i, col in enumerate(df.columns):
                count = df[col].count()
                display_name = reverse_cols.get(col, col)
                self.csv_info.setItem(i, 0, QTableWidgetItem(display_name))
                self.csv_info.setItem(i, 1, QTableWidgetItem(str(count)))
        else:
            self.csv_info.setRowCount(len(df))
            self.csv_info.setColumnCount(len(df.columns))
            reverse_cols = self.name_map[original_name]["reverse_columns"]
            headers = [reverse_cols.get(c, c) for c in df.columns]
            self.csv_info.setHorizontalHeaderLabels(headers)
            for i in range(len(df)):
                for j in range(len(df.columns)):
                    self.csv_info.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))
        self.csv_info.resizeColumnsToContents()
        
    def closeEvent(self, event):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to close the application?",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Ok:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    window = CSVSQLApp()
    window.showMaximized()
    app.exec()