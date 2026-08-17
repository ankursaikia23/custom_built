from PyQt6.QtWidgets import QSlider
from PyQt6.QtCore import Qt

class ZoomPlugin:
    def __init__(self,window):
        self.window=window
        self.zoom=100
        self.slider=QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(50,200)
        self.slider.setValue(100)
        self.slider.valueChanged.connect(self.change_zoom)

    def widget(self):
        return self.slider

    def change_zoom(self,value):
        self.zoom=value
        self.window.table.setStyleSheet(f"QTableWidget{{font-size:{value//10}pt;}}")