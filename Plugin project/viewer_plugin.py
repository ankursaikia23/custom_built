import os
import fitz
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage,QPixmap
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QScrollArea,QSpinBox,QFrame,QSizePolicy

class ViewerScrollArea(QScrollArea):
    def __init__(self,viewer):
        super().__init__()
        self.viewer=viewer

    def wheelEvent(self,event):
        if self.viewer.current_type in ("image","pdf"):
            delta=event.angleDelta().y()
            if delta==0:
                event.accept()
                return
            current=self.viewer.scale.value()
            step=10
            new_value=current+step if delta>0 else current-step
            new_value=max(1,min(500,new_value))
            if new_value!=current:
                self.viewer.zoom_at_cursor(event.position().toPoint(),new_value)
            event.accept()
            return
        super().wheelEvent(event)
        
class ViewerPlugin(QWidget):
    def __init__(self,spreadsheet):
        super().__init__(spreadsheet)
        self.spreadsheet=spreadsheet
        self.current_path=None
        self.current_type=None
        self.image=None
        self.pdf_document=None
        self.pdf_pages=[]
        self.last_zoom_pos=None
        self.last_scale=100
        self.expanded=True
        self.setMinimumWidth(250)
        self.header=QHBoxLayout()
        self.header.setContentsMargins(4,4,4,4)
        self.header.setSpacing(5)
        self.toggle_button=QPushButton("☰")
        self.toggle_button.setFixedSize(30,28)
        self.toggle_button.clicked.connect(self.toggle)
        self.header.addWidget(self.toggle_button)
        self.title=QLabel("Viewer")
        self.title.setStyleSheet("font-weight:bold;")
        self.header.addWidget(self.title)
        self.header.addStretch()
        self.scale_label=QLabel("Scale")
        self.header.addWidget(self.scale_label)
        self.scale=QSpinBox()
        self.scale.setRange(1,500)
        self.scale.setValue(100)
        self.scale.setSuffix("%")
        self.scale.setFixedWidth(80)
        self.scale.valueChanged.connect(self.change_scale)
        self.header.addWidget(self.scale)
        self.main_layout=QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        self.main_layout.addLayout(self.header)
        self.frame=QFrame()
        self.frame_layout=QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(0,0,0,0)
        self.frame_layout.setSpacing(0)
        self.scroll_area=ViewerScrollArea(self)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.image_label=QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
        self.scroll_area.setWidget(self.image_label)
        self.frame_layout.addWidget(self.scroll_area)
        self.frame.setVisible(True)
        self.main_layout.addWidget(self.frame)
        self.show_message("Select an image or PDF")
    
    def show_message(self,text):
        self.image_label.clear()
        self.image_label.setText(text)
        self.image_label.setMinimumSize(0,0)
        self.title.setText("Viewer")
        self.current_path=None
        self.current_type=None
        self.image=None
        self.pdf_pages=[]
        self.pdf_document=None
        self.scale.blockSignals(True)
        self.scale.setValue(100)
        self.scale.blockSignals(False)
    
    def toggle(self):
        if self.expanded:
            self.expanded=False
            self.toggle_button.setText("☰")
            self.setMinimumWidth(0)
            self.setMaximumWidth(30)
            self.frame.hide()
            self.title.hide()
            self.scale_label.hide()
            self.scale.hide()
            if hasattr(self.spreadsheet,"viewer_splitter"):
                self.spreadsheet.viewer_splitter.setSizes([self.spreadsheet.viewer_splitter.width()-30,30])
        else:
            self.expanded=True
            self.toggle_button.setText("☰")
            self.setMaximumWidth(16777215)
            self.frame.show()
            self.title.show()
            self.scale_label.show()
            self.scale.show()
            if hasattr(self.spreadsheet,"viewer_splitter"):
                total=self.spreadsheet.viewer_splitter.width()
                half=max(250,total//2)
                self.spreadsheet.viewer_splitter.setSizes([half,half])
    
    def zoom_at_cursor(self,pos,value):
        old_scale=self.scale.value()
        if old_scale==value:
            return
        old_x=self.scroll_area.horizontalScrollBar().value()
        old_y=self.scroll_area.verticalScrollBar().value()
        viewport_pos=pos
        image_x=old_x+viewport_pos.x()
        image_y=old_y+viewport_pos.y()
        self.scale.blockSignals(True)
        self.scale.setValue(value)
        self.scale.blockSignals(False)
        self.display_current()
        ratio=value/old_scale
        new_x=int(image_x*ratio-viewport_pos.x())
        new_y=int(image_y*ratio-viewport_pos.y())
        self.scroll_area.horizontalScrollBar().setValue(max(0,new_x))
        self.scroll_area.verticalScrollBar().setValue(max(0,new_y))
    
    def change_scale(self,value):
        if self.current_type in ("image","pdf"):
            self.display_current()
    
    def display_image(self):
        if self.image is None or self.image.isNull():
            return
        scale=self.scale.value()/100.0
        width=max(1,int(self.image.width()*scale))
        height=max(1,int(self.image.height()*scale))
        pixmap=QPixmap.fromImage(self.image)
        pixmap=pixmap.scaled(width,height,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(pixmap.size())
        self.image_label.setMinimumSize(pixmap.size())
    
    def display_pdf(self):
        if not self.pdf_pages:
            return
        scale=self.scale.value()/100.0
        pixmaps=[]
        total_width=0
        total_height=0
        spacing=15
        for page_image in self.pdf_pages:
            width=max(1,int(page_image.width()*scale))
            height=max(1,int(page_image.height()*scale))
            pixmap=QPixmap.fromImage(page_image).scaled(width,height,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            pixmaps.append(pixmap)
            total_width=max(total_width,pixmap.width())
            total_height+=pixmap.height()
        if len(pixmaps)>1:
            total_height+=spacing*(len(pixmaps)-1)
        canvas=QPixmap(max(1,total_width),max(1,total_height))
        canvas.fill(Qt.GlobalColor.white)
        painter=None
        from PyQt6.QtGui import QPainter
        painter=QPainter(canvas)
        y=0
        for pixmap in pixmaps:
            x=(total_width-pixmap.width())//2
            painter.drawPixmap(x,y,pixmap)
            y+=pixmap.height()+spacing
        painter.end()
        self.image_label.setPixmap(canvas)
        self.image_label.resize(canvas.size())
        self.image_label.setMinimumSize(canvas.size())
    
    def display_current(self):
        if self.current_type=="image":
            self.display_image()
        elif self.current_type=="pdf":
            self.display_pdf()
    
    def show_file(self,path):
        if not path:
            self.show_message("Select an image or PDF")
            return
        path=os.path.abspath(path)
        if not os.path.exists(path):
            self.show_message("File not found:\n"+path)
            return
        self.current_path=path
        self.title.setText(os.path.basename(path))
        self.scale.blockSignals(True)
        self.scale.setValue(100)
        self.scale.blockSignals(False)
        self.image_label.clear()
        self.image=None
        self.pdf_pages=[]
        self.pdf_document=None
        ext=os.path.splitext(path)[1].lower()
        if ext==".pdf":
            try:
                document=fitz.open(path)
                if document.page_count==0:
                    document.close()
                    self.show_message("Unable to load PDF")
                    return
                self.current_type="pdf"
                self.pdf_document=document
                for page_number in range(document.page_count):
                    page=document.load_page(page_number)
                    pixmap=page.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
                    image=QImage(pixmap.samples,pixmap.width,pixmap.height,pixmap.stride,QImage.Format.Format_RGB888).copy()
                    if not image.isNull():
                        self.pdf_pages.append(image)
                if not self.pdf_pages:
                    document.close()
                    self.show_message("Unable to render PDF")
                    return
                self.display_pdf()
            except Exception:
                self.show_message("Unable to load PDF")
            return
        image=QImage(path)
        if image.isNull():
            self.show_message("Unable to load image")
            return
        self.current_type="image"
        self.image=image
        self.display_image()
    
    def show_cell(self,row,col):
        image_path=self.spreadsheet.image_plugin.image_path(row,col)
        if image_path:
            self.show_file(image_path)
            return
        pdf_path=self.spreadsheet.pdf_plugin.pdf_path(row,col)
        if pdf_path:
            self.show_file(pdf_path)
            return
        self.clear()
    
    def clear(self):
        self.show_message("Select an image or PDF")