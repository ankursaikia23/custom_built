import sys
import os
import random
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QGroupBox, QScrollArea, QFrame, QMessageBox,
    QListView
)

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CORRECT_FILE = os.path.join(APP_DIR, "March 2026.csv")
SELECTED_CORRECT_FILE = CORRECT_FILE
correct_csv_selected = False
pd.set_option("display.max_colwidth", None)

question_col = None
answer_col = None
option_cols = []
score = 0
attempted = 0
correct_count = 0
selected_num_questions = None
questions_master = None
review_log = []
marked_errors = []
df_all = None
selected_files = []
timer_duration = 0
timer = None
time_left = 0
reveal_answers_during_quiz = True
exam_mode = False
correct_marks = 1.0
incorrect_marks = 0.25

def load_filtered_questions_from_files(files):
    global question_col, answer_col, option_cols
    if not files:
        raise FileNotFoundError("No CSV files provided.")
    frames = []
    for f in files:
        if not os.path.exists(f):
            continue
        df_local = pd.read_csv(f)
        df_local.columns = df_local.columns.str.strip().str.lower()
        df_local['__source_file__'] = os.path.basename(f)
        df_local['__original_csv_index__'] = df_local.index
        df_local['__original_csv_row__'] = df_local.index + 2
        frames.append(df_local)
    if not frames:
        raise FileNotFoundError("No valid CSV files found.")
    df_concat = pd.concat(frames, ignore_index=True, sort=False)
    cols = list(df_concat.columns)
    question_candidates = [c for c in cols if 'question' in c]
    answer_candidates = [c for c in cols if 'answer' in c]
    option_candidates = [c for c in cols if 'option' in c]
    if not question_candidates or not answer_candidates or not option_candidates:
        raise ValueError("Could not find required columns.")
    question_col = sorted(question_candidates)[0]
    answer_col = sorted(answer_candidates)[0]
    option_cols = sorted([c for c in option_candidates if c in cols])
    if os.path.exists(SELECTED_CORRECT_FILE):
        correct_df = pd.read_csv(SELECTED_CORRECT_FILE)
        correct_df.columns = correct_df.columns.str.strip().str.lower()
        if question_col in correct_df.columns:
            correct_questions = set(correct_df[question_col].astype(str).str.strip().str.lower())
            df_concat = df_concat[~df_concat[question_col].astype(str).str.strip().str.lower().isin(correct_questions)]
            df_concat = df_concat.reset_index(drop=True)
    globals().update({"question_col": question_col, "answer_col": answer_col, "option_cols": option_cols})
    return df_concat

def append_to_csv(filename, row):
    try:
        columns = ["Question", "Option1", "Option2", "Option3", "Option4", "Option5", "Answer"]
        if not os.path.exists(filename):
            pd.DataFrame(columns=columns).to_csv(filename, index=False)
        df_existing = pd.read_csv(filename)
        df_existing.columns = [c.strip() for c in df_existing.columns]
        q_text = str(row["question"]).strip().lower()
        if "Question" in df_existing.columns:
            existing_questions = df_existing["Question"].astype(str).str.strip().str.lower().values
            if q_text in existing_questions:
                return
        new_values = {
            "Question": row["question"],
            "Answer": row["answer"]
        }
        for i in range(5):
            new_values[f"Option{i+1}"] = row["options"][i] if i < len(row["options"]) else ""
        new_row = pd.DataFrame([new_values])
        df_existing = pd.concat([df_existing, new_row], ignore_index=True)
        df_existing = df_existing.reindex(columns=columns)
        df_existing.to_csv(filename, index=False)
    except Exception as e:
        print("CSV ERROR:", e)
        
class QuizMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
        QWidget {
            background-color: #f1f5f9;
            color: #1e293b;
            font-family: Segoe UI, Arial;
        }
        QGroupBox {
            border: 1px solid #cbd5e1;
            border-radius: 14px;
            background-color: #ffffff;
            margin-top: 10px;
        }   
        QPushButton {
            border-radius: 12px;
            padding: 8px;
            border: 1px solid #cbd5e1;
            background-color: #ffffff;
            font-weight:bold;
        }
        QPushButton:hover {
            background-color: #e2e8f0;
        }
        QComboBox {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 6px;
            border: 1px solid #cbd5e1;
        }
        QLabel {
            color: #1e293b;
        }
        """)
        self.setWindowTitle("Quiz App (PyQt)")
        self.setMinimumSize(850, 600)
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QVBoxLayout(self.central)
        self.start_group = QGroupBox()
        self.quiz_group = QGroupBox()
        self.end_group = QGroupBox()
        self.main_layout.addWidget(self.start_group)
        self.main_layout.addWidget(self.quiz_group)
        self.main_layout.addWidget(self.end_group)
        self.init_start()
        self.init_quiz()
        self.init_end()
        self.show_start()
        self.minimize_attempts = 0
        self.selected_mode = None
        self.selected_answer_mode = None

    def select_csvs(self):
        global df_all, selected_files
        paths, _ = QFileDialog.getOpenFileNames(self, "Select quiz CSV(s)", "", "CSV Files (*.csv)")
        if paths:
            selected_files = paths
            try:
                df_all = load_filtered_questions_from_files(selected_files)
                total = len(df_all)
                self.total_q_label.setText(f"Total: {total}")
                self.update_question_options(total)
                self.files_dropdown.clear()
                for f in selected_files:
                    name = os.path.basename(f)
                    self.files_dropdown.addItem(name, f)
                self.show_start()
                self.update_start_button_state()
            except Exception:
                self.total_q_label.setText("Error loading CSV")

    def select_correct_csv(self):
        global SELECTED_CORRECT_FILE, df_all, correct_csv_selected
        path, _ = QFileDialog.getOpenFileName(self, "Select Correct CSV", "", "CSV Files (*.csv)")
        if path:
            SELECTED_CORRECT_FILE = path
            correct_csv_selected = True
            try:
                df_correct = pd.read_csv(path)
                count = len(df_correct)
            except Exception:
                count = 0
            fname = os.path.basename(SELECTED_CORRECT_FILE) if SELECTED_CORRECT_FILE else "None"
            short_name = fname[:15] + "..." if len(fname) > 15 else fname
            self.correct_file_label.setText(
                f"<span style='color:#2563eb;'>File:</span> {short_name}  |  "
                f"<span style='color:#16a34a;'>Correct:</span> {count}"
            )
            self.correct_file_label.setToolTip(fname)
            if selected_files:
                try:
                    df_all = load_filtered_questions_from_files(selected_files)
                    total = len(df_all)
                    self.total_q_label.setText(f"Total: {total}")
                    self.update_question_options(total)
                    self.files_dropdown.clear()
                    for f in selected_files:
                        name = os.path.basename(f)
                        self.files_dropdown.addItem(name, f)
                    self.show_start()
                    self.update_start_button_state()
                except Exception:
                    self.total_q_label.setText("Error")
                    
    def clear_correct_csv(self):
        global SELECTED_CORRECT_FILE, df_all, correct_csv_selected    
        if not os.path.exists(SELECTED_CORRECT_FILE):
            QMessageBox.information(self, "Info", "No correct CSV file found.")
            return    
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear the correct CSV?\n\nThis will reset your progress.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            columns = ["Question", "Option1", "Option2", "Option3", "Option4", "Option5", "Answer"]
            pd.DataFrame(columns=columns).to_csv(SELECTED_CORRECT_FILE, index=False)
            QMessageBox.information(self, "Success", "Correct CSV cleared successfully.")
            fname = os.path.basename(SELECTED_CORRECT_FILE) if SELECTED_CORRECT_FILE else "None"
            short_name = fname[:15] + "..." if len(fname) > 15 else fname            
            self.correct_file_label.setText(
                f"<span style='color:#2563eb;'>File:</span> {short_name} | "
                f"<span style='color:#16a34a;'>Correct:</span> 0"
            )            
            self.correct_file_label.setToolTip(fname)
            if selected_files:
                df_all = load_filtered_questions_from_files(selected_files)
                total = len(df_all)
                self.total_q_label.setText(f"Total: {total}")
            else:
                df_all = None
            self.show_start()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to clear CSV:\n{e}")
            
    def refresh_questions(self):
        global df_all, selected_files
        if not selected_files:
            QMessageBox.warning(self, "No Files", "Please select CSV files first.")
            return
        try:
            df_all = load_filtered_questions_from_files(selected_files)
            total = len(df_all)
            self.total_q_label.setText(f"Total: {total}")
            QMessageBox.information(self, "Refreshed", "Questions refreshed successfully.")
            self.show_start()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh:\n{e}")
            
    def refresh_counts_only(self):
        global df_all, selected_files, SELECTED_CORRECT_FILE
        try:
            if selected_files:
                df_all = load_filtered_questions_from_files(selected_files)
                total = len(df_all)
                self.total_q_label.setText(f"Total: {total}")
                self.update_question_options(total)
            else:
                total = 0
            self.available_label.setText(
                f"<span style='color:#2563eb;'>Available:</span> {total}"
            )
            if os.path.exists(SELECTED_CORRECT_FILE):
                try:
                    df_correct = pd.read_csv(SELECTED_CORRECT_FILE)
                    count = len(df_correct)
                except Exception:
                    count = 0
                fname = os.path.basename(SELECTED_CORRECT_FILE) if SELECTED_CORRECT_FILE else "None"
                short_name = fname[:15] + "..." if len(fname) > 15 else fname
                self.correct_file_label.setText(
                    f"<span style='color:#2563eb;'>File:</span> {short_name}  |  "
                    f"<span style='color:#16a34a;'>Correct:</span> {count}"
                )
                self.correct_file_label.setToolTip(fname)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Refresh failed:\n{e}")
        
    def init_start(self):
        l = QVBoxLayout(self.start_group)
        main_split = QHBoxLayout()
        l.addLayout(main_split)
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(10)
        self.master_reset_btn = QPushButton("MASTER RESET")
        self.master_reset_btn.setMinimumHeight(60)
        self.master_reset_btn.setStyleSheet("""
        font-size:20px;
        background-color:#111827;
        color:white;
        border-radius:12px;
        font-weight:bold;
        """)
        self.master_reset_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(20, 20, 20, 20)
        main_split.addWidget(left_container, 4)
        main_split.addWidget(right_container, 6)
        self.avail_label = QLabel("")
        self.total_q_label = QLabel("")
        self.total_q_label.hide()
        self.avail_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.avail_label.setStyleSheet("font-size:25px;")
        left_layout.addWidget(self.avail_label)
        mock_group = QGroupBox()
        mock_group.setStyleSheet("""
        QGroupBox {
            border: 2px solid #cbd5e1;
            border-radius: 16px;
            background-color: #ffffff;
        }
        """)
        mock_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        mock_layout = QVBoxLayout(mock_group)
        mock_layout.setSpacing(10)
        mock_title = QLabel("Mock Mode")
        mock_title.setAlignment(Qt.AlignCenter)
        mock_title.setStyleSheet("font-size:24px; font-weight:700; margin-bottom:10px;")
        mock_layout.addWidget(mock_title)
        mock_row = QHBoxLayout()
        self.practice_mode_btn = QPushButton("Practice")
        self.exam_mode_btn = QPushButton("Exam")
        for btn in [self.practice_mode_btn, self.exam_mode_btn]:
            btn.setMinimumHeight(60)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet("""
                font-size:18px;
                background-color:#ffffff;
                border:2px solid #cbd5e1;
                border-radius:12px;
            """)
        mock_row.addWidget(self.practice_mode_btn)
        mock_row.addWidget(self.exam_mode_btn)
        mock_layout.addLayout(mock_row)
        answer_group = QGroupBox()
        answer_group.setStyleSheet("""
        QGroupBox {
            border: 2px solid #cbd5e1;
            border-radius: 16px;
            background-color: #ffffff;
        }
        """)
        answer_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        answer_layout = QVBoxLayout(answer_group)
        answer_layout.setSpacing(10)
        answer_title = QLabel("Answer Mode")
        answer_title.setAlignment(Qt.AlignCenter)
        answer_title.setStyleSheet("font-size:24px; font-weight:700; margin-bottom:10px;")
        answer_layout.addWidget(answer_title)
        answer_row = QHBoxLayout()
        self.mode_random_btn = QPushButton("Random")
        self.mode_reveal_btn = QPushButton("Answer Reveal")
        self.mode_hidden_btn = QPushButton("Answer Hidden")
        for btn in [self.mode_random_btn, self.mode_reveal_btn, self.mode_hidden_btn]:
            btn.setMinimumHeight(60)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet("""
                font-size:18px;
                background-color:#ffffff;
                border:2px solid #cbd5e1;
                border-radius:12px;
            """)
        answer_row.addWidget(self.mode_random_btn)
        answer_row.addWidget(self.mode_reveal_btn)
        answer_row.addWidget(self.mode_hidden_btn)
        answer_layout.addLayout(answer_row)
        score_group = QGroupBox()
        score_group.setStyleSheet("""
        QGroupBox {
            border: 2px solid #cbd5e1;
            border-radius: 16px;
            background-color: #ffffff;
        }
        """)
        score_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        score_layout = QVBoxLayout(score_group)
        score_layout.setSpacing(10)
        score_title = QLabel("Score Specifications")
        score_title.setAlignment(Qt.AlignCenter)
        score_title.setStyleSheet("font-size:24px; font-weight:700; margin-bottom:10px;")
        score_layout.addWidget(score_title)
        row = QHBoxLayout()        
        label_correct = QLabel("Each Correct")
        label_correct.setAlignment(Qt.AlignCenter)
        label_correct.setStyleSheet("""
        QLabel {
            font-size:18px;
            font-weight:bold;
            border:2px solid #cbd5e1;
            border-radius:12px;
            padding:8px;
            background-color:#ffffff;
        }
        """)
        label_correct.setStyleSheet("font-size:18px; font-weight:bold;")
        label_correct.setMinimumWidth(120)
        self.correct_score_combo = QComboBox()
        self.correct_score_combo.setEditable(True)
        self.correct_score_combo.addItems(["1", "2", "3", "4"])
        self.correct_score_combo.setCurrentText("1")
        self.correct_score_combo.setStyleSheet("font-size:18px;")
        label_incorrect = QLabel("Each Incorrect")
        label_incorrect.setAlignment(Qt.AlignCenter)
        label_incorrect.setStyleSheet("""
        QLabel {
            font-size:18px;
            font-weight:bold;
            border:2px solid #cbd5e1;
            border-radius:12px;
            padding:8px;
            background-color:#ffffff;
        }
        """)
        label_incorrect.setStyleSheet("font-size:18px; font-weight:bold;")
        label_incorrect.setMinimumWidth(140)
        self.incorrect_score_combo = QComboBox()
        self.incorrect_score_combo.setEditable(True)
        self.incorrect_score_combo.addItems(["0", "0.25", "0.5", "1", "2"])
        self.incorrect_score_combo.setCurrentText("0.25")
        self.incorrect_score_combo.setStyleSheet("font-size:18px;")
        row.addWidget(label_correct, 4)
        row.addWidget(self.correct_score_combo, 2)
        row.addWidget(label_incorrect, 4)
        row.addWidget(self.incorrect_score_combo, 2)
        score_layout.addLayout(row)
        score_layout.addStretch()
        self.answer_overlay = QFrame(answer_group)
        self.answer_overlay.setStyleSheet("""
        background-color: rgba(255,255,255,180);
        border-radius:16px;
        """)
        self.answer_overlay.hide()        
        overlay_layout = QVBoxLayout(self.answer_overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)
        overlay_label = QLabel("Not available in Exam Mode")
        overlay_label.setStyleSheet("font-size:20px; font-weight:bold;")
        overlay_label.setAlignment(Qt.AlignCenter)
        overlay_layout.addWidget(overlay_label)
        row1 = QHBoxLayout()
        self.load_csv_btn = QPushButton("Load CSV")
        self.load_csv_btn.setMinimumHeight(40)
        self.load_csv_btn.setStyleSheet("""
        font-size:18px;
        background-color:#0ea5e9;
        color:white;
        border-radius:12px;
        font-weight:bold;
        """)        
        self.combo = QComboBox()
        self.available_label = QLabel("")
        self.available_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.available_label.setTextFormat(Qt.RichText)
        self.available_label.setStyleSheet("""
        font-size:18px;
        font-weight:bold;
        """)
        self.combo.setStyleSheet("""
        QComboBox {
            font-size:18px;
        }
        QComboBox QAbstractItemView {
            font-size:18px;
        }
        """)
        self.combo.setMinimumHeight(40)
        self.combo.setStyleSheet("""
        font-size:18px;
        background-color:#ffffff;
        border-radius:10px;
        padding:6px;
        font-weight:bold;
        """)
        self.files_dropdown = QComboBox()
        self.files_dropdown.setView(QListView())
        self.files_dropdown.view().setWordWrap(True)
        self.files_dropdown.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.files_dropdown.setMinimumHeight(40)
        self.files_dropdown.setStyleSheet("""
        font-size:16px;
        background-color:#ffffff;
        border-radius:10px;
        padding:6px;
        font-weight:bold;
        """)
        self.files_dropdown.addItem("No files selected")
        row1.addWidget(self.load_csv_btn)
        row1.addWidget(self.available_label)
        row1.addWidget(self.combo)
        row1.addWidget(self.files_dropdown)
        row2 = QHBoxLayout()
        self.select_correct_btn = QPushButton("Select Correct CSV")
        self.select_correct_btn.setMinimumHeight(40)
        self.select_correct_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.select_correct_btn.setStyleSheet("""
        font-size:18px;
        background-color:#22c55e;
        color:white;
        border-radius:12px;
        font-weight:bold;
        """)        
        self.correct_file_label = QLabel("No files selected")
        self.correct_file_label.setMinimumHeight(40)
        self.correct_file_label.setWordWrap(True)
        self.correct_file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.correct_file_label.setTextFormat(Qt.RichText)
        self.correct_file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.correct_file_label.setStyleSheet("""
        font-size:15px;
        background-color:#ffffff;
        border-radius:10px;
        border:1px solid #cbd5e1;
        padding:10px;
        font-weight:bold;
        """)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedWidth(100)
        self.reset_btn.setMinimumHeight(40)
        self.reset_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reset_btn.setStyleSheet("""
        font-size:18px;
        background-color:#ef4444;
        color:white;
        border-radius:12px;
        font-weight:bold;
        """)
        row2.addWidget(self.select_correct_btn, 3)
        row2.addWidget(self.correct_file_label, 5)
        row2.addWidget(self.reset_btn, 1)
        selection_group = QGroupBox()
        selection_group.setStyleSheet("""
        QGroupBox {
            border: 2px solid #cbd5e1;
            border-radius: 16px;
            background-color: #ffffff;
        }
        """)
        selection_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        selection_layout = QVBoxLayout(selection_group)
        selection_layout.setSpacing(12)
        selection_layout.setContentsMargins(15, 15, 15, 15)
        selection_title = QLabel("Selections")
        selection_title.setAlignment(Qt.AlignCenter)
        selection_title.setStyleSheet("font-size:24px; font-weight:700; margin-bottom:10px;")
        selection_layout.addWidget(selection_title)
        selection_layout.addLayout(row1)
        selection_layout.addLayout(row2)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.refresh_btn.setStyleSheet("""
        font-size:18px;
        background-color:#3b82f6;
        color:white;
        border-radius:12px;
        font-weight:bold;
        """)        
        selection_layout.addWidget(self.refresh_btn)
        left_layout.addWidget(self.master_reset_btn)
        left_layout.addWidget(mock_group)
        left_layout.addWidget(answer_group)
        left_layout.addWidget(score_group)        
        left_layout.addWidget(selection_group)
        left_layout.addStretch()
        row4 = QHBoxLayout()
        self.start_btn = QPushButton("Start Quiz")
        self.start_btn.setMinimumHeight(70)
        self.start_btn.setStyleSheet("""
        background-color:#22c55e;
        color:white;
        font-size:26px;
        font-weight:bold;
        border-radius:16px;
        """)
        self.exit_btn2 = QPushButton("Exit")
        self.exit_btn2.setMinimumHeight(70)
        self.exit_btn2.setStyleSheet("""
        background-color:#ef4444;
        color:white;
        font-size:24px;
        border-radius:16px;
        """)
        row4.addWidget(self.start_btn)
        row4.addWidget(self.exit_btn2)
        left_layout.addLayout(row4)
        self.instructions_box = QLabel("Instructions will appear here...")
        self.instructions_box.setWordWrap(True)
        self.instructions_box.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.instructions_box.setStyleSheet("""
            font-size:18px;
            background-color:#ffffff;
            border:1px solid #cbd5e1;
            border-radius:12px;
            padding:15px;
        """)
        right_layout.addWidget(self.instructions_box)
        self.start_btn.clicked.connect(self.on_start)
        self.update_start_button_state()
        self.mode_random_btn.clicked.connect(lambda: self.set_mode("random"))
        self.mode_reveal_btn.clicked.connect(lambda: self.set_mode("reveal"))
        self.mode_hidden_btn.clicked.connect(lambda: self.set_mode("hidden"))
        self.exit_btn2.clicked.connect(self.close)
        self.load_csv_btn.clicked.connect(self.select_csvs)
        self.select_correct_btn.clicked.connect(self.select_correct_csv)
        self.reset_btn.clicked.connect(self.reset_all)
        self.practice_mode_btn.clicked.connect(lambda: self.set_exam_mode(False))
        self.exam_mode_btn.clicked.connect(lambda: self.set_exam_mode(True))
        self.master_reset_btn.clicked.connect(self.master_reset)
        self.refresh_btn.clicked.connect(self.refresh_counts_only)
        
    def update_question_options(self, total):
        base_opts = [10, 20, 30, 40, 50]
        opts = [n for n in base_opts if n <= total]    
        if total < 50 and total not in opts:
            opts.append(total)
        opts = sorted(opts)
        self.combo.clear()
        model = QStandardItemModel()
        for n in opts:
            opt_item = QStandardItem(str(n))
            opt_item.setData(n, Qt.UserRole)
            opt_item.setData(str(n), Qt.DisplayRole)
            model.appendRow(opt_item)
        self.combo.setModel(model)
        if opts:
            self.combo.setCurrentIndex(0)
        else:
            self.combo.addItem("No options", None)

    def show_start(self):
        global df_all
        self.start_group.show()
        self.quiz_group.hide()
        self.end_group.hide()
        if df_all is None:
            self.total_q_label.setText("Total: 0")
            self.files_dropdown.clear()
            self.files_dropdown.addItem("No files selected")
            self.start_btn.setEnabled(False)
            self.combo.clear()
            self.combo.addItem("No options", None)
            self.available_label.setText(
                "<span style='color:#2563eb;'>Available:</span> 0"
            )
            return
        if df_all.empty:
            self.total_q_label.setText("Total: 0")
            self.start_btn.setEnabled(True)
            self.combo.clear()
            self.combo.addItem("No options", None)
            self.available_label.setText(
                "<span style='color:#2563eb;'>Available:</span> 0"
            )
            return
        total = len(df_all)
        self.total_q_label.setText(f"Total: {total}")
        self.available_label.setText(
            f"<span style='color:#2563eb;'>Available:</span> {total}"
        )
        if total == 0:
            QMessageBox.information(
                self,
                "No Questions",
                "All questions are already answered.\n\nClick 'Reset' to restart."
            )
        self.update_question_options(total)
        self.start_btn.setEnabled(True)
        
    def set_mode(self, mode):
        global reveal_answers_during_quiz        
        if mode == "reveal":
            reveal_answers_during_quiz = True
        elif mode == "hidden":
            reveal_answers_during_quiz = False
        elif mode == "random":
            reveal_answers_during_quiz = random.choice([True, False])
        self.selected_answer_mode = mode
        for btn in [self.mode_random_btn, self.mode_reveal_btn, self.mode_hidden_btn]:
            btn.setStyleSheet("font-size:20px;")
        sender = self.sender()
        sender.setStyleSheet("font-size:20px; background-color:#22c55e; border:2px solid #16a34a; color:white;")

    def set_exam_mode(self, is_exam):
        global exam_mode, reveal_answers_during_quiz
        exam_mode = is_exam
        self.selected_mode = "exam" if is_exam else "practice"
        if is_exam:
            reveal_answers_during_quiz = False
            self.answer_overlay.show()
            self.showMaximized()
            self.setFixedSize(self.size())
            self.practice_mode_btn.setStyleSheet("font-size:18px;")
            self.exam_mode_btn.setStyleSheet("font-size:18px; background-color:#22c55e; color:white; border:2px solid #16a34a;")
        else:
            self.answer_overlay.hide()
            self.showMaximized()
            self.setMinimumSize(850, 600)
            self.setMaximumSize(16777215, 16777215)
            self.practice_mode_btn.setStyleSheet("font-size:18px; background-color:#22c55e; color:white; border:2px solid #16a34a;")
            self.exam_mode_btn.setStyleSheet("font-size:18px;")

    def reset_all(self):
        global SELECTED_CORRECT_FILE, df_all, correct_csv_selected
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "This will clear correct CSV and reload questions. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            columns = ["Question", "Option1", "Option2", "Option3", "Option4", "Option5", "Answer"]
            pd.DataFrame(columns=columns).to_csv(SELECTED_CORRECT_FILE, index=False)
            if selected_files:
                df_all = load_filtered_questions_from_files(selected_files)
                total = len(df_all)
                self.total_q_label.setText(f"Total: {total}")
                self.update_question_options(total)
            else:
                df_all = None
                self.update_question_options(0)  
            QMessageBox.information(self, "Reset", "Reset completed.")
            fname = os.path.basename(SELECTED_CORRECT_FILE) if SELECTED_CORRECT_FILE else "None"
            short_name = fname[:15] + "..." if len(fname) > 15 else fname      
            self.correct_file_label.setText(
                f"<span style='color:#2563eb;'>File:</span> {short_name}  |  "
                f"<span style='color:#16a34a;'>Correct:</span> 0"
            )
            self.correct_file_label.setToolTip(fname)
            self.correct_file_label.setToolTip(fname)
            self.show_start()
            self.update_start_button_state()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            
    def master_reset(self):
        global df_all, selected_files, SELECTED_CORRECT_FILE
        global selected_num_questions, exam_mode, reveal_answers_during_quiz, correct_csv_selected
        df_all = None
        selected_files = []
        SELECTED_CORRECT_FILE = CORRECT_FILE
        correct_csv_selected = False
        selected_num_questions = None    
        exam_mode = False
        reveal_answers_during_quiz = True
        self.answer_overlay.hide()
        self.files_dropdown.clear()
        self.files_dropdown.addItem("No files selected")    
        self.combo.clear()
        self.update_question_options(0)
        self.correct_file_label.setText("No files selected")
        self.total_q_label.setText("Total: 0")
        self.avail_label.setText("")
        self.available_label.setText(
            "<span style='color:#2563eb;'>Available:</span> 0"
        )
        default_style = """
        font-size:18px;
        background-color:#ffffff;
        border:2px solid #cbd5e1;
        border-radius:12px;
        """
        for btn in [
            self.practice_mode_btn,
            self.exam_mode_btn,
            self.mode_random_btn,
            self.mode_reveal_btn,
            self.mode_hidden_btn
        ]:
            btn.setStyleSheet(default_style)
        self.start_btn.setEnabled(False)
        self.show_start()
        self.update_start_button_state()
        
    def update_start_button_state(self):
        global selected_files, correct_csv_selected
        if selected_files and correct_csv_selected:
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet("""
                background-color:#22c55e;
                color:white;
                font-size:26px;
                font-weight:bold;
                border-radius:16px;
            """)
        else:
            self.start_btn.setEnabled(False)
            self.start_btn.setStyleSheet("""
                background-color:#94a3b8;
                color:white;
                font-size:26px;
                font-weight:bold;
                border-radius:16px;
            """)

    def on_start(self):
        global selected_num_questions, timer_duration, time_left, timer, df_all, correct_csv_selected
        if self.selected_mode is None:
            QMessageBox.warning(self, "Error", "Select Mock Mode")
            return
        if not exam_mode and self.selected_answer_mode is None:
            QMessageBox.warning(self, "Error", "Select Answer Mode")
            return
        if not selected_files:
            QMessageBox.warning(self, "Error", "Please load quiz CSV file(s).")
            return
        if not correct_csv_selected:
            QMessageBox.warning(self, "Error", "Please select a Correct CSV file.")
            return
        if df_all is None or len(df_all) == 0:
            QMessageBox.warning(self, "Error", "No questions available. Please load valid CSV(s).")
            return
        if self.combo.count() == 0:
            QMessageBox.warning(self, "Error", "No question count available.")
            return
        selected_num_questions = int(self.combo.currentText())
        global correct_marks, incorrect_marks
        try:
            correct_marks = float(self.correct_score_combo.currentText())
        except:
            correct_marks = 1.0
        try:
            incorrect_marks = float(self.incorrect_score_combo.currentText())
        except:
            incorrect_marks = 0.25
        if correct_marks <= incorrect_marks:
            QMessageBox.warning(
                self,
                "Invalid Scoring",
                "Correct marks must be greater than Incorrect marks."
            )
            return
        if exam_mode:
            global reveal_answers_during_quiz
            reveal_answers_during_quiz = False
        if selected_num_questions is None:
            QMessageBox.warning(self, "Error", "Invalid selection")
            return
        total = len(df_all)
        self.total_q_label.setText(f"Total: {total}")
        if total == 0:
            QMessageBox.information(
                self,
                "No Questions",
                "All questions are already answered.\n\nClick 'Reset' to restart."
            )
            return
        if selected_num_questions == 10:
            timer_duration = 5 * 60
        elif selected_num_questions == 20:
            timer_duration = 10 * 60
        elif selected_num_questions == 30:
            timer_duration = 15 * 60
        elif selected_num_questions == 40:
            timer_duration = 20 * 60
        elif selected_num_questions == 50:
            timer_duration = 25 * 60
        else:
            timer_duration = selected_num_questions * 30
        time_left = timer_duration
        if timer:
            timer.stop()
        self.start_quiz()
        
    def init_quiz(self):
        l = QVBoxLayout(self.quiz_group)
        self.timer_label = QLabel("")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size:48px; font-weight:bold; color:green;")
        l.addWidget(self.timer_label)
        self.status_scroll = QScrollArea()
        self.status_scroll.setStyleSheet("""
        border:1px solid #cbd5e1;
        border-radius:10px;
        background-color:#ffffff;
        """)
        self.status_scroll.setWidgetResizable(True)
        self.status_scroll.setFixedHeight(55)
        self.status_container = QWidget()
        self.status_layout = QHBoxLayout(self.status_container)
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_scroll.setWidget(self.status_container)
        l.addWidget(self.status_scroll)
        self.q_label = QLabel("")
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet("""
        font-weight:bold;
        font-size:25px;
        border:1px solid #cbd5e1;
        border-radius:12px;
        padding:12px;
        background-color:#e2e8f0;
        """)
        self.q_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        l.addWidget(self.q_label)
        self.opts_layout = QVBoxLayout()
        l.addLayout(self.opts_layout)
        self.skip_btn = QPushButton("Mark for Review")
        self.skip_btn.setStyleSheet("background-color:#f0ad4e;font-size:20px;")
        self.skip_btn.setMinimumHeight(56)
        self.mark_btn = QPushButton("Mark for Error")
        self.mark_btn.setStyleSheet("background-color:#ef4444;border:2px solid #dc2626;color:white;font-size:25px;")
        self.mark_btn.setMinimumHeight(56)
        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.setStyleSheet("background-color:#6c757d;color:white;font-size:20px;")
        self.clear_btn.setMinimumHeight(56)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setStyleSheet("background-color:#0275d8;color:white;font-size:25px;")
        self.pause_btn.setMinimumHeight(56)
        h = QHBoxLayout()
        h.addWidget(self.skip_btn)
        h.addWidget(self.mark_btn)
        h.addWidget(self.clear_btn)
        h.addWidget(self.pause_btn)
        l.addLayout(h)
        self.feedback = QLabel("")
        self.feedback.setWordWrap(True)
        self.feedback.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.feedback.setStyleSheet("""
        font-size:28px;
        font-weight:bold;
        border:1px solid #cbd5e1;
        border-radius:10px;
        padding:10px;
        background-color:#ffffff;
        """)
        l.addWidget(self.feedback)
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("""
        font-size:26px;
        font-weight:bold;
        border:1px solid #cbd5e1;
        border-radius:10px;
        padding:8px;
        background-color:#ffffff;
        """)
        l.addWidget(self.stats_label)
        self.ctrl_layout = QHBoxLayout()
        l.addLayout(self.ctrl_layout)
        self.skip_btn.clicked.connect(self.mark_for_review)
        self.mark_btn.clicked.connect(self.mark)
        self.clear_btn.clicked.connect(self.clear_selection)
        self.pause_btn.clicked.connect(self.pause_resume)
        self.pause_overlay = QFrame(self.quiz_group)
        self.pause_overlay.setParent(self.quiz_group)
        self.pause_overlay.raise_()
        self.pause_overlay.setGeometry(self.quiz_group.rect())
        self.pause_overlay.setStyleSheet("background-color: white;")
        self.pause_overlay.setGeometry(0, 0, 10000, 10000)
        self.pause_overlay.hide()
        overlay_layout = QVBoxLayout(self.pause_overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)
        overlay_layout.setSpacing(20)
        overlay_layout.setAlignment(Qt.AlignCenter)
        self.pause_label = QLabel("Quiz is Paused")
        self.pause_label.setStyleSheet("color: black; font-size: 40px; font-weight: bold;")
        self.pause_label.setAlignment(Qt.AlignCenter)
        self.resume_btn_overlay = QPushButton("Resume")
        self.resume_btn_overlay.setMinimumHeight(60)
        self.resume_btn_overlay.setStyleSheet("font-size: 25px; background-color: #5bc0de; color: white;")
        self.restart_btn_overlay = QPushButton("Restart")
        self.restart_btn_overlay.setMinimumHeight(60)
        self.restart_btn_overlay.setStyleSheet("font-size: 25px; background-color: #5cb85c; color: white;")        
        self.quit_btn_overlay = QPushButton("Quit")
        self.quit_btn_overlay.setMinimumHeight(60)
        self.quit_btn_overlay.setStyleSheet("font-size: 25px; background-color: #d9534f; color: white;")
        self.submit_btn_overlay = QPushButton("Submit Quiz")
        self.submit_btn_overlay.setMinimumHeight(60)
        self.submit_btn_overlay.setStyleSheet("font-size: 25px; background-color: #5cb85c; color: white;")
        overlay_layout.addWidget(self.pause_label)
        overlay_layout.addSpacing(20)
        overlay_layout.addWidget(self.resume_btn_overlay)
        overlay_layout.addSpacing(20)
        overlay_layout.addWidget(self.restart_btn_overlay)
        overlay_layout.addWidget(self.quit_btn_overlay)
        overlay_layout.addWidget(self.submit_btn_overlay)
        self.resume_btn_overlay.clicked.connect(self.pause_resume)
        self.restart_btn_overlay.clicked.connect(self.restart_quiz)
        self.quit_btn_overlay.clicked.connect(self.quit)
        self.submit_btn_overlay.clicked.connect(self.handle_submit)

    def set_options_enabled(self, enabled):
        if not hasattr(self, "state") or not self.state:
            return
        if self.index < 0 or self.index >= len(self.state):
            return
        st = self.state[self.index]
        for i in range(self.opts_layout.count()):
            w = self.opts_layout.itemAt(i).widget()
            if not w:
                continue
            is_error = any(me["question"] == self.questions.iloc[self.index][question_col] for me in marked_errors)
            if is_error:
                w.setEnabled(False)
            elif reveal_answers_during_quiz and st["answered"]:
                w.setEnabled(False)
            else:
                w.setEnabled(enabled)
        if any(me["question"] == self.questions.iloc[self.index][question_col] for me in marked_errors):
            self.skip_btn.setEnabled(False)
        else:
            self.skip_btn.setEnabled(enabled)

    def pause_resume(self):
        global timer
        if self.pause_btn.text() == "Pause":
            timer.stop()
            self.pause_btn.setText("Resume")
            self.pause_overlay.setGeometry(self.quiz_group.rect())
            self.pause_overlay.raise_()
            self.pause_overlay.show()
        else:
            timer.start(1000)
            self.pause_btn.setText("Pause")
            self.pause_overlay.hide()

    def start_quiz(self):
        global df_all, score, attempted, correct_count, review_log, marked_errors, questions_master, timer, time_left
        if hasattr(self, "pause_overlay"):
            self.pause_overlay.hide()
            self.pause_btn.setText("Pause")
        score = 0
        attempted = 0
        correct_count = 0
        review_log = []
        marked_errors = []
        self.minimize_attempts = 0
        if exam_mode:
            self.setFixedSize(self.size())
        else:
            self.setMinimumSize(850, 600)
            self.setMaximumSize(16777215, 16777215)
        df_shuffled = df_all.sample(frac=1).reset_index(drop=True)
        questions_master = df_shuffled
        if selected_num_questions and len(questions_master) > selected_num_questions:
            questions_master = questions_master.iloc[:selected_num_questions]
        self.questions = questions_master.reset_index(drop=True)
        self.index = 0
        for i in reversed(range(self.status_layout.count())):
            widget = self.status_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.status_buttons = []
        for i in range(len(self.questions)):
            b = QPushButton(str(i+1))
            b.setFixedSize(40, 40)
            b.setStyleSheet(
                "font-size:18px;"
                "border-radius:20px;"
                "border:1px solid #cbd5e1;"
                "background-color:#ffffff;"
            )
            b.clicked.connect(lambda _, x=i: self.jump_to_question(x))
            self.status_layout.addWidget(b)
            self.status_buttons.append(b)
        self.state = []
        for i in range(len(self.questions)):
            row = self.questions.iloc[i]
            opts = [row[c] for c in option_cols if c in row and pd.notna(row[c])]
            random.shuffle(opts)
            self.state.append({
                "answered": False,
                "selected": None,
                "unanswered": True,
                "marked": False,
                "options": opts,
                "attempt_counted": False
            })
        self.update_stats_line()
        if exam_mode:
            self.pause_btn.hide()
        else:
            self.pause_btn.show()
        self.show_question()
        time_left = timer_duration
        if timer is None:
            timer = QTimer()
            timer.timeout.connect(self.update_timer)
        else:
            timer.stop()
            try:
                timer.timeout.disconnect()
            except Exception:
                pass
            timer.timeout.connect(self.update_timer)
        timer.start(1000)
        
    def update_status_colors(self):
        for i, st in enumerate(self.state):
            btn = self.status_buttons[i]
            row = self.questions.iloc[i]
            is_error = any(me["question"] == row[question_col] for me in marked_errors)
            if is_error:
                btn.setStyleSheet("background-color:gray;color:white;font-size:18px;border-radius:20px;")
            elif st["marked"]:
                btn.setStyleSheet("background-color:yellow;color:black;font-size:18px;border-radius:20px;")
            elif st["answered"]:
                if reveal_answers_during_quiz:
                    if str(st["selected"]).strip().lower() == str(row[answer_col]).strip().lower():
                        btn.setStyleSheet("background-color:#22c55e;border:2px solid #16a34a;color:white;font-size:18px;border-radius:20px;")
                    else:
                        btn.setStyleSheet("background-color:#ef4444;border:2px solid #dc2626;color:white;font-size:18px;border-radius:20px;")
                else:
                    btn.setStyleSheet("background-color:#3b82f6;border:2px solid #2563eb;color:white;font-size:18px;border-radius:20px;")    
            else:
                btn.setStyleSheet("font-size:18px; border-radius:20px;")
                
    def update_stats_line(self):
        global score, correct_count, attempted, reveal_answers_during_quiz
        attempted = sum(1 for st in self.state if st["selected"] is not None)    
        if reveal_answers_during_quiz:
            incorrect = attempted - correct_count
            self.stats_label.setText(f"Correct: {correct_count}   Incorrect: {incorrect}   Score: {score}")
        else:
            self.stats_label.setText(f"Attempted: {attempted}")

    def jump_to_question(self, idx):
        self.index = idx
        self.show_question()

    def update_timer(self):
        global time_left
        if time_left <= 0:
            timer.stop()
            self.end()
        else:
            mins, secs = divmod(time_left, 60)
            self.timer_label.setText(f"{mins:02d}:{secs:02d}")
            time_left -= 1

    def show_question(self):
        self.start_group.hide()
        self.quiz_group.show()
        self.end_group.hide()    
        for i in reversed(range(self.opts_layout.count())):
            w = self.opts_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self.feedback.setText("")
        row = self.questions.iloc[self.index]
        self.current_row = row
        self.q_label.setText(f"Q{self.index+1}/{len(self.questions)}: {row[question_col]}")
        st = self.state[self.index]
        opts = self.state[self.index]["options"]
        is_error = any(me["question"] == row[question_col] for me in marked_errors)
        for o in opts:
            btn = QPushButton()
            btn.real_value = str(o)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(64)
            btn.setStyleSheet("""
            text-align:left;
            font-size:25px;
            border:1px solid #cbd5e1;
            border-radius:10px;
            padding:10px;
            background-color:#ffffff;
            """)
            btn.setText(str(o).replace("&&", "&").replace("&", "&&"))
            btn.clicked.connect(lambda _, b=btn: self.answer(b, row))
            if is_error:
                btn.setEnabled(False)
            else:
                btn.setEnabled(not (reveal_answers_during_quiz and st["answered"]))
            if st["answered"]:
                if reveal_answers_during_quiz:
                    if str(o) == str(row[answer_col]):
                        btn.setStyleSheet("background-color:#22c55e;border:2px solid #16a34a;color:white;font-size:25px;")
                    elif str(o) == str(st["selected"]):
                        btn.setStyleSheet("background-color:#ef4444;border:2px solid #dc2626;color:white;font-size:25px;")
                else:
                    if str(o) == str(st["selected"]):
                        btn.setStyleSheet("background-color:#3b82f6;border:2px solid #2563eb;color:white;font-size:25px;")
            else:
                if str(o) == str(st["selected"]):
                    btn.setStyleSheet("background-color:#3b82f6;border:2px solid #2563eb;color:white;font-size:25px;")
            self.opts_layout.addWidget(btn)
        if is_error:
            self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:red;")
            self.feedback.setText("Marked for Error ❗")    
            self.skip_btn.setEnabled(False)
            self.skip_btn.setStyleSheet("background-color:#94a3b8;color:white;font-size:20px;")
            self.clear_btn.setEnabled(False)
            self.clear_btn.setStyleSheet("background-color:#94a3b8;color:white;font-size:20px;")        
            for i in range(self.opts_layout.count()):
                w = self.opts_layout.itemAt(i).widget()
                if w:
                    w.setEnabled(False)
                    w.setStyleSheet("""
                        text-align:left;
                        font-size:25px;
                        border:1px solid #cbd5e1;
                        border-radius:10px;
                        padding:10px;
                        background-color:#e5e7eb;
                        color:#94a3b8;
                    """)
        elif st["marked"]:
            self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:orange;")
            self.feedback.setText("Marked for Review ⚠️")
            self.skip_btn.setEnabled(True)
        elif st["answered"]:
            if reveal_answers_during_quiz:
                self.skip_btn.setEnabled(False)
                self.skip_btn.setStyleSheet("background-color:#94a3b8;color:white;font-size:20px;")
                if st["selected"] == str(row[answer_col]):
                    self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:green;")
                    self.feedback.setText("Correct!")
                else:
                    self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:red;")
                    self.feedback.setText(f"Wrong! Correct: {row[answer_col]}")
            else:
                self.feedback.setText("")
        else:
            self.skip_btn.setEnabled(True)
            self.skip_btn.setStyleSheet("background-color:#f0ad4e;font-size:20px;")
        
            self.clear_btn.setEnabled(True)
            self.clear_btn.setStyleSheet("background-color:#6c757d;color:white;font-size:20px;")
        if reveal_answers_during_quiz:
            self.clear_btn.hide()
        else:
            self.clear_btn.show()
        self.show_controls()
        self.update_status_colors()
        self.update_stats_line()

    def answer(self, btn, row):
        global score, attempted, correct_count
        st = self.state[self.index]
        st["selected"] = btn.real_value
        st["answered"] = True
        st["marked"] = False
        st["unanswered"] = False
        if reveal_answers_during_quiz:
            for i in range(self.opts_layout.count()):
                w = self.opts_layout.itemAt(i).widget()
                if w:
                    w.setEnabled(False)
            if btn.real_value == str(row[answer_col]):
                score += correct_marks
                correct_count += 1
                review_log.append(("Correct", row[question_col], row[answer_col]))
                clean_row = {
                    "question": str(row[question_col]),
                    "answer": str(row[answer_col]),
                    "options": [str(row[c]) for c in option_cols if c in row and pd.notna(row[c])]
                }
                append_to_csv(SELECTED_CORRECT_FILE, clean_row)
                self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:green;")
                self.feedback.setText("Correct!")
            else:
                score -= incorrect_marks
                review_log.append(("Incorrect", row[question_col], row[answer_col]))
                self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:red;")
                self.feedback.setText(f"Wrong! | Correct: {row[answer_col]}")
            attempted = sum(1 for s in self.state if s["selected"] is not None)
            self.feedback.setText(self.feedback.text() + f"<br>Attempted: {attempted} | Correct: {correct_count} | Score: {score}")
        else:
            self.feedback.setText("")
        self.update_status_colors()
        self.update_stats_line()
        self.show_question()

    def mark(self):
        row = self.current_row
        qtext = row[question_col]
        occurrences = []
        for _, r in df_all.iterrows():
            if str(r.get(question_col)) == str(qtext):
                occurrences.append((r['__source_file__'], int(r['__original_csv_row__'])))
        if occurrences:
            marked_errors.append({"question": qtext, "occurrences": occurrences})
        st = self.state[self.index]
        st["marked"] = True
        st["unanswered"] = True
        st["selected"] = None
        st["answered"] = False
        for i in range(self.opts_layout.count()):
            w = self.opts_layout.itemAt(i).widget()
            if w:
                w.setEnabled(False)
                w.setStyleSheet("""
                    text-align:left;
                    font-size:25px;
                    border:1px solid #cbd5e1;
                    border-radius:10px;
                    padding:10px;
                    background-color:#e5e7eb;
                    color:#94a3b8;
                """)
        self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:red;")
        self.feedback.setText("Marked ❗")
        self.update_stats_line()
        self.update_status_colors()
        self.show_question()
            
    def clear_selection(self):
        if reveal_answers_during_quiz:
            return    
        st = self.state[self.index]
        st["selected"] = None
        st["answered"] = False
        st["unanswered"] = True
        st["marked"] = False
        self.feedback.setText("")
        self.update_status_colors()
        self.update_stats_line()
        self.show_question()
            
    def mark_for_review(self):
        st = self.state[self.index]
        st["marked"] = True
        st["unanswered"] = True
        self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:orange;")
        self.feedback.setText("Marked for Review ⚠️")
        self.update_status_colors()
    
    def show_controls(self):
        for i in reversed(range(self.ctrl_layout.count())):
            w = self.ctrl_layout.itemAt(i).widget()
            if w:
                w.deleteLater()    
        prev_btn = QPushButton("Previous")
        prev_btn.setStyleSheet("background-color:#5bc0de;color:white;font-size:25px;")
        prev_btn.setMinimumHeight(56)
        prev_btn.clicked.connect(self.go_previous)
        r = QPushButton("Restart")
        r.setStyleSheet("background-color:#22c55e;border:2px solid #16a34a;color:white;font-size:25px;")
        r.setMinimumHeight(56)
        q = QPushButton("Quit")
        q.setStyleSheet("background-color:#ef4444;border:2px solid #dc2626;color:white;font-size:25px;")
        q.setMinimumHeight(56)
        self.ctrl_layout.addWidget(r)
        self.ctrl_layout.addWidget(prev_btn)
        self.ctrl_layout.addWidget(q)
        r.clicked.connect(self.restart_quiz)
        q.clicked.connect(self.quit)
        if self.index+1 < len(self.questions):
            n = QPushButton("Next")
            n.setStyleSheet("background-color:#5bc0de;color:white;font-size:25px;")
            n.setMinimumHeight(56)
            self.ctrl_layout.addWidget(n)
            n.clicked.connect(lambda: (setattr(self, "index", self.index+1), self.show_question()))
        else:
            loop_btn = QPushButton("Go to First")
            loop_btn.setStyleSheet("background-color:#337ab7;color:white;font-size:25px;")
            loop_btn.setMinimumHeight(56)
            self.ctrl_layout.addWidget(loop_btn)
            loop_btn.clicked.connect(lambda: (setattr(self, "index", 0), self.show_question()))
        submit_btn = QPushButton("Submit Quiz")
        submit_btn.setStyleSheet("background-color:#22c55e;border:2px solid #16a34a;color:white;font-size:25px;")
        submit_btn.setMinimumHeight(56)
        self.ctrl_layout.addWidget(submit_btn)
        submit_btn.clicked.connect(self.handle_submit)

    def go_previous(self):
        if self.index > 0:
            self.index -= 1
        else:
            self.index = len(self.questions) - 1
        self.show_question()
        
    def confirm_action(self, message="Are you sure?"):
        reply = QMessageBox.question(
            self,
            "Confirm",
            message,
            QMessageBox.Ok | QMessageBox.Cancel
        )
        return reply == QMessageBox.Ok
    
    def restart_quiz(self):
        if not self.confirm_action("Are you sure you want to restart?"):
            return
        if hasattr(self, "pause_overlay"):
            self.pause_overlay.hide()
        self.start_quiz()

    def quit(self):
        global selected_num_questions
        if not self.confirm_action("Are you sure you want to quit?"):
            return
        selected_num_questions = None
        if hasattr(self, "pause_overlay"):
            self.pause_overlay.hide()
        self.show_start()

    def init_end(self):
        l = QVBoxLayout(self.end_group)
        self.summary = QLabel("")
        self.summary.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        l.addWidget(self.summary)
        self.review = QTableWidget()
        l.addWidget(self.review)
        h = QHBoxLayout()
        rb = QPushButton("Restart")
        qb = QPushButton("Quit")
        rb.setStyleSheet("background-color:#22c55e;border:2px solid #16a34a;color:white;font-size:25px;")
        qb.setStyleSheet("background-color:#ef4444;border:2px solid #dc2626;color:white;font-size:25px;")
        rb.setMinimumHeight(56)
        qb.setMinimumHeight(56)
        rb.clicked.connect(self.start_quiz)
        qb.clicked.connect(self.show_start)
        h.addWidget(rb)
        h.addWidget(qb)
        l.addLayout(h)

    def end(self):
        if hasattr(self, "pause_overlay"):
            self.pause_overlay.hide()
        self.start_group.hide()
        self.quiz_group.hide()
        self.end_group.show()
        if timer:
            timer.stop()
        global attempted, correct_count, score
        if not reveal_answers_during_quiz:
            attempted = 0
            correct_count = 0
            score = 0
            for i, row in self.questions.iterrows():
                st = self.state[i]
                if st["selected"] is not None:
                    attempted += 1
                    if str(st["selected"]).strip().lower() == str(row[answer_col]).strip().lower():
                        correct_count += 1
                        score += correct_marks
                        clean_row = {
                            "question": str(row[question_col]),
                            "answer": str(row[answer_col]),
                            "options": [str(row[c]) for c in option_cols if c in row and pd.notna(row[c])]
                        }
                        append_to_csv(SELECTED_CORRECT_FILE, clean_row)
                    else:
                        score -= incorrect_marks
        success_pct = (correct_count / attempted * 100) if attempted > 0 else 0
        self.summary.setText(
            f"<h2>"
            f"<b>FINISHED</b> | "
            f"<b>ATTEMPTED</b>: <span style='color:green'>{attempted}</span> | "
            f"<b>CORRECT</b>: <span style='color:green'>{correct_count}</span> | "
            f"<b>SCORE</b>: <span style='color:green'>{score}</span> | "
            f"<b>SUCCESS %</b>: <span style='color:green'>{success_pct:.2f}%</span>"
            f"</h2>"
        )
        self.summary.setAlignment(Qt.AlignCenter)
        error_questions = set(me["question"] for me in marked_errors)
        review_rows = []
        for i, row in self.questions.iterrows():
            st = self.state[i]
            if row[question_col] in error_questions:
                status = "Marked for Error"
            elif st["selected"] is None:
                status = "Unanswered"
            elif st["marked"]:
                status = "Marked for Review"
            elif st["answered"]:
                if st["selected"] == str(row[answer_col]):
                    status = "Correct"
                else:
                    status = "Incorrect"
            else:
                status = "Unanswered"
            source_file = row.get("__source_file__", "")
            orig_row = row.get("__original_csv_row__", None)
            if orig_row is None:
                try:
                    orig_row = int(row.get("__original_csv_index__", i)) + 2
                except Exception:
                    orig_row = ""
            source_text = f"{source_file} | {int(orig_row)}" if source_file else (f"row {int(orig_row)}" if orig_row != "" else "")
            review_rows.append({
                "Status": status,
                "Question": row[question_col],
                "Answer": row[answer_col],
                "Source": source_text
            })
        dfv = pd.DataFrame(review_rows)
        self.review.setRowCount(len(dfv))
        self.review.setColumnCount(4)
        self.review.setHorizontalHeaderLabels(dfv.columns)
        for i, (_, r) in enumerate(dfv.iterrows()):
            status = str(r["Status"]).lower()
            if status == "correct":
                bg_color = "#dcfce7"
            elif status == "incorrect":
                bg_color = "#fef9c3"
            elif status == "marked for error":
                bg_color = "#fee2e2"
            elif status == "unanswered":
                bg_color = "#e5e7eb"
            elif status == "marked for review":
                bg_color = "#fde68a"
            else:
                bg_color = "#ffffff"
            for j, c in enumerate(dfv.columns):
                item = QTableWidgetItem(str(r[c]))
                item.setBackground(QColor(bg_color))
                self.review.setItem(i, j, item)
        header = self.review.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        total_width = self.review.viewport().width()
        self.review.setColumnWidth(0, int(total_width * 0.15))
        self.review.setColumnWidth(1, int(total_width * 0.45))
        self.review.setColumnWidth(2, int(total_width * 0.25))
        self.review.setColumnWidth(3, int(total_width * 0.15))
        self.review.setWordWrap(True)
        self.review.resizeRowsToContents()
        self.review.setEditTriggers(QTableWidget.NoEditTriggers)
            
    def handle_submit(self):
        if not self.confirm_action("Are you sure you want to submit the quiz?"):
            return
        self.end()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "answer_overlay"):
            self.answer_overlay.setGeometry(self.answer_overlay.parent().rect())
        if hasattr(self, "pause_overlay"):
            self.pause_overlay.setGeometry(self.quiz_group.rect())
            
    def focusOutEvent(self, event):
        if exam_mode:
            self.activateWindow()
            self.raise_()
            self.minimize_attempts += 1
            if self.minimize_attempts == 1:
                msg = QMessageBox(self)
                msg.setWindowTitle("Warning")
                msg.setText("Leaving the quiz is not allowed.\n\nNext attempt will auto-submit.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setWindowModality(Qt.ApplicationModal)
                msg.exec_()
            elif self.minimize_attempts >= 2:
                self.end()
        super().focusOutEvent(event)
            
    def closeEvent(self, event):
        if self.confirm_action("Are you sure you want to exit?"):
            event.accept()
        else:
            event.ignore()
            
def main():
    app = QApplication(sys.argv)
    w = QuizMainWindow()
    w.show()
    w.showMaximized()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()