class ThemePlugin:
    def __init__(self,window):
        self.window=window
        self.dark=False
    
    def apply_dark(self):
        self.dark=True
        self.window.setStyleSheet("QMainWindow{background:#202020;}QTableWidget{background:#303030;color:white;}")
    
    def apply_light(self):
        self.dark=False
        self.window.setStyleSheet("")
    
    def toggle(self):
        if self.dark:
            self.apply_light()
        else:
            self.apply_dark()