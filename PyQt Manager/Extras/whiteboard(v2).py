import sys, json, math, time
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, QByteArray
from PyQt5.QtGui import QPainter, QPen, QColor, QImage, QPixmap, QTransform, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QColorDialog, QToolBar, QSpinBox, QComboBox, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsSimpleTextItem, QGraphicsTextItem, QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel, QFontComboBox, QSlider
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtSvg import QSvgGenerator
from PyQt5.QtGui import QPainterPath, QMouseEvent, QTextCursor

class FreehandItem(QGraphicsPathItem):
    def __init__(self, path, pen):
        super().__init__(path)
        self.setPen(pen)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

    def to_dict(self):
        data = {"type":"freehand","pen_color":self.pen().color().name(),"pen_width":self.pen().widthF(),"path":self.path().toFillPolygon().toList()}
        return data

class ArrowItem(QGraphicsLineItem):
    def __init__(self, line, pen):
        super().__init__(line)
        self.setPen(pen)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        p2 = self.line().p2()
        p1 = self.line().p1()
        angle = math.atan2(p2.y()-p1.y(), p2.x()-p1.x())
        arrow_size = max(6, self.pen().width()*3)
        pA = QPointF(p2.x() - arrow_size*math.cos(angle - math.pi/6), p2.y() - arrow_size*math.sin(angle - math.pi/6))
        pB = QPointF(p2.x() - arrow_size*math.cos(angle + math.pi/6), p2.y() - arrow_size*math.sin(angle + math.pi/6))
        painter.setBrush(self.pen().color())
        painter.drawPolygon(p2, pA, pB)

class ResizableRect(QGraphicsRectItem):
    def __init__(self, rect, pen, brush=QColor(0,0,0,0)):
        super().__init__(rect)
        self.setPen(pen)
        self.setBrush(brush)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
    def to_dict(self):
        return {"type":"rect","x":self.rect().x(),"y":self.rect().y(),"w":self.rect().width(),"h":self.rect().height(),"pen_color":self.pen().color().name(),"pen_width":self.pen().widthF(),"fill":self.brush().color().name()}

class ResizableEllipse(QGraphicsEllipseItem):
    def __init__(self, rect, pen, brush=QColor(0,0,0,0)):
        super().__init__(rect)
        self.setPen(pen)
        self.setBrush(brush)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
    def to_dict(self):
        return {"type":"ellipse","x":self.rect().x(),"y":self.rect().y(),"w":self.rect().width(),"h":self.rect().height(),"pen_color":self.pen().color().name(),"pen_width":self.pen().widthF(),"fill":self.brush().color().name()}

class WhiteboardScene(QGraphicsScene):
    def __init__(self, w, h):
        super().__init__(0,0,w,h)
        self.background = QGraphicsRectItem(0,0,w,h)
        self.background.setBrush(QColor("white"))
        self.background.setPen(QPen(Qt.NoPen))
        self.addItem(self.background)
        self.pen_color = QColor(Qt.black)
        self.pen_width = 3
        self.tool = "pen"
        self.temp_item = None
        self.path = None
        self.highlighter_alpha = 100
        self.grid_visible = False
        self.snap = False
        self.max_undo = 20
        self.undo_stack = []
        self.redo_stack = []
        self.push_undo()

    def set_tool(self, t):
        self.tool = t

    def set_pen(self, color, width):
        self.pen_color = color
        self.pen_width = width

    def toggle_grid(self, v):
        self.grid_visible = v
        self.update_grid()

    def update_grid(self):
        for it in list(self.items()):
            if isinstance(it, QGraphicsRectItem) and it.data(0) == "grid":
                self.removeItem(it)
        if not self.grid_visible:
            return
        spacing = 50
        w = int(self.width())
        h = int(self.height())
        pen = QPen(QColor(220,220,220))
        for x in range(0,w,spacing):
            g = QGraphicsLineItem(x,0,x,h)
            g.setPen(pen)
            g.setZValue(-1)
            g.setData(0,"grid")
            self.addItem(g)
        for y in range(0,h,spacing):
            g = QGraphicsLineItem(0,y,w,y)
            g.setPen(pen)
            g.setZValue(-1)
            g.setData(0,"grid")
            self.addItem(g)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event); return
        p = event.scenePos()
        if self.tool == "pen" or self.tool == "eraser" or self.tool=="highlighter":
            pen = QPen(self.pen_color if self.tool!="eraser" else QColor(self.background.brush().color()), self.pen_width if self.tool!="highlighter" else max(6,self.pen_width*3), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            if self.tool=="highlighter":
                c = QColor(self.pen_color)
                c.setAlpha(self.highlighter_alpha)
                pen.setColor(c)
            self.path = QPainterPath(p)
            self.temp_item = QGraphicsPathItem(self.path)
            self.temp_item.setPen(pen)
            self.temp_item.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.addItem(self.temp_item)
        elif self.tool in ("rect","ellipse","line","arrow"):
            pen = QPen(self.pen_color, self.pen_width)
            self.origin = p
            if self.tool=="rect":
                self.temp_item = ResizableRect(QRectF(p,p), pen)
            elif self.tool=="ellipse":
                self.temp_item = ResizableEllipse(QRectF(p,p), pen)
            elif self.tool=="line" or self.tool=="arrow":
                self.temp_item = ArrowItem(QRectF(p,p).toRect(), pen) if False else QGraphicsLineItem(p.x(),p.y(),p.x(),p.y())
                self.temp_item.setPen(pen)
                self.temp_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.addItem(self.temp_item)
        elif self.tool=="text":
            ti = QGraphicsTextItem("Double-click to edit")
            ti.setDefaultTextColor(self.pen_color)
            f = QFont()
            f.setPointSize(14)
            ti.setFont(f)
            ti.setTextInteractionFlags(Qt.TextEditorInteraction)
            ti.setPos(p)
            ti.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
            self.addItem(ti)
            ti.setFocus()
            self.push_undo()
        elif self.tool=="select":
            super().mousePressEvent(event)
        elif self.tool=="fill":
            items = self.items(p)
            for it in items:
                if isinstance(it, (ResizableRect, ResizableEllipse)):
                    it.setBrush(QColor(self.pen_color))
                    self.push_undo()
                    break
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        p = event.scenePos()
        if self.temp_item and self.tool in ("pen","eraser","highlighter"):
            self.path.lineTo(p)
            self.temp_item.setPath(self.path)
            return
        if self.temp_item and self.tool in ("rect","ellipse"):
            r = QRectF(self.origin,p).normalized()
            self.temp_item.setRect(r)
            return
        if self.temp_item and self.tool in ("line","arrow"):
            if isinstance(self.temp_item, QGraphicsLineItem):
                self.temp_item.setLine(self.origin.x(),self.origin.y(),p.x(),p.y())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.temp_item and self.tool in ("pen","eraser","highlighter"):
            fh = FreehandItem(self.temp_item.path(), self.temp_item.pen())
            fh.setZValue(1)
            self.addItem(fh)
            self.removeItem(self.temp_item)
            self.temp_item = None
            self.path = None
            self.push_undo()
            return
        if self.temp_item and self.tool in ("rect","ellipse"):
            self.temp_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.push_undo()
            self.temp_item = None
            return
        if self.temp_item and self.tool in ("line","arrow"):
            line = self.temp_item.line() if isinstance(self.temp_item, QGraphicsLineItem) else None
            if line:
                if self.tool=="arrow":
                    ai = ArrowItem(line, self.temp_item.pen())
                    self.addItem(ai)
                    self.removeItem(self.temp_item)
                else:
                    self.temp_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                self.push_undo()
            self.temp_item = None
            return
        super().mouseReleaseEvent(event)

    def push_undo(self):
        state = self.serialize()
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) < 2:
            return
        cur = self.undo_stack.pop()
        self.redo_stack.append(cur)
        prev = self.undo_stack[-1]
        self.deserialize(prev)

    def redo(self):
        if not self.redo_stack:
            return
        s = self.redo_stack.pop()
        self.deserialize(s)
        self.undo_stack.append(s)

    def serialize(self):
        items = []
        for it in self.items():
            if it is self.background: continue
            if isinstance(it, FreehandItem):
                pts = []
                p = it.path().toFillPolygon()
                for pt in p:
                    pts.append([pt.x(),pt.y()])
                items.append({"t":"freehand","color":it.pen().color().name(),"w":it.pen().widthF(),"pts":pts,"z":it.zValue()})
            elif isinstance(it, ResizableRect):
                r = it.rect()
                items.append({"t":"rect","x":r.x(),"y":r.y(),"w":r.width(),"h":r.height(),"pen":it.pen().color().name(),"pw":it.pen().widthF(),"fill":it.brush().color().name(),"z":it.zValue()})
            elif isinstance(it, ResizableEllipse):
                r = it.rect()
                items.append({"t":"ellipse","x":r.x(),"y":r.y(),"w":r.width(),"h":r.height(),"pen":it.pen().color().name(),"pw":it.pen().widthF(),"fill":it.brush().color().name(),"z":it.zValue()})
            elif isinstance(it, ArrowItem):
                l = it.line()
                items.append({"t":"arrow","x1":l.x1(),"y1":l.y1(),"x2":l.x2(),"y2":l.y2(),"pen":it.pen().color().name(),"pw":it.pen().widthF(),"z":it.zValue()})
            elif isinstance(it, QGraphicsLineItem):
                l = it.line()
                items.append({"t":"line","x1":l.x1(),"y1":l.y1(),"x2":l.x2(),"y2":l.y2(),"pen":it.pen().color().name(),"pw":it.pen().widthF(),"z":it.zValue()})
            elif isinstance(it, QGraphicsTextItem):
                items.append({"t":"text","x":it.pos().x(),"y":it.pos().y(),"text":it.toPlainText(),"color":it.defaultTextColor().name(),"font_size":it.font().pointSize(),"z":it.zValue()})
        return json.dumps(items)

    def deserialize(self, j):
        self.clear_scene_items()
        try:
            items = json.loads(j)
        except:
            return
        for o in items:
            t = o.get("t")
            if t=="freehand":
                p = QPainterPath()
                pts = o.get("pts",[])
                if pts:
                    p.moveTo(QPointF(pts[0][0],pts[0][1]))
                    for xy in pts[1:]:
                        p.lineTo(QPointF(xy[0],xy[1]))
                pen = QPen(QColor(o.get("color","#000000")), o.get("w",2), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                fh = FreehandItem(p, pen)
                fh.setZValue(o.get("z",1))
                self.addItem(fh)
            elif t=="rect":
                r = QRectF(o["x"],o["y"],o["w"],o["h"])
                pen = QPen(QColor(o.get("pen","#000000")), o.get("pw",2))
                brush = QColor(o.get("fill","#000000"))
                ri = ResizableRect(r, pen, brush)
                ri.setZValue(o.get("z",2))
                self.addItem(ri)
            elif t=="ellipse":
                r = QRectF(o["x"],o["y"],o["w"],o["h"])
                pen = QPen(QColor(o.get("pen","#000000")), o.get("pw",2))
                brush = QColor(o.get("fill","#000000"))
                ei = ResizableEllipse(r, pen, brush)
                ei.setZValue(o.get("z",2))
                self.addItem(ei)
            elif t=="arrow":
                l = QGraphicsLineItem(o["x1"],o["y1"],o["x2"],o["y2"])
                pen = QPen(QColor(o.get("pen","#000000")), o.get("pw",2))
                ai = ArrowItem(l.line(), pen)
                ai.setZValue(o.get("z",3))
                self.addItem(ai)
            elif t=="line":
                l = QGraphicsLineItem(o["x1"],o["y1"],o["x2"],o["y2"])
                pen = QPen(QColor(o.get("pen","#000000")), o.get("pw",2))
                l.setPen(pen)
                l.setZValue(o.get("z",2))
                self.addItem(l)
            elif t=="text":
                ti = QGraphicsTextItem(o.get("text",""))
                ti.setPos(o.get("x",0),o.get("y",0))
                ti.setDefaultTextColor(QColor(o.get("color","#000000")))
                f = QFont()
                f.setPointSize(max(8,o.get("font_size",12)))
                ti.setFont(f)
                ti.setTextInteractionFlags(Qt.TextEditorInteraction)
                ti.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
                ti.setZValue(o.get("z",4))
                self.addItem(ti)

    def clear_scene_items(self):
        for it in list(self.items()):
            if it is self.background: continue
            self.removeItem(it)

class WhiteboardView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self._pan = False
        self._last = None
        self.scale_factor = 1.0

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.2 if delta>0 else 1/1.2
            self.scale_factor *= factor
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._pan = True
            self._last = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan and self._last:
            diff = event.pos() - self._last
            self._last = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - diff.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - diff.y())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._pan = False
            self.setCursor(Qt.ArrowCursor)
            return
        super().mouseReleaseEvent(event)

class WhiteboardMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Whiteboard")
        self.scene_w = 1600
        self.scene_h = 1000
        self.scene = WhiteboardScene(self.scene_w, self.scene_h)
        self.view = WhiteboardView(self.scene)
        self.setCentralWidget(self.view)
        self.create_toolbar()
        self.create_sidepanel()
        self.create_shortcuts()
        self.resize(1200,800)
        self.scene.update_grid()

    def create_toolbar(self):
        tb = QToolBar("Tools")
        self.addToolBar(tb)
        self.tool_select = QComboBox()
        self.tool_select.addItems(["select","pen","highlighter","eraser","line","arrow","rect","ellipse","text","fill"])
        self.tool_select.currentTextChanged.connect(self.change_tool)
        tb.addWidget(self.tool_select)
        self.color_btn = QAction("Color", self)
        self.color_btn.triggered.connect(self.choose_color)
        tb.addAction(self.color_btn)
        tb.addWidget(QLabel("Size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1,60)
        self.size_spin.setValue(3)
        self.size_spin.valueChanged.connect(self.change_size)
        tb.addWidget(self.size_spin)
        self.font_box = QFontComboBox()
        tb.addWidget(self.font_box)
        self.font_size = QSpinBox()
        self.font_size.setRange(6,72)
        self.font_size.setValue(14)
        tb.addWidget(self.font_size)
        self.grid_btn = QAction("Grid", self, checkable=True)
        self.grid_btn.toggled.connect(lambda v: self.scene.toggle_grid(v))
        tb.addAction(self.grid_btn)
        self.snap_btn = QAction("Snap", self, checkable=True)
        self.snap_btn.toggled.connect(lambda v: setattr(self.scene,'snap',v))
        tb.addAction(self.snap_btn)
        undo_act = QAction("Undo", self); undo_act.triggered.connect(self.scene.undo); tb.addAction(undo_act)
        redo_act = QAction("Redo", self); redo_act.triggered.connect(self.scene.redo); tb.addAction(redo_act)
        clear_act = QAction("Clear", self); clear_act.triggered.connect(self.clear_board); tb.addAction(clear_act)
        save_act = QAction("Save Project", self); save_act.triggered.connect(self.save_project); tb.addAction(save_act)
        load_act = QAction("Load Project", self); load_act.triggered.connect(self.load_project); tb.addAction(load_act)
        exp_act = QAction("Export PNG", self); exp_act.triggered.connect(self.export_png); tb.addAction(exp_act)
        pdf_act = QAction("Export PDF", self); pdf_act.triggered.connect(self.export_pdf); tb.addAction(pdf_act)
        svg_act = QAction("Export SVG", self); svg_act.triggered.connect(self.export_svg); tb.addAction(svg_act)
        autosave_act = QAction("Autosave", self, checkable=True); autosave_act.setChecked(True); autosave_act.toggled.connect(self.toggle_autosave); tb.addAction(autosave_act)
        self.current_color = QColor(Qt.black)
        self.change_tool("pen")

    def create_sidepanel(self):
        w = QWidget()
        layout = QVBoxLayout()
        self.layer_list = QListWidget()
        layout.addWidget(QLabel("Layers"))
        layout.addWidget(self.layer_list)
        btns = QHBoxLayout()
        add = QPushButton("Add Bg")
        add.clicked.connect(self.add_bg_image)
        btns.addWidget(add)
        delb = QPushButton("Delete")
        delb.clicked.connect(self.delete_selected)
        btns.addWidget(delb)
        layout.addLayout(btns)
        zoom_layout = QHBoxLayout()
        zoom_in = QPushButton("Zoom +"); zoom_in.clicked.connect(lambda: self.view.scale(1.2,1.2))
        zoom_out = QPushButton("Zoom -"); zoom_out.clicked.connect(lambda: self.view.scale(1/1.2,1/1.2))
        zoom_layout.addWidget(zoom_in); zoom_layout.addWidget(zoom_out)
        layout.addLayout(zoom_layout)
        layout.addStretch()
        container = QWidget()
        container.setLayout(layout)
    
        from PyQt5.QtWidgets import QDockWidget
        dock = QDockWidget("Side Panel", self)
        dock.setWidget(container)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def create_shortcuts(self):
        self.shortcut_map = {
            Qt.Key_Z: self.scene.undo,
            Qt.Key_Y: self.scene.redo,
            Qt.Key_S: lambda: self.save_project(),
        }

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self.scene.undo(); return
            if event.key() == Qt.Key_Y:
                self.scene.redo(); return
            if event.key() == Qt.Key_S:
                self.save_project(); return
        super().keyPressEvent(event)

    def change_tool(self, t):
        self.scene.set_tool(t)

    def choose_color(self):
        c = QColorDialog.getColor(initial=self.current_color, parent=self)
        if c.isValid():
            self.current_color = c
            self.scene.set_pen(c, self.size_spin.value())

    def change_size(self, v):
        self.scene.set_pen(self.current_color, v)

    def clear_board(self):
        reply = QMessageBox.question(self, "Clear", "Clear the board?", QMessageBox.Yes | QMessageBox.No)
        if reply==QMessageBox.Yes:
            self.scene.clear_scene_items()
            self.scene.push_undo()

    def save_project(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Whiteboard Project (*.wbjson)")
        if not fname: return
        data = self.scene.serialize()
        with open(fname, "w") as f:
            f.write(data)
        QMessageBox.information(self, "Saved", "Project saved.")

    def load_project(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Whiteboard Project (*.wbjson)")
        if not fname: return
        with open(fname, "r") as f:
            data = f.read()
        self.scene.deserialize(data)
        self.scene.push_undo()

    def export_png(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export PNG", "", "PNG Image (*.png)")
        if not fname: return
        img = QImage(self.scene.width(), self.scene.height(), QImage.Format_ARGB32)
        img.fill(QColor("white"))
        p = QPainter(img)
        self.scene.render(p)
        p.end()
        img.save(fname)
        QMessageBox.information(self, "Exported", "Exported PNG.")

    def export_pdf(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not fname: return
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(fname)
        painter = QPainter(printer)
        self.scene.render(painter)
        painter.end()
        QMessageBox.information(self, "Exported", "Exported PDF.")

    def export_svg(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export SVG", "", "SVG Files (*.svg)")
        if not fname: return
        svg = QSvgGenerator()
        svg.setFileName(fname)
        svg.setSize(self.scene.sceneRect().size().toSize())
        svg.setViewBox(self.scene.sceneRect())
        painter = QPainter(svg)
        self.scene.render(painter)
        painter.end()
        QMessageBox.information(self, "Exported", "Exported SVG.")

    def add_bg_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Import Image", "", "Images (*.png *.jpg *.bmp)")
        if not fname: return
        pix = QPixmap(fname)
        pi = self.scene.addPixmap(pix.scaled(self.scene.width(), self.scene.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        pi.setZValue(-2)
        pi.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.scene.push_undo()

    def delete_selected(self):
        for it in self.scene.selectedItems():
            self.scene.removeItem(it)
        self.scene.push_undo()

    def toggle_autosave(self, v):
        if v:
            self.autosave_timer = QTimer(self); self.autosave_timer.timeout.connect(self.autosave); self.autosave_timer.start(15000)
        else:
            try: self.autosave_timer.stop()
            except: pass

    def autosave(self):
        t = int(time.time())
        fname = f"autosave_{t}.wbjson"
        with open(fname,"w") as f:
            f.write(self.scene.serialize())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = WhiteboardMain()
    w.show()
    sys.exit(app.exec_())