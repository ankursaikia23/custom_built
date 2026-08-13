from PyQt6.QtWidgets import(
    QPlainTextEdit, QListWidget, QListWidgetItem, QFrame, QVBoxLayout, QTableWidgetItem
)
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt

class TypeArea(QPlainTextEdit):

    def __init__(self,parent=None):
        super().__init__(parent)
        self.plugin=None

    def keyPressEvent(self,event):
        if self.plugin and self.plugin.handle_editor_key(event):
            return
        super().keyPressEvent(event)

class FormulaBarPlugin:

    FUNCTIONS=[
        "SUM",
        "AVERAGE",
        "COUNT",
        "MIN",
        "MAX"
    ]

    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.updating=False
        self.formula_mode=False
        self.selecting_formula=False
        self.type_area=TypeArea()
        self.type_area.plugin=self
        self.type_area.setFixedHeight(
            self.type_area.fontMetrics().lineSpacing()*5+12
        )
        self.popup=QFrame()
        self.popup.setWindowFlags(
            Qt.WindowType.Tool|
            Qt.WindowType.FramelessWindowHint
        )
        self.popup.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout=QVBoxLayout(self.popup)
        layout.setContentsMargins(0,0,0,0)
        self.list_widget=QListWidget()
        layout.addWidget(self.list_widget)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.list_widget.setMouseTracking(True)
        self.list_widget.itemClicked.connect(self.popup_item_clicked)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.list_widget.itemClicked.connect(self.popup_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.popup_item_clicked)
        self.popup.hide()
        self.type_area.document().contentsChanged.connect(
            self.apply_bar
        )

    def widget(self):
        return self.type_area
    
    def apply_bar(self):
        if self.updating:
            return
    
        text=self.type_area.toPlainText()    
        self.formula_mode=text.startswith("=")
        self.update_popup()
        self.commit_to_cell()
    
    def show_popup(self,prefix):
        self.list_widget.clear()
        prefix=prefix.upper()
        for function in self.FUNCTIONS:
            if function.startswith(prefix):
                self.list_widget.addItem(QListWidgetItem(function))
        if self.list_widget.count()==0:
            self.popup.hide()
            return
        self.list_widget.setCurrentRow(0)
        self.popup.resize(180,150)
        point=self.table.viewport().mapToGlobal(
            self.table.visualRect(
                self.table.currentIndex()
            ).bottomLeft()
        )
        self.popup.move(point)
        self.popup.show()
        self.list_widget.setFocus()
    
    def hide_popup(self):
        self.popup.hide()
    
    def current_function_prefix(self):
        text=self.type_area.toPlainText()
        cursor=self.type_area.textCursor().position()
    
        if cursor==0:
            return None
    
        text=text[:cursor]
    
        if not text.startswith("="):
            return None
    
        if "(" in text:
            return None
    
        return text[1:]
    
    def update_popup(self):
        text=self.type_area.toPlainText()
    
        if not text.startswith("="):
            self.hide_popup()
            return
    
        cursor=self.type_area.textCursor().position()
        prefix=text[1:cursor]
    
        if "(" in prefix:
            self.hide_popup()
            return
    
        self.show_popup(prefix)
        
    def popup_item_clicked(self,item):
        if item is None:
            return
        self.list_widget.setCurrentItem(item)
        self.insert_selected_function()
        self.type_area.setFocus()
    
    def insert_selected_function(self):
        item=self.list_widget.currentItem()
    
        if item is None:
            return
    
        text="="+item.text()+"("
    
        self.updating=True
        self.formula_mode=True
        self.selecting_formula=False
    
        self.type_area.setPlainText(text)
    
        cursor=self.type_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.type_area.setTextCursor(cursor)
    
        self.updating=False
        self.hide_popup()
        self.table.setFocus()
        
    def update_bar(self,currentRow,currentColumn,previousRow,previousColumn):
        if self.updating or self.selecting_formula:
            return
    
        self.table=self.spreadsheet.table
        self.updating=True
    
        item=self.table.item(currentRow,currentColumn)
    
        if item:
            formula=item.data(Qt.ItemDataRole.UserRole)
    
            if isinstance(formula,str) and formula.startswith("="):
                self.type_area.setPlainText(formula)
                self.formula_mode=True
            else:
                self.type_area.setPlainText(item.text())
                self.formula_mode=False
        else:
            self.type_area.clear()
            self.formula_mode=False
    
        self.updating=False
    
    def commit_to_cell(self):
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
        self.table.blockSignals(True)
        item.setText(text)
    
        if text.startswith("="):
            item.setData(Qt.ItemDataRole.UserRole,text)
        else:
            item.setData(Qt.ItemDataRole.UserRole,None)
    
        self.table.blockSignals(False)
    
        if not text.startswith("="):
            return
    
        if text.endswith("("):
            return
    
        if text.endswith(":"):
            return
    
        if hasattr(self.spreadsheet,"formula_plugin"):
            self.spreadsheet.formula_plugin.apply_formula(
                row,
                column
            )
            
    def handle_editor_key(self,event):
        if self.popup.isVisible():
            if event.key()==Qt.Key.Key_Down:
                row=self.list_widget.currentRow()
                if row<self.list_widget.count()-1:
                    self.list_widget.setCurrentRow(row+1)
                return True
            if event.key()==Qt.Key.Key_Up:
                row=self.list_widget.currentRow()
                if row>0:
                    self.list_widget.setCurrentRow(row-1)
                return True
            if event.key() in(
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Tab
            ):
                self.insert_selected_function()
                self.type_area.setFocus()
                return True
            if event.key()==Qt.Key.Key_Escape:
                self.hide_popup()
                self.formula_mode=False
                self.selecting_formula=False
                self.type_area.setFocus()
                return True
    
        if event.key() in(
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):
            self.commit_to_cell()
            return True
    
        return False