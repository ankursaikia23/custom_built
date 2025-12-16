import sys
import os
import random
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QGroupBox, QScrollArea, QFrame
)

from PyQt5.QtCore import Qt, QTimer

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CORRECT_FILE = os.path.join(APP_DIR, "correct1.csv")

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
    question_col = question_candidates[0]
    answer_col = answer_candidates[0]
    option_cols = [c for c in option_candidates if c in cols]
    if os.path.exists(CORRECT_FILE):
        correct_df = pd.read_csv(CORRECT_FILE)
        correct_df.columns = correct_df.columns.str.strip().str.lower()
        if question_col in correct_df.columns:
            df_concat = df_concat[~df_concat[question_col].isin(correct_df[question_col])]
            df_concat = df_concat.reset_index(drop=True)
    globals().update({"question_col": question_col, "answer_col": answer_col, "option_cols": option_cols})
    return df_concat

def append_to_csv(filename, row):
    global question_col, answer_col, option_cols
    try:
        dirpath = os.path.dirname(os.path.abspath(filename))
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        columns = [question_col] + option_cols + [answer_col]
        columns = [c.strip().lower() for c in columns]
        if not os.path.exists(filename):
            df_new = pd.DataFrame(columns=columns)
            df_new.to_csv(filename, index=False)
        df_existing = pd.read_csv(filename)
        df_existing.columns = df_existing.columns.str.strip().str.lower()
        for c in columns:
            if c not in df_existing.columns:
                df_existing[c] = pd.NA
        q_text = str(row.get(question_col) if question_col in row.index else row.get(question_col.lower(), ""))
        if question_col in df_existing.columns:
            if (df_existing[question_col].astype(str) == q_text).any():
                return
        new_values = {}
        for c in columns:
            val = None
            if c in row.index:
                val = row.get(c)
            elif c.lower() in row.index:
                val = row.get(c.lower())
            else:
                val = row.get(c)
            new_values[c] = val
        new_row = pd.DataFrame([new_values], columns=columns)
        df_existing = pd.concat([df_existing, new_row], ignore_index=True, sort=False)
        df_existing = df_existing.loc[:, columns]
        df_existing.to_csv(filename, index=False)
    except Exception:
        pass

class QuizMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quiz App (PyQt)")
        self.setMinimumSize(850, 600)
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QVBoxLayout(self.central)
        self.top_buttons_layout = QHBoxLayout()
        self.load_btn = QPushButton("Open / Load CSV(s)")
        self.exit_btn = QPushButton("Exit")
        for b in [self.load_btn, self.exit_btn]:
            b.setMinimumHeight(56)
            b.setStyleSheet("font-size:25px;background-color:#5bc0de;color:white;")
        self.top_buttons_layout.addWidget(self.load_btn)
        self.top_buttons_layout.addWidget(self.exit_btn)
        self.main_layout.addLayout(self.top_buttons_layout)
        self.start_group = QGroupBox()
        self.quiz_group = QGroupBox()
        self.end_group = QGroupBox()
        self.main_layout.addWidget(self.start_group)
        self.main_layout.addWidget(self.quiz_group)
        self.main_layout.addWidget(self.end_group)
        self.load_btn.clicked.connect(self.select_csvs)
        self.exit_btn.clicked.connect(self.close)
        self.init_start()
        self.init_quiz()
        self.init_end()
        self.show_start()

    def select_csvs(self):
        global df_all, selected_files
        paths, _ = QFileDialog.getOpenFileNames(self, "Select quiz CSV(s)", "", "CSV Files (*.csv)")
        if paths:
            selected_files = paths
            try:
                df_all = load_filtered_questions_from_files(selected_files)
                total = len(df_all)
                self.avail_label.setText(f"<h3>Loaded {len(selected_files)} file(s) | Total: {total}</h3>")
                self.show_start()
            except Exception as e:
                self.avail_label.setText(f"<h3 style='color:red;'>Error loading CSV: {e}</h3>")

    def init_start(self):
        l = QVBoxLayout(self.start_group)
        self.avail_label = QLabel("")
        self.avail_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.avail_label.setStyleSheet("font-size:25px;")
        l.addWidget(self.avail_label)
        self.combo = QComboBox()
        self.combo.setStyleSheet("font-size:25px;")
        self.combo.setMinimumHeight(56)
        l.addWidget(self.combo)
        self.mode_label = QLabel("Answer Reveal Mode:")
        self.mode_label.setStyleSheet("font-size:22px;")
        l.addWidget(self.mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.setStyleSheet("font-size:22px;")
        self.mode_combo.setMinimumHeight(48)
        self.mode_combo.addItem("Show answers immediately")
        self.mode_combo.addItem("Hide answers until review")
        l.addWidget(self.mode_combo)
        self.start_btn = QPushButton("Start Quiz")
        self.start_btn.setStyleSheet("background-color:#5cb85c;color:white;font-size:25px;")
        self.start_btn.setMinimumHeight(56)
        l.addWidget(self.start_btn)
        self.start_btn.clicked.connect(self.on_start)

    def show_start(self):
        global df_all
        self.start_group.show()
        self.quiz_group.hide()
        self.end_group.hide()
        if df_all is None or df_all.empty:
            self.avail_label.setText("<h3>No questions available! Please load CSV(s).</h3>")
            self.start_btn.setEnabled(False)
            self.combo.clear()
            return
        total = len(df_all)
        self.avail_label.setText(f"<h3>Total Questions Available: {total}</h3>")
        opts = [n for n in [10,20,30,40,50] if n<=total]
        if total not in opts:
            opts.append(total)
        self.combo.clear()
        for n in opts:
            self.combo.addItem(str(n))
        self.start_btn.setEnabled(True)

    def on_start(self):
        global selected_num_questions, timer_duration, time_left, timer
        selected_num_questions = int(self.combo.currentText())
        global reveal_answers_during_quiz
        reveal_answers_during_quiz = (self.mode_combo.currentText() == "Show answers immediately")
        if selected_num_questions == 10:
            timer_duration = 5*60
        elif selected_num_questions == 20:
            timer_duration = 10*60
        elif selected_num_questions == 30:
            timer_duration = 15*60
        elif selected_num_questions == 40:
            timer_duration = 20*60
        elif selected_num_questions == 50:
            timer_duration = 25*60
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
        self.status_scroll.setWidgetResizable(True)
        self.status_scroll.setFixedHeight(55)
        
        self.status_container = QWidget()
        self.status_layout = QHBoxLayout(self.status_container)
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_scroll.setWidget(self.status_container)
        l.addWidget(self.status_scroll)
        self.q_label = QLabel("")
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet("font-weight:bold;font-size:25px;")
        self.q_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        l.addWidget(self.q_label)
        self.opts_layout = QVBoxLayout()
        l.addLayout(self.opts_layout)
        self.skip_btn = QPushButton("Mark for Review")
        self.skip_btn.setStyleSheet("background-color:#f0ad4e;font-size:20px;")
        self.skip_btn.setMinimumHeight(56)
        self.mark_btn = QPushButton("Mark for Error")
        self.mark_btn.setStyleSheet("background-color:#d9534f;color:white;font-size:25px;")
        self.mark_btn.setMinimumHeight(56)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setStyleSheet("background-color:#0275d8;color:white;font-size:25px;")
        self.pause_btn.setMinimumHeight(56)
        h = QHBoxLayout()
        h.addWidget(self.skip_btn)
        h.addWidget(self.mark_btn)
        h.addWidget(self.pause_btn)
        l.addLayout(h)
        self.feedback = QLabel("")
        self.feedback.setWordWrap(True)
        self.feedback.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.feedback.setStyleSheet("font-size:28px; font-weight:bold;")
        l.addWidget(self.feedback)
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("font-size:26px;font-weight:bold;")
        l.addWidget(self.stats_label)
        self.ctrl_layout = QHBoxLayout()
        l.addLayout(self.ctrl_layout)
        self.skip_btn.clicked.connect(self.skip)
        self.mark_btn.clicked.connect(self.mark)
        self.pause_btn.clicked.connect(self.pause_resume)

    def set_options_enabled(self, enabled):
        st = self.state[self.index]
        for i in range(self.opts_layout.count()):
            w = self.opts_layout.itemAt(i).widget()
            if not w:
                continue
            if st["answered"] or st["marked"]:
                w.setEnabled(False)
            else:
                w.setEnabled(enabled)
        if st["marked"]:
            self.skip_btn.setEnabled(False)
        else:
            self.skip_btn.setEnabled(enabled)

    def pause_resume(self):
        global timer
        if self.pause_btn.text() == "Pause":
            timer.stop()
            self.pause_btn.setText("Resume")
            self.set_options_enabled(False)
        else:
            timer.start(1000)
            self.pause_btn.setText("Pause")
            self.set_options_enabled(True)

    def start_quiz(self):
        global df_all, score, attempted, correct_count, review_log, marked_errors, questions_master, timer, time_left
        score = attempted = correct_count = 0
        review_log = []
        marked_errors = []
        self.update_stats_line()
        df_shuffled = df_all.sample(frac=1).reset_index(drop=True)
        questions_master = df_shuffled
        if selected_num_questions and len(questions_master) > selected_num_questions:
            questions_master = questions_master.iloc[:selected_num_questions]
        self.questions = questions_master.reset_index(drop=True)
        self.index = 0
        self.status_buttons = []
        for i in range(len(self.questions)):
            b = QPushButton(str(i+1))
            b.setFixedSize(40, 40)
            b.setStyleSheet(
                "font-size:18px;"
                "border-radius:20px;"
            )
            b.clicked.connect(lambda _, x=i: self.jump_to_question(x))
            self.status_layout.addWidget(b)
            self.status_buttons.append(b)
        self.state = []
        for _ in range(len(self.questions)):
            self.state.append({
                "answered": False,
                "selected": None,
                "unanswered": True,
                "marked": False,
                "attempt_counted": False
            })
        self.show_question()
        time_left = timer_duration
        if not timer:
            timer = QTimer()
            timer.timeout.connect(self.update_timer)
        timer.start(1000)
        
    def update_status_colors(self):
        for i, st in enumerate(self.state):
            btn = self.status_buttons[i]
    
            if any(me["question"] == self.questions.iloc[i][question_col] for me in marked_errors):
                btn.setStyleSheet(
                    "background-color:gray;"
                    "color:white;"
                    "font-size:18px;"
                    "border-radius:20px;"
                )
            elif st["marked"]:
                btn.setStyleSheet(
                    "background-color:yellow;"
                    "color:black;"
                    "font-size:18px;"
                    "border-radius:20px;"
                )
            elif st["answered"]:
                if reveal_answers_during_quiz:
                    row = self.questions.iloc[i]
                    if st["selected"] == str(row[answer_col]):
                        btn.setStyleSheet(
                            "background-color:#5cb85c;"
                            "color:white;"
                            "font-size:18px;"
                            "border-radius:20px;"
                        )
                    else:
                        btn.setStyleSheet(
                            "background-color:#d9534f;"
                            "color:white;"
                            "font-size:18px;"
                            "border-radius:20px;"
                        )
                else:
                    btn.setStyleSheet(
                        "background-color:blue;"
                        "color:white;"
                        "font-size:18px;"
                        "border-radius:20px;"
                    )
            
            else:
                btn.setStyleSheet("font-size:18px; border-radius:20px;")
                
    def update_stats_line(self):
        global score, correct_count, attempted, reveal_answers_during_quiz
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
        opts = [row[c] for c in option_cols if c in row and pd.notna(row[c])]
        random.shuffle(opts)
        for o in opts:
            btn = QPushButton(str(o))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(64)
            btn.setStyleSheet("text-align:left;font-size:25px;")
            btn.setText(str(o).replace("&&", "&").replace("&", "&&"))
            btn.clicked.connect(lambda _, b=btn: self.answer(b, row))
            if st["answered"]:
                btn.setEnabled(False)
                if reveal_answers_during_quiz:
                    if str(row[answer_col]) == str(o):
                        btn.setStyleSheet("background-color:#5cb85c;color:white;font-size:25px;")
                else:
                    if st["selected"] == str(o):
                        btn.setStyleSheet("background-color:blue;color:white;font-size:25px;")
            if st["marked"]:
                btn.setEnabled(False)
            self.opts_layout.addWidget(btn)
        if st["answered"]:
            if reveal_answers_during_quiz:
                if st["selected"] == str(row[answer_col]):
                    self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:green;")
                    self.feedback.setText("Correct!")
                else:
                    self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:red;")
                    self.feedback.setText(f"Wrong! Correct: {row[answer_col]}")
            else:
                self.feedback.setText("")
        if st["marked"]:
            self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:red;")
            self.feedback.setText("Marked ❗")
            self.skip_btn.setEnabled(False)
        else:
            self.skip_btn.setEnabled(True)
        self.show_controls()
        self.update_status_colors()
        self.update_stats_line()

    def answer(self, btn, row):
        global score, attempted, correct_count
        for i in range(self.opts_layout.count()):
            w = self.opts_layout.itemAt(i).widget()
            if w:
                w.setEnabled(False)
        st = self.state[self.index]
        st["answered"] = True
        st["selected"] = btn.text()
        st["unanswered"] = False
        if not st["attempt_counted"]:
            attempted += 1
            st["attempt_counted"] = True
        if btn.text() == str(row[answer_col]):
            score += 1
            correct_count += 1
            review_log.append(("Correct", row[question_col], row[answer_col]))
            append_to_csv(CORRECT_FILE, row)
        
            if reveal_answers_during_quiz:
                self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:green;")
                self.feedback.setText("Correct!")
        
            self.update_stats_line()
            self.update_status_colors()
        
        else:
            score -= 0.25
            review_log.append(("Incorrect", row[question_col], row[answer_col]))
        
            if reveal_answers_during_quiz:
                self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:red;")
                self.feedback.setText(f"Wrong! | Correct: {row[answer_col]}")
        
            self.update_status_colors()
        
        if reveal_answers_during_quiz:
            self.feedback.setText(self.feedback.text() + f"<br>Attempted: {attempted} | Correct: {correct_count} | Score: {score}")
        else:
            self.feedback.setText("")
        self.show_controls()

    def skip(self):
        global attempted
        st = self.state[self.index]
        st["unanswered"] = True
        if not st["attempt_counted"]:
            attempted += 1
            st["attempt_counted"] = True
        self.update_stats_line()
        if self.index+1 < len(self.questions):
            self.index += 1
            self.update_status_colors()
            self.show_question()
        else:
            self.index = 0
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
        self.feedback.setStyleSheet("font-size:28px;font-weight:bold;color:red;")
        self.feedback.setText("Marked ❗")
        global attempted
        if not st["attempt_counted"]:
            attempted += 1
            st["attempt_counted"] = True
        self.update_stats_line()
        if self.index+1 < len(self.questions):
            self.index += 1
            self.update_status_colors()
            self.show_question()
        else:
            self.index = 0
            self.show_question()

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
        r.setStyleSheet("background-color:#5cb85c;color:white;font-size:25px;")
        r.setMinimumHeight(56)
        q = QPushButton("Quit")
        q.setStyleSheet("background-color:#d9534f;color:white;font-size:25px;")
        q.setMinimumHeight(56)
        self.ctrl_layout.addWidget(prev_btn)
        self.ctrl_layout.addWidget(r)
        self.ctrl_layout.addWidget(q)
        submit_btn = QPushButton("Submit Quiz")
        submit_btn.setStyleSheet("background-color:#5cb85c;color:white;font-size:25px;")
        submit_btn.setMinimumHeight(56)
        self.ctrl_layout.addWidget(submit_btn)
        submit_btn.clicked.connect(self.end)
        r.clicked.connect(self.start_quiz)
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

    def go_previous(self):
        if self.index > 0:
            self.index -= 1
        else:
            self.index = len(self.questions) - 1
        self.show_question()

    def quit(self):
        global selected_num_questions
        selected_num_questions = None
        self.show_start()

    def init_end(self):
        l = QVBoxLayout(self.end_group)
        self.summary = QLabel("")
        self.summary.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        l.addWidget(self.summary)
        self.review = QTableWidget()
        l.addWidget(self.review)
        self.marked = QTableWidget()
        l.addWidget(self.marked)
        h = QHBoxLayout()
        rb = QPushButton("Restart")
        qb = QPushButton("Quit")
        rb.setStyleSheet("background-color:#5cb85c;color:white;font-size:25px;")
        qb.setStyleSheet("background-color:#d9534f;color:white;font-size:25px;")
        rb.setMinimumHeight(56)
        qb.setMinimumHeight(56)
        rb.clicked.connect(self.start_quiz)
        qb.clicked.connect(self.show_start)
        h.addWidget(rb)
        h.addWidget(qb)
        l.addLayout(h)

    def end(self):
        self.start_group.hide()
        self.quiz_group.hide()
        self.end_group.show()
        if timer:
            timer.stop()
        self.summary.setText(f"<h3>Finished!</h3><p>Attempted:{attempted} | Correct:{correct_count} | Score:{score}</p>")
        review_rows = []
        
        for i, row in self.questions.iterrows():
            st = self.state[i]
        
            if i in [r for r in range(len(self.questions)) if any(me["question"] == row[question_col] for me in marked_errors)]:
                status = "Marked for Error"
            elif st["marked"]:
                status = "Marked for Review"
            elif st["answered"]:
                if st["selected"] == str(row[answer_col]):
                    status = "Correct"
                else:
                    status = "Incorrect"
            elif st["unanswered"]:
                status = "Unanswered"
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
                "Question": row[question_col],
                "Answer": row[answer_col],
                "Source": source_text,
                "Status": status
            })
        
        dfv = pd.DataFrame(review_rows)
        self.review.setRowCount(len(dfv))
        self.review.setColumnCount(4)
        self.review.setHorizontalHeaderLabels(dfv.columns)
        
        for i, (_, r) in enumerate(dfv.iterrows()):
            for j, c in enumerate(dfv.columns):
                self.review.setItem(i, j, QTableWidgetItem(str(r[c])))
        
        header = self.review.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.review.resizeRowsToContents()
        self.review.resizeColumnsToContents()
        self.review.setWordWrap(True)

        if marked_errors:
            records = []
            for me in marked_errors:
                q = me["question"]
                occ = me["occurrences"]
                occ_str = "; ".join([f"{fn} (row {rn})" for fn, rn in occ])
                records.append((occ_str, q))
            dfm = pd.DataFrame(records, columns=["CSV(s) and Row(s)", "Question"])
            self.marked.setRowCount(len(dfm))
            self.marked.setColumnCount(2)
            self.marked.setHorizontalHeaderLabels(dfm.columns)
            for i, (_, r) in enumerate(dfm.iterrows()):
                for j, c in enumerate(dfm.columns):
                    self.marked.setItem(i, j, QTableWidgetItem(str(r[c])))
            header_m = self.marked.horizontalHeader()
            header_m.setSectionResizeMode(0, QHeaderView.Interactive)
            header_m.setSectionResizeMode(1, QHeaderView.Interactive)
            self.marked.setColumnWidth(0, int(self.marked.width() * 0.20))
            self.marked.setColumnWidth(1, int(self.marked.width() * 0.80))
            
            self.marked.setWordWrap(True)
            self.marked.resizeRowsToContents()
            self.marked.resizeColumnsToContents()
            self.marked.setTextElideMode(Qt.ElideNone)

def main():
    app = QApplication(sys.argv)
    w = QuizMainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()