import sys,cv2,os,re,csv
import numpy as np
from PyQt5.QtWidgets import QApplication,QWidget,QPushButton,QVBoxLayout,QFileDialog,QProgressBar,QLabel
from PyQt5.QtCore import QThread,pyqtSignal,Qt
import easyocr

class Worker(QThread):
    progress=pyqtSignal(int)
    finished=pyqtSignal(list)
    def __init__(self,video_path):
        super().__init__()
        self.video_path=video_path
        self.reader=easyocr.Reader(['en'])
    def run(self):
        cap=cv2.VideoCapture(self.video_path)
        fps=cap.get(cv2.CAP_PROP_FPS) or 25
        frame_step=int(fps*3)
        total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        qlist=[]
        idx=0
        last_qnum=None
        while True:
            ret=False
            for _ in range(frame_step):
                ret,frame=cap.read()
                if not ret:
                    break
                h, w = frame.shape[:2]
                frame = frame[0:int(h*0.6), 0:w]
            
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if not ret: break
            results=self.reader.readtext(frame,detail=1)
            lines=[(r[1],r[0]) for r in results]
            question,qnum,opt_start_idx=None,None,None
            for i,(txt,box) in enumerate(lines):
                m=re.match(r'^\s*(\d{1,3})\.\s*(.*)',txt)
                if m:
                    qnum=int(m.group(1))
                    question=m.group(2)
                if re.match(r'^\(?[aA]\)?\s*',txt) and opt_start_idx is None:
                    opt_start_idx=i
            options=[]
            if opt_start_idx is not None:
                for j in range(opt_start_idx,opt_start_idx+5):
                    if j<len(lines):
                        t=re.sub(r'^\(?[a-eA-E]\)?\s*','',lines[j][0])
                        options.append(t)
            if len(options)<4:
                opts_candidates=[l[0] for l in lines if re.match(r'^\(?[a-eA-E]\)?\s*',l[0]) or re.search(r'\bonce\b',l[0].lower())]
                for oc in opts_candidates:
                    t=re.sub(r'^\(?[a-eA-E]\)?\s*','',oc)
                    if t not in options: options.append(t)
            hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
            lower=np.array([5,100,100])
            upper=np.array([25,255,255])
            mask=cv2.inRange(hsv,lower,upper)
            best_idx,best_score=-1,0
            for k,(ln,bb) in enumerate(lines):
                pts=np.array(bb,np.int32).reshape((-1,1,2))
                x,y,w,h=cv2.boundingRect(pts)
                roi=mask[y:y+h,x:x+w]
                score=int(np.sum(roi>0))
                if score>best_score:
                    best_score=score
                    best_idx=k
            answer_text=''
            if best_score>50 and best_idx!=-1:
                ans_line=lines[best_idx][0]
                cleaned=re.sub(r'^\(?[a-eA-E]\)?\s*','',ans_line).strip()
                for opt in options:
                    if cleaned and cleaned in opt:
                        answer_text=opt
                        break
                if answer_text=='' and cleaned: answer_text=cleaned
            if answer_text=='' and len(options)>2: answer_text=options[2]
            if qnum and question and len(options)>0:
                record=[question]+[options[k] if k<len(options) else '' for k in range(5)]+[answer_text]
                if qnum!=last_qnum:
                    qlist.append(record)
                    last_qnum=qnum
            self.progress.emit(int(100*idx/total) if total else 0)
        cap.release()
        self.finished.emit(qlist)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MCQ Extractor')
        self.resize(320,200)
        self.layout=QVBoxLayout()
        self.label=QLabel('No file selected',alignment=Qt.AlignCenter)
        self.btn=QPushButton('Choose Video')
        self.start=QPushButton('Start Extraction')
        self.progress=QProgressBar()
        for w in [self.label,self.btn,self.start]:
            w.setStyleSheet("font-size:14px;")
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btn)
        self.layout.addWidget(self.start)
        self.layout.addWidget(self.progress)
        self.setLayout(self.layout)
        self.btn.clicked.connect(self.choose)
        self.start.clicked.connect(self.start_extraction)
        self.video_path=None
    def choose(self):
        path,_=QFileDialog.getOpenFileName(self,'Open Video','','Video Files (*.mp4 *.mkv *.avi)')
        if path:
            self.video_path=path
            self.label.setText(os.path.basename(path))
    def start_extraction(self):
        if not self.video_path: return
        self.worker=Worker(self.video_path)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.done)
        self.worker.start()
    def done(self,rows):
        if not rows:
            self.label.setText('No questions found')
            return
        out='extracted_mcqs.csv'
        hdr=['Question','Option1','Option2','Option3','Option4','Option5','Answer']
        with open(out,'w',newline='',encoding='utf-8') as f:
            w=csv.writer(f)
            w.writerow(hdr)
            for r in rows: w.writerow(r)
        self.label.setText('Saved to '+out)
        self.progress.setValue(100)

if __name__=='__main__':
    app=QApplication(sys.argv)
    w=App()
    w.show()
    sys.exit(app.exec_())