from PyQt6.QtWidgets import (
    QToolBar,
    QComboBox
)
from PyQt6.QtGui import QAction


class SpreadsheetToolbar(QToolBar):
    def __init__(self):
        super().__init__()

        self.setMovable(False)

        self.addAction(
            QAction("New", self)
        )

        self.addAction(
            QAction("Save", self)
        )

        self.addAction(
            QAction("Undo", self)
        )

        self.addAction(
            QAction("Redo", self)
        )

        # ==========================================
        # Font formatting
        # ==========================================

        self.bold_action = QAction(
            "Bold",
            self
        )

        self.bold_action.setCheckable(True)

        self.addAction(
            self.bold_action
        )

        self.italic_action = QAction(
            "Italic",
            self
        )

        self.italic_action.setCheckable(True)

        self.addAction(
            self.italic_action
        )

        self.underline_action = QAction(
            "Underline",
            self
        )

        self.underline_action.setCheckable(True)

        self.addAction(
            self.underline_action
        )

        # ==========================================
        # Font family
        # ==========================================

        self.font_family_combo = QComboBox()

        self.font_family_combo.addItems([
            "Arial",
            "Times New Roman",
            "Courier New",
            "Verdana",
            "Calibri",
        ])

        self.font_family_combo.setCurrentText(
            "Arial"
        )

        self.addWidget(
            self.font_family_combo
        )

        # ==========================================
        # Font size
        # ==========================================

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

        self.font_size_combo.setCurrentText(
            "10"
        )

        self.addWidget(
            self.font_size_combo
        )

        # ==========================================
        # Text color
        # ==========================================

        self.text_color_action = QAction(
            "Text Color",
            self
        )

        self.addAction(
            self.text_color_action
        )
        
        # ==========================================
        # Background color
        # ==========================================
        
        self.background_color_action = QAction(
            "Fill Color",
            self
        )
        
        self.addAction(
            self.background_color_action
        )

        # ==========================================
        # Horizontal alignment
        # ==========================================

        self.horizontal_alignment_combo = QComboBox()

        self.horizontal_alignment_combo.addItems([
            "Left",
            "Center",
            "Right",
        ])

        self.horizontal_alignment_combo.setCurrentText(
            "Left"
        )

        self.addWidget(
            self.horizontal_alignment_combo
        )

        # ==========================================
        # Vertical alignment
        # ==========================================

        self.vertical_alignment_combo = QComboBox()

        self.vertical_alignment_combo.addItems([
            "Top",
            "Center",
            "Bottom",
        ])

        self.vertical_alignment_combo.setCurrentText(
            "Center"
        )

        self.addWidget(
            self.vertical_alignment_combo
        )
