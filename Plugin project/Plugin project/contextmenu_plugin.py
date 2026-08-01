from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import Qt

class ContextMenuPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_menu)

    def show_menu(self,pos):
        menu=QMenu(self.table)
        copy_action=menu.addAction("Copy")
        cut_action=menu.addAction("Cut")
        paste_action=menu.addAction("Paste")
        menu.addSeparator()
        image_action=menu.addAction("Insert Image")
        pdf_action=menu.addAction("Insert PDF")
        remove_action=menu.addAction("Remove Item")
        action=menu.exec(self.table.viewport().mapToGlobal(pos))
        if action==copy_action and hasattr(self.spreadsheet,"clipboard_plugin"):
            self.spreadsheet.clipboard_plugin.copy_selection()
        elif action==cut_action and hasattr(self.spreadsheet,"clipboard_plugin"):
            self.spreadsheet.clipboard_plugin.cut_selection()
        elif action==paste_action and hasattr(self.spreadsheet,"clipboard_plugin"):
            self.spreadsheet.clipboard_plugin.paste_selection()
        elif action==image_action and hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.insert_image()
        elif action==pdf_action and hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.insert_pdf()
        elif action==remove_action:
            r=self.table.currentRow()
            c=self.table.currentColumn()
            self.table.takeItem(r,c)
            self.table.removeCellWidget(r,c)
            if hasattr(self.spreadsheet,"image_plugin"):
                self.spreadsheet.image_plugin.images.pop((r,c),None)
            if hasattr(self.spreadsheet,"pdf_plugin"):
                self.spreadsheet.pdf_plugin.pdfs.pop((r,c),None)