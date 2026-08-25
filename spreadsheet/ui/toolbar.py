from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction

class SpreadsheetToolbar(QToolBar):
    def __init__(self):
        super().__init__()
        self.setMovable(False)
        self.addAction(QAction("New",self))
        self.addAction(QAction("Save",self))
        self.addAction(QAction("Undo",self))
        self.addAction(QAction("Redo",self))