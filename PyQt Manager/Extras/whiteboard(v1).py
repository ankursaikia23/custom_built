import sys
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QImage, QPainter, QPen, QColor, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QFileDialog, QColorDialog,
    QToolBar, QLabel, QSpinBox, QComboBox, QMessageBox
)

class Canvas(QLabel):
    def __init__(self, parent=None, width=1200, height=800, bg_color=Qt.white):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.bg_color = QColor(bg_color)
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.clear_image()

        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = QColor(Qt.black)
        self.pen_width = 3
        self.tool = "pen"
        self.temp_image = None

        self.undo_stack = []
        self.max_undo = 20

        self.pending_text = ""

    def clear_image(self):
        self.image.fill(self.bg_color)
        self.setPixmap(QPixmap.fromImage(self.image))

    def push_undo(self):
        if len(self.undo_stack) >= self.max_undo:
            self.undo_stack.pop(0)
        self.undo_stack.append(self.image.copy())

    def undo(self):
        if not self.undo_stack:
            return
        self.image = self.undo_stack.pop()
        self.setPixmap(QPixmap.fromImage(self.image))

    def set_pen_color(self, qcolor):
        self.pen_color = QColor(qcolor)

    def set_pen_width(self, w):
        self.pen_width = max(1, int(w))

    def set_tool(self, tool_name):
        self.tool = tool_name

    def import_image(self, filename):
        img = QImage(filename)
        if img.isNull():
            return False
        self.push_undo()
        painter = QPainter(self.image)
        scaled = img.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.image.width() - scaled.width()) // 2
        y = (self.image.height() - scaled.height()) // 2
        painter.drawImage(x, y, scaled)
        painter.end()
        self.setPixmap(QPixmap.fromImage(self.image))
        return True

    def save_image(self, filename):
        return self.image.save(filename)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self.push_undo()
        self.drawing = True
        self.last_point = event.pos()
        if self.tool in ("line", "rect", "ellipse"):
            self.temp_image = self.image.copy()
        self.update()

    def mouseMoveEvent(self, event):
        if not self.drawing:
            return
        pos = event.pos()
        if self.tool == "pen":
            painter = QPainter(self.image)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, pos)
            painter.end()
            self.last_point = QPoint(pos)
            self.setPixmap(QPixmap.fromImage(self.image))

        elif self.tool == "eraser":
            painter = QPainter(self.image)
            erase_pen = QPen(self.bg_color, self.pen_width*2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(erase_pen)
            painter.drawLine(self.last_point, pos)
            painter.end()
            self.last_point = QPoint(pos)
            self.setPixmap(QPixmap.fromImage(self.image))

        elif self.tool in ("line", "rect", "ellipse"):
            self.image = self.temp_image.copy()
            painter = QPainter(self.image)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            if self.tool == "line":
                painter.drawLine(self.last_point, pos)
            else:
                rect = QRect(self.last_point, pos)
                if self.tool == "rect":
                    painter.drawRect(rect)
                else:
                    painter.drawEllipse(rect)
            painter.end()
            self.setPixmap(QPixmap.fromImage(self.image))

    def mouseReleaseEvent(self, event):
        if not self.drawing or event.button() != Qt.LeftButton:
            return
        self.drawing = False
        pos = event.pos()
        if self.tool in ("line", "rect", "ellipse"):
            self.temp_image = None
        self.setPixmap(QPixmap.fromImage(self.image))

    def mouseDoubleClickEvent(self, event):
        if self.tool == "text":
            text, ok = QFileDialog.getText(self, "Enter text", "Text to place:")
            if ok and text:
                self.push_undo()
                painter = QPainter(self.image)
                pen = QPen(self.pen_color)
                painter.setPen(pen)
                painter.drawText(event.pos(), text)
                painter.end()
                self.setPixmap(QPixmap.fromImage(self.image))

class WhiteboardMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Whiteboard")
        self.canvas = Canvas(self, width=1200, height=800)
        self.setCentralWidget(self.canvas)
        self.create_toolbar()
        self.resize(1220, 860)

    def create_toolbar(self):
        tb = QToolBar("Tools")
        self.addToolBar(tb)

        tool_select = QComboBox()
        tool_select.addItems(["pen", "eraser", "line", "rect", "ellipse", "text"])
        tool_select.currentTextChanged.connect(self.canvas.set_tool)
        tb.addWidget(tool_select)

        color_act = QAction("Color", self)
        color_act.triggered.connect(self.choose_color)
        tb.addAction(color_act)

        tb.addSeparator()
        tb.addWidget(QLabel(" Pen size: "))
        size_spin = QSpinBox()
        size_spin.setRange(1, 50)
        size_spin.setValue(3)
        size_spin.valueChanged.connect(self.canvas.set_pen_width)
        tb.addWidget(size_spin)

        clear_act = QAction("Clear", self)
        clear_act.triggered.connect(self.clear_canvas)
        tb.addAction(clear_act)

        undo_act = QAction("Undo", self)
        undo_act.triggered.connect(self.canvas.undo)
        tb.addAction(undo_act)

        import_act = QAction("Import Image", self)
        import_act.triggered.connect(self.import_image)
        tb.addAction(import_act)

        save_act = QAction("Save", self)
        save_act.triggered.connect(self.save_image)
        tb.addAction(save_act)

        export_act = QAction("Export PNG", self)
        export_act.triggered.connect(self.save_image)
        tb.addAction(export_act)

    def choose_color(self):
        color = QColorDialog.getColor(initial=self.canvas.pen_color, parent=self, title="Choose pen color")
        if color.isValid():
            self.canvas.set_pen_color(color)

    def clear_canvas(self):
        reply = QMessageBox.question(self, "Clear", "Clear the whiteboard?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.canvas.push_undo()
            self.canvas.clear_image()

    def import_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open image", "", "Images (*.png *.jpg *.bmp *.svg)")
        if fname:
            ok = self.canvas.import_image(fname)
            if not ok:
                QMessageBox.warning(self, "Import failed", "Could not load image.")

    def save_image(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save image", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)")
        if fname:
            ok = self.canvas.save_image(fname)
            if not ok:
                QMessageBox.warning(self, "Save failed", "Could not save image.")

def main():
    app = QApplication(sys.argv)
    w = WhiteboardMainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()