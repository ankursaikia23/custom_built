import sys
from PyQt5.QtWidgets import QApplication
from app import BookkeepingApp

def main():
    app=QApplication(sys.argv)
    window=BookkeepingApp()
    window.show()
    sys.exit(app.exec_())

if __name__=="__main__":
    main()