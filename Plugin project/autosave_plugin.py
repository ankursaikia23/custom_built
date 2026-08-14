from PyQt6.QtCore import QTimer

class AutoSavePlugin:
    def __init__(self,window):
        self.window=window
        self.timer=QTimer()
        self.timer.timeout.connect(self.autosave)
        self.timer.start(300000)

    def autosave(self):
        if not hasattr(self.window,"file_plugin"):
            return
        if not self.window.file_plugin.current_file:
            return
        if not getattr(self.window,"is_modified",False):
            return
        self.window.file_plugin.autosave_file()