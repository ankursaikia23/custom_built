import sys, os, csv, re
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QMessageBox
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import pytesseract
from pytesseract import Output

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.btn = QPushButton('Select Folder')
        self.btn.clicked.connect(self.open_folder)
        layout = QVBoxLayout()
        layout.addWidget(self.btn)
        self.setLayout(layout)
        self.setWindowTitle('Image to CSV')
        self.resize(300, 120)

    def preprocess(self, pil_img):
        """Basic preprocessing to improve OCR on colored/highlighted boxes."""
        img = pil_img.convert('L')
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img = ImageOps.autocontrast(img)
        img = img.point(lambda p: 255 if p > 180 else 0)
        return img

    def parse_text_lines(self, text_lines):
        """
        Given a list of OCR text lines (in reading order), returns:
        - question_text (with original line breaks preserved)
        - list of 5 options (strings)
        - answer_text (the selected option's full text) or '' if not found
        """
        options = [''] * 5
        question_lines = []
        collecting_options = False
        current_idx = None

        answer_letter = None

        opt_header_re = re.compile(r'^\s*([A-E])\s*[\.\)]\s*(.*)$', re.I)
        answer_re = re.compile(r'^\s*Answer\s*[:\-\s]\s*([A-E])\s*$', re.I)

        for raw in text_lines:
            line = raw.strip()
            if not line:
                continue

            am = answer_re.match(line)
            if am:
                answer_letter = am.group(1).upper()
                continue

            m = opt_header_re.match(line)
            if m:
                collecting_options = True
                current_idx = ord(m.group(1).upper()) - 65
                if 0 <= current_idx < 5:
                    options[current_idx] = m.group(2).strip()
                else:
                    current_idx = None
            else:
                if collecting_options and current_idx is not None:
                    options[current_idx] = (options[current_idx] + ' ' + line).strip()
                else:
                    question_lines.append(line)

        question_text = '\n'.join(question_lines).strip()

        answer_text = ''
        if answer_letter:
            idx = ord(answer_letter) - 65
            if 0 <= idx < 5:
                answer_text = options[idx].strip()

        for i in range(5):
            if options[i]:
                options[i] = re.sub(r'^[A-E]\s*[\.\)]\s*', '', options[i], flags=re.I).strip()

        return question_text, options, answer_text

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if not folder:
            return

        imgs = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        rows = []
        for f in imgs:
            p = os.path.join(folder, f)
            pil = Image.open(p)

            proc = self.preprocess(pil)

            config = r'--oem 3 --psm 6'
            data = pytesseract.image_to_data(proc, output_type=Output.DICT, config=config)

            lines = []
            current_line_num = -1
            current_line_text = []
            n = len(data['text'])
            for i in range(n):
                txt_raw = data['text'][i]
                txt = str(txt_raw).strip()
                
                conf_raw = data['conf'][i]
                try:
                    conf = int(conf_raw)
                except:
                    conf = -1
                
                line_num = int(data['line_num'][i])
                
                if txt:
                    if line_num != current_line_num:
                        if current_line_text:
                            lines.append(' '.join(current_line_text).strip())
                        current_line_text = [txt]
                        current_line_num = line_num
                    else:
                        current_line_text.append(txt)
            if current_line_text:
                lines.append(' '.join(current_line_text).strip())

            if not lines:
                raw_text = pytesseract.image_to_string(proc, config=config)
                lines = [ln for ln in raw_text.splitlines() if ln.strip()]

            question, opts, answer_text = self.parse_text_lines(lines)

            rows.append([question] + opts + [answer_text])

        out = os.path.join(folder, 'output.csv')
        with open(out, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['Question','Option1','Option2','Option3','Option4','Option5','Answer'])
            w.writerows(rows)

        QMessageBox.information(self, 'Done', 'CSV created:\n' + out)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = App()
    w.show()
    app.exec_()