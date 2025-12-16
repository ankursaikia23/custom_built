import sys, re, csv, os, cv2
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QProgressBar, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout, QSpinBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
import pytesseract
import numpy as np

def parse_ocr_text(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    option_re = re.compile(r'^[\(\[]?[A-Ea-e][\)\]\.\-:\)]?\s*(.+)$')
    option_marker_re = re.compile(r'^[\(\[]?([A-Ea-e])[\)\]\.\-:\)]?')
    question_lines, options, answer = [], [], ""
    for ln in lines:
        low = ln.lower()
        if 'answer' in low or 'ans:' in low:
            m = re.search(r'([A-Ea-e])', ln)
            if m:
                answer = m.group(1).upper()
    found_options = False
    for ln in lines:
        m = option_marker_re.match(ln)
        if m:
            found_options = True
            mm = option_re.match(ln)
            if mm:
                options.append(mm.group(1).strip())
            else:
                options.append(option_marker_re.sub('', ln).strip())
        else:
            if not found_options:
                question_lines.append(ln)
            else:
                if options:
                    options[-1] += ' ' + ln
                else:
                    question_lines.append(ln)
    if not options:
        joined = " ".join(lines)
        parts = re.split(r'\b(?=[A-Ea-e][\)\.\-:\)]\s)', joined)
        if len(parts) > 1:
            question_lines = [parts[0].strip()]
            for p in parts[1:]:
                options.append(re.sub(r'^[\(\[]?[A-Ea-e][\)\]\.\-:\)]?\s*', '', p).strip())
    question = " ".join(question_lines).strip()
    while len(options) < 5:
        options.append("")
    if answer and answer.isalpha():
        idx = ord(answer.upper()) - ord('A')
        if 0 <= idx < len(options):
            answer = f"{answer.upper()} - {options[idx]}"
        else:
            answer = answer.upper()
    return {'question': question, 'options': options[:5], 'answer': answer}

class ExtractThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    status = pyqtSignal(str)
    def __init__(self, video_path, frame_step=10, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.frame_step = int(frame_step)
    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            self.status.emit("Failed to open video.")
            self.finished.emit([])
            return
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        parsed_items, frame_idx = [], 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % self.frame_step == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.bilateralFilter(gray, 9, 75, 75)
                gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
                pil_img = Image.fromarray(gray)
                try:
                    text = pytesseract.image_to_string(pil_img, lang='hin+eng', config='--psm 6')
                except:
                    text = ""
                parsed = parse_ocr_text(text)
                if parsed:
                    if not parsed_items or parsed_items[-1]['question'] != parsed['question']:
                        parsed_items.append(parsed)
                pct = int((frame_idx / total_frames) * 100)
                self.progress.emit(pct)
            frame_idx += 1
        cap.release()
        self.progress.emit(100)
        self.status.emit(f"Parsed {len(parsed_items)} items.")
        self.finished.emit(parsed_items)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to CSV OCR Extractor")
        self.resize(900, 600)
        self.video_path = None
        self.parsed_items = []
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.select_btn = QPushButton("Select Video")
        self.select_btn.clicked.connect(self.select_video)
        btn_layout.addWidget(self.select_btn)
        self.frame_step_label = QLabel("Frame Step:")
        btn_layout.addWidget(self.frame_step_label)
        self.frame_step_spin = QSpinBox()
        self.frame_step_spin.setRange(1, 100)
        self.frame_step_spin.setValue(10)
        btn_layout.addWidget(self.frame_step_spin)
        self.extract_btn = QPushButton("Extract")
        self.extract_btn.clicked.connect(self.extract_questions)
        self.extract_btn.setEnabled(False)
        btn_layout.addWidget(self.extract_btn)
        self.save_btn = QPushButton("Save CSV")
        self.save_btn.clicked.connect(self.save_csv)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        self.info_label = QLabel("No file selected.")
        layout.addWidget(self.info_label)
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Question","Option1","Option2","Option3","Option4","Option5","Answer"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.thread = None
    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select video file", "", "Video Files (*.mp4 *.mkv *.avi *.mov);;All Files (*)")
        if path:
            self.video_path = path
            self.info_label.setText(os.path.basename(path))
            self.extract_btn.setEnabled(True)
    def extract_questions(self):
        if not self.video_path:
            QMessageBox.warning(self, "No file", "Select a video first.")
            return
        self.extract_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.table.setRowCount(0)
        self.progress.setValue(0)
        step = self.frame_step_spin.value()
        self.thread = ExtractThread(self.video_path, frame_step=step)
        self.thread.progress.connect(self.on_progress)
        self.thread.finished.connect(self.on_finished)
        self.thread.status.connect(self.on_status)
        self.thread.start()
        self.info_label.setText("Processing...")
    def on_progress(self, val):
        self.progress.setValue(val)
    def on_status(self, txt):
        self.info_label.setText(txt)
    def on_finished(self, items):
        self.parsed_items = items
        self.populate_table(items)
        self.extract_btn.setEnabled(True)
        self.save_btn.setEnabled(bool(items))
        QMessageBox.information(self, "Done", f"Extracted {len(items)} items.")
    def populate_table(self, items):
        self.table.setRowCount(0)
        for it in items:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(it.get('question', '')))
            for i in range(5):
                self.table.setItem(r, 1+i, QTableWidgetItem(it['options'][i] if i < len(it['options']) else ''))
            self.table.setItem(r, 6, QTableWidgetItem(it.get('answer', '')))
    def save_csv(self):
        if not self.parsed_items:
            QMessageBox.warning(self, "No data", "No data to save.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "questions.csv", "CSV files (*.csv)")
        if not path:
            return
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Question","Option1","Option2","Option3","Option4","Option5","Answer"])
            for it in self.parsed_items:
                writer.writerow([it.get('question','')] + it.get('options',['']*5) + [it.get('answer','')])
        QMessageBox.information(self, "Saved", f"Saved {len(self.parsed_items)} rows.")
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
