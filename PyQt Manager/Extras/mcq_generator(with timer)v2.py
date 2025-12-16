import sys
import os
import random
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QGroupBox
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
question_status = {}
correct_count = 0
skipped_count = 0
selected_num_questions = None
questions_master = None
review_log = []
marked_errors = []
df_all = None
selected_files = []
timer_duration = 0
timer = None
time_left = 0

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
    if "__user_answer__" not in df_concat.columns:
        df_concat["__user_answer__"] = pd.Series(dtype="object")
    if "__marked__" not in df_concat.columns:
        df_concat["__marked__"] = pd.Series(dtype="bool")
    cols = list(df_concat.columns)
    question_candidates = [c for c in cols if 'question' in c]
    answer_candidates = [c for c in cols if 'answer' in c]
    option_candidates = [c for c in cols if 'option' in c]
    if not question_candidates or not answer_candidates or not option_candidates:
        raise ValueError("❌ Could not find required columns (question, answer, optionX) in the selected CSV file(s).")
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
                print(f"[append_to_csv] question already present, skipping: {q_text[:80]}")
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
        print(f"[append_to_csv] saved question to: {filename}")
    except Exception as exc:
        print(f"[append_to_csv] ERROR saving to {filename}: {exc}")

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
                self.avail_label.setText(f"<h3>✅ Loaded {len(selected_files)} file(s) | Total: {total}</h3>")
                self.show_start()
            except Exception as e:
                self.avail_label.setText(f"<h3 style='color:red;'>❌ Error loading CSV: {e}</h3>")

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
            self.avail_label.setText("<h3>🎉 No questions available! Please load CSV(s).</h3>")
            self.start_btn.setEnabled(False)
            self.combo.clear()
            return
        total = len(df_all)
        self.avail_label.setText(f"<h3>📊 Total Questions Available: {total}</h3>")
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
        self.q_label = QLabel("")
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet("font-weight:bold;font-size:25px;")
        self.q_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        l.addWidget(self.q_label)
        self.opts_layout = QVBoxLayout()
        l.addLayout(self.opts_layout)
        self.skip_btn = QPushButton("Skip")
        self.skip_btn.setStyleSheet("background-color:#f0ad4e;font-size:25px;")
        self.skip_btn.setMinimumHeight(56)
        self.mark_btn = QPushButton("Mark ⚠️")
        self.mark_btn.setStyleSheet("background-color:#d9534f;color:white;font-size:25px;")
        self.mark_btn.setMinimumHeight(56)
        self.pause_btn = QPushButton("Pause ⏸")
        self.pause_btn.setStyleSheet("background-color:#f0ad4e;color:white;font-size:25px;")
        self.pause_btn.setMinimumHeight(56)
        self.resume_btn = QPushButton("Resume ▶️")
        self.resume_btn.setStyleSheet("background-color:#5cb85c;color:white;font-size:25px;")
        self.resume_btn.setMinimumHeight(56)
        self.resume_btn.setEnabled(False)

        h = QHBoxLayout()
        h.addWidget(self.skip_btn)
        h.addWidget(self.mark_btn)
        h.addWidget(self.pause_btn)
        h.addWidget(self.resume_btn)
        l.addLayout(h)
        self.feedback = QLabel("")
        self.feedback.setWordWrap(True)
        self.feedback.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.feedback.setStyleSheet("font-size:28px; font-weight:bold; color:#222;")
        l.addWidget(self.feedback)
        self.ctrl_layout = QHBoxLayout()
        l.addLayout(self.ctrl_layout)
        self.prev_btn = QPushButton("Previous ⬅️")
        self.prev_btn.setStyleSheet("background-color:#337ab7;color:white;font-size:25px;")
        self.prev_btn.setMinimumHeight(56)
        self.next_btn = QPushButton("Next ➡️")
        self.next_btn.setStyleSheet("background-color:#337ab7;color:white;font-size:25px;")
        self.next_btn.setMinimumHeight(56)
        
        self.prev_btn.clicked.connect(self.go_previous)
        self.next_btn.clicked.connect(self.go_next)
        
        self.ctrl_layout.addWidget(self.prev_btn)
        self.ctrl_layout.addWidget(self.next_btn)
        self.skip_btn.clicked.connect(self.skip)
        self.mark_btn.clicked.connect(self.mark)
        self.pause_btn.clicked.connect(self.pause_quiz)
        self.resume_btn.clicked.connect(self.resume_quiz)

    def start_quiz(self):
        global df_all, score, attempted, correct_count, skipped_count, review_log, marked_errors, questions_master, timer, time_left
        score = attempted = correct_count = skipped_count = 0
        review_log = []
        marked_errors = []
        df_shuffled = df_all.sample(frac=1).reset_index(drop=True)
        questions_master = df_shuffled
        if selected_num_questions and len(questions_master) > selected_num_questions:
            questions_master = questions_master.iloc[:selected_num_questions]
        self.questions = questions_master.reset_index(drop=True)
        self.index = 0
        self.show_question()
        time_left = timer_duration
        if not timer:
            timer = QTimer()
            timer.timeout.connect(self.update_timer)
        timer.start(1000)

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
    
        opts = [row[c] for c in option_cols if c in row and pd.notna(row[c])]
        random.shuffle(opts)
        
        prev = question_status.get(self.index, None)
        marked = self.questions.at[self.index, "__marked__"] if "__marked__" in self.questions.columns else False
        
        for o in opts:
            btn = QPushButton(str(o))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(64)
            btn.setStyleSheet("text-align:left;font-size:25px;")
            btn.setText(str(o).replace("&&", "&").replace("&", "&&"))
    
            if prev or marked:
                correct_answer = str(row[answer_col])
                selected_answer = prev["selected"] if prev else None
                if btn.text() == correct_answer:
                    btn.setStyleSheet(btn.styleSheet() + "background-color:lightgreen;")
                if selected_answer and selected_answer != correct_answer and btn.text() == selected_answer:
                    btn.setStyleSheet(btn.styleSheet() + "background-color:#ff7f7f;")
                btn.setEnabled(False)
            else:
                btn.clicked.connect(lambda _, b=btn: self.answer(b, row))
    
            self.opts_layout.addWidget(btn)

    def answer(self, btn, row):
        global score, attempted, correct_count
    
        for i in range(self.opts_layout.count()):
            w = self.opts_layout.itemAt(i).widget()
            if w:
                w.setEnabled(False)
    
        attempted += 1
        user_answer = str(btn.text())
        self.questions.at[self.index, "__user_answer__"] = user_answer
    
        correct_answer = str(row[answer_col])
        is_correct = user_answer == correct_answer
    
        if is_correct:
            score += 1
            correct_count += 1
            review_log.append(("Correct", row[question_col], correct_answer))
            append_to_csv(CORRECT_FILE, row)
            feedback_text = "✅ Correct!"
        else:
            score -= 0.25
            review_log.append(("Incorrect", row[question_col], correct_answer))
            feedback_text = f"❌ Wrong! | Correct: {correct_answer}"
    
        question_status[self.index] = {
            "selected": user_answer,
            "correct": is_correct,
            "skipped": False
        }
    
        self.feedback.setText(
            f"{feedback_text}<br>Attempted: {attempted} | Correct: {correct_count} | Skipped: {skipped_count} | Score: {score}"
        )
    
        for i in range(self.opts_layout.count()):
            option_btn = self.opts_layout.itemAt(i).widget()
            if option_btn:
                opt_text = str(option_btn.text())
                if opt_text == correct_answer:
                    option_btn.setStyleSheet(option_btn.styleSheet() + "background-color:lightgreen;")
                elif opt_text == user_answer and not is_correct:
                    option_btn.setStyleSheet(option_btn.styleSheet() + "background-color:#ff7f7f;")

    def skip(self):
        global skipped_count, attempted
        skipped_count += 1
        attempted += 1
    
        question_status[self.index] = {
            "selected": None,
            "correct": False,
            "skipped": True
        }
    
        if self.index+1 < len(self.questions):
            self.index += 1
            self.show_question()
        else:
            self.end()

    def mark(self):
        row = self.current_row
        qtext = row[question_col]
        occurrences = [(r['__source_file__'], int(r['__original_csv_row__'])) for _, r in df_all.iterrows() if str(r[question_col]) == str(qtext)]
        if occurrences:
            marked_errors.append({"question": qtext, "occurrences": occurrences})
    
        for i in range(self.opts_layout.count()):
            w = self.opts_layout.itemAt(i).widget()
            if w:
                w.setEnabled(False)
    
        if self.index+1 < len(self.questions):
            self.index += 1
            self.show_question()
        else:
            self.end()
            
    def go_previous(self):
        if self.index > 0:
            self.index -= 1
            self.show_question()
    
    def go_next(self):
        if self.index+1 < len(self.questions):
            self.index += 1
            self.show_question()
        else:
            self.end()
            
    def pause_quiz(self):
        global timer
        if timer and timer.isActive():
            timer.stop()
        for i in range(self.opts_layout.count()):
            w = self.opts_layout.itemAt(i).widget()
            if w:
                w.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.mark_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)
        self.feedback.setText("⏸ Quiz Paused")
    
    def resume_quiz(self):
        global timer
        if timer:
            timer.start(1000)
        for i in range(self.opts_layout.count()):
            w = self.opts_layout.itemAt(i).widget()
            if w:
                w.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.mark_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.feedback.setText("")

    def show_controls(self):
        for i in reversed(range(self.ctrl_layout.count())):
            w = self.ctrl_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        
        prev_btn = QPushButton("Previous")
        next_btn = QPushButton("Next")
        prev_btn.setStyleSheet("background-color:#f0ad4e;font-size:25px;")
        next_btn.setStyleSheet("background-color:#5bc0de;color:white;font-size:25px;")
        prev_btn.setMinimumHeight(56)
        next_btn.setMinimumHeight(56)
        
        self.ctrl_layout.addWidget(prev_btn)
        self.ctrl_layout.addWidget(next_btn)
        
        prev_btn.clicked.connect(lambda: self.go_previous())
        next_btn.clicked.connect(lambda: self.go_next())
        
    def review_results(self):
        self.start_group.hide()
        self.quiz_group.hide()
        self.end_group.show()
    
        for i in reversed(range(self.end_group.layout().count())):
            w = self.end_group.layout().itemAt(i).widget()
            if w:
                w.setParent(None)
    
        self.review_table = QTableWidget()
        self.review_table.setRowCount(len(self.questions))
        self.review_table.setColumnCount(2)
        headers = ["Question"] + option_cols + ["Selected"]
        self.review_table.setHorizontalHeaderLabels(["Question", "Options"])
        self.end_group.layout().addWidget(self.review_table)
    
        for i, row in self.questions.iterrows():
            self.review_table.setItem(i, 0, QTableWidgetItem(str(row[question_col])))
    
            options_text = ""
            correct_ans = row[answer_col]
            user_ans = row.get("__user_answer__", None)
            
            for opt_col in option_cols:
                opt_val = str(row.get(opt_col, ""))
                if opt_val == correct_ans:
                    opt_val = f"✅ {opt_val}"
                if user_ans and opt_val == user_ans and user_ans != correct_ans:
                    opt_val = f"❌ {opt_val}"
                options_text += opt_val + "\n"
            
            item = QTableWidgetItem(options_text.strip())
            item.setFlags(Qt.ItemIsEnabled)
            self.review_table.setItem(i, 1, item)
    
            sel = row.get("__user_answer__", "")
            self.review_table.setItem(i, len(option_cols) + 1, QTableWidgetItem(str(sel)))
    
        self.review_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.review_table.resizeRowsToContents()
        
        if marked_errors:
            self.marked = QTableWidget()
            self.end_group.layout().addWidget(self.marked)
            self.marked.setRowCount(len(marked_errors))
            self.marked.setColumnCount(2)
            self.marked.setHorizontalHeaderLabels(["CSV(s) and Row(s)", "Question"])
            for i, me in enumerate(marked_errors):
                q = me["question"]
                occ = me["occurrences"]
                occ_str = "; ".join([f"{fn} (row {rn})" for fn, rn in occ])
                self.marked.setItem(i, 0, QTableWidgetItem(occ_str))
                self.marked.setItem(i, 1, QTableWidgetItem(q))
            self.marked.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

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
        self.summary.setText(f"<h3>🎉 Finished!</h3><p>Attempted:{attempted} | Correct:{correct_count} | Skipped:{skipped_count} | Score:{score}</p>")
        self.review_results()
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
            self.marked.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

def main():
    app = QApplication(sys.argv)
    w = QuizMainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()