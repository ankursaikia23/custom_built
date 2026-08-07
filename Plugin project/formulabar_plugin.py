from PyQt6.QtWidgets import QPlainTextEdit, QTableWidgetItem, QListWidget, QFrame, QVBoxLayout
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt, QPoint

class TypeArea(QPlainTextEdit):
    def keyPressEvent(self,event):
        plugin=getattr(self,"plugin",None)

        if plugin and plugin.popup.isVisible():

            if event.key()==Qt.Key.Key_Down:
                row=plugin.list_widget.currentRow()
                if row<plugin.list_widget.count()-1:
                    plugin.list_widget.setCurrentRow(row+1)
                return

            if event.key()==Qt.Key.Key_Up:
                row=plugin.list_widget.currentRow()
                if row>0:
                    plugin.list_widget.setCurrentRow(row-1)
                return

            if event.key() in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Tab
            ):
                plugin.insert_selected_function()
                return

            if event.key()==Qt.Key.Key_Escape:
                plugin.popup.hide()
                plugin.selecting_formula=False
                return

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

        if plugin:
            plugin.on_formula_text_changed()

class FormulaBarPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.type_area=TypeArea()
        self.type_area.plugin=self
        self.type_area.setFixedHeight(
            self.type_area.fontMetrics().lineSpacing()*5+12
        )    
        self.updating=False
        self.selecting_formula=False
        self.functions=[
            "SUM",
            "AVERAGE",
            "COUNT",
            "MIN",
            "MAX"
        ]
        self.popup=QFrame(self.spreadsheet)
        self.popup.setWindowFlags(Qt.WindowType.Popup)
        self.popup.setFrameShape(QFrame.Shape.Box)
        layout=QVBoxLayout(self.popup)
        layout.setContentsMargins(0,0,0,0)
        self.list_widget=QListWidget()
        layout.addWidget(self.list_widget)
        self.popup.hide()
        self.type_area.document().contentsChanged.connect(self.apply_bar)
        self.type_area.textChanged.connect(self.on_formula_text_changed)
        self.list_widget.itemClicked.connect(self.insert_selected_function)

    def widget(self):
        return self.type_area
    
    def on_formula_text_changed(self):
        if self.updating:
            return
    
        text=self.type_area.toPlainText()
    
        if not text.startswith("="):
            self.popup.hide()
            self.selecting_formula=False
            return
    
        self.selecting_formula=True
        cursor=self.type_area.textCursor().position()
        keyword=text[1:cursor].upper()
        self.list_widget.clear()
    
        for function in self.functions:
            if function.startswith(keyword):
                self.list_widget.addItem(function)
    
        if self.list_widget.count()==0:
            self.popup.hide()
            return
    
        self.list_widget.setCurrentRow(0)
        point=self.type_area.mapToGlobal(
            QPoint(
                0,
                self.type_area.height()
            )
        )
        self.popup.move(point)
        height=self.list_widget.sizeHintForRow(0)
        
        if height<1:
            height=22
    
        self.popup.resize(
            180,
            min(
                150,
                height*self.list_widget.count()+4
            )
        )
        self.popup.show()

    def update_bar(self,currentRow,currentColumn,previousRow,previousColumn):
        self.updating=True
        self.table=self.spreadsheet.table
        self.type_area.blockSignals(True)
    
        item=self.table.item(currentRow,currentColumn)
    
        if item:
            formula=item.data(Qt.ItemDataRole.UserRole)
            if isinstance(formula,str) and formula.startswith("="):
                self.type_area.setPlainText(formula)
            else:
                self.type_area.setPlainText(item.text())
        else:
            self.type_area.clear()
    
        self.type_area.blockSignals(False)
        self.updating=False

    def apply_bar(self):
        if self.updating:
            return
    
        self.table=self.spreadsheet.table
        row=self.table.currentRow()
        column=self.table.currentColumn()
    
        if row<0 or column<0:
            return
    
        item=self.table.item(row,column)
    
        if item is None:
            item=QTableWidgetItem()
            self.table.setItem(row,column,item)
    
        text=self.type_area.toPlainText()    
        self.selecting_formula=text.startswith("=")
        self.table.blockSignals(True)
    
        if text.startswith("="):
            item.setData(Qt.ItemDataRole.UserRole,text)
            item.setText(text)
        else:
            item.setData(Qt.ItemDataRole.UserRole,None)
            item.setText(text)
    
        self.table.blockSignals(False)
        lines=max(1,text.count("\n")+1)
        fm=self.table.fontMetrics()
        self.table.setRowHeight(
            row,
            max(
                30,
                lines*fm.lineSpacing()+10
            )
        )
        
        if text.startswith("="):
            return
        
        if hasattr(self.spreadsheet,"formula_plugin"):
            self.spreadsheet.formula_plugin.apply_formula(
                row,
                column
            )
            
    def insert_selected_function(self):
        item=self.list_widget.currentItem()
    
        if item is None:
            return
    
        self.updating=True
        text="="+item.text()+"("
        self.type_area.setPlainText(text)
        cursor=self.type_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        self.type_area.setTextCursor(cursor)
        self.popup.hide()
        self.selecting_formula=True
        self.updating=False
    
    def update_formula_reference(self,reference):
        if not self.selecting_formula:
            return
    
        text=self.type_area.toPlainText()
        left=text.find("(")
    
        if left==-1:
            return
    
        text=text[:left+1]+reference+")"
        self.updating=True
        self.type_area.setPlainText(text)    
        cursor=self.type_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.type_area.setTextCursor(cursor)
        self.updating=False
        self.apply_bar()