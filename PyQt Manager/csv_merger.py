import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QListWidget, QMessageBox
)
from PyQt5.QtCore import Qt

class CSV_Merger(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Merger (Drag & Drop to Reorder)")
        self.resize(500, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.btn_select = QPushButton("Choose CSV Files")
        self.btn_select.clicked.connect(self.choose_files)
        layout.addWidget(self.btn_select)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        self.file_list.setDragDropMode(QListWidget.InternalMove)
        self.file_list.setDefaultDropAction(Qt.MoveAction)
        layout.addWidget(self.file_list)

        self.btn_merge = QPushButton("Merge CSVs In This Order")
        self.btn_merge.clicked.connect(self.merge_csv)
        layout.addWidget(self.btn_merge)

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select CSV Files", "", "CSV Files (*.csv)"
        )
        if files:
            self.file_list.clear()
            self.file_list.addItems(files)

    def merge_csv(self):
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "No Files", "Please select CSV files first.")
            return

        try:
            ordered_files = [
                self.file_list.item(i).text()
                for i in range(self.file_list.count())
            ]

            frames = [pd.read_csv(f) for f in ordered_files]
            merged = pd.concat(frames, ignore_index=True)

            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save Merged CSV", "merged.csv", "CSV Files (*.csv)"
            )

            if save_path:
                merged.to_csv(save_path, index=False)
                QMessageBox.information(
                    self, "Success", f"Merged CSV saved to:\n{save_path}"
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSV_Merger()
    window.show()
    sys.exit(app.exec_())