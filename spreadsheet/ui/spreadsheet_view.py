from PyQt6.QtWidgets import (
    QTableWidget,
    QStyledItemDelegate
)
from PyQt6.QtCore import (
    Qt,
    pyqtSignal
)
from PyQt6.QtGui import (
    QPen,
    QColor
)


class BorderDelegate(QStyledItemDelegate):

    def paint(
        self,
        painter,
        option,
        index
    ):

        super().paint(
            painter,
            option,
            index
        )

        borders = index.data(
            Qt.ItemDataRole.UserRole + 1
        )

        if not borders:
            return

        painter.save()

        rect = option.rect

        style_map = {
            "solid": Qt.PenStyle.SolidLine,
            "dashed": Qt.PenStyle.DashLine,
            "dotted": Qt.PenStyle.DotLine
        }

        for side, border in borders.items():

            if side not in (
                "top",
                "bottom",
                "left",
                "right"
            ):
                continue

            style = border.get(
                "style",
                "solid"
            )

            width = max(
                1,
                int(
                    border.get(
                        "width",
                        1
                    )
                )
            )

            color = QColor(
                border.get(
                    "color",
                    "#000000"
                )
            )

            pen = QPen(
                color
            )

            pen.setWidth(
                width
            )

            pen.setStyle(
                style_map.get(
                    style,
                    Qt.PenStyle.SolidLine
                )
            )

            painter.setPen(
                pen
            )

            half_width = width // 2

            if side == "top":

                y = rect.top() + half_width

                painter.drawLine(
                    rect.left(),
                    y,
                    rect.right(),
                    y
                )

            elif side == "bottom":

                y = rect.bottom() - half_width

                painter.drawLine(
                    rect.left(),
                    y,
                    rect.right(),
                    y
                )

            elif side == "left":

                x = rect.left() + half_width

                painter.drawLine(
                    x,
                    rect.top(),
                    x,
                    rect.bottom()
                )

            elif side == "right":

                x = rect.right() - half_width

                painter.drawLine(
                    x,
                    rect.top(),
                    x,
                    rect.bottom()
                )

        painter.restore()


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

        # ==========================================
        # Border rendering
        # ==========================================

        self.setItemDelegate(
            BorderDelegate(self)
        )

        # ==========================================
        # Selection
        # ==========================================

        self.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection
        )

        self.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectItems
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

    def keyPressEvent(self, event):

        # ==========================================
        # Enter / Shift + Enter
        # ==========================================

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

        # ==========================================
        # Delete / Backspace
        # ==========================================

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

        # ==========================================
        # Ctrl + C
        # ==========================================

        if (
            event.key() == Qt.Key.Key_C
            and event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        ):

            self.copyRequested.emit()

            return

        # ==========================================
        # Ctrl + V
        # ==========================================

        if (
            event.key() == Qt.Key.Key_V
            and event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        ):

            self.pasteRequested.emit()

            return

        # ==========================================
        # Default keyboard handling
        # ==========================================

        super().keyPressEvent(event)