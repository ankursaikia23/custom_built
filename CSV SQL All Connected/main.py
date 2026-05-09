import sys
from PyQt6.QtWidgets import QApplication
from app import CSVSQLApp

if __name__ == "__main__":
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    window = CSVSQLApp()
    window.showMaximized()
    app.exec()