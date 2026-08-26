from PyQt6.QtWidgets import QLineEdit

class FormulaBar(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Enter value or formula")