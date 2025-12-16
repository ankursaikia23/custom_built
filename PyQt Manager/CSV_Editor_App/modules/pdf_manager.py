from PyQt5.QtCore import QThread, pyqtSignal
import PyPDF2

class PDFLoaderThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        text = ""
        try:
            with open(self.path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except:
            text = "Failed to load PDF"
        self.finished.emit(text)
