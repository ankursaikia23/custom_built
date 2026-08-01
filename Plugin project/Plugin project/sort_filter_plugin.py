from PyQt6.QtWidgets import QInputDialog
class SortFilterPlugin:
    def __init__(self,window):
        self.window=window
        self.table=window.table
    def sort_column(self):
        column,ok=QInputDialog.getInt(self.window,"Sort","Column:")
        if ok:
            self.table.sortItems(column)
    def sort_column_descending(self):
        column,ok=QInputDialog.getInt(self.window,"Sort","Column:")
        if ok:
            self.table.sortItems(column,1)
    def enable_filter(self):
        self.table.setSortingEnabled(True)