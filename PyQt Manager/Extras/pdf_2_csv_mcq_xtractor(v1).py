import os
import re
import pandas as pd
import PyPDF2
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel

class PDFExtractor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Question Extractor")
        self.setGeometry(200, 200, 400, 200)
        self.layout = QVBoxLayout()
        
        self.label = QLabel("Select a folder with PDFs to extract questions:")
        self.layout.addWidget(self.label)
        
        self.button = QPushButton("Select Folder")
        self.button.clicked.connect(self.select_folder)
        self.layout.addWidget(self.button)
        
        self.setLayout(self.layout)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.process_folder(folder_path)
    
    def process_folder(self, folder_path):
        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
        if not pdf_files:
            self.label.setText("No PDFs found in the selected folder.")
            return
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(folder_path, pdf_file)
            questions = self.extract_questions_from_pdf(pdf_path)
            
            if questions:
                csv_name = f"{os.path.splitext(pdf_file)[0]}({len(questions)}).csv"
                csv_path = os.path.join(folder_path, csv_name)
                df = pd.DataFrame(questions)
                df.to_csv(csv_path, index=False)
                print(f"Saved: {csv_name} with {len(questions)} questions")
            else:
                print(f"No questions extracted from {pdf_file}")
        
        self.label.setText("Processing completed!")

    def extract_questions_from_pdf(self, pdf_path):
        pdf_text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    pdf_text += page.extract_text() + " "
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
            return []

        clean_text = re.sub(r'\s+', ' ', pdf_text).strip()
        
        pattern = re.compile(
            r"Ques\s*:\s*(.*?)\s*A\.\s*(.*?)\s*B\.\s*(.*?)\s*C\.\s*(.*?)\s*D\.\s*(.*?)\s*E\.\s*(.*?)\s*Answer\s*:\s*Option\s*([A-E])",
            re.IGNORECASE
        )
        
        matches = pattern.findall(clean_text)
        data = []
        for match in matches:
            question, opt1, opt2, opt3, opt4, opt5, ans_letter = match
            options = [opt1, opt2, opt3, opt4, opt5]
            answer = options[ord(ans_letter.upper()) - ord('A')]
            data.append({
                "Question": question.strip(),
                "Option1": opt1.strip(),
                "Option2": opt2.strip(),
                "Option3": opt3.strip(),
                "Option4": opt4.strip(),
                "Option5": opt5.strip(),
                "Answer": answer.strip()
            })
        return data

if __name__ == "__main__":
    app = QApplication([])
    extractor = PDFExtractor()
    extractor.show()
    app.exec()