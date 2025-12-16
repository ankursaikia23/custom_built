import sys
import os
import cv2
import tempfile
import shutil
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QMessageBox, QProgressBar, QLabel
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class ConverterThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, video_path, pdf_path, seconds_per_frame=2, diff_threshold=20):
        super().__init__()
        self.video_path = video_path
        self.pdf_path = pdf_path
        self.seconds_per_frame = max(1, seconds_per_frame)
        self.diff_threshold = diff_threshold

    def frame_difference(self, f1, f2):
        """Return mean absolute difference between two frames."""
        if f1 is None or f2 is None:
            return 9999
        diff = cv2.absdiff(f1, f2)
        return np.mean(diff)

    def run(self):
        temp_dir = tempfile.mkdtemp(prefix="v2p_")
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.error.emit("Could not open video file.")
                return

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_interval = max(1, int(fps * self.seconds_per_frame))
            frames_used = max(1, total_frames // frame_interval)

            c = canvas.Canvas(self.pdf_path, pagesize=A4)
            page_w, page_h = A4

            frame_count = 0
            processed = 0
            prev_frame_small = None
            added_pages = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
                if frame_count % frame_interval != 0:
                    continue

                small = cv2.resize(frame, (64, 64))
                if prev_frame_small is not None:
                    diff = self.frame_difference(small, prev_frame_small)
                    if diff < self.diff_threshold:
                        continue
                prev_frame_small = small

                fh, fw, _ = frame.shape
                aspect = fw / fh
                max_w, max_h = page_w * 0.9, page_h * 0.9
                if aspect > max_w / max_h:
                    draw_w = max_w
                    draw_h = max_w / aspect
                else:
                    draw_h = max_h
                    draw_w = max_h * aspect
                x = (page_w - draw_w) / 2
                y = (page_h - draw_h) / 2

                img_path = os.path.join(temp_dir, f"frame_{frame_count}.jpg")
                cv2.imwrite(img_path, frame)
                c.drawImage(ImageReader(img_path), x, y, width=draw_w, height=draw_h)
                c.showPage()

                processed += 1
                added_pages += 1

                percent = int((processed / frames_used) * 100)
                self.progress.emit(min(100, percent))

                if added_pages >= 200:
                    break

            cap.release()
            c.save()
            self.progress.emit(100)
            self.finished.emit(self.pdf_path)

        except Exception as e:
            self.error.emit(f"Exception: {e}")
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

class VideoToPDFApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video → PDF (Optimized)")
        self.resize(720, 480)
        layout = QVBoxLayout()

        self.info_label = QLabel("Select a video and convert to PDF")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.btn = QPushButton("Select Video and Convert")
        self.btn.setFixedHeight(36)
        self.btn.clicked.connect(self.on_click)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setAlignment(Qt.AlignCenter)
        self.progress.hide()

        layout.addWidget(self.info_label)
        layout.addWidget(self.btn)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        self.thread = None

    def on_click(self):
        video_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.webm)")
        if not video_path:
            return
        pdf_path, _ = QFileDialog.getSaveFileName(self, "Save PDF As", "", "PDF Files (*.pdf)")
        if not pdf_path:
            return
        if not pdf_path.lower().endswith(".pdf"):
            pdf_path += ".pdf"

        self.btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.info_label.setText("Converting...")

        self.thread = ConverterThread(video_path, pdf_path, seconds_per_frame=2, diff_threshold=20)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.on_finished)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_finished(self, pdf_path):
        self.btn.setEnabled(True)
        self.progress.hide()
        self.info_label.setText("Done")
        QMessageBox.information(self, "Done", f"PDF saved as:\n{pdf_path}")

    def on_error(self, msg):
        self.btn.setEnabled(True)
        self.progress.hide()
        self.info_label.setText("Error")
        QMessageBox.critical(self, "Error", msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoToPDFApp()
    window.show()
    sys.exit(app.exec_())