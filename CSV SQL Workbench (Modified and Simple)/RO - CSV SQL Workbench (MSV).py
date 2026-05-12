import sys
import sqlite3
import pandas as pd
import re
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QTableWidget,
    QTableWidgetItem, QLabel, QHBoxLayout, QSplitter,
    QAbstractItemView, QComboBox, QCompleter, QTextEdit, QMenu, QHeaderView,
    QDialog, QMessageBox, QLineEdit, QListWidget
)
# from PyQt6.QtWidgets import QPlainTextEdit, QSizePolicy
from PyQt6.QtCore import Qt, QStringListModel, QEvent
from PyQt6.QtGui import QTextCursor, QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from reportlab.platypus import TableStyle, SimpleDocTemplate, Table
from reportlab.lib import colors
# from functools import partial

class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, document, app):
        super().__init__(document)
        self.app = app
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#808080"))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)
        self.pattern = re.compile(r"(?!x)x")
        self._last_keywords = []
        self.update_pattern()

    def update_pattern(self):
        try:
            keywords = self.app.get_keywords()
            keywords = [k.upper() for k in keywords if isinstance(k, str) and k.strip()]
            keywords = sorted(set(keywords), key=len, reverse=True)
            if keywords == self._last_keywords:
                return
            self._last_keywords = keywords
            if not keywords:
                self.pattern = re.compile(r"(?!x)x")
                return
            pattern = r"\b(" + "|".join(map(re.escape, keywords)) + r")\b"
            self.pattern = re.compile(pattern)
        except Exception:
            self.pattern = re.compile(r"(?!x)x")

    def highlightBlock(self, text):
        if not self.pattern:
            return
        try:
            for match in self.pattern.finditer(text):
                self.setFormat(
                    match.start(),
                    match.end() - match.start(),
                    self.keyword_format
                )
        except Exception:
            pass

class SQLTextEdit(QTextEdit):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.completer = None
        self.completer_model = QStringListModel([])

    def setCompleter(self, completer):
        self.completer = completer
        completer.setWidget(self)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setModel(self.completer_model)
        completer.activated.connect(self.insertCompletion)

    def insertCompletion(self, completion):
        if not completion:
            return
        tc = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        if not tc.hasSelection():
            tc.movePosition(
                QTextCursor.MoveOperation.PreviousWord,
                QTextCursor.MoveMode.KeepAnchor
            )
        tc.removeSelectedText()
        tc.insertText(completion + " ")
        self.setTextCursor(tc)

    def extract_table_context(self, text):
        tables = []
        patterns = [
            r'\bFROM\s+([a-zA-Z_]\w*)',
            r'\bJOIN\s+([a-zA-Z_]\w*)',
            r'\bUPDATE\s+([a-zA-Z_]\w*)',
            r'\bINTO\s+([a-zA-Z_]\w*)'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean = str(match).strip().lower()
                if clean and clean not in tables:
                    tables.append(clean)
        return tables

    def last_keyword(self, text):
        cursor_pos = self.textCursor().position()
        tokens = re.findall(r'[A-Z_]+', text[:cursor_pos].upper())
        keywords = set(k.upper() for k in self.app.get_keywords())
        for token in reversed(tokens):
            if token in keywords:
                return token
        return None

    def keyPressEvent(self, event):
        if (
            event.modifiers() &
            Qt.KeyboardModifier.ControlModifier
        ):
            QTextEdit.keyPressEvent(self, event)
            return
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (
                Qt.Key.Key_Enter,
                Qt.Key.Key_Return
            ):
                index = self.completer.popup().currentIndex()
                if index.isValid():
                    self.insertCompletion(index.data())
                self.completer.popup().hide()
                return
            if event.key() in (
                Qt.Key.Key_Up,
                Qt.Key.Key_Down
            ):
                self.completer.popup().keyPressEvent(event)
                return
        if event.key() in (
            Qt.Key.Key_Up,
            Qt.Key.Key_Down
        ):
            cursor = self.textCursor()
            doc = self.document()
            current_block = cursor.block()
            if (
                event.key() == Qt.Key.Key_Up and
                current_block == doc.firstBlock()
            ):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Start,
                        QTextCursor.MoveMode.KeepAnchor
                    )
                else:
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Start
                    )
                self.setTextCursor(cursor)
                return
            if (
                event.key() == Qt.Key.Key_Down and
                current_block == doc.lastBlock()
            ):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    cursor.movePosition(
                        QTextCursor.MoveOperation.End,
                        QTextCursor.MoveMode.KeepAnchor
                    )
                else:
                    cursor.movePosition(
                        QTextCursor.MoveOperation.End
                    )
                self.setTextCursor(cursor)
                return
        if event.key() == Qt.Key.Key_Tab:
            if not self.completer:
                self.insertPlainText("    ")
                return
            tc = self.textCursor()
            tc.select(QTextCursor.SelectionType.WordUnderCursor)
            prefix = tc.selectedText().strip()
            full_text = self.toPlainText()
            context_tables = self.extract_table_context(full_text)
            suggestions = set()
            suggestions.update(self.app.get_keywords())
            suggestions.update(self.app.tables.keys())
            for table_name, df in self.app.tables.items():
                if df is not None and hasattr(df, "columns"):
                    suggestions.update([
                        str(col).strip().lower()
                        for col in df.columns.tolist()
                    ])
            if context_tables:
                for table in context_tables:
                    df = self.app.tables.get(table)
                    if df is not None and hasattr(df, "columns"):
                        suggestions.update([
                            str(col).strip().lower()
                            for col in df.columns.tolist()
                        ])
            filtered = sorted([
                s for s in suggestions
                if str(s).strip() and (
                    not prefix or
                    str(s).lower().startswith(prefix.lower())
                )
            ])
            self.completer_model.setStringList(filtered)
            self.completer.setCompletionPrefix(prefix)
            popup = self.completer.popup()
            popup_width = (
                popup.sizeHintForColumn(0) +
                popup.verticalScrollBar().sizeHint().width() +
                20
            )
            cr = self.cursorRect()
            cr.setWidth(max(150, popup_width))
            self.completer.complete(cr)
            return
        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):
            tc = self.textCursor()
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
        self.sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.tables = {}
        self.name_map = {}
        self.saved_queries = {}
        self.custom_queries_window = None
        self.queries_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_queries.json")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "sql_keywords.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.keyword_data = json.load(f)
        except Exception:
            self.keyword_data = {"SQL": []}
        if os.path.exists(self.queries_path):
            try:
                with open(self.queries_path, "r", encoding="utf-8") as f:
                    self.saved_queries = json.load(f)
            except Exception:
                self.saved_queries = {}
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        self.load_btn = QPushButton("LOAD CSV(s)")
        self.cancel_btn = QPushButton("CANCEL CSV(s)")
        self.run_btn = QPushButton("RUN QUERY")
        self.clear_btn = QPushButton("CLEAR")
        self.help_btn = QPushButton("KEYWORDS")
        self.export_btn = QPushButton("EXPORT")
        self.queries_btn = QPushButton("CUSTOM QUERIES")
        self.buttons = [
            self.load_btn, self.cancel_btn, self.queries_btn, self.run_btn,
            self.clear_btn, self.help_btn, self.export_btn
        ]
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
        for b in self.buttons:
            b.setFont(font)
        self.query_box = SQLTextEdit(self)
        font = QFont("Consolas", 11)
        self.query_box.setFont(font)
        self.highlighter = SQLHighlighter(self.query_box.document(), self)
        self.refresh_highlighter()
        self.completer = QCompleter([])
        self.query_box.setCompleter(self.completer)
        menu = QMenu()
        menu.addAction("Export as CSV", self.export_csv)
        menu.addAction("Export as PDF", self.export_pdf)
        self.export_btn.setMenu(menu)
        self.queries_btn.clicked.connect(self.show_queries_popup)
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.result_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.horizontalHeader().setStretchLastSection(False)
        self.table_selector = QComboBox()
        self.table_selector.addItem("Select Table")
        self.table_selector.setEnabled(False)
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Table Mode", "Detail Mode"])
        self.csv_info = QTableWidget()
        self.csv_info.setAlternatingRowColors(True)
        self.csv_info.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.csv_info.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.csv_info.horizontalHeader().setStretchLastSection(False)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        top_bar.addWidget(self.load_btn)
        top_bar.addWidget(self.cancel_btn)
        top_bar.addWidget(self.queries_btn)
        top_bar.addWidget(self.run_btn)
        top_bar.addWidget(self.clear_btn)
        top_bar.addWidget(self.help_btn)
        top_bar.addWidget(self.export_btn)        
        status_bar = QHBoxLayout()
        status_bar.setSpacing(10)
        status_bar.addWidget(self.source_info, 0)
        status_bar.addWidget(self.result_info, 0)
        status_bar.addStretch(1)
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0,0,0,0)
        top_layout.addLayout(top_bar)
        top_layout.addLayout(status_bar)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)
        query_layout.setContentsMargins(6, 6, 6, 6)
        query_splitter = QSplitter(Qt.Orientation.Horizontal)
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)        
        top_editor_bar = QHBoxLayout()
        top_editor_bar.setContentsMargins(0, 0, 0, 0)        
        self.query_name_tag = QLabel("Untitled")
        self.query_name_tag.setStyleSheet("""
            QLabel {
                background-color: #95a5a6;
                color: white;
                padding: 4px 10px;
                border-radius: 8px;
                font-weight: bold;
            }
        """)
        save_query_btn = QPushButton("Save Query")
        save_query_btn.clicked.connect(self.save_query)
        top_editor_bar.addWidget(self.query_name_tag, alignment=Qt.AlignmentFlag.AlignLeft)
        top_editor_bar.addStretch()
        top_editor_bar.addWidget(save_query_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.query_box.setMinimumWidth(700)
        editor_layout.addLayout(top_editor_bar)
        editor_layout.addWidget(self.query_box)
        self.query_status = QTextEdit()
        self.query_status.setFont(QFont("Consolas", 10))
        self.query_status.setReadOnly(True)
        query_splitter.addWidget(editor_container)
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
        self.layout.addWidget(top_widget, 0)
        self.layout.addWidget(main_splitter, 1)
        main_splitter.setSizes([350, 650])
        bottom_splitter.setSizes([300, 500])
        self.setStyleSheet("""
            QWidget { background-color: #f5f7fa; font-size: 13px; }
            QPushButton { background-color: #4a90e2; color: white; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background-color: #357abd; }
            QTextEdit { background: white; border: 1px solid #d0d7de; border-radius: 6px; padding: 6px; }
            QTableWidget { 
                background: white; 
                border: 1px solid #d0d7de; 
                border-radius: 6px; 
                gridline-color: #e5e7eb;
                selection-background-color: #d3d3d3;
                selection-color: black;
            }
            QLabel { padding: 4px; color: #333; }
        """)
        self.load_btn.clicked.connect(self.load_csv)
        self.cancel_btn.clicked.connect(self.clear_csvs)
        self.run_btn.clicked.connect(self.run_query)
        self.clear_btn.clicked.connect(self.clear_all)
        self.help_btn.clicked.connect(self.show_help)
        self.query_box.setFocus()
        self.current_query_name = None
        self.query_dirty = False
        self.query_box.textChanged.connect(self.track_query_changes)

    def load_csv(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select CSV files",
            "",
            "CSV Files (*.csv);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        files = [
            f for f in files
            if f.lower().endswith(".csv")
        ]
        if not files:
            return
        if self.table_selector.count() == 0:
            self.table_selector.addItem("Select Table")
        if self.source_info.count() == 0:
            self.source_info.addItem("Source: - | Rows: -")
            self.source_info.setItemData(
                0,
                "No source",
                Qt.ItemDataRole.ToolTipRole
            )
        last_loaded_display_name = None
        for file in files:
            try:
                try:
                    df = pd.read_csv(file, low_memory=False)
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(
                            file,
                            low_memory=False,
                            encoding="utf-8-sig"
                        )
                    except UnicodeDecodeError:
                        df = pd.read_csv(
                            file,
                            low_memory=False,
                            encoding="latin1"
                        )
                original_table_name = os.path.splitext(
                    os.path.basename(file)
                )[0]
                clean_table_name = re.sub(
                    r'\W+',
                    '_',
                    original_table_name
                ).lower().strip('_')
                base_name = clean_table_name
                counter = 1
                while clean_table_name in self.tables:
                    clean_table_name = f"{base_name}_{counter}"
                    counter += 1
                original_columns = df.columns.tolist()
                seen = {}
                clean_columns = []
                for col in original_columns:
                    clean = re.sub(
                        r'\W+',
                        '_',
                        str(col)
                    ).lower().strip('_')
                    if not clean:
                        clean = "col"
                    if clean in seen:
                        seen[clean] += 1
                        clean = f"{clean}_{seen[clean]}"
                    else:
                        seen[clean] = 0
                    clean_columns.append(clean)
                df.columns = clean_columns
                df.to_sql(
                    clean_table_name,
                    self.sqlite_conn,
                    if_exists="replace",
                    index=False,
                    method="multi"
                )
                self.tables[clean_table_name] = df
                self.table_selector.setEnabled(True)
                display_name = original_table_name
                counter = 1
                while display_name in self.name_map:
                    display_name = f"{original_table_name}_{counter}"
                    counter += 1
                self.name_map[display_name] = {
                    "clean": clean_table_name,
                    "columns": dict(zip(original_columns, clean_columns)),
                    "reverse_columns": dict(zip(clean_columns, original_columns))
                }
                self.table_selector.addItem(display_name)
                if (
                    self.source_info.count() == 1 and
                    self.source_info.itemText(0) == "Source: - | Rows: -"
                ):
                    self.source_info.clear()
                self.source_info.addItem(
                    f"{display_name} | Rows: {len(df)}"
                )
                self.source_info.setItemData(
                    self.source_info.count() - 1,
                    display_name,
                    Qt.ItemDataRole.ToolTipRole
                )
                last_loaded_display_name = display_name
            except Exception as e:
                self.query_status.setText(f"Error:\n{str(e)}")
        if last_loaded_display_name:
            index = self.table_selector.findText(last_loaded_display_name)
            if index >= 0:
                self.table_selector.setCurrentIndex(index)
        elif self.table_selector.count() > 1:
            self.table_selector.setCurrentIndex(1)
        else:
            self.table_selector.setCurrentIndex(0)
        self.update_table_view()
        self.update_source_tooltip()
        self.set_active_query(None, saved=True)
        
    def get_keywords(self):
        return sorted(set(
            k for k in self.keyword_data.get("SQL", [])
            if isinstance(k, str) and k.strip()
        ))
    
    def refresh_highlighter(self):
        self.highlighter.update_pattern()
        self.highlighter.rehighlight()
        if self.query_box.completer:
            self.query_box.completer.model().setStringList([])
            self.query_box.completer.setCompletionPrefix("")

    def clear_csvs(self):
        try:
            if self.sqlite_conn:
                self.sqlite_conn.close()
        except Exception:
            pass
        self.sqlite_conn = sqlite3.connect(
            ":memory:",
            check_same_thread=False
        )
        self.tables.clear()
        self.name_map.clear()
        self.table_selector.clear()
        self.table_selector.addItem("Select Table")
        self.table_selector.setEnabled(False)
        self.csv_info.clear()
        self.csv_info.setRowCount(0)
        self.csv_info.setColumnCount(0)
        self.source_info.clear()
        self.source_info.addItem("Source: - | Rows: -")
        self.source_info.setItemData(
            0,
            "No source",
            Qt.ItemDataRole.ToolTipRole
        )
        self.source_info.setToolTip("No source")
        self.query_status.clear()
        self.reset_result_table()
        self.update_source_tooltip()

    def export_csv(self):
        if self.result_table.rowCount() == 0:
            self.query_status.setText("No data to export")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not path:
            return    
        rows = self.result_table.rowCount()
        cols = self.result_table.columnCount()
        headers = []
        for i in range(cols):
            item = self.result_table.horizontalHeaderItem(i)
            headers.append(item.text() if item else f"col_{i}")
        data = []
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
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF",
            "",
            "PDF Files (*.pdf)"
        )
        if not path:
            return
        rows = self.result_table.rowCount()
        cols = self.result_table.columnCount()
        headers = []
        for i in range(cols):
            item = self.result_table.horizontalHeaderItem(i)
            headers.append(item.text() if item else f"col_{i}")
        data = [headers]
        max_cell_length = 200
        for i in range(rows):
            row = []
            for j in range(cols):
                item = self.result_table.item(i, j)
                value = item.text() if item else ""
                value = str(value)
                if len(value) > max_cell_length:
                    value = value[:max_cell_length] + "..."
                row.append(value)
            data.append(row)
        try:
            pdf = SimpleDocTemplate(
                path,
                rightMargin=20,
                leftMargin=20,
                topMargin=20,
                bottomMargin=20
            )
            available_width = 540
            col_width = max(60, available_width / max(cols, 1))
            col_widths = [col_width] * cols
            table = Table(
                data,
                colWidths=col_widths,
                repeatRows=1
            )
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP")
            ]))
            pdf.build([table])
            self.query_status.setText("PDF exported successfully")
        except Exception as e:
            self.query_status.setText(f"Error:\n{str(e)}")
        
    def save_query(self):
        text = self.query_box.toPlainText().strip()
        if not text:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Save Query")
        dialog.resize(420, 220)
        layout = QVBoxLayout(dialog)
        mode_dropdown = QComboBox()
        mode_dropdown.addItems(["New Query", "Overwrite Existing Query"])
        query_name_input = QLineEdit()
        query_name_input.setPlaceholderText("Enter query name")
        existing_dropdown = QComboBox()
        existing_dropdown.addItems(sorted(self.saved_queries.keys()))
        existing_dropdown.setVisible(False)
        rename_input = QLineEdit()
        rename_input.setPlaceholderText("Rename query (optional)")
        rename_input.setVisible(False)
        layout.addWidget(mode_dropdown)
        layout.addWidget(query_name_input)
        layout.addWidget(existing_dropdown)
        layout.addWidget(rename_input)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        def update_mode():
            mode = mode_dropdown.currentText()
            if mode == "New Query":
                query_name_input.setVisible(True)
                existing_dropdown.setVisible(False)
                rename_input.setVisible(False)
            else:
                query_name_input.setVisible(False)
                existing_dropdown.setVisible(True)
                rename_input.setVisible(True)
        
        mode_dropdown.currentIndexChanged.connect(update_mode)
        update_mode()
        
        def do_save():
            mode = mode_dropdown.currentText()
            if mode == "New Query":
                final_name = " ".join(query_name_input.text().strip().split())
                if not final_name:
                    QMessageBox.warning(
                        self,
                        "Invalid Name",
                        "Query name cannot be empty"
                    )
                    return
                if final_name in self.saved_queries:
                    reply = QMessageBox.question(
                        self,
                        "Overwrite Query",
                        f"'{final_name}' already exists. Do you want to overwrite it?",
                        QMessageBox.StandardButton.Ok |
                        QMessageBox.StandardButton.Cancel,
                        QMessageBox.StandardButton.Cancel
                    )
                    if reply != QMessageBox.StandardButton.Ok:
                        return
            else:
                selected_query = existing_dropdown.currentText().strip()
                rename_value = " ".join(rename_input.text().strip().split())
                final_name = rename_value if rename_value else selected_query
                if not selected_query:
                    QMessageBox.warning(
                        self,
                        "Invalid Selection",
                        "Please select a query to overwrite"
                    )
                    return
                if (
                    final_name != selected_query and
                    final_name in self.saved_queries
                ):
                    reply = QMessageBox.question(
                        self,
                        "Overwrite Query",
                        f"'{final_name}' already exists. Do you want to overwrite it?",
                        QMessageBox.StandardButton.Ok |
                        QMessageBox.StandardButton.Cancel,
                        QMessageBox.StandardButton.Cancel
                    )
                    if reply != QMessageBox.StandardButton.Ok:
                        return
                if final_name != selected_query:
                    self.saved_queries.pop(selected_query, None)
            current_db = "SQL"
            files = list(self.name_map.keys())
            self.saved_queries[final_name] = {
                "query": text,
                "db": current_db,
                "files": files
            }
            with open(self.queries_path, "w", encoding="utf-8") as f:
                json.dump(self.saved_queries, f, indent=2, ensure_ascii=False)
            self.set_active_query(final_name, saved=True)
            dialog.accept()
        
        save_btn.clicked.connect(do_save)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()
            
    def show_queries_popup(self):
        if self.custom_queries_window:
            if self.custom_queries_window.isMinimized():
                self.custom_queries_window.showNormal()
            self.custom_queries_window.raise_()
            self.custom_queries_window.activateWindow()
            return
        window = QMainWindow(self)
        self.custom_queries_window = window    
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        window.setWindowTitle("Custom Queries")
        window.resize(1000, 700)
        window.setWindowState(Qt.WindowState.WindowMaximized)
        window.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        central = QWidget()
        layout = QVBoxLayout(central)
        window.setCentralWidget(central)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_container = QVBoxLayout()
        left_widget = QWidget()
        left_widget.setLayout(left_container)
        notification_box = QListWidget()
        notification_box.setFixedHeight(40)
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Query",
            "DB",
            "Files",
            "Load",
            "Edit",
            "Delete"
        ])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        header = table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents
        )
        left_container.addWidget(notification_box, 1)
        left_container.addWidget(table, 9)
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        name_input = QLineEdit()
        name_input.setMinimumWidth(250)
        name_input.setSizePolicy(
            name_input.sizePolicy().horizontalPolicy(),
            name_input.sizePolicy().verticalPolicy()
        )
        query_input = QTextEdit()
        self.custom_query_input = query_input
        query_input.installEventFilter(self)    
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        clear_btn = QPushButton("Clear")
        cancel_btn = QPushButton("Close")
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(cancel_btn)
        name_row = QHBoxLayout()
        query_name_label = QLabel("No Query File Loaded")
        query_name_label.setWordWrap(False)
        query_name_label.setMinimumWidth(150)
        query_name_label.setMaximumWidth(350)
        query_name_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        query_name_label.setStyleSheet("""
            QLabel {
                background-color: #95a5a6;
                color: white;
                padding: 6px 10px;
                border-radius: 8px;
                font-weight: bold;
            }
        """)
        name_row.addWidget(QLabel("Query Name"))
        name_row.addStretch()
        name_row.addWidget(query_name_label)
        editor_layout.addLayout(name_row)
        editor_layout.addWidget(name_input)
        editor_layout.addWidget(QLabel("SQL Query"))
        editor_layout.addWidget(query_input)
        editor_layout.addLayout(btn_row)
        splitter.addWidget(left_widget)
        splitter.addWidget(editor_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)
        current_edit = {"name": None}
        unsaved = {"flag": False}
    
        def update_editor_query_tag():
            if current_edit["name"]:
                name = current_edit["name"]
            else:
                name = "No Query File Loaded"
            if unsaved["flag"]:
                name += " *"
            query_name_label.setText(name)
            query_name_label.setToolTip(name)
    
        def notify(msg):
            notification_box.clear()
            notification_box.addItem(msg)
    
        def check_unsaved():
            if unsaved["flag"]:
                reply = QMessageBox.question(
                    window,
                    "Unsaved Changes",
                    "Exit without saving?",
                    QMessageBox.StandardButton.Ok |
                    QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel
                )
                if reply != QMessageBox.StandardButton.Ok:
                    return True
            return False
    
        def load_into_editor(name):
            if check_unsaved():
                return
            data = self.saved_queries.get(name, {})
            query = (
                data.get("query", "")
                if isinstance(data, dict)
                else ""
            )
            name_input.setText(name)
            query_input.setPlainText(query)
            current_edit["name"] = name
            unsaved["flag"] = False
            update_editor_query_tag()
    
        def load_to_main(name):
            if check_unsaved():
                return
            data = self.saved_queries.get(name, {})    
            query = (
                data.get("query", "")
                if isinstance(data, dict)
                else ""
            )
            self.query_box.setPlainText(query)
            self.set_active_query(name, saved=True)
            notify(f"{name} loaded")
    
        def delete_query_inline(name):
            reply = QMessageBox.question(
                window,
                "Delete",
                f"Delete '{name}'?",
                QMessageBox.StandardButton.Ok |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Ok:
                if name in self.saved_queries:
                    del self.saved_queries[name]
                if current_edit["name"] == name:
                    name_input.clear()
                    query_input.clear()
                    current_edit["name"] = None
                    unsaved["flag"] = False
                    update_editor_query_tag()
                with open(self.queries_path, "w", encoding="utf-8") as f:
                    json.dump(self.saved_queries, f, indent=2, ensure_ascii=False)
                refresh_table()
    
        def refresh_table():
            table.setRowCount(len(self.saved_queries))
            for row, (name, data) in enumerate(
                self.saved_queries.items()
            ):
                db_val = (
                    data.get("db", "")
                    if isinstance(data, dict)
                    else ""
                )
                files_val = (
                    data.get("files", [])
                    if isinstance(data, dict)
                    else []
                )
                name_item = QTableWidgetItem(name)
                name_item.setToolTip(name)
                db_item = QTableWidgetItem(db_val)
                db_item.setToolTip(db_val)
                table.setItem(row, 0, name_item)
                table.setItem(row, 1, db_item)
                combo = QComboBox()
                combo.addItems(files_val)
                combo.setToolTip("\n".join(files_val))
                for i, f in enumerate(files_val):
                    combo.setItemData(
                        i,
                        f,
                        Qt.ItemDataRole.ToolTipRole
                    )
                table.setCellWidget(row, 2, combo)
                load_button = QPushButton("Load")
                edit_button = QPushButton("Edit")
                delete_button = QPushButton("Delete")
                load_button.clicked.connect(
                    lambda _, n=name: load_to_main(n)
                )
                edit_button.clicked.connect(
                    lambda _, n=name: load_into_editor(n)
                )
                delete_button.clicked.connect(
                    lambda _, n=name: delete_query_inline(n)
                )
                table.setCellWidget(row, 3, load_button)
                table.setCellWidget(row, 4, edit_button)
                table.setCellWidget(row, 5, delete_button)
    
        def save_edit():
            old_name = current_edit["name"]
            if not old_name:
                return
            new_name = " ".join(
                name_input.text().strip().split()
            )  
            new_query = query_input.toPlainText().strip()
            if not new_name or not new_query:
                return
            data = self.saved_queries.get(old_name, {})    
            if isinstance(data, dict):
                updated = data
                updated["query"] = new_query
            else:
                updated = {
                    "query": new_query,
                    "db": "",
                    "files": []
                }
            if new_name != old_name:
                self.saved_queries.pop(old_name, None)
            self.saved_queries[new_name] = updated
            with open(self.queries_path, "w", encoding="utf-8") as f:
                json.dump(self.saved_queries, f, indent=2, ensure_ascii=False)
            if self.current_query_name == old_name:
                self.set_active_query(new_name, saved=True)
            notify(f"{new_name} edited")
            current_edit["name"] = new_name
            unsaved["flag"] = False
            update_editor_query_tag()
            refresh_table()
    
        def mark_unsaved():
            current_name = current_edit["name"]
            current_query = query_input.toPlainText().strip()
            current_title = " ".join(name_input.text().strip().split())
            if not current_name:
                if current_query or current_title:
                    unsaved["flag"] = True
                else:
                    unsaved["flag"] = False
            else:
                saved_data = self.saved_queries.get(current_name, {})
                saved_query = (
                    saved_data.get("query", "").strip()
                    if isinstance(saved_data, dict)
                    else ""
                )
                saved_name = current_name.strip()
                unsaved["flag"] = (
                    current_query != saved_query or
                    current_title != saved_name
                )
            update_editor_query_tag()
            
        name_input.textChanged.connect(mark_unsaved)
    
        def clear_editor():
            if unsaved["flag"]:
                reply = QMessageBox.question(
                    window,
                    "Unsaved Changes",
                    "Clear without saving?",
                    QMessageBox.StandardButton.Ok |
                    QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel
                )
                if reply != QMessageBox.StandardButton.Ok:
                    return
            name_input.clear()
            query_input.clear()
            current_edit["name"] = None
            unsaved["flag"] = False
            update_editor_query_tag()
    
        def attempt_close():
            if check_unsaved():
                return
            window.close()
    
        save_btn.clicked.connect(save_edit)
        clear_btn.clicked.connect(clear_editor)
        cancel_btn.clicked.connect(attempt_close)
        refresh_table()
    
        def custom_close_event(event):
            if check_unsaved():
                event.ignore()
                return
            self.custom_queries_window = None    
            event.accept()
    
        window.closeEvent = custom_close_event
        
        def resize_event(event):
            update_editor_query_tag()
            QMainWindow.resizeEvent(window, event)
        
        window.resizeEvent = resize_event
    
        def popup_keypress(event):
            if (
                event.modifiers() ==
                Qt.KeyboardModifier.ControlModifier and
                event.key() == Qt.Key.Key_S
            ):
                if current_edit["name"]:
                    save_edit()
                return
            QMainWindow.keyPressEvent(window, event)
            
        query_input.textChanged.connect(mark_unsaved)
        window.keyPressEvent = popup_keypress
        window.show()
        
    def format_name(self, name):
        if not isinstance(name, str):
            return ""
        return name if len(name) <= 30 else name[:27] + "..."
    
    def update_source_tooltip(self):
        index = self.source_info.currentIndex()
        if self.source_info.count() == 0 or index < 0:
            self.source_info.setToolTip("")
            return
        tooltip = self.source_info.itemData(
            index,
            Qt.ItemDataRole.ToolTipRole
        )
        if tooltip and str(tooltip).strip():
            self.source_info.setToolTip(str(tooltip))
        else:
            self.source_info.setToolTip("No source")
                
    def populate_result_table(self, rows, headers):
        self.result_table.setUpdatesEnabled(False)
        self.result_table.clearContents()
        self.result_table.setRowCount(len(rows))
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(rows or []):
            for j in range(len(headers)):
                val = row[j] if j < len(row) and row[j] is not None else ""
                if pd.isna(val):
                    val = ""
                self.result_table.setItem(
                    i,
                    j,
                    QTableWidgetItem(str(val))
                )
        self.result_table.resizeColumnsToContents()
        self.result_table.setUpdatesEnabled(True)

    def run_query(self):
        query = self.query_box.toPlainText().strip()
        if not query:
            self.query_status.setText("No query to execute")
            return
        tables_in_query = re.findall(
            r'\b(?:FROM|JOIN|UPDATE|INTO)\s+["`\[]?([a-zA-Z_][\w]*)["`\]]?',
            query,
            re.IGNORECASE
        )
        cursor = None
        try:
            conn = self.sqlite_conn
            cursor = conn.cursor()
            cursor.execute(query)
            has_result = cursor.description is not None
            if has_result:
                headers = [desc[0] for desc in cursor.description]
                rows = cursor.fetchmany(1000)
                self.populate_result_table(rows, headers)
                self.result_table.horizontalHeader().setSectionResizeMode(
                    QHeaderView.ResizeMode.Interactive
                )
                self.result_info.setText(
                    f"Rows affected: {len(rows)} | Columns: {len(headers)}"
                )
                msg = f"Query executed successfully\nRows returned: {len(rows)}"
                if len(rows) >= 1000:
                    msg += "\nNote: Results limited to 1000 rows"
                self.query_status.setText(msg)
            else:
                conn.commit()
                affected = cursor.rowcount if cursor.rowcount != -1 else 0
                self.reset_result_table()
                self.result_info.setText(
                    f"Rows affected: {affected} | Columns: 0"
                )
                self.query_status.setText(
                    f"Query executed\nRows affected: {affected}"
                )
            self.source_info.blockSignals(True)
            self.source_info.clear()
            self.source_info.blockSignals(False)
            if tables_in_query and self.tables:
                full_names = []
                for table in sorted(set(tables_in_query)):
                    if table in self.tables:
                        max_rows = len(self.tables[table])
                        display_name = next(
                            (
                                k for k, v in self.name_map.items()
                                if v["clean"] == table
                            ),
                            table
                        )
                        short_name = self.format_name(display_name)
                        self.source_info.addItem(
                            f"{short_name} | Rows: {max_rows}"
                        )
                        self.source_info.setItemData(
                            self.source_info.count() - 1,
                            display_name,
                            Qt.ItemDataRole.ToolTipRole
                        )
                        full_names.append(display_name)
                if full_names:
                    self.source_info.setToolTip("\n".join(full_names))
                else:
                    self.source_info.addItem("Source: - | Rows: -")
                    self.source_info.setItemData(
                        0,
                        "No source",
                        Qt.ItemDataRole.ToolTipRole
                    )
                    self.source_info.setToolTip("No source")
            else:
                self.source_info.addItem("Source: - | Rows: -")
                self.source_info.setItemData(
                    0,
                    "No source",
                    Qt.ItemDataRole.ToolTipRole
                )
                self.source_info.setToolTip("No source")
            self.update_source_tooltip()
        except Exception as e:
            self.query_status.setText(f"Error:\n{str(e)}")
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            
    def reset_result_table(self):
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.result_info.setText("Rows affected: 0 | Columns: 0")

    def clear_all(self):
        self.query_box.clear()
        self.set_active_query(None, saved=True)
        self.query_box.setFocus()
        self.reset_result_table()
        self.source_info.clear()
        self.source_info.addItem("Source: - | Rows: -")
        self.source_info.setItemData(
            0,
            "No source",
            Qt.ItemDataRole.ToolTipRole
        )
        self.update_source_tooltip()
        self.query_status.clear()
        
    def show_help(self):
        dialog=QDialog(self)
        dialog.setWindowTitle("SQL Keywords Editor")
        dialog.resize(1000,700)
        layout=QVBoxLayout(dialog)
        text=QTextEdit()
        text.setFont(QFont("Consolas",10))
        text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        if "SQL" in self.keyword_data and isinstance(self.keyword_data["SQL"],list):
            formatted='{\n  "SQL": [\n    '
            line=[]
            max_width=120
            current_len=4
            for keyword in self.keyword_data["SQL"]:
                item=f'"{keyword}"'
                extra=len(item)+(2 if line else 0)
                if current_len+extra>max_width:
                    formatted+=", ".join(line)+",\n    "
                    line=[item]
                    current_len=4+len(item)
                else:
                    line.append(item)
                    current_len+=extra
            if line:
                formatted+=", ".join(line)
            formatted+='\n  ]\n}'
        else:
            formatted=json.dumps(self.keyword_data,indent=2)
        text.setPlainText(formatted)
        btn_row=QHBoxLayout()
        save_btn=QPushButton("Save")
        close_btn=QPushButton("Close")
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(close_btn)
        layout.addWidget(text)
        layout.addLayout(btn_row)
        state={"saved_text":text.toPlainText()}
        duplicate_format=QTextCharFormat()
        duplicate_format.setBackground(QColor("yellow"))
        
        def highlight_duplicates():
            selections=[]
            try:
                parsed=json.loads(text.toPlainText())
                if not isinstance(parsed,dict) or "SQL" not in parsed or not isinstance(parsed["SQL"],list):
                    text.setExtraSelections([])
                    return
                positions={}
                pattern=re.compile(r'"([^"]+)"')
                for match in pattern.finditer(text.toPlainText()):
                    keyword=match.group(1).strip().upper()
                    positions.setdefault(keyword,[]).append((match.start(1),match.end(1)))
                for keyword,ranges in positions.items():
                    if len(ranges)>1:
                        for start,end in ranges:
                            selection=QTextEdit.ExtraSelection()
                            selection.cursor=text.textCursor()
                            selection.cursor.setPosition(start)
                            selection.cursor.setPosition(end,QTextCursor.MoveMode.KeepAnchor)
                            selection.format=duplicate_format
                            selections.append(selection)
            except Exception:
                pass
            text.setExtraSelections(selections)
            
        def normalize_and_validate():
            current_text=text.toPlainText()
            parsed=json.loads(current_text)
            if not isinstance(parsed,dict):
                raise ValueError("Root must be a JSON object")
            if "SQL" not in parsed:
                raise ValueError("Missing 'SQL' key")
            if not isinstance(parsed["SQL"],list):
                raise ValueError("'SQL' must be a list")
            cleaned=[]
            seen=set()
            for item in parsed["SQL"]:
                if not isinstance(item,str):
                    continue
                keyword=item.strip().upper()
                if keyword and keyword not in seen:
                    seen.add(keyword)
                    cleaned.append(keyword)
            parsed={"SQL":cleaned}
            formatted='{\n  "SQL": [\n    '
            line=[]
            max_width=120
            current_len=4
            for keyword in cleaned:
                item=f'"{keyword}"'
                extra=len(item)+(2 if line else 0)
                if current_len+extra>max_width:
                    formatted+=", ".join(line)+",\n    "
                    line=[item]
                    current_len=4+len(item)
                else:
                    line.append(item)
                    current_len+=extra
            if line:
                formatted+=", ".join(line)
            formatted+='\n  ]\n}'
            return parsed,formatted
        
        def save_keywords():
            try:
                parsed,formatted=normalize_and_validate()
            except Exception as e:
                QMessageBox.warning(dialog,"Invalid JSON",f"Error:\n{str(e)}")
                return
            reply=QMessageBox.question(dialog,"Save Keywords","Are you sure?",QMessageBox.StandardButton.Ok|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
            if reply!=QMessageBox.StandardButton.Ok:
                return
            base_dir=os.path.dirname(os.path.abspath(__file__))
            json_path=os.path.join(base_dir,"sql_keywords.json")
            with open(json_path,"w",encoding="utf-8") as f:
                json.dump(parsed,f,indent=2,ensure_ascii=False)
            self.keyword_data=parsed
            self.refresh_highlighter()
            self.completer.model().setStringList([])
            self.query_box.completer_model.setStringList([])
            text.blockSignals(True)
            text.setPlainText(formatted)
            text.blockSignals(False)
            state["saved_text"]=formatted
            highlight_duplicates()
            self.query_status.setText("Keywords saved")
        
        def attempt_close():
            if text.toPlainText()!=state["saved_text"]:
                reply=QMessageBox.question(dialog,"Unsaved Changes","Exit without saving?",QMessageBox.StandardButton.Ok|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
                if reply!=QMessageBox.StandardButton.Ok:
                    return
            dialog.accept()
        
        def keypress(event):
            if event.modifiers()==Qt.KeyboardModifier.ControlModifier and event.key()==Qt.Key.Key_S:
                save_keywords()
                return
            QDialog.keyPressEvent(dialog,event)
            
        def close_event(event):
            if text.toPlainText()!=state["saved_text"]:
                reply=QMessageBox.question(dialog,"Unsaved Changes","Exit without saving?",QMessageBox.StandardButton.Ok|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
                if reply!=QMessageBox.StandardButton.Ok:
                    event.ignore()
                    return
            event.accept()
        
        text.textChanged.connect(highlight_duplicates)
        save_btn.clicked.connect(save_keywords)
        close_btn.clicked.connect(attempt_close)
        dialog.keyPressEvent=keypress
        dialog.closeEvent=close_event
        highlight_duplicates()
        dialog.exec()
        
    def eventFilter(self, obj, event):
        if obj == getattr(self, "custom_query_input", None):
            if event.type() == QEvent.Type.KeyPress:
                if event.key() in (
                    Qt.Key.Key_Up,
                    Qt.Key.Key_Down
                ):
                    cursor = obj.textCursor()
                    doc = obj.document()
                    current_block = cursor.block()
                    first_block = doc.firstBlock()
                    last_block = doc.lastBlock()
    
                    if (
                        event.key() == Qt.Key.Key_Up and
                        current_block == first_block and
                        cursor.positionInBlock() == 0
                    ):
                        cursor.movePosition(
                            QTextCursor.MoveOperation.Start
                        )
                        obj.setTextCursor(cursor)
                        return True
    
                    if (
                        event.key() == Qt.Key.Key_Down and
                        current_block == last_block and
                        cursor.positionInBlock() ==
                        len(current_block.text())
                    ):
                        cursor.movePosition(
                            QTextCursor.MoveOperation.End
                        )
                        obj.setTextCursor(cursor)
                        return True
    
        return super().eventFilter(obj, event)

    def update_table_view(self):
        original_name = self.table_selector.currentText().strip()
        if original_name == "Select Table":
            return
        if original_name not in self.name_map:
            return
        clean_name = self.name_map.get(original_name, {}).get("clean")
        if not clean_name:
            return
        df = self.tables.get(clean_name)
        if df is None:
            return
        reverse_cols = self.name_map[original_name]["reverse_columns"]
        if self.mode_selector.currentText() == "Table Mode":
            self.csv_info.setRowCount(len(df.columns))
            self.csv_info.setColumnCount(2)
            self.csv_info.setHorizontalHeaderLabels(
                ["Column", "Non-Null Rows"]
            )
            for i, col in enumerate(df.columns):
                count = df[col].count()
                display_name = reverse_cols.get(col, col)
                self.csv_info.setItem(
                    i,
                    0,
                    QTableWidgetItem(display_name)
                )
                self.csv_info.setItem(
                    i,
                    1,
                    QTableWidgetItem(str(count))
                )
        else:
            max_rows = min(len(df), 1000)
            self.csv_info.setRowCount(max_rows)
            self.csv_info.setColumnCount(len(df.columns))
            headers = [
                reverse_cols.get(c, c)
                for c in df.columns
            ]
            self.csv_info.setHorizontalHeaderLabels(headers)
            for i in range(max_rows):
                for j in range(len(df.columns)):
                    value = df.iat[i, j]
                    if pd.isna(value):
                        value = ""
                    self.csv_info.setItem(
                        i,
                        j,
                        QTableWidgetItem(str(value))
                    )
        self.csv_info.resizeColumnsToContents()
        
    def update_query_name_tag(self):
        name = self.current_query_name if self.current_query_name else "Untitled"
        if self.query_dirty:
            name += " *"
        self.query_name_tag.setText(name)
    
    def track_query_changes(self):
        current_text = self.query_box.toPlainText().strip()
        if self.current_query_name:
            saved_data = self.saved_queries.get(
                self.current_query_name,
                {}
            )
            saved_query = (
                saved_data.get("query", "").strip()
                if isinstance(saved_data, dict)
                else ""
            )
            self.query_dirty = current_text != saved_query
        else:
            self.query_dirty = bool(current_text)
        if not self.query_box.hasFocus():
            self.query_dirty = False
        self.update_query_name_tag()
    def set_active_query(self, name=None, saved=True):
        self.current_query_name = name
        self.query_dirty = not saved
        self.update_query_name_tag()
        
    def keyPressEvent(self, event):
        if (
            event.modifiers() == Qt.KeyboardModifier.ControlModifier and
            event.key() == Qt.Key.Key_S
        ):
            current_text = self.query_box.toPlainText().strip()
            if (
                self.current_query_name and
                self.current_query_name in self.saved_queries and
                current_text
            ):
                saved_data = self.saved_queries.get(
                    self.current_query_name,
                    {}
                )
                if not isinstance(saved_data, dict):
                    saved_data = {
                        "query": "",
                        "db": "",
                        "files": []
                    }
                saved_data["query"] = current_text
                saved_data["db"] = "SQL"
                saved_data["files"] = list(self.name_map.keys())
                self.saved_queries[self.current_query_name] = saved_data
                with open(self.queries_path, "w", encoding="utf-8") as f:
                    json.dump(self.saved_queries, f, indent=2, ensure_ascii=False)
                self.set_active_query(
                    self.current_query_name,
                    saved=True
                )
                self.query_status.setText(
                    f"{self.current_query_name} saved"
                )
            else:
                self.save_query()
            return
        super().keyPressEvent(event)
        
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to close the application?",
            QMessageBox.StandardButton.Ok |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Ok:
            try:
                if self.sqlite_conn:
                    self.sqlite_conn.close()
            except Exception:
                pass
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