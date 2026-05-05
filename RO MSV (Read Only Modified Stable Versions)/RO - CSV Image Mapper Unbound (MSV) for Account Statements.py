import sys
import os
import csv
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QSplitter, QComboBox, QDialog,
    QMessageBox
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap, QIcon, QColor

LOCK_COLOR = QColor(220, 220, 220)
MOD_COLOR = QColor(128, 0, 32)

COMMON_DATE_FORMATS = [
    "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d",
    "%m-%d-%Y", "%d-%m-%Y", "%Y-%m-%d",
    "%m.%d.%Y", "%d.%m.%Y", "%Y.%m.%d",
    "%m_%d_%Y", "%d_%m_%Y", "%Y_%m_%d",
    "%m %d %Y", "%d %m %Y", "%Y %m %d",
]

def normalize_date(value, manual_fmt=None):
    value = value.strip()
    if manual_fmt:
        try:
            return datetime.strptime(value, manual_fmt).strftime("%Y-%m-%d")
        except:
            pass
    for fmt in COMMON_DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except:
            continue
    try:
        parts = value.replace("-", "/").split("/")
        if len(parts) == 3:
            m, d, y = parts
            return datetime(int(y), int(m), int(d)).strftime("%Y-%m-%d")
    except:
        pass
    return None

class ImageViewer(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.original = None
        self.scale = 1.0
        self.current_path = None

    def set_image(self, path):
        pix = QPixmap(path)
        if pix.isNull():
            return
        self.original = pix
        self.scale = 1.0
        self.current_path = path
        self.update_view()

    def update_view(self):
        if not self.original:
            return
        viewer_width = self.width()
        viewer_height = self.height()
        scaled_width = int(viewer_width * self.scale)
        scaled_height = int(viewer_height * self.scale)    
        scaled_width = min(scaled_width, viewer_width)
        scaled_height = min(scaled_height, viewer_height)
        self.setPixmap(self.original.scaled(
            scaled_width,
            scaled_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def resizeEvent(self, e):
        self.update_view()

    def wheelEvent(self, e):
        if not self.original:
            return
        self.scale *= 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self.scale = max(0.1, min(10, self.scale))
        self.update_view()

class ColumnSelector(QDialog):
    def __init__(self, headers):
        super().__init__()
        self.combo = QComboBox()
        self.combo.addItems(headers)
        btn = QPushButton("Select")
        layout = QVBoxLayout(self)
        layout.addWidget(self.combo)
        layout.addWidget(btn)
        btn.clicked.connect(self.accept)

    def index(self):
        return self.combo.currentIndex()

class FocusSelector(QDialog):
    def __init__(self, headers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Columns")
        self.checkboxes = []
        layout = QVBoxLayout(self)
        for header in headers:
            cb = QPushButton(header)
            cb.setCheckable(True)
            cb.setChecked(True)
            self.checkboxes.append(cb)
            layout.addWidget(cb)
        btn_layout = QHBoxLayout()
        select_all = QPushButton("Select All")
        remove_all = QPushButton("Remove All")
        alternate = QPushButton("Select Alternate")
        apply_btn = QPushButton("Apply")
        btn_layout.addWidget(select_all)
        btn_layout.addWidget(remove_all)
        btn_layout.addWidget(alternate)
        layout.addLayout(btn_layout)
        layout.addWidget(apply_btn)
        select_all.clicked.connect(self.select_all)
        remove_all.clicked.connect(self.remove_all)
        alternate.clicked.connect(self.select_alternate)
        apply_btn.clicked.connect(self.accept)

    def selected_columns(self):
        return [i for i, cb in enumerate(self.checkboxes) if cb.isChecked()]

    def select_all(self):
        for cb in self.checkboxes:
            cb.setChecked(True)

    def remove_all(self):
        for cb in self.checkboxes:
            cb.setChecked(False)

    def select_alternate(self):
        for i, cb in enumerate(self.checkboxes):
            cb.setChecked(i % 2 == 0)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("CSVImageApp", "Mapper")
        self.csv_path = None
        self.image_folder = None
        self.headers = []
        self.ref_col = None
        self.insert_col = None
        self.locked_columns = set()
        self.original_rows = []
        self.dirty = False
        self._switching_mode = False
        self.focus_mode = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MAPPER")
        self.setWindowState(Qt.WindowMaximized)    
        self.csv_btn = QPushButton("LOAD CSV")
        self.csv_status = QLabel("NONE")    
        self.img_btn = QPushButton("LOAD FOLDER")
        self.img_status = QLabel("NONE")    
        self.ref_combo = QComboBox()
        self.ref_combo.setEnabled(False)        
        self.ins_combo = QComboBox()
        self.ins_combo.setEnabled(False)
        self.date_fmt = QComboBox()
        self.date_fmt.setEditable(True)
        self.date_fmt.addItems(["Auto Detect", "MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])    
        self.modify_btn = QPushButton("MODIFY")
        self.focus_btn = QPushButton("FOCUSED VIEW")
        self.clear_col_btn = QPushButton("CLEAR COLUMN")
        self.revert_btn = QPushButton("REVERT CHANGES")
        self.switch_combo = QComboBox()
        self.switch_combo.addItems(["MAPPER", "VIEWER", "RESOLVER"])
        self.switch_combo.setCurrentText("MAPPER")
        self.save_btn = QPushButton("SAVE")
        self.exit_btn = QPushButton("EXIT")    
        main = QHBoxLayout(self)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
    
        for b in [
            self.csv_btn,
            self.img_btn,
            self.modify_btn,
            self.focus_btn,
            self.clear_col_btn,
            self.revert_btn,
            self.switch_combo,
            self.save_btn,
            self.exit_btn
        ]:
            b.setStyleSheet("text-align: left;")
    
        sidebar_layout.addWidget(self.csv_btn)
        sidebar_layout.addWidget(self.csv_status) 
        sidebar_layout.addWidget(self.img_btn)
        sidebar_layout.addWidget(self.img_status)
        sidebar_layout.addWidget(QLabel("SELECT REF COLUMN"))
        sidebar_layout.addWidget(self.ref_combo)        
        sidebar_layout.addWidget(QLabel("SELECT INSERT COLUMN"))
        sidebar_layout.addWidget(self.ins_combo)
        sidebar_layout.addWidget(QLabel("DATE FORMAT"))
        sidebar_layout.addWidget(self.date_fmt)
        sidebar_layout.addWidget(self.modify_btn)
        sidebar_layout.addWidget(self.focus_btn)
        sidebar_layout.addWidget(self.clear_col_btn)
        sidebar_layout.addWidget(self.revert_btn)
        sidebar_layout.addWidget(self.switch_combo)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.save_btn)
        sidebar_layout.addWidget(self.exit_btn)
        split = QSplitter(Qt.Horizontal)
        self.table = QTableWidget()
        self.viewer = ImageViewer()
        split.addWidget(self.table)
        split.addWidget(self.viewer)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        main.addWidget(sidebar)
        main.addWidget(split)
        self.csv_btn.clicked.connect(self.toggle_csv)
        self.img_btn.clicked.connect(self.toggle_images)
        self.ref_combo.currentIndexChanged.connect(self.validate_ref_selection)
        self.ins_combo.currentIndexChanged.connect(self.validate_insert_selection)
        self.modify_btn.clicked.connect(self.modify)
        self.clear_col_btn.clicked.connect(self.clear_column)
        self.revert_btn.clicked.connect(self.revert_changes)
        self.save_btn.clicked.connect(self.save)
        self.switch_combo.currentTextChanged.connect(self.switch_mode)
        self.focus_btn.clicked.connect(self.toggle_focus_view)
        self.exit_btn.clicked.connect(self.close) 
        self.table.itemChanged.connect(self.mark_modified)
        self.table.itemSelectionChanged.connect(self.update_image)
        self.table.horizontalHeader().sectionClicked.connect(self.toggle_column_lock)
        
    def generate_meta(self, save_path):
        meta_path = save_path + ".meta.json"
        data = {}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item and item.data(Qt.UserRole):
                    key = f"{r},{c}"
                    filename = os.path.basename(item.data(Qt.UserRole))
                    data[key] = {"path": filename, "updated_at": timestamp}
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = {}
        existing.update(data)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=4)

    def switch_mode(self, mode):
        if mode == "MAPPER":
            return
        if self.dirty:
            res = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Switch without saving?",
                QMessageBox.Ok | QMessageBox.Cancel
            )
            if res != QMessageBox.Ok:
                self.switch_combo.setCurrentText("EDITOR")
                return
        if mode == "RESOLVER":
            self.r = Resolver()
            self.r.show()
        elif mode == "VIEWER":
            self.v = Viewer()
            self.v.show()
        self._switching_mode = True
        self.close()

    def toggle_focus_view(self):
        if not self.headers:
            return
        if not self.focus_mode:
            dlg = FocusSelector(self.headers, self)
            if dlg.exec_():
                selected = dlg.selected_columns()
                for col in range(self.table.columnCount()):
                    self.table.setColumnHidden(col, col not in selected)
                self.focus_btn.setText("IN FOCUS")
                self.focus_btn.setStyleSheet("background-color: #4CAF50; color: white;")
                self.focus_mode = True
        else:
            for col in range(self.table.columnCount()):
                self.table.setColumnHidden(col, False)
            self.focus_btn.setText("FOCUSED VIEW")
            self.focus_btn.setStyleSheet("")
            self.focus_mode = False

    def populate_table(self, rows):
        self.table.blockSignals(True)
        self.table.setColumnCount(len(self.headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(self.headers)
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                item = QTableWidgetItem(v)
                if v.strip():
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setData(Qt.UserRole, "original")
                self.table.setItem(r, c, item)
        self.table.blockSignals(False)

    def load_csv(self, path):
        self.csv_path = path
        self.locked_columns.clear()
        self.dirty = False
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.headers = rows[0]
        self.ref_combo.blockSignals(True)
        self.ins_combo.blockSignals(True)     
        self.ref_combo.clear()
        self.ins_combo.clear()
        self.ref_combo.addItems(self.headers)
        self.ins_combo.addItems(self.headers)
        self.ref_combo.setCurrentIndex(-1)
        self.ins_combo.setCurrentIndex(-1)
        self.ref_combo.setEnabled(True)
        self.ins_combo.setEnabled(True)
        self.ref_combo.blockSignals(False)
        self.ins_combo.blockSignals(False)
        self.original_rows = rows[1:]
        self.populate_table(self.original_rows)
        self.csv_status.setText(os.path.basename(path))
        self.csv_btn.setText("UNLOAD CSV")

    def toggle_csv(self):
        if self.csv_path:
            self.table.clear()
            self.csv_path = None
            self.headers = []
            self.original_rows = []
            self.csv_btn.setText("LOAD CSV")
            self.csv_status.setText("None")
            return
        path, _ = QFileDialog.getOpenFileName(self, "CSV", "", "CSV (*.csv)")
        if path:
            self.load_csv(path)

    def toggle_images(self):
        if self.image_folder:
            self.image_folder = None
            self.img_status.setText("NONE")
            self.img_btn.setText("LOAD FOLDER")
            return
        folder = QFileDialog.getExistingDirectory(self, "Images")
        if folder:
            self.image_folder = folder
            self.img_status.setText(os.path.basename(folder))
            self.img_btn.setText("UNLOAD FOLDER")
            
    def validate_ref_selection(self):
        if self.table.rowCount() == 0:
            return
        index = self.ref_combo.currentIndex()
        if index < 0:
            return
        if index == self.ins_combo.currentIndex():
            QMessageBox.warning(self, "Invalid Selection",
                                "Reference and Insert columns cannot be the same.")
            self.ref_combo.setCurrentIndex(-1)
            self.ref_col = None
            return
        if not self.is_date_column(index):
            QMessageBox.warning(self, "Invalid Reference Column",
                                "Reference column must contain valid dates.")
            self.ref_combo.setCurrentIndex(-1)
            self.ref_col = None
            return
        self.ref_col = index
    
    def validate_insert_selection(self):
        index = self.ins_combo.currentIndex()
        if index < 0:
            return
        if index == self.ref_combo.currentIndex():
            QMessageBox.warning(self, "Invalid Selection",
                                "Insert and Reference columns cannot be the same.")
            self.ins_combo.setCurrentIndex(-1)
            self.insert_col = None
            return
        self.insert_col = index

    def is_date_column(self, col_index):
        valid_count = 0
        invalid_count = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, col_index)
            if not item:
                continue
            value = item.text().strip()
            if not value:
                continue
            if normalize_date(value):
                valid_count += 1
            else:
                invalid_count += 1
        return valid_count > 0 and invalid_count <= valid_count

    def toggle_column_lock(self, col):
        header = self.headers[col]
        self.locked_columns.symmetric_difference_update({col})
        locked = col in self.locked_columns
        self.table.horizontalHeaderItem(col).setText(header + (" 🔒" if locked else ""))
        for row in range(self.table.rowCount()):
            item = self.table.item(row, col)
            if not item:
                continue
            if locked:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(LOCK_COLOR)
            else:
                if item.data(Qt.UserRole) != "original":
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setBackground(Qt.white)

    def mark_modified(self, item):
        if item.data(Qt.UserRole) == "original":
            return
        item.setForeground(MOD_COLOR)
        self.dirty = True

    def modify(self):
        if None in (self.ref_col, self.insert_col) or not self.image_folder:
            return
        text = self.date_fmt.currentText()
        manual_fmt = text if "%" in text else None
        images = {os.path.splitext(f)[0]: os.path.join(self.image_folder, f)
                  for f in os.listdir(self.image_folder)}
        overwrite_count = 0
        for r in range(self.table.rowCount()):
            ref = self.table.item(r, self.ref_col)
            if not ref:
                continue
            key = normalize_date(ref.text(), manual_fmt)
            if key and key in images:
                existing_item = self.table.item(r, self.insert_col)
                if existing_item and existing_item.data(Qt.UserRole):
                    overwrite_count += 1
        if overwrite_count > 0:
            res = QMessageBox.question(
                self,
                "Overwrite Warning",
                f"{overwrite_count} existing image(s) will be overwritten. Continue?",
                QMessageBox.Ok | QMessageBox.Cancel
            )
            if res != QMessageBox.Ok:
                return
        for r in range(self.table.rowCount()):
            ref = self.table.item(r, self.ref_col)
            if not ref:
                continue
            key = normalize_date(ref.text(), manual_fmt)
            if key and key in images:
                item = QTableWidgetItem(key)
                item.setIcon(QIcon(QPixmap(images[key]).scaled(48, 48, Qt.KeepAspectRatio)))
                item.setData(Qt.UserRole, images[key])
                item.setForeground(MOD_COLOR)
                self.table.setItem(r, self.insert_col, item)
        self.dirty = True
        inserted_cells = 0
        for r in range(self.table.rowCount()):
            item = self.table.item(r, self.insert_col)
            if item and item.text().strip() != "":
                inserted_cells += 1    
        remaining_cells = self.table.rowCount() - inserted_cells
        msg = QMessageBox()
        msg.setWindowTitle("Insert Column Completed")
        msg.setText(f"Cells inserted: {inserted_cells}\nCells remaining: {remaining_cells}")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def clear_column(self):
        col = self.table.currentColumn()
        if col < 0 or col in self.locked_columns:
            return
        res = QMessageBox.question(self, "Clear Column",
                                   "Are you sure you want to clear this column?",
                                   QMessageBox.Yes | QMessageBox.Cancel)
        if res != QMessageBox.Yes:
            return
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, col)
            if not item:
                continue
            if item.data(Qt.UserRole) == "original":
                continue
            item.setText("")
            item.setIcon(QIcon())
            item.setData(Qt.UserRole, None)
            item.setForeground(MOD_COLOR)
        self.table.blockSignals(False)
        self.dirty = True
        cleared_cells = 0
        for r in range(self.table.rowCount()):
            item = self.table.item(r, col)
            if item and item.text().strip() == "":
                cleared_cells += 1
        msg = QMessageBox()
        msg.setWindowTitle("Column Cleared")
        msg.setText(f"Column '{self.headers[col]}' cleared.\nTotal cells cleared: {cleared_cells}")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def revert_changes(self):
        if not self.dirty:
            return
        res = QMessageBox.question(self, "Revert",
                                   "Revert all changes?",
                                   QMessageBox.Yes | QMessageBox.Cancel)
        if res == QMessageBox.Yes:
            self.populate_table(self.original_rows)
            self.dirty = False

    def update_image(self):
        items = self.table.selectedItems()
        if items:
            path = items[0].data(Qt.UserRole)
            if path and os.path.exists(path):
                self.viewer.set_image(path)

    def save(self):
        if not self.csv_path:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)
            for r in range(self.table.rowCount()):
                writer.writerow([
                    self.table.item(r, c).text() if self.table.item(r, c) else ""
                    for c in range(self.table.columnCount())
                ])
        self.generate_meta(path)
        self.dirty = False

    def closeEvent(self, event):
        if self._switching_mode:
            event.accept()
            return
        if self.dirty:
            res = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Exit without saving?",
                QMessageBox.Yes | QMessageBox.Cancel
            )
            if res != QMessageBox.Yes:
                event.ignore()
                return
        event.accept()

class Viewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Image Viewer")
        self.setWindowState(Qt.WindowMaximized)
        self.meta = {}
        self.csv_path = None
        self.meta_path = None
        self.focus_mode = False
        self.image_folder = None
        self.image_index = {}
        self.csv_btn = QPushButton("LOAD CSV")
        self.csv_status = QLabel("NONE")
        self.meta_btn = QPushButton("LOAD META")
        self.meta_status = QLabel("NONE")
        self.focus_btn = QPushButton("FOCUSED VIEW")
        self.switch_combo = QComboBox()
        self.switch_combo.addItems(["MAPPER", "VIEWER", "RESOLVER"])
        self.switch_combo.setCurrentText("VIEWER")
        main = QHBoxLayout(self)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
        buttons = [
            self.csv_btn,
            self.meta_btn,
            self.focus_btn,
            self.switch_combo
        ]
        for b in buttons:
            b.setStyleSheet("text-align: left;")
        sidebar_layout.addWidget(self.csv_btn)
        sidebar_layout.addWidget(self.csv_status)
        sidebar_layout.addWidget(self.meta_btn)
        sidebar_layout.addWidget(self.meta_status)
        sidebar_layout.addWidget(self.focus_btn)
        sidebar_layout.addWidget(self.switch_combo)
        sidebar_layout.addStretch()
        split = QSplitter(Qt.Horizontal)
        self.table = QTableWidget()
        self.viewer = ImageViewer()
        split.addWidget(self.table)
        split.addWidget(self.viewer)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        main.addWidget(sidebar)
        main.addWidget(split)
        self.csv_btn.clicked.connect(self.toggle_csv)
        self.meta_btn.clicked.connect(self.toggle_meta)
        self.switch_combo.currentTextChanged.connect(self.switch_mode)
        self.focus_btn.clicked.connect(self.toggle_focus_view)
        self.table.itemSelectionChanged.connect(self.show_image)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

    def switch_mode(self, mode):
        if mode == "VIEWER":
            return
        if mode == "MAPPER":
            self.e = App()
            self.e.show()
        elif mode == "RESOLVER":
            self.r = Resolver()
            self.r.show()
        self.close()

    def toggle_focus_view(self):
        if self.table.columnCount() == 0:
            return
        if not self.focus_mode:
            headers = [self.table.horizontalHeaderItem(i).text()
                       for i in range(self.table.columnCount())]
            dlg = FocusSelector(headers, self)
            if dlg.exec_():
                selected = dlg.selected_columns()
                for col in range(self.table.columnCount()):
                    self.table.setColumnHidden(col, col not in selected)
                self.focus_btn.setText("IN FOCUS")
                self.focus_btn.setStyleSheet("background-color: #4CAF50; color: white;")
                self.focus_mode = True
        else:
            for col in range(self.table.columnCount()):
                self.table.setColumnHidden(col, False)
            self.focus_btn.setText("FOCUSED VIEW")
            self.focus_btn.setStyleSheet("")
            self.focus_mode = False

    def toggle_csv(self):
        if self.csv_path:
            self.table.clear()
            self.csv_path = None
            self.csv_btn.setText("LOAD CSV")
            self.csv_status.setText("None")
            return
        path, _ = QFileDialog.getOpenFileName(self, "CSV", "", "CSV (*.csv)")
        if not path:
            return
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.table.setRowCount(len(rows) - 1)
        self.table.setColumnCount(len(rows[0]))
        self.table.setHorizontalHeaderLabels(rows[0])
        for r, row in enumerate(rows[1:]):
            for c, v in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(v))
        self.csv_path = path
        self.csv_btn.setText("UNLOAD CSV")
        self.csv_status.setText(os.path.basename(path))

    def toggle_meta(self):
        if self.meta_path:
            self.meta = {}
            self.meta_path = None
            self.meta_btn.setText("LOAD META")
            self.meta_status.setText("NONE")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Meta", "", "JSON (*.json)")
        if not path:
            return
        with open(path, encoding="utf-8") as f:
            self.meta = json.load(f)
        self.meta_path = path
        self.meta_btn.setText("UNLOAD META")
        self.meta_status.setText(os.path.basename(path))
        
    def auto_detect_image_folder(self, filename):
        search_roots = []
        if self.meta_path:
            search_roots.append(os.path.dirname(self.meta_path))
        if self.csv_path:
            search_roots.append(os.path.dirname(self.csv_path))
        checked = set()
        for root in search_roots:
            for dirpath, dirnames, filenames in os.walk(root):
                if dirpath in checked:
                    continue
                checked.add(dirpath)
                if filename in filenames:
                    return dirpath
        return None
    
    def build_image_index(self, folder):
        self.image_index = {}
        try:
            for f in os.listdir(folder):
                full_path = os.path.join(folder, f)
                if os.path.isfile(full_path):
                    self.image_index[f] = full_path
        except:
            pass

    def show_image(self):
        items = self.table.selectedItems()
        if not items:
            return
        r = items[0].row()
        c = items[0].column()
        key = f"{r},{c}"
        if key not in self.meta:
            return
        value = self.meta[key]
        filename = value.get("path") if isinstance(value, dict) else value
        if not filename:
            return
        if filename in self.image_index:
            self.viewer.set_image(self.image_index[filename])
            return
        if self.image_folder:
            path = os.path.join(self.image_folder, filename)
            if os.path.exists(path):
                self.viewer.set_image(path)
                return
        folder = self.auto_detect_image_folder(filename)
        if folder:
            self.image_folder = folder
            self.build_image_index(folder)
            if filename in self.image_index:
                self.viewer.set_image(self.image_index[filename])
                return
            path = os.path.join(folder, filename)
            if os.path.exists(path):
                self.viewer.set_image(path)
                return
        print(f"[WARN] Image not found: {filename}")
                
class Resolver(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Resolver")
        self.setWindowState(Qt.WindowMaximized)
        self.folder_a = None
        self.folder_b = None
        self.dirty = False
        self._switching_mode = False
        self.row_data = {}
        self.load_a_btn = QPushButton("LOAD FOLDER A")
        self.status_a = QLabel("NONE")
        self.load_b_btn = QPushButton("LOAD FOLDER B")
        self.status_b = QLabel("NONE")
        self.merge_btn = QPushButton("PREVIEW MERGE")
        self.select_mode_combo = QComboBox()
        self.select_mode_combo.addItems(["ALL A", "ALL B", "NONE"])
        self.save_btn = QPushButton("SAVE")
        self.exit_btn = QPushButton("EXIT")
        self.switch_combo = QComboBox()
        self.switch_combo.addItems(["MAPPER", "VIEWER", "RESOLVER"])
        self.switch_combo.setCurrentText("RESOLVER")
        main = QHBoxLayout(self)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
        for b in [self.load_a_btn, self.load_b_btn, self.merge_btn, self.switch_combo]:
            b.setStyleSheet("text-align: left;")
        sidebar_layout.addWidget(self.load_a_btn)
        sidebar_layout.addWidget(self.status_a)
        sidebar_layout.addWidget(self.load_b_btn)
        sidebar_layout.addWidget(self.status_b)
        sidebar_layout.addWidget(self.merge_btn)
        sidebar_layout.addWidget(self.select_mode_combo)
        sidebar_layout.addWidget(self.switch_combo)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.save_btn)
        sidebar_layout.addWidget(self.exit_btn)
        self.table = QTableWidget()
        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.table)
        self.viewer_widget = QWidget()
        viewer_layout = QVBoxLayout(self.viewer_widget)
        self.viewer_top = ImageViewer()
        self.viewer_separator = QLabel()
        self.viewer_separator.setFixedHeight(2)
        self.viewer_separator.setStyleSheet("background-color: black;")
        self.viewer_bottom = ImageViewer()
        viewer_layout.addWidget(self.viewer_top)
        viewer_layout.addWidget(self.viewer_separator)
        viewer_layout.addWidget(self.viewer_bottom)
        split.addWidget(self.viewer_widget)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        main.addWidget(sidebar)
        main.addWidget(split)
        self.load_a_btn.clicked.connect(self.load_a)
        self.load_b_btn.clicked.connect(self.load_b)
        self.merge_btn.clicked.connect(self.preview_merge)
        self.select_mode_combo.currentTextChanged.connect(self.apply_select_mode)
        self.save_btn.clicked.connect(self.save)
        self.exit_btn.clicked.connect(self.close)
        self.switch_combo.currentTextChanged.connect(self.switch_mode)
        self.table.cellClicked.connect(self.show_preview)

    def load_a(self):
        folder = QFileDialog.getExistingDirectory(self, "Folder A")
        if folder:
            self.folder_a = folder
            self.status_a.setText(os.path.basename(folder))

    def load_b(self):
        folder = QFileDialog.getExistingDirectory(self, "Folder B")
        if folder:
            self.folder_b = folder
            self.status_b.setText(os.path.basename(folder))

    def preview_merge(self):
        if not self.folder_a or not self.folder_b:
            return
        files_a = set(os.listdir(self.folder_a))
        files_b = set(os.listdir(self.folder_b))
        conflicts = sorted(list(files_a & files_b))
        self.auto_merge_files = list(files_a ^ files_b)
        self.table.setRowCount(len(conflicts))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Filename", "Action"])    
        self.row_data = {}
        for row_idx, f in enumerate(conflicts):
            self.table.setItem(row_idx, 0, QTableWidgetItem(f))    
            btn_a = QPushButton("A")
            btn_b = QPushButton("B")        
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(btn_a)
            layout.addWidget(btn_b)
            self.table.setCellWidget(row_idx, 1, container)
            self.row_data[row_idx] = {
                "files": [
                    os.path.join(self.folder_a, f),
                    os.path.join(self.folder_b, f)
                ],
                "choice": None
            }
            btn_a.clicked.connect(lambda _, r=row_idx: self.select_a(r))
            btn_b.clicked.connect(lambda _, r=row_idx: self.select_b(r))
        self.dirty = True

    def show_preview(self, row, col):
        data = self.row_data.get(row)
        if not data:
            return
        self.viewer_top.set_image(data["files"][0])
        self.viewer_bottom.set_image(data["files"][1])

    def select_a(self, row):
        data = self.row_data.get(row)
        if not data:
            return
        data["choice"] = "A"
        self.update_row_visual(row, selected="A")
    
    def select_b(self, row):
        data = self.row_data.get(row)
        if not data:
            return
        data["choice"] = "B"
        self.update_row_visual(row, selected="B")

    def update_row_visual(self, row, selected):
        for c in range(self.table.columnCount()):
            item = self.table.item(row, c)
            if item:
                item.setBackground(QColor(144, 238, 144))
        cell_widget = self.table.cellWidget(row, 1)
        if cell_widget:
            for i in range(cell_widget.layout().count()):
                w = cell_widget.layout().itemAt(i).widget()
                if isinstance(w, QPushButton):
                    if w.text() == selected:
                        w.setStyleSheet("background-color: green; color: white;")
                    else:
                        w.setStyleSheet("")

    def apply_select_mode(self, mode):
        for r in range(self.table.rowCount()):
            if mode == "ALL A":
                self.select_a(r)
            elif mode == "ALL B":
                self.select_b(r)
            elif mode == "NONE":
                data = self.row_data.get(r)
                if data:
                    data["choice"] = None
                    self.update_row_visual(r, selected=None)
        self.dirty = True

    def save(self):
        target = QFileDialog.getExistingDirectory(self, "Select Merged Folder")
        if not target:
            return
        for data in self.row_data.values():
            choice = data.get("choice")
            if choice == "A":
                f = data["files"][0]
            elif choice == "B":
                f = data["files"][1]
            else:
                continue
            if os.path.exists(f):
                import shutil
                shutil.copy2(f, os.path.join(target, os.path.basename(f)))
                        
        if hasattr(self, "auto_merge_files"):
            import shutil
            for f in self.auto_merge_files:
                path_a = os.path.join(self.folder_a, f)
                path_b = os.path.join(self.folder_b, f)
                if os.path.exists(path_a):
                    shutil.copy2(path_a, os.path.join(target, f))
                elif os.path.exists(path_b):
                    shutil.copy2(path_b, os.path.join(target, f))
        QMessageBox.information(self, "Done", "Selected files exported.")
        self.dirty = False

    def switch_mode(self, mode):
        if mode == "RESOLVER":
            return
        if self.dirty:
            res = QMessageBox.question(self, "Unsaved Changes", "Switch without saving?", QMessageBox.Ok | QMessageBox.Cancel)
            if res != QMessageBox.Ok:
                self.switch_combo.setCurrentText("RESOLVER")
                return
        if mode == "MAPPER":
            self.e = App()
            self.e.show()
        elif mode == "VIEWER":
            self.v = Viewer()
            self.v.show()
        self._switching_mode = True
        self.close()

    def closeEvent(self, event):
        if self._switching_mode:
            event.accept()
            return
        if self.dirty:
            res = QMessageBox.question(self, "Unsaved Changes", "Exit without saving?", QMessageBox.Yes | QMessageBox.Cancel)
            if res != QMessageBox.Yes:
                event.ignore()
                return
        event.accept()

class Intro(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Image Tool")
        self.setFixedSize(300, 150)
        viewer_btn = QPushButton("VIEWER")
        editor_btn = QPushButton("MAPPER")
        resolver_btn = QPushButton("RESOLVER")
        layout = QVBoxLayout(self)
        layout.addWidget(viewer_btn)
        layout.addWidget(editor_btn)
        layout.addWidget(resolver_btn)
        viewer_btn.clicked.connect(self.open_viewer)
        editor_btn.clicked.connect(self.open_editor)
        resolver_btn.clicked.connect(self.open_resolver)

    def open_viewer(self):
        self.v = Viewer()
        self.v.show()
        self.close()

    def open_editor(self):
        self.e = App()
        self.e.show()
        self.close()
        
    def open_resolver(self):
        self.r = Resolver()
        self.r.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Intro()
    w.show()
    sys.exit(app.exec_())