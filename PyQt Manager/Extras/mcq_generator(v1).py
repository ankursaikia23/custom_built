import sys
import os
import random
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QSpinBox, QGroupBox, QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt

CORRECT_FILE = "correct1.csv"

def detect_columns(df):
    cols = [c.strip().lower() for c in df.columns]
    question_candidates = [c for c in cols if 'question' in c]
    answer_candidates = [c for c in cols if 'answer' in c]
    option_candidates = [c for c in cols if 'option' in c]
    return question_candidates, answer_candidates, option_candidates

def append_to_csv_if_new(filename, question_col, answer_col, option_cols, row):
    columns = [question_col] + option_cols + [answer_col]
    if os.path.exists(filename):
        existing = pd.read_csv(filename)
        existing.columns = existing.columns.str.strip().str.lower()
    else:
        existing = pd.DataFrame(columns=columns)
    if question_col in existing.columns and ((existing[question_col] == row[question_col]).any()):
        return
    new_row = {c: (row[c] if c in row and pd.notna(row[c]) else "") for c in columns}
    existing = pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True)
    existing.to_csv(filename, index=False)

class QuizApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCQ Quiz App")
        self.resize(800, 500)

        self.merged_df = pd.DataFrame()
        self.question_col = None
        self.answer_col = None
        self.option_cols = []
        self.questions_master = pd.DataFrame()
        self.current_index = 0
        self.selected_count = 0

        self.score = 0.0
        self.attempted = 0
        self.correct_count = 0
        self.skipped_count = 0
        self.review_log = []
        self.marked_errors = []

        self._build_ui()
        self.show_home()

    def _build_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.home_box = QGroupBox()
        hb = QVBoxLayout()
        self.home_box.setLayout(hb)

        self.files_label = QLabel("No files selected.")
        self.select_btn = QPushButton("Select CSV Files")
        self.select_btn.clicked.connect(self.on_select_files)

        row_layout = QHBoxLayout()
        row_layout.addWidget(self.select_btn)
        row_layout.addStretch()

        hb.addWidget(self.files_label)
        hb.addLayout(row_layout)

        setup_h = QHBoxLayout()
        setup_h.addWidget(QLabel("Number of questions:"))
        self.spin_count = QSpinBox()
        self.spin_count.setMinimum(1)
        self.spin_count.setMaximum(1)
        self.spin_count.setValue(10)
        setup_h.addWidget(self.spin_count)
        self.start_btn = QPushButton("Start Quiz")
        self.start_btn.clicked.connect(self.on_start_quiz)
        setup_h.addWidget(self.start_btn)
        hb.addLayout(setup_h)

        self.quiz_box = QGroupBox()
        qv = QVBoxLayout()
        self.quiz_box.setLayout(qv)

        self.progress_label = QLabel("")
        self.question_label = QLabel("")
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        qv.addWidget(self.progress_label)
        qv.addWidget(self.question_label)

        self.options_widget = QWidget()
        self.options_layout = QVBoxLayout()
        self.options_widget.setLayout(self.options_layout)
        qv.addWidget(self.options_widget)

        ctrl_layout = QHBoxLayout()
        self.skip_btn = QPushButton("Skip Question")
        self.skip_btn.clicked.connect(self.on_skip)
        self.mark_err_btn = QPushButton("Mark as Error ⚠️")
        self.mark_err_btn.clicked.connect(self.on_mark_error)
        ctrl_layout.addWidget(self.skip_btn)
        ctrl_layout.addWidget(self.mark_err_btn)
        ctrl_layout.addStretch()
        qv.addLayout(ctrl_layout)

        self.status_label = QLabel("")
        qv.addWidget(self.status_label)

        self.controls_after = QWidget()
        ca_layout = QHBoxLayout()
        self.controls_after.setLayout(ca_layout)
        self.next_btn = QPushButton("Next Question")
        self.next_btn.clicked.connect(self.on_next)
        self.restart_btn = QPushButton("Restart Quiz")
        self.restart_btn.clicked.connect(self.on_restart)
        self.quit_btn = QPushButton("Quit Quiz")
        self.quit_btn.clicked.connect(self.on_quit)
        ca_layout.addWidget(self.next_btn)
        ca_layout.addWidget(self.restart_btn)
        ca_layout.addWidget(self.quit_btn)
        qv.addWidget(self.controls_after)

        self.summary_box = QGroupBox()
        sv = QVBoxLayout()
        self.summary_box.setLayout(sv)
        self.summary_label = QLabel("")
        self.review_area = QScrollArea()
        self.review_area.setWidgetResizable(True)
        sv.addWidget(self.summary_label)
        sv.addWidget(self.review_area)

        self.layout.addWidget(self.home_box)
        self.layout.addWidget(self.quiz_box)
        self.layout.addWidget(self.summary_box)

        self.quiz_box.hide()
        self.summary_box.hide()

    def show_home(self):
        self.home_box.show()
        self.quiz_box.hide()
        self.summary_box.hide()

    def on_select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select CSV files", "", "CSV Files (*.csv);;All Files (*)")
        if not files:
            return
        self.load_and_merge_files(files)

    def load_and_merge_files(self, files):
        merged_rows = []
        assigned_option_cols = set()
        question_col = None
        answer_col = None
        option_cols = []

        for f in files:
            try:
                df = pd.read_csv(f)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not read {f}: {e}")
                continue
            df.columns = df.columns.str.strip().str.lower()
            q_cands, a_cands, opt_cands = detect_columns(df)
            if not q_cands or not a_cands or not opt_cands:
                QMessageBox.information(self, "Skipping file", f"File {os.path.basename(f)} doesn't contain required columns (question, answer, option...). Skipping.")
                continue

            qcol = q_cands[0]
            acol = a_cands[0]
            optcols = opt_cands

            if question_col is None:
                question_col = qcol
            if answer_col is None:
                answer_col = acol
            for oc in optcols:
                assigned_option_cols.add(oc)

            for idx, row in df.iterrows():
                original_csv_row = int(idx) + 2
                rowd = {}
                rowd[question_col] = row.get(qcol, "")
                rowd["__source_file__"] = os.path.basename(f)
                rowd["__original_csv_row__"] = original_csv_row
                rowd[answer_col] = row.get(acol, "")
                for i, oc in enumerate(optcols):
                    rowd[f"option_{i+1}"] = row.get(oc, "")
                merged_rows.append(rowd)

        if not merged_rows:
            QMessageBox.warning(self, "No data", "No suitable CSV rows were loaded. Make sure selected files contain question/answer/option columns.")
            return

        merged_df = pd.DataFrame(merged_rows)

        max_opts = max([len([c for c in merged_df.columns if str(c).startswith("option_")]) , 1])
        option_cols = [f"option_{i+1}" for i in range(max_opts)]

        for oc in option_cols:
            if oc not in merged_df.columns:
                merged_df[oc] = ""

        merged_df['__norm_question__'] = merged_df[question_col].astype(str).str.strip().str.lower()
        before = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset='__norm_question__').reset_index(drop=True)
        after = len(merged_df)

        if os.path.exists(CORRECT_FILE):
            try:
                correct_df = pd.read_csv(CORRECT_FILE)
                correct_df.columns = correct_df.columns.str.strip().str.lower()
                correct_qs = None
                for c in correct_df.columns:
                    if 'question' in c:
                        correct_qs = c
                        break
                if correct_qs:
                    existing_norm = correct_df[correct_qs].astype(str).str.strip().str.lower()
                    merged_df = merged_df[~merged_df['__norm_question__'].isin(existing_norm)].reset_index(drop=True)
            except Exception:
                pass

        self.merged_df = merged_df
        self.question_col = question_col
        self.answer_col = answer_col
        self.option_cols = option_cols

        self.files_label.setText(f"{len(files)} file(s) selected — merged rows: {before}, after dedupe: {after}. Available after filtering: {len(self.merged_df)}")
        total = max(1, len(self.merged_df))
        self.spin_count.setMaximum(total)
        self.spin_count.setValue(min(10, total))

    def on_start_quiz(self):
        if self.merged_df is None or self.merged_df.empty:
            QMessageBox.warning(self, "No data", "Load at least one valid CSV file first.")
            return
        self.selected_count = self.spin_count.value()
        self.questions_master = self.merged_df.sample(frac=1).reset_index(drop=True)
        if len(self.questions_master) > self.selected_count:
            self.questions_master = self.questions_master.iloc[:self.selected_count].reset_index(drop=True)

        self.score = 0.0
        self.attempted = 0
        self.correct_count = 0
        self.skipped_count = 0
        self.review_log = []
        self.marked_errors = []
        self.current_index = 0

        self.home_box.hide()
        self.summary_box.hide()
        self.quiz_box.show()
        self.show_question()

    def show_question(self):
        self.controls_after.hide()
        idx = self.current_index
        total = len(self.questions_master)
        if idx >= total:
            self.end_quiz()
            return
        row = self.questions_master.iloc[idx]
        self.progress_label.setText(f"Q{idx+1} / {total}")
        qtext = str(row[self.question_col])
        self.question_label.setText(qtext)

        options = []
        for oc in self.option_cols:
            v = row.get(oc, "")
            if pd.notna(v) and str(v).strip() != "":
                options.append(str(v))
        ans = str(row.get(self.answer_col, "")).strip()
        if ans and ans not in options:
            options.append(ans)

        if len(options) < 2:
            options += [f"Option {i}" for i in range(1, 5)]
        options = options[:6]
        random.shuffle(options)

        for i in reversed(range(self.options_layout.count())):
            w = self.options_layout.takeAt(i).widget()
            if w:
                w.setParent(None)

        self.option_buttons = []
        for opt in options:
            btn = QPushButton(opt)
            btn.setSizePolicy(btn.sizePolicy().horizontalPolicy(), btn.sizePolicy().verticalPolicy())
            btn.clicked.connect(self.make_option_handler(opt))
            self.options_layout.addWidget(btn)
            self.option_buttons.append(btn)

        self.status_label.setText(f"Attempted: {self.attempted} | Correct: {self.correct_count} | Skipped: {self.skipped_count} | Score: {self.score:.2f}")

    def make_option_handler(self, option_text):
        def handler():
            for b in self.option_buttons:
                b.setDisabled(True)
            self.skip_btn.setDisabled(True)
            self.mark_err_btn.setDisabled(True)

            row = self.questions_master.iloc[self.current_index]
            correct_answer = str(row.get(self.answer_col, "")).strip()
            self.attempted += 1
            if option_text == correct_answer:
                self.score += 1
                self.correct_count += 1
                self.review_log.append(("Correct", row[self.question_col], correct_answer))
                try:
                    append_to_csv_if_new(CORRECT_FILE, self.question_col, self.answer_col, self.option_cols, row)
                except Exception:
                    pass
                self.status_label.setText(self.status_label.text() + "    ✅ Correct!")
            else:
                self.score -= 0.25
                self.review_log.append(("Incorrect", row[self.question_col], correct_answer))
                self.status_label.setText(self.status_label.text() + f"    ❌ Wrong! Correct: {correct_answer}")

            self.controls_after.show()
            self.skip_btn.setDisabled(False)
            self.mark_err_btn.setDisabled(False)
        return handler

    def on_skip(self):
        row = self.questions_master.iloc[self.current_index]
        self.skipped_count += 1
        self.attempted += 1
        self.review_log.append(("Skipped", row[self.question_col], row.get(self.answer_col, "")))
        self.on_next()

    def on_mark_error(self):
        row = self.questions_master.iloc[self.current_index]
        original_csv_row = int(row.get("__original_csv_row__", -1))
        question_text = row.get(self.question_col, "")
        entry = (original_csv_row, question_text)
        if entry not in self.marked_errors:
            self.marked_errors.append(entry)
        QMessageBox.information(self, "Marked", "Marked this question for review (will show in 'Marked Errors').")

    def on_next(self):
        self.current_index += 1
        if self.current_index >= len(self.questions_master):
            self.end_quiz()
            return
        self.show_question()

    def on_restart(self):
        self.current_index = 0
        self.score = 0.0
        self.attempted = 0
        self.correct_count = 0
        self.skipped_count = 0
        self.review_log = []
        self.marked_errors = []
        self.show_question()

    def on_quit(self):
        self.end_quiz(return_home=True)

    def end_quiz(self, return_home=False):
        total_attempted = self.attempted
        summary = (f"<h2>🎉 Quiz finished!</h2>"
                   f"<p>Attempted: {self.attempted} | Correct: {self.correct_count} | Skipped: {self.skipped_count} | Final Score: {self.score:.2f}</p>")
        self.summary_label.setText(summary)

        review_df = pd.DataFrame(self.review_log, columns=["Status", "Question", "Answer"]) if self.review_log else pd.DataFrame(columns=["Status","Question","Answer"])
        marked_df = pd.DataFrame(self.marked_errors, columns=["CSV Row Number", "Question"]) if self.marked_errors else pd.DataFrame(columns=["CSV Row Number","Question"])

        html = "<h3>📘 Review Log</h3>"
        if not review_df.empty:
            html += review_df.to_html(index=False, escape=False)
        else:
            html += "<p>No items in review.</p>"

        html += "<h3>⚠️ Marked Questions (CSV Reference)</h3>"
        if not marked_df.empty:
            html += marked_df.to_html(index=False, escape=False)
        else:
            html += "<p>No marked questions.</p>"

        container = QLabel()
        container.setTextFormat(Qt.RichText)
        container.setText(html)
        container.setWordWrap(True)
        container.setMinimumWidth(700)
        container.setMinimumHeight(300)
        self.review_area.setWidget(container)

        self.quiz_box.hide()
        self.summary_box.show()
        if return_home:
            self.home_box.show()
        else:
            pass

def main():
    app = QApplication(sys.argv)
    win = QuizApp()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
