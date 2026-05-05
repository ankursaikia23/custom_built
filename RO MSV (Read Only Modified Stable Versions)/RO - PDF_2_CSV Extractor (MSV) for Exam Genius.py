import sys
import re
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def extract_questions_from_text(text):
    lines = text.splitlines()
    rows = []
    i = 0

    def collect_block(start, stop_labels):
        collected = []
        k = start
        while k < len(lines):
            s = lines[k].strip()
            if any(s.startswith(lbl) for lbl in stop_labels):
                break
            if s:
                collected.append(s)
            k += 1
        return " ".join(collected), k
    while i < len(lines):
        line = lines[i].strip()

        if (
            line.lower().startswith("ques:") or 
            re.match(r"^q[\.\:\)]\s", line.lower()) or 
            re.match(r"^q\s", line.lower())
        ):
            q_first = ""
            if ":" in line:
                q_first = line.split(":", 1)[1].strip()
            else:
                q_first = re.sub(r"^q[\.\:\)]\s*", "", line.strip(), flags=re.IGNORECASE)
            question_text, pos = collect_block(
                i + 1,
                ["A)", "B)", "C)", "D)", "E)", "Answer", "ANSWER", "Ans", "Correct"]
            )
            if q_first:
                question_text = q_first + " " + question_text if question_text else q_first
            options = ["", "", "", "", ""]
            for idx, label in enumerate(["A)", "B)", "C)", "D)", "E)"]):
                if pos < len(lines) and lines[pos].strip().startswith(label):
                    first = lines[pos].strip().split(")", 1)[1].strip()
                    next_labels = []
                    if idx < 4:
                        next_labels.append(chr(ord("A") + idx + 1) + ")")
                    next_labels.extend(["Answer", "ANSWER", "Ans", "Correct"])
                    block, new_pos = collect_block(pos + 1, next_labels)
                    options[idx] = first + (" " + block if block else "")
                    pos = new_pos
                else:
                    break
            answer_text = ""
            while pos < len(lines):
                al = lines[pos].strip()
                al_low = al.lower()
                if al_low.startswith(("answer", "ans", "correct")):
                    after = al.split(":", 1)[-1].strip()
                    m = re.search(r"\b([A-Ea-e])\b", after)
                    if m:
                        letter = m.group(1).upper()
                        aidx = ord(letter) - ord("A")
                        if 0 <= aidx < 5:
                            answer_text = options[aidx]
                    break
                pos += 1
            rows.append([
                question_text,
                options[0],
                options[1],
                options[2],
                options[3],
                options[4],
                answer_text
            ])
            i = pos + 1
        else:
            i += 1
    return rows, text

def extract_text_from_pdf(pdf_path):
    text = []
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""
    return "\n".join(text)

def save_modified_pdf(text, output_path):
    try:
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        lines = []
        max_chars = 100
        for i in range(0, len(text), max_chars):
            lines.append(text[i:i+max_chars])
        y = height - 50
        for line in lines:
            if y < 50:
                c.showPage()
                y = height - 50
            c.drawString(40, y, line)
            y -= 15
        c.save()
    except Exception as e:
        print(f"Error saving modified PDF: {e}")

class PDFExtractorThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(int, int)

    def __init__(self, pdf_folder, output_folder):
        super().__init__()
        self.pdf_folder = pdf_folder
        self.output_folder = output_folder

    def run(self):
        pdf_files = [f for f in os.listdir(self.pdf_folder) if f.lower().endswith(".pdf")]
        total_questions = 0
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.pdf_folder, pdf_file)
            self.progress.emit(f"Processing {pdf_file} ...")
            text = extract_text_from_pdf(pdf_path)
            if not text.strip():
                self.progress.emit(f"⚠ Could not extract text from {pdf_file}")
                continue
            rows, mod_text = extract_questions_from_text(text)
            if rows:
                csv_name = f"{os.path.splitext(pdf_file)[0]} ({len(rows)}).csv"
                csv_path = os.path.join(self.output_folder, csv_name)
                df = pd.DataFrame(rows, columns=["Question", "Option1", "Option2", "Option3", "Option4", "Option5", "Answer"])
                try:
                    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                    self.progress.emit(f"✅ {len(rows)} questions extracted → {csv_name}")
                    total_questions += len(rows)
                except Exception as e:
                    self.progress.emit(f"❌ Failed to save CSV for {pdf_file}: {e}")
            else:
                self.progress.emit(f"⚠ No questions found in {pdf_file}")
        self.finished.emit(len(pdf_files), total_questions)

class PDFBatchExtractor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch PDF Question Extractor")
        self.resize(500, 180)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.label_status = QLabel("Select a folder containing PDFs and an output folder.")
        layout.addWidget(self.label_status)
        self.btn_select_folders = QPushButton("Select PDF Folder & Output Folder")
        self.btn_select_folders.clicked.connect(self.select_folders)
        layout.addWidget(self.btn_select_folders)
        self.setLayout(layout)

    def select_folders(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing PDFs")
        if not folder:
            return
        self.label_status.setText("Processing PDFs... Please wait.")
        QApplication.processEvents()
        self.thread = PDFExtractorThread(folder, folder)
        self.thread.progress.connect(self.update_status)
        self.thread.finished.connect(self.extraction_finished)
        self.thread.start()

    def update_status(self, message):
        self.label_status.setText(message)
        QApplication.processEvents()

    def extraction_finished(self, total_pdfs, total_questions):
        QMessageBox.information(self, "Extraction Completed",
                                f"Processed {total_pdfs} PDFs.\nTotal questions extracted: {total_questions}")
        self.label_status.setText(f"Done! Processed {total_pdfs} PDFs. Total questions: {total_questions}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFBatchExtractor()
    window.show()
    sys.exit(app.exec_())