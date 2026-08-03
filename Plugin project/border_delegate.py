from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QPen
from PyQt6.QtCore import Qt

class BorderDelegate(QStyledItemDelegate):
    def paint(self,painter,option,index):
        super().paint(painter,option,index)
        item=index.model().itemData(index)

        painter.save()

        pen=QPen(Qt.GlobalColor.black)
        pen.setWidth(1)
        painter.setPen(pen)

        rect=option.rect

        if item.get(Qt.ItemDataRole.UserRole+1):
            style=item[Qt.ItemDataRole.UserRole+1]

            if style=="all":
                painter.drawRect(rect)

            elif style=="top":
                painter.drawLine(
                    rect.topLeft(),
                    rect.topRight()
                )

            elif style=="bottom":
                painter.drawLine(
                    rect.bottomLeft(),
                    rect.bottomRight()
                )

            elif style=="left":
                painter.drawLine(
                    rect.topLeft(),
                    rect.bottomLeft()
                )

            elif style=="right":
                painter.drawLine(
                    rect.topRight(),
                    rect.bottomRight()
                )

        painter.restore()