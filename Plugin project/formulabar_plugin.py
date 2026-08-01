from PyQt6.QtWidgets import QPlainTextEdit,QTableWidgetItem
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt

class TypeArea(QPlainTextEdit):
    def keyPressEvent(self,event):
        if event.modifiers()&Qt.KeyboardModifier.ControlModifier:
            cursor=self.textCursor()
            anchor=cursor.anchor()
            if event.key()==Qt.Key.Key_Up:
                super().keyPressEvent(event)
                cursor=self.textCursor()
                cursor.setPosition(anchor,QTextCursor.MoveMode.MoveAnchor)
                cursor.setPosition(0,QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
                return
            elif event.key()==Qt.Key.Key_Down:
                super().keyPressEvent(event)
                cursor=self.textCursor()
                cursor.setPosition(anchor,QTextCursor.MoveMode.MoveAnchor)
                cursor.setPosition(self.document().characterCount()-1,QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
                return
        cursor=self.textCursor()
        if event.key()==Qt.Key.Key_Up and cursor.blockNumber()==0:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            return
        if event.key()==Qt.Key.Key_Down and cursor.blockNumber()==self.document().blockCount()-1:
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
            return
        super().keyPressEvent(event)

class FormulaBarPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.type_area=TypeArea()
        self.type_area.setFixedHeight(self.type_area.fontMetrics().lineSpacing()*5+12)
        self.updating=False
        self.table.currentCellChanged.connect(self.update_bar)
        self.type_area.document().contentsChanged.connect(self.apply_bar)

    def widget(self):
        return self.type_area

    def update_bar(self,currentRow,currentColumn,previousRow,previousColumn):
        self.updating=True
        self.type_area.blockSignals(True)
        item=self.table.item(currentRow,currentColumn)
        if item:
            self.type_area.setPlainText(item.text())
        else:
            self.type_area.clear()
        self.type_area.blockSignals(False)
        self.updating=False

    def apply_bar(self):
        if self.updating:
            return
        r=self.table.currentRow()
        c=self.table.currentColumn()
        if r<0 or c<0:
            return
        item=self.table.item(r,c)
        if item is None:
            item=QTableWidgetItem()
            self.table.setItem(r,c,item)
        text=self.type_area.toPlainText()
        self.table.blockSignals(True)
        item.setText(text)
        self.table.blockSignals(False)
        lines=max(1,text.count("\n")+1)
        fm=self.table.fontMetrics()
        self.table.setRowHeight(r,max(30,lines*fm.lineSpacing()+10))