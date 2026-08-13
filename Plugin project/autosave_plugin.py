from PyQt6.QtCore import QTimer

class AutoSavePlugin:
    def __init__(self,window):
        self.window=window
        self.timer=QTimer()
        self.timer.timeout.connect(self.autosave)
        self.timer.start(300000)
        
    def autosave(self):
        if hasattr(self.window,"file_plugin") and self.window.file_plugin.current_file:
            self.window.file_plugin.save_file(auto=True)