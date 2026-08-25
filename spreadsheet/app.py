import sys
from PyQt6.QtWidgets import QApplication, QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spreadsheet")
        self.resize(1200,800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6f8;
            }
        """)

def main():
    app=QApplication(sys.argv)
    app.setApplicationName("Spreadsheet")
    app.setOrganizationName("Spreadsheet")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")
    window=MainWindow()
    window.show()
    sys.exit(app.exec())
if __name__=="__main__":
    main()