from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtCore import Qt, pyqtSignal

class SpreadsheetView(QTableWidget):

    deleteRequested = pyqtSignal(list)
    copyRequested = pyqtSignal()
    pasteRequested = pyqtSignal()

    def __init__(self):
        super().__init__(50, 26)

        self.setHorizontalHeaderLabels(
            [chr(65 + i) for i in range(26)]
        )

        self.verticalHeader().setDefaultSectionSize(24)
        self.horizontalHeader().setDefaultSectionSize(90)

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Return:

            row = self.currentRow()
            column = self.currentColumn()

            if (
                event.modifiers()
                & Qt.KeyboardModifier.ShiftModifier
            ):
                if row > 0:
                    self.setCurrentCell(
                        row - 1,
                        column
                    )
                return

            super().keyPressEvent(event)

            if row < self.rowCount() - 1:
                self.setCurrentCell(
                    row + 1,
                    column
                )

            return

        if event.key() in (
            Qt.Key.Key_Delete,
            Qt.Key.Key_Backspace,
        ):

            references = []

            for item in self.selectedItems():

                reference = (
                    f"{chr(65 + item.column())}"
                    f"{item.row() + 1}"
                )

                if reference not in references:
                    references.append(reference)

            if not references:

                row = self.currentRow()
                column = self.currentColumn()

                if row >= 0 and column >= 0:
                    references.append(
                        f"{chr(65 + column)}"
                        f"{row + 1}"
                    )

            self.deleteRequested.emit(
                references
            )

            return

        if (
            event.key() == Qt.Key.Key_C
            and event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        ):
            self.copyRequested.emit()
            return

        if (
            event.key() == Qt.Key.Key_V
            and event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        ):
            self.pasteRequested.emit()
            return

        super().keyPressEvent(event)