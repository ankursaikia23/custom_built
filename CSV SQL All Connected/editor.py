import re
from PyQt6.QtWidgets import QTextEdit, QCompleter
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QTextCursor

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