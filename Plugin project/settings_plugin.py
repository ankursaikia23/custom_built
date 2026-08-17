from PyQt6.QtCore import QSettings

class SettingsPlugin:
    def __init__(self,window):
        self.window=window
        self.settings=QSettings("CustomBuilt","Spreadsheet")

    def save_setting(self,key,value):
        self.settings.setValue(key,value)

    def get_setting(self,key,default=None):
        return self.settings.value(key,default)

    def save_window_state(self):
        self.save_setting("geometry",self.window.saveGeometry())
        self.save_setting("state",self.window.saveState())

    def restore_window_state(self):
        geometry=self.get_setting("geometry")
        state=self.get_setting("state")
        if geometry:
            self.window.restoreGeometry(geometry)
        if state:
            self.window.restoreState(state)