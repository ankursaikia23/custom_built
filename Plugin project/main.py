import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt
from grid_plugin import GridPlugin
from cell_plugin import CellPlugin
from sidebar_plugin import SidebarPlugin
from statusbar_plugin import StatusBarPlugin
from formulabar_plugin import FormulaBarPlugin
from contextmenu_plugin import ContextMenuPlugin
from keyboard_plugin import KeyboardPlugin
from format_plugin import FormatPlugin
from alignment_plugin import AlignmentPlugin
from color_plugin import ColorPlugin
from border_plugin import BorderPlugin, BorderDelegate
from image_plugin import ImagePlugin
from pdf_plugin import PDFPlugin
from date_plugin import DatePlugin
from clipboard_plugin import ClipboardPlugin
from history_plugin import HistoryPlugin
from file_plugin import FilePlugin
from formula_plugin import FormulaPlugin
from search_plugin import SearchPlugin
from zoom_plugin import ZoomPlugin
from sort_filter_plugin import SortFilterPlugin
from chart_plugin import ChartPlugin
from validation_plugin import ValidationPlugin
from comment_plugin import CommentPlugin
from theme_plugin import ThemePlugin
from settings_plugin import SettingsPlugin
from tab_plugin import TabPlugin
from viewer_plugin import ViewerPlugin

class SpreadsheetWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.menuBar().hide()
        self.setWindowTitle("Spreadsheet")
        self.resize(1200,700)
        self.tab_plugin=TabPlugin(self)
        self.grid_plugin=GridPlugin()
        self.grid_plugin.spreadsheet=self
        self.table=self.grid_plugin.widget()
        self.tab_plugin.add_tab(self.table,"Sheet1")
        self.toolbar_plugin=SidebarPlugin(self)
        self.statusbar_plugin=StatusBarPlugin(self)
        self.formulabar_plugin=FormulaBarPlugin(self)
        self.cell_plugin=CellPlugin(self)
        self.contextmenu_plugin=ContextMenuPlugin(self)
        self.keyboard_plugin=KeyboardPlugin(self)
        self.format_plugin=FormatPlugin(self)
        self.alignment_plugin=AlignmentPlugin(self)
        self.color_plugin=ColorPlugin(self)
        self.border_plugin=BorderPlugin(self)
        self.image_plugin=ImagePlugin(self)
        self.pdf_plugin=PDFPlugin(self)
        self.date_plugin=DatePlugin(self)
        self.clipboard_plugin=ClipboardPlugin(self)
        self.history_plugins={}
        self.history_plugin=HistoryPlugin(self)
        self.history_plugins[self.table]=self.history_plugin
        self.file_plugin=FilePlugin(self)
        self.formula_plugin=FormulaPlugin(self)
        self.search_plugin=SearchPlugin(self)
        self.zoom_plugin=ZoomPlugin(self)
        self.sort_filter_plugin=SortFilterPlugin(self)
        self.chart_plugin=ChartPlugin(self)
        self.validation_plugin=ValidationPlugin(self)
        self.comment_plugin=CommentPlugin(self)
        self.theme_plugin=ThemePlugin(self)
        self.settings_plugin=SettingsPlugin(self)
        self.viewer_plugin=ViewerPlugin(self)
        self.container=QWidget()
        self.main_layout=QHBoxLayout(self.container)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.toolbar_plugin)
        self.right_panel=QWidget()
        self.right_layout=QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0,0,0,0)
        self.right_layout.setSpacing(0)
        self.right_layout.addWidget(self.formulabar_plugin.widget())
        self.right_layout.addWidget(self.tab_plugin.widget())
        self.viewer_splitter=QSplitter(Qt.Orientation.Horizontal)
        self.viewer_splitter.setChildrenCollapsible(False)
        self.viewer_splitter.addWidget(self.right_panel)
        self.viewer_splitter.addWidget(self.viewer_plugin)
        self.viewer_splitter.setSizes([600,600])
        self.main_layout.addWidget(self.viewer_splitter)
        self.main_layout.setStretch(0,0)
        self.main_layout.setStretch(1,1)
        self.setCentralWidget(self.container)
        self.statusBar().addPermanentWidget(self.zoom_plugin.widget())
        self.table.cellChanged.connect(self.formula_plugin.apply_formula)
        self.table.currentCellChanged.connect(self.formulabar_plugin.update_bar)
        self.table.currentCellChanged.connect(
            lambda row,col,prev_row,prev_col:self.viewer_plugin.show_cell(row,col)
            )
        self.tab_plugin.tabs.currentChanged.connect(self.change_active_tab)
        self.settings_plugin.restore_window_state()
        self.connect_actions()
        self.grid_plugin.selection_changed_callback=self.update_toolbar_state
        self.is_modified=False
        self.table.itemChanged.connect(self.mark_modified)
        
    def connect_actions(self):
        self.toolbar_plugin.new_action.triggered.connect(self.file_plugin.new_file)
        self.toolbar_plugin.new_tab_action.triggered.connect(self.file_plugin.new_tab)
        self.toolbar_plugin.open_action.triggered.connect(self.file_plugin.open_file)
        self.toolbar_plugin.save_action.triggered.connect(self.file_plugin.save_file)
        self.toolbar_plugin.scale_action.triggered.connect(self.file_plugin.set_export_scale)
        self.toolbar_plugin.refresh_action.triggered.connect(self.refresh_sheet)
        self.toolbar_plugin.undo_action.triggered.connect(lambda:self.history_plugin.undo())
        self.toolbar_plugin.redo_action.triggered.connect(lambda:self.history_plugin.redo())
        self.toolbar_plugin.copy_action.triggered.connect(self.clipboard_plugin.copy_selection)
        self.toolbar_plugin.cut_action.triggered.connect(self.clipboard_plugin.cut_selection)
        self.toolbar_plugin.paste_action.triggered.connect(self.clipboard_plugin.paste_selection)
        self.toolbar_plugin.bold_action.triggered.connect(self.format_plugin.set_bold)
        self.toolbar_plugin.italic_action.triggered.connect(self.format_plugin.set_italic)
        self.toolbar_plugin.underline_action.triggered.connect(self.format_plugin.set_underline)
        self.toolbar_plugin.strike_action.triggered.connect(self.format_plugin.set_strike)
        self.toolbar_plugin.wrap_action.triggered.connect(self.format_plugin.toggle_wrap_text)
        self.toolbar_plugin.merge_action.triggered.connect(self.grid_plugin.merge_selected_cells)
        self.toolbar_plugin.horizontal_alignment.currentTextChanged.connect(self.change_horizontal_alignment)
        self.toolbar_plugin.vertical_alignment.currentTextChanged.connect(self.change_vertical_alignment)
        self.toolbar_plugin.font_color_action.triggered.connect(self.color_plugin.set_font_color)
        self.toolbar_plugin.fill_color_action.triggered.connect(self.color_plugin.set_background_color)
        self.toolbar_plugin.all_border_action.triggered.connect(lambda:self.border_plugin.apply_border("all"))    
        self.toolbar_plugin.outer_border_action.triggered.connect(lambda:self.border_plugin.apply_border("outer"))
        self.toolbar_plugin.inner_border_action.triggered.connect(lambda:self.border_plugin.apply_border("inner"))        
        self.toolbar_plugin.top_border_action.triggered.connect(lambda:self.border_plugin.apply_border("top"))
        self.toolbar_plugin.bottom_border_action.triggered.connect(lambda:self.border_plugin.apply_border("bottom"))
        self.toolbar_plugin.left_border_action.triggered.connect(lambda:self.border_plugin.apply_border("left"))
        self.toolbar_plugin.right_border_action.triggered.connect(lambda:self.border_plugin.apply_border("right"))
        self.toolbar_plugin.no_border_action.triggered.connect(lambda:self.border_plugin.apply_border("none"))
        self.toolbar_plugin.sum_action.triggered.connect(lambda:self.formula_plugin.insert_function("SUM"))
        self.toolbar_plugin.average_action.triggered.connect(lambda:self.formula_plugin.insert_function("AVERAGE"))
        self.toolbar_plugin.count_action.triggered.connect(lambda:self.formula_plugin.insert_function("COUNT"))
        self.toolbar_plugin.min_action.triggered.connect(lambda:self.formula_plugin.insert_function("MIN"))
        self.toolbar_plugin.max_action.triggered.connect(lambda:self.formula_plugin.insert_function("MAX"))
        self.toolbar_plugin.date_action.triggered.connect(self.date_plugin.insert_date)
        self.toolbar_plugin.image_action.triggered.connect(self.image_plugin.insert_image)
        self.toolbar_plugin.pdf_action.triggered.connect(self.pdf_plugin.insert_pdf)
        self.toolbar_plugin.export_pdf_action.triggered.connect(self.file_plugin.export_pdf)
        self.toolbar_plugin.export_image_action.triggered.connect(self.file_plugin.export_image)
        self.toolbar_plugin.export_sheet_action.triggered.connect(self.file_plugin.export_file)
        
    def refresh_sheet(self):
        table=self.tab_plugin.current_table()
        if table is None:
            return
        self.table=table
        self.formula_plugin.recalculate()
        default_row=30
        default_col=100
        for row in range(table.rowCount()):
            used=False
            for col in range(table.columnCount()):
                item=table.item(row,col)
                if item and item.text():
                    used=True
                    break
            if used:
                table.resizeRowToContents(row)
            else:
                table.setRowHeight(row,default_row)
        for col in range(table.columnCount()):
            used=False
            for row in range(table.rowCount()):
                item=table.item(row,col)
                if item and item.text():
                    used=True
                    break
            if used:
                table.resizeColumnToContents(col)
            else:
                table.setColumnWidth(col,default_col)
        table.viewport().update()
        
    def change_horizontal_alignment(self,text):
        if text=="Left":
            self.alignment_plugin.align_left()
        elif text=="Center":
            self.alignment_plugin.align_center()
        elif text=="Right":
            self.alignment_plugin.align_right()
        
    def change_vertical_alignment(self,text):
        if text=="Top":
            self.alignment_plugin.align_top()
        elif text=="Middle":
            self.alignment_plugin.align_middle()
        elif text=="Bottom":
            self.alignment_plugin.align_bottom()
        
    def update_toolbar_state(self):
        state=self.format_plugin.get_selected_cell_format()
        if state is None:
            self.toolbar_plugin.bold_action.setChecked(False)
            self.toolbar_plugin.italic_action.setChecked(False)
            self.toolbar_plugin.underline_action.setChecked(False)
            self.toolbar_plugin.strike_action.setChecked(False)
            return
        self.toolbar_plugin.bold_action.setChecked(state["bold"])
        self.toolbar_plugin.italic_action.setChecked(state["italic"])
        self.toolbar_plugin.underline_action.setChecked(state["underline"])
        self.toolbar_plugin.strike_action.setChecked(state["strike"])
    
    def change_active_tab(self,index):
        table=self.tab_plugin.current_table()
        if table:
            try:
                table.cellChanged.disconnect()
            except:
                pass
            try:
                table.itemChanged.disconnect()
            except:
                pass
            self.table=table
            self.grid_plugin.table=table
            self.grid_plugin.spreadsheet=self
            self.cell_plugin.table=table
            self.format_plugin.table=table
            self.alignment_plugin.table=table
            self.color_plugin.table=table
            self.border_plugin.table=table
            self.image_plugin.table=table
            self.image_plugin.images=self.image_plugin.images_map.setdefault(table,{})
            self.image_plugin.refresh_images()
            self.pdf_plugin.table=table
            self.pdf_plugin.pdfs=self.pdf_plugin.pdfs_map.setdefault(table,{})
            self.pdf_plugin.refresh_pdfs()
            self.comment_plugin.comments=self.comment_plugin.comments_map.setdefault(table,{})
            self.border_plugin.border_data=self.border_plugin.border_data_map.setdefault(table,{})
            self.border_plugin.delegate=BorderDelegate(self.border_plugin,table)
            table.setItemDelegate(self.border_plugin.delegate)
            self.clipboard_plugin.table=table
            if table not in self.history_plugins:
                self.history_plugins[table]=HistoryPlugin(self)
            self.history_plugin=self.history_plugins[table]
            self.history_plugin.table=table
            self.file_plugin.table=table
            self.formula_plugin.window=self
            self.formulabar_plugin.table=table
            self.keyboard_plugin.table=table
            table.cellChanged.connect(self.formula_plugin.apply_formula)
            table.currentCellChanged.connect(self.formulabar_plugin.update_bar)
            table.itemChanged.connect(self.mark_modified)
            self.formulabar_plugin.table=table
            table.setFocus()
            self.formulabar_plugin.popup.hide()
            self.formulabar_plugin.selecting_formula=False
    
    def mark_modified(self):
        self.is_modified=True
        self.formula_plugin.recalculate()
    
    def keyPressEvent(self,event):
        if self.keyboard_plugin.handle_key_press(event):
            return
        super().keyPressEvent(event)
        
    def closeEvent(self,event):
        reply=QMessageBox.question(
            self,
            "Exit Spreadsheet",
            "Do you want to save before closing?",
            QMessageBox.StandardButton.Yes|
            QMessageBox.StandardButton.No|
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes
        )
    
        if reply==QMessageBox.StandardButton.Cancel:
            event.ignore()
            return
    
        if reply==QMessageBox.StandardButton.Yes:
            self.file_plugin.save_file()
    
        self.settings_plugin.save_window_state()
        event.accept()

if __name__=="__main__":
    app=QApplication(sys.argv)
    window=SpreadsheetWindow()
    window.show()
    sys.exit(app.exec())