import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFrame, QHBoxLayout, QComboBox, QMenu, QScrollArea
)

class SidebarPlugin(QFrame):
    def __init__(self,spreadsheet):
        super().__init__()
        self.spreadsheet=spreadsheet
        self.expanded=True
        self.setObjectName("Sidebar")
        self.sidebar_width=self.calculate_sidebar_width()
        self.setFixedWidth(self.sidebar_width)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
        #Sidebar{
        background:#f5f5f5;
        border-right:1px solid #d0d0d0;
        }
        QPushButton,QToolButton{
        text-align:left;
        padding-left:12px;
        height:38px;
        border:none;
        background:transparent;
        font-size:11pt;
        }
        QPushButton:hover,QToolButton:hover{
        background:#e8e8e8;
        }
        QPushButton:pressed,QToolButton:pressed{
        background:#dcdcdc;
        }
        QMenu{
        background:#f5f5f5;
        border:1px solid #d0d0d0;
        }
        QMenu::item{
        padding:8px 28px 8px 12px;
        }
        QMenu::item:selected{
        background:#e8e8e8;
        }
        """)
        self.main_layout=QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.scroll_area=QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.content=QWidget()
        self.layout=QVBoxLayout(self.content)
        self.layout.setContentsMargins(4,4,4,4)
        self.layout.setSpacing(5)
        self.scroll_area.setWidget(self.content)
        self.main_layout.addWidget(self.scroll_area)
        self.header=QHBoxLayout()
        self.layout.addLayout(self.header)
        self.toggle_button=QPushButton("☰")
        self.toggle_button.setFixedHeight(24)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        self.header.addWidget(self.toggle_button)
        self.header.addStretch()
        self.buttons=[]
        self.new_action=QAction(self.get_icon("New File"),"New File",spreadsheet)
        self.open_action=QAction(self.get_icon("Open File"),"Open File",spreadsheet)
        self.save_action=QAction(self.get_icon("Save File"),"Save File",spreadsheet)
        self.new_tab_action=QAction(self.get_icon("New Tab"),"New Tab",spreadsheet)
        self.export_pdf_action=QAction(self.get_icon("Export PDF"),"Export PDF",spreadsheet)
        self.export_image_action=QAction(self.get_icon("Export Image"),"Export Image",spreadsheet)
        self.export_sheet_action=QAction(self.get_icon("Export Spreadsheet"),"Export Spreadsheet",spreadsheet)
        self.undo_action=QAction("Undo",spreadsheet)
        self.redo_action=QAction("Redo",spreadsheet)
        self.refresh_action=QAction(QIcon("icons/Refresh.png"),"Refresh",self)
        self.scale_action=QAction("Scale Up / Down",spreadsheet)
        self.copy_action=QAction("Copy",spreadsheet)
        self.cut_action=QAction("Cut",spreadsheet)
        self.paste_action=QAction("Paste",spreadsheet)
        self.bold_action=QAction("Bold",spreadsheet)
        self.bold_action.setCheckable(True)
        self.italic_action=QAction("Italic",spreadsheet)
        self.italic_action.setCheckable(True)
        self.underline_action=QAction("Underline",spreadsheet)
        self.underline_action.setCheckable(True)
        self.strike_action=QAction("Strikethrough",spreadsheet)
        self.strike_action.setCheckable(True)
        self.wrap_action=QAction("Wrap Text",spreadsheet)
        self.wrap_action.setCheckable(True)
        self.merge_action=QAction("Merge Cells",spreadsheet)
        self.unmerge_action=QAction("Unmerge Cells",spreadsheet)
        self.font_color_action=QAction("Font Color",spreadsheet)
        self.fill_color_action=QAction("Fill Color",spreadsheet)
        self.image_action=QAction(self.get_icon("Insert Image"),"Insert Image",spreadsheet)
        self.pdf_action=QAction(self.get_icon("Insert PDF"),"Insert PDF",spreadsheet)
        self.date_action=QAction(self.get_icon("Insert Date"),"Insert Date",spreadsheet)
        self.file_operations_button=self.add_master_button("File Operations","File Operations")
        self.file_operations_menu=QMenu(self)
        self.file_operations_button.clicked.connect(
            lambda:self.file_operations_menu.exec(
                self.file_operations_button.mapToGlobal(
                    self.file_operations_button.rect().bottomLeft()
                    )
                )
            )
        self.file_operations_menu.addAction(self.new_action)
        self.file_operations_menu.addAction(self.open_action)
        self.file_operations_menu.addAction(self.save_action)
        self.file_operations_menu.addAction(self.new_tab_action)
        self.file_operations_menu.addSeparator()
        self.file_operations_menu.addAction(self.export_pdf_action)
        self.file_operations_menu.addAction(self.export_image_action)
        self.file_operations_menu.addAction(self.export_sheet_action)
        self.insert_operations_button=self.add_master_button("Insert Operations","Insert Operations")
        self.insert_operations_menu=QMenu(self)
        self.insert_operations_button.clicked.connect(
            lambda:self.insert_operations_menu.exec(
                self.insert_operations_button.mapToGlobal(
                    self.insert_operations_button.rect().bottomLeft()
                    )
                )
            )
        self.insert_operations_menu.addAction(self.image_action)
        self.insert_operations_menu.addAction(self.pdf_action)
        self.insert_operations_menu.addAction(self.date_action)
        self.add_button("Undo","Undo",self.undo_action)
        self.add_button("Redo","Redo",self.redo_action)
        self.add_button("Scale Up / Down","Scale Up Down",self.scale_action)
        self.add_button("Refresh","Refresh",self.refresh_action)
        self.add_separator()
        self.add_button("Copy","Copy",self.copy_action)
        self.add_button("Cut","Cut",self.cut_action)
        self.add_button("Paste","Paste",self.paste_action)
        self.add_separator()
        self.add_button("Bold","Bold",self.bold_action)
        self.add_button("Italic","Italic",self.italic_action)
        self.add_button("Underline","Underline",self.underline_action)
        self.add_button("Strikethrough","Strikethrough",self.strike_action)
        self.add_button("Wrap Text","Wrap Text",self.wrap_action)
        self.add_button("Merge","Merge",self.merge_action)
        self.add_button("Unmerge","Unmerge",self.unmerge_action)
        self.add_separator()
        self.add_button("Font Color","Font Color",self.font_color_action)
        self.add_button("Fill Color","Fill Color",self.fill_color_action)
        self.horizontal_alignment=QComboBox()
        self.horizontal_alignment.addItems(["Left","Center","Right"])
        self.vertical_alignment=QComboBox()
        self.vertical_alignment.addItems(["Top","Middle","Bottom"])
        self.layout.addWidget(self.horizontal_alignment)
        self.layout.addWidget(self.vertical_alignment)
        self.border_button=QPushButton("Borders")
        self.border_button.setProperty("full_text","Borders")
        self.border_button.setIcon(self.get_icon("Borders"))
        self.border_button.setIconSize(QSize(12,12))
        self.border_button.setFixedHeight(24)
        self.border_menu=QMenu(self)
        self.border_button.setMenu(self.border_menu)
        self.border_button.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.border_button.setStyleSheet("text-align:left;padding-left:12px;")
        self.all_border_action=self.border_menu.addAction("All Borders")
        self.outer_border_action=self.border_menu.addAction("Outer Borders")
        self.inner_border_action=self.border_menu.addAction("Inner Borders")
        self.top_border_action=self.border_menu.addAction("Top Border")
        self.bottom_border_action=self.border_menu.addAction("Bottom Border")
        self.left_border_action=self.border_menu.addAction("Left Border")
        self.right_border_action=self.border_menu.addAction("Right Border")
        self.no_border_action=self.border_menu.addAction("No Border")
        self.layout.addWidget(self.border_button)
        self.formula_button=QPushButton("Formulas")
        self.formula_button.setProperty("full_text","Formulas")
        self.formula_button.setIcon(self.get_icon("Formulas"))
        self.formula_button.setIconSize(QSize(12,12))
        self.formula_button.setFixedHeight(24)
        self.formula_menu=QMenu(self)
        self.formula_button.setMenu(self.formula_menu)
        self.formula_button.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.formula_button.setStyleSheet("text-align:left;padding-left:12px;")
        self.sum_action=self.formula_menu.addAction("SUM")
        self.average_action=self.formula_menu.addAction("AVERAGE")
        self.count_action=self.formula_menu.addAction("COUNT")
        self.min_action=self.formula_menu.addAction("MIN")
        self.max_action=self.formula_menu.addAction("MAX")
        self.layout.addWidget(self.formula_button)
        self.layout.addStretch()

    def get_icon(self,name):
        icon_path=os.path.join(os.path.dirname(__file__),"icons",name+".png")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return QIcon()

    def calculate_sidebar_width(self):
        texts=[
            "File Operations",
            "Insert Operations",
            "Undo",
            "Redo",
            "Copy",
            "Cut",
            "Paste",
            "Bold",
            "Italic",
            "Underline",
            "Strikethrough",
            "Wrap Text",
            "Unmerge Cells",
            "Font Color",
            "Fill Color",
            "Borders",
            "Formulas"
        ]
        metrics=QFontMetrics(self.font())
        longest=max(metrics.horizontalAdvance(text) for text in texts)
        return longest+70

    def add_master_button(self,text,icon_name):
        button=QPushButton()
        button.setText(text+"  ▾")
        button.setIcon(self.get_icon(icon_name))
        button.setIconSize(QSize(12,12))
        button.setFixedHeight(24)
        button.setProperty("full_text",text)
        button.setStyleSheet("text-align:left;padding-left:12px;padding-right:12px;")
        self.layout.addWidget(button)
        self.buttons.append(button)
        return button

    def add_button(self,text,icon_name,action):
        button=QPushButton(text)
        button.setIcon(self.get_icon(icon_name))
        button.setIconSize(QSize(12,12))
        button.setFixedHeight(24)
        button.setProperty("full_text",text)
        button.clicked.connect(action.trigger)
        self.layout.addWidget(button)
        self.buttons.append(button)
        return button

    def add_separator(self):
        line=QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)

    def toggle_sidebar(self):
        self.expanded=not self.expanded
        if self.expanded:
            self.setFixedWidth(self.sidebar_width)
            for button in self.buttons:
                button.setText(button.property("full_text"))
            self.border_button.setText("Borders")
            self.formula_button.setText("Formulas")
        else:
            self.setFixedWidth(60)
            for button in self.buttons:
                button.setText("")
            self.border_button.setText("")
            self.formula_button.setText("")