from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem

class KeyboardPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def handle_key_press(self,event):
        if event.modifiers()==Qt.KeyboardModifier.ControlModifier:
            if event.key()==Qt.Key.Key_C:
                if hasattr(self.spreadsheet,"clipboard_plugin"):
                    self.spreadsheet.clipboard_plugin.copy_selection()
                return True

            elif event.key()==Qt.Key.Key_X:
                if hasattr(self.spreadsheet,"clipboard_plugin"):
                    self.spreadsheet.clipboard_plugin.cut_selection()
                return True

            elif event.key()==Qt.Key.Key_V:
                if hasattr(self.spreadsheet,"clipboard_plugin"):
                    self.spreadsheet.clipboard_plugin.paste_selection()
                return True

            elif event.key()==Qt.Key.Key_Z:
                if hasattr(self.spreadsheet,"history_plugin"):
                    self.spreadsheet.history_plugin.undo()
                return True

            elif event.key()==Qt.Key.Key_Y:
                if hasattr(self.spreadsheet,"history_plugin"):
                    self.spreadsheet.history_plugin.redo()
                return True

        if event.key() in(
            Qt.Key.Key_Delete,
            Qt.Key.Key_Backspace
        ):
            selected=list(self.table.selectedItems())
            if not selected:
                return True
            
            snapshots=[]
            for item in selected:
                snapshots.append(
                    self.spreadsheet.history_plugin.create_cell_snapshot(
                        item.row(),
                        item.column()
                    )
                )
            
            self.table.blockSignals(True)
            try:
                for item in selected:
                    item.setText("")
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        None
                    )
            finally:
                self.table.blockSignals(False)
            
            if hasattr(self.spreadsheet,"history_plugin"):
                self.spreadsheet.history_plugin.push_operation(
                    snapshots,
                    [],
                    "delete_contents"
                )
            
            self.spreadsheet.is_modified=True
            
            for item in selected:
                self.spreadsheet.cell_plugin.finish_edit(item)
            
            return True

        if event.key()==Qt.Key.Key_Equal:
            row=self.table.currentRow()
            col=self.table.currentColumn()

            if row<0 or col<0:
                return True

            item=self.table.item(row,col)

            if item is None:
                item=QTableWidgetItem()
                self.table.setItem(row,col,item)

            formula_bar=getattr(
                self.spreadsheet,
                "formulabar_plugin",
                None
            )

            if formula_bar is not None:
                formula_bar.updating=True
                formula_bar.formula_mode=True
                formula_bar.selecting_formula=False

                formula_bar.type_area.setPlainText("=")
                formula_bar.type_area.setFocus()

                cursor=formula_bar.type_area.textCursor()
                cursor.movePosition(
                    cursor.MoveOperation.End
                )
                formula_bar.type_area.setTextCursor(cursor)

                formula_bar.updating=False

                if hasattr(
                    formula_bar,
                    "update_popup"
                ):
                    formula_bar.update_popup()

            return True

        if event.key() in(
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):
            if self.table.state()==self.table.State.EditingState:
                current_item=self.table.currentItem()

                if current_item is not None:
                    self.table.closePersistentEditor(
                        current_item
                    )

                self.table.clearFocus()

                r=self.table.currentRow()
                c=self.table.currentColumn()

                if r<self.table.rowCount()-1:
                    self.table.setCurrentCell(
                        r+1,
                        c
                    )

                return True

            row=self.table.currentRow()
            col=self.table.currentColumn()

            if row<0 or col<0:
                return True

            item=self.table.item(row,col)

            if item is None:
                item=QTableWidgetItem("")
                self.table.setItem(row,col,item)

            if hasattr(
                self.spreadsheet,
                "cell_plugin"
            ):
                self.spreadsheet.cell_plugin.start_edit(
                    item
                )

            return True

        return False