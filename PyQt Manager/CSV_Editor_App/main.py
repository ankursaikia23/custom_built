import sys
from PyQt5.QtWidgets import QApplication
from ui_main import CSVEditor

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = CSVEditor()
    editor.show()
    sys.exit(app.exec_())
