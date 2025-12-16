import sys, os, pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget,
    QFileDialog, QLabel, QHBoxLayout, QListWidgetItem, QDialog, QTextEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt

class SilentMessage(QDialog):
    def __init__(self, title, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText(text)
        layout.addWidget(self.text)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    @staticmethod
    def show_message(title, text, parent=None):
        dlg = SilentMessage(title, text, parent)
        dlg.exec_()

class ExcelToCSV(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel → CSV (Editable Sheet Names, Silent)")
        self.resize(600, 400)
        self.entries = []
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        info = QLabel("1. Select Excel files (.xlsx, .xls, .xlsm)\n"
                      "2. Double-click any sheet name to rename\n"
                      "3. Click Convert to create CSVs with edited names")
        info.setWordWrap(True)
        layout.addWidget(info)

        row = QHBoxLayout()
        b1 = QPushButton("Select Excel files")
        b1.clicked.connect(self.select_files)
        row.addWidget(b1)
        b2 = QPushButton("Clear list")
        b2.clicked.connect(self.clear_list)
        row.addWidget(b2)
        layout.addLayout(row)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.edit_item)
        layout.addWidget(self.list_widget)

        row2 = QHBoxLayout()
        b3 = QPushButton("Convert")
        b3.clicked.connect(self.convert)
        row2.addWidget(b3)
        b4 = QPushButton("Quit")
        b4.clicked.connect(self.close)
        row2.addWidget(b4)
        layout.addLayout(row2)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Excel files", os.path.expanduser("~"),
            "Excel files (*.xlsx *.xls *.xlsm);;All files (*.*)"
        )
        if not files:
            return
        added = 0
        for f in files:
            try:
                sheets = pd.ExcelFile(f).sheet_names
                for s in sheets:
                    outname = f"{os.path.splitext(os.path.basename(f))[0]}__{s}.csv"
                    self.entries.append((f, s, outname))
                    item = QListWidgetItem(outname)
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    self.list_widget.addItem(item)
                    added += 1
            except Exception as e:
                SilentMessage.show_message("Error", f"Failed to read {f}:\n{e}", self)
        if added:
            SilentMessage.show_message("Sheets Loaded", f"Loaded {added} sheet(s).", self)

    def clear_list(self):
        self.entries.clear()
        self.list_widget.clear()

    def edit_item(self, item):
        self.list_widget.editItem(item)

    def convert(self):
        if not self.entries:
            SilentMessage.show_message("No Sheets", "Please select Excel files first.", self)
            return

        for i in range(self.list_widget.count()):
            self.entries[i] = (
                self.entries[i][0],
                self.entries[i][1],
                self.list_widget.item(i).text().strip()
            )

        created, failed = [], []
        for path, sheet, outname in self.entries:
            try:
                df = pd.read_excel(path, sheet_name=sheet)
                outdir = os.path.dirname(path)
                outpath = os.path.join(outdir, outname)
                df.to_csv(outpath, index=False)
                created.append(outpath)
            except Exception as e:
                failed.append((outname, str(e)))

        msg = ""
        if created:
            msg += "Created:\n" + "\n".join(created)
        if failed:
            msg += "\n\nFailed:\n" + "\n".join(f"{x}: {y}" for x, y in failed)
        SilentMessage.show_message("Conversion Finished", msg or "No output created.", self)

def main():
    app = QApplication(sys.argv)
    w = ExcelToCSV()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()