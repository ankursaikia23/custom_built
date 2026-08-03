from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt

class BorderPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet

    def apply_border(self,style):
        table=self.spreadsheet.table
        indexes=table.selectedIndexes()

        if not indexes:
            return

        for index in indexes:
            item=table.item(index.row(),index.column())

            if item is None:
                item=QTableWidgetItem("")
                table.setItem(
                    index.row(),
                    index.column(),
                    item
                )

            item.setData(
                Qt.ItemDataRole.UserRole+1,
                style
            )

        table.viewport().update()

    def remove_border(self):
        table=self.spreadsheet.table
        indexes=table.selectedIndexes()

        if not indexes:
            return

        for index in indexes:
            item=table.item(index.row(),index.column())

            if item:
                item.setData(
                    Qt.ItemDataRole.UserRole+1,
                    None
                )

        table.viewport().update()