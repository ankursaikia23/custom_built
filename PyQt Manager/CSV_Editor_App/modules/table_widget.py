import uuid
import re
import pandas as pd
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QTextEdit, QPlainTextEdit, QStyledItemDelegate
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat

class SmartTextEdit(QPlainTextEdit):
    def keyPressEvent(self, event):
        key = event.key()
        cursor = self.textCursor()
        text_len = len(self.toPlainText())
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        ctrl = bool(event.modifiers() & Qt.ControlModifier)

        if key == Qt.Key_Home:
            cursor.setPosition(0, QTextCursor.KeepAnchor if shift else QTextCursor.MoveAnchor)
            self.setTextCursor(cursor)
            return
        elif key == Qt.Key_End:
            cursor.setPosition(text_len, QTextCursor.KeepAnchor if shift else QTextCursor.MoveAnchor)
            self.setTextCursor(cursor)
            return
        elif key == Qt.Key_Up and ctrl:
            cursor.setPosition(0, QTextCursor.KeepAnchor if shift else QTextCursor.MoveAnchor)
            self.setTextCursor(cursor)
            return
        elif key == Qt.Key_Down and ctrl:
            cursor.setPosition(text_len, QTextCursor.KeepAnchor if shift else QTextCursor.MoveAnchor)
            self.setTextCursor(cursor)
            return
        super().keyPressEvent(event)

from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QTextCursor

class CellDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = SmartTextEdit(parent)
        editor.installEventFilter(self)
        return editor

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            cursor = obj.textCursor()
            key = event.key()
            shift = bool(event.modifiers() & Qt.ShiftModifier)
            ctrl = bool(event.modifiers() & Qt.ControlModifier)

            if key == Qt.Key_Home:
                if ctrl:
                    cursor.movePosition(QTextCursor.Start, QTextCursor.KeepAnchor if shift else QTextCursor.MoveAnchor)
                else:
                    cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor if shift else QTextCursor.MoveAnchor)
                obj.setTextCursor(cursor)
                return True

            elif key == Qt.Key_End:
                if ctrl:
                    cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor if shift else QTextCursor.MoveAnchor)
                else:
                    cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor if shift else QTextCursor.MoveAnchor)
                obj.setTextCursor(cursor)
                return True

        return super().eventFilter(obj, event)

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
        self.dark_mode_enabled = False
        self.setItemDelegate(CellDelegate())

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
        if self.undo_stack:
            row, col, text = self.undo_stack.pop()
            item = self.item(row, col)
            if item:
                self.redo_stack.append((row, col, item.text()))
                item.setText(text)

    def perform_redo(self):
        if self.redo_stack:
            row, col, text = self.redo_stack.pop()
            item = self.item(row, col)
            if item:
                self.undo_stack.append((row, col, item.text()))
                item.setText(text)

    def copy_selection(self):
        selected = self.selectedIndexes()
        if not selected: return
        data = {}
        for idx in selected:
            data[(idx.row(), idx.column())] = self.item(idx.row(), idx.column()).text() if self.item(idx.row(), idx.column()) else ""
        self._internal_clipboards = data

    def paste_selection(self):
        selected = self.selectedIndexes()
        if not selected or not self._internal_clipboards: return
        min_row = min(idx.row() for idx in selected)
        min_col = min(idx.column() for idx in selected)
        for (r_offset, c_offset), text in self._internal_clipboards.items():
            row = min_row + r_offset; col = min_col + c_offset
            if row < self.rowCount() and col < self.columnCount():
                self.setItem(row, col, QTableWidgetItem(text))

    def cut_selection(self):
        self.copy_selection()
        self.delete_selection()

    def delete_selection(self):
        selected = self.selectedIndexes()
        if not selected: return
        for idx in selected:
            item = self.item(idx.row(), idx.column())
            if item:
                self.undo_stack.append((idx.row(), idx.column(), item.text()))
                item.setText("")
        self.redo_stack.clear()

    def freeze_first_column(self):
        if self.columnCount() > 0:
            self.setColumnWidth(0, self.columnWidth(0))
            self.setColumnHidden(0, False)
