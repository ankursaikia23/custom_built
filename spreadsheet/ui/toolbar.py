from PyQt6.QtWidgets import (
    QToolBar,
    QComboBox
)
from PyQt6.QtGui import QAction

class SpreadsheetToolbar(QToolBar):
    def __init__(self):
        super().__init__()
        self.setMovable(False)

        self.addAction(QAction("New", self))
        self.addAction(QAction("Save", self))
        self.addAction(QAction("Undo", self))
        self.addAction(QAction("Redo", self))

        self.bold_action = QAction("Bold", self)
        self.bold_action.setCheckable(True)
        self.addAction(self.bold_action)

        self.italic_action = QAction("Italic", self)
        self.italic_action.setCheckable(True)
        self.addAction(self.italic_action)

        self.underline_action = QAction("Underline", self)
        self.underline_action.setCheckable(True)
        self.addAction(self.underline_action)

        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Arial",
            "Times New Roman",
            "Courier New",
            "Verdana",
            "Calibri",
        ])
        self.font_family_combo.setCurrentText("Arial")
        self.addWidget(self.font_family_combo)

        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems([
            "8",
            "9",
            "10",
            "11",
            "12",
            "14",
            "16",
            "18",
            "20",
            "24",
            "28",
            "32",
        ])
        self.font_size_combo.setCurrentText("10")
        self.addWidget(self.font_size_combo)

        self.text_color_action = QAction(
            "Text Color",
            self
        )
        self.addAction(self.text_color_action)

        self.background_color_action = QAction(
            "Fill Color",
            self
        )
        self.addAction(self.background_color_action)

        self.horizontal_alignment_combo = QComboBox()
        self.horizontal_alignment_combo.addItems([
            "Left",
            "Center",
            "Right",
        ])
        self.horizontal_alignment_combo.setCurrentText("Left")
        self.addWidget(self.horizontal_alignment_combo)

        self.vertical_alignment_combo = QComboBox()
        self.vertical_alignment_combo.addItems([
            "Top",
            "Center",
            "Bottom",
        ])
        self.vertical_alignment_combo.setCurrentText("Center")
        self.addWidget(self.vertical_alignment_combo)

        self.number_format_combo = QComboBox()
        self.number_format_combo.addItems([
            "General",
            "Number",
            "Integer",
            "Currency",
            "Percentage",
            "Date",
        ])
        self.number_format_combo.setCurrentText("General")
        self.addWidget(self.number_format_combo)
        self.border_side_combo = QComboBox()
        self.border_side_combo.addItems([
            "None",
            "Top",
            "Bottom",
            "Left",
            "Right",
        ])
        self.border_side_combo.setCurrentText("None")
        self.addWidget(self.border_side_combo)
        
        self.border_style_combo = QComboBox()
        self.border_style_combo.addItems([
            "Solid",
            "Dashed",
            "Dotted",
            "Double",
        ])
        self.border_style_combo.setCurrentText("Solid")
        self.addWidget(self.border_style_combo)
        
        self.border_width_combo = QComboBox()
        self.border_width_combo.addItems([
            "1",
            "2",
            "3",
        ])
        self.border_width_combo.setCurrentText("1")
        self.addWidget(self.border_width_combo)
        
        self.border_color_action = QAction(
            "Border Color",
            self
        )
        self.addAction(self.border_color_action)