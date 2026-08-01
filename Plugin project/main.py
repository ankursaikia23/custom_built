import sys
from PyQt6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout
from grid_plugin import GridPlugin
from cell_plugin import CellPlugin
from toolbar_plugin import ToolbarPlugin
from menu_plugin import MenuPlugin
from statusbar_plugin import StatusBarPlugin
from formulabar_plugin import FormulaBarPlugin
from contextmenu_plugin import ContextMenuPlugin
from keyboard_plugin import KeyboardPlugin
from format_plugin import FormatPlugin
from alignment_plugin import AlignmentPlugin
from color_plugin import ColorPlugin
from image_plugin import ImagePlugin
from pdf_plugin import PDFPlugin
from date_plugin import DatePlugin
from clipboard_plugin import ClipboardPlugin
from history_plugin import HistoryPlugin
from file_plugin import FilePlugin

class SpreadsheetWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spreadsheet")
        self.resize(1200,700)
        self.grid_plugin=GridPlugin()
        self.table=self.grid_plugin.widget()
        self.toolbar_plugin=ToolbarPlugin(self)
        self.menu_plugin=MenuPlugin(self)
        self.statusbar_plugin=StatusBarPlugin(self)
        self.formulabar_plugin=FormulaBarPlugin(self)
        self.cell_plugin=CellPlugin(self)
        self.contextmenu_plugin=ContextMenuPlugin(self)
        self.keyboard_plugin=KeyboardPlugin(self)
        self.format_plugin=FormatPlugin(self)
        self.alignment_plugin=AlignmentPlugin(self)
        self.color_plugin=ColorPlugin(self)
        self.image_plugin=ImagePlugin(self)
        self.pdf_plugin=PDFPlugin(self)
        self.date_plugin=DatePlugin(self)
        self.clipboard_plugin=ClipboardPlugin(self)
        self.history_plugin=HistoryPlugin(self)
        self.file_plugin=FilePlugin(self)
        self.container=QWidget()
        self.layout=QVBoxLayout(self.container)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.formulabar_plugin.widget())
        self.layout.addWidget(self.table)
        self.setCentralWidget(self.container)
        self.connect_actions()
        
    def connect_actions(self):
        self.menu_plugin.new_action.triggered.connect(self.file_plugin.new_file)
        self.menu_plugin.open_action.triggered.connect(self.file_plugin.open_file)
        self.menu_plugin.save_action.triggered.connect(self.file_plugin.save_file)
        self.menu_plugin.export_pdf_action.triggered.connect(self.file_plugin.export_pdf)
        self.menu_plugin.insert_image_action.triggered.connect(self.image_plugin.insert_image)
        self.menu_plugin.insert_pdf_action.triggered.connect(self.pdf_plugin.insert_pdf)
        self.toolbar_plugin.new_action.triggered.connect(self.file_plugin.new_file)
        self.toolbar_plugin.open_action.triggered.connect(self.file_plugin.open_file)
        self.toolbar_plugin.save_action.triggered.connect(self.file_plugin.save_file)
        self.toolbar_plugin.undo_action.triggered.connect(self.history_plugin.undo)
        self.toolbar_plugin.redo_action.triggered.connect(self.history_plugin.redo)
        self.toolbar_plugin.copy_action.triggered.connect(self.clipboard_plugin.copy_selection)
        self.toolbar_plugin.cut_action.triggered.connect(self.clipboard_plugin.cut_selection)
        self.toolbar_plugin.paste_action.triggered.connect(self.clipboard_plugin.paste_selection)
        self.toolbar_plugin.image_action.triggered.connect(self.image_plugin.insert_image)
        self.toolbar_plugin.pdf_action.triggered.connect(self.pdf_plugin.insert_pdf)
        self.toolbar_plugin.export_pdf_action.triggered.connect(self.file_plugin.export_pdf)

    def keyPressEvent(self,event):
        if self.keyboard_plugin.handle_key_press(event):
            return
        super().keyPressEvent(event)
        
if __name__=="__main__":
    app=QApplication(sys.argv)
    window=SpreadsheetWindow()
    window.show()
    sys.exit(app.exec())