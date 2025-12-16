import sys
import os
import json
import gzip
import csv
import time
from datetime import datetime
from collections import deque
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QListWidget, QMessageBox, QLabel, QLineEdit,
    QProgressBar, QInputDialog, QMenu, QAction, QTableView,
    QDialog, QHeaderView, QCheckBox, QSpinBox, QComboBox, QStatusBar
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem

def fast_count_rows(path):
    try:
        with open(path, 'rb') as f:
            count = 0
            for chunk in iter(lambda: f.read(8192 * 8), b''):
                count += chunk.count(b'\n')
        return max(0, count - 1)
    except:
        try:
            df = pd.read_csv(path, nrows=0)
            return len(pd.read_csv(path))
        except:
            return 0

def detect_delimiter_and_encoding(path):
    try:
        with open(path, 'rb') as f:
            sample = f.read(8192)
        try:
            sample_text = sample.decode('utf-8')
            enc = 'utf-8'
        except:
            try:
                sample_text = sample.decode('latin1')
                enc = 'latin1'
            except:
                sample_text = sample.decode('utf-8', errors='ignore')
                enc = 'utf-8'
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample_text, delimiters=[',',';','\t','|'])
        delim = dialect.delimiter
        return delim, enc
    except:
        return ',', 'utf-8'

class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df
    def rowCount(self, parent=QModelIndex()):
        return len(self._df.index)
    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)
    def data(self, index, role=0):
        if role == Qt.DisplayRole:
            val = self._df.iat[index.row(), index.column()]
            return str(val)
        return None
    def headerData(self, section, orientation, role=0):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(self._df.index[section])
        return None

class PreviewDialog(QDialog):
    def __init__(self, df, title="Preview"):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(800, 500)
        l = QVBoxLayout()
        self.setLayout(l)
        v = QTableView()
        m = PandasModel(df)
        v.setModel(m)
        v.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        l.addWidget(v)

class CSVListItem(QListWidgetItem):
    def __init__(self, text, path, rowcount):
        super().__init__(text)
        self.setData(Qt.UserRole, path)
        self.setData(Qt.UserRole+1, rowcount)

class CSV_Merger(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Merger Pro")
        self.resize(900, 700)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.top_row = QHBoxLayout()
        self.layout.addLayout(self.top_row)

        self.btn_add = QPushButton("Add CSV")
        self.btn_add.clicked.connect(self.add_files)
        self.top_row.addWidget(self.btn_add)

        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.clicked.connect(self.remove_selected)
        self.top_row.addWidget(self.btn_remove)

        self.btn_move_up = QPushButton("Move Up")
        self.btn_move_up.clicked.connect(lambda: self.move_items(-1))
        self.top_row.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("Move Down")
        self.btn_move_down.clicked.connect(lambda: self.move_items(1))
        self.top_row.addWidget(self.btn_move_down)

        self.btn_top = QPushButton("Move Top")
        self.btn_top.clicked.connect(lambda: self.move_to_extreme(True))
        self.top_row.addWidget(self.btn_top)

        self.btn_bottom = QPushButton("Move Bottom")
        self.btn_bottom.clicked.connect(lambda: self.move_to_extreme(False))
        self.top_row.addWidget(self.btn_bottom)

        self.btn_sort_az = QPushButton("Sort A-Z")
        self.btn_sort_az.clicked.connect(lambda: self.sort_list(True))
        self.top_row.addWidget(self.btn_sort_az)

        self.btn_sort_za = QPushButton("Sort Z-A")
        self.btn_sort_za.clicked.connect(lambda: self.sort_list(False))
        self.top_row.addWidget(self.btn_sort_za)

        self.mid_row = QHBoxLayout()
        self.layout.addLayout(self.mid_row)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.setDragDropMode(QListWidget.InternalMove)
        self.file_list.model().rowsMoved.connect(self.snapshot_state)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.open_context_menu)
        self.file_list.itemSelectionChanged.connect(self.update_status)
        self.mid_row.addWidget(self.file_list)

        bottom_panel = QVBoxLayout()
        self.layout.addLayout(bottom_panel)

        self.row_label = QLabel("Total Rows: 0")
        bottom_panel.addWidget(self.row_label)

        self.details_label = QLabel("Files: 0 | Selected: 0")
        bottom_panel.addWidget(self.details_label)

        self.template_input = QLineEdit("merged_[DATE]_[ROWCOUNT].csv")
        bottom_panel.addWidget(QLabel("Filename template"))
        bottom_panel.addWidget(self.template_input)

        self.checkbox_dedupe = QCheckBox("Remove duplicate rows after merge")
        bottom_panel.addWidget(self.checkbox_dedupe)

        self.checkbox_aligncols = QCheckBox("Align columns (union + fill NA)")
        bottom_panel.addWidget(self.checkbox_aligncols)

        sort_box = QHBoxLayout()
        self.sort_input = QLineEdit()
        self.sort_input.setPlaceholderText("Sort by column (comma sep)")
        sort_box.addWidget(self.sort_input)
        self.sort_dir = QComboBox()
        self.sort_dir.addItems(["asc","desc"])
        sort_box.addWidget(self.sort_dir)
        bottom_panel.addLayout(sort_box)

        split_box = QHBoxLayout()
        self.split_spin = QSpinBox()
        self.split_spin.setRange(0, 100_000_000)
        self.split_spin.setValue(0)
        split_box.addWidget(QLabel("Split rows limit"))
        split_box.addWidget(self.split_spin)
        bottom_panel.addLayout(split_box)

        self.chk_compress = QCheckBox("Compress output (.gz)")
        bottom_panel.addWidget(self.chk_compress)

        pb = QHBoxLayout()
        self.preview_btn = QPushButton("Preview Selected")
        self.preview_btn.clicked.connect(self.preview_selected)
        pb.addWidget(self.preview_btn)
        self.btn_preview_merged = QPushButton("Preview Merged")
        self.btn_preview_merged.clicked.connect(self.preview_merged)
        pb.addWidget(self.btn_preview_merged)
        bottom_panel.addLayout(pb)

        act = QHBoxLayout()
        self.btn_undo = QPushButton("Undo")
        self.btn_undo.clicked.connect(self.undo)
        act.addWidget(self.btn_undo)
        self.btn_redo = QPushButton("Redo")
        self.btn_redo.clicked.connect(self.redo)
        act.addWidget(self.btn_redo)
        self.btn_savelist = QPushButton("Save List")
        self.btn_savelist.clicked.connect(self.save_list)
        act.addWidget(self.btn_savelist)
        self.btn_loadlist = QPushButton("Load List")
        self.btn_loadlist.clicked.connect(self.load_list)
        act.addWidget(self.btn_loadlist)
        bottom_panel.addLayout(act)

        mbox = QHBoxLayout()
        self.btn_merge = QPushButton("Merge & Save")
        self.btn_merge.clicked.connect(self.merge_csv)
        mbox.addWidget(self.btn_merge)
        self.btn_merge_auto = QPushButton("Auto Merge Folder")
        self.btn_merge_auto.clicked.connect(self.auto_merge_folder)
        mbox.addWidget(self.btn_merge_auto)
        bottom_panel.addLayout(mbox)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.layout.addWidget(self.progress)

        bottom_row = QHBoxLayout()
        self.layout.addLayout(bottom_row)

        self.status = QStatusBar()
        bottom_row.addWidget(self.status)

        self.dark_mode = QCheckBox("Dark Mode")
        self.dark_mode.stateChanged.connect(self.toggle_dark_mode)
        bottom_row.addWidget(self.dark_mode)

        self.file_list.keyPressEvent = self.keyPressEventOverride
        self.undo_stack = deque(maxlen=100)
        self.redo_stack = deque(maxlen=100)
        self.snapshot_state()
        self.recent_dirs = deque(maxlen=10)

    def toggle_dark_mode(self, s):
        if s:
            self.setStyleSheet("QWidget{background:#2b2b2b;color:#ddd}QLineEdit,QListWidget,QTableView{background:#3a3a3a;color:#fff}")
        else:
            self.setStyleSheet("")

    def add_files(self):
        start = self.recent_dirs[0] if self.recent_dirs else ""
        files,_= QFileDialog.getOpenFileNames(self,"Select CSV Files",start,"CSV Files (*.csv)")
        if files:
            for f in files:
                if not any(self.file_list.item(i).data(Qt.UserRole)==f for i in range(self.file_list.count())):
                    item = self._make_item(os.path.basename(f),f)
                    self.file_list.addItem(item)
            self.recent_dirs.appendleft(os.path.dirname(files[0]))
            self.snapshot_state()
            self.update_row_count()

    def _make_item(self,label,path):
        rc = fast_count_rows(path)
        item = CSVListItem(f"{label} ({rc} rows)",path,rc)
        return item

    def remove_selected(self):
        for it in reversed(self.file_list.selectedItems()):
            self.file_list.takeItem(self.file_list.row(it))
        self.snapshot_state()
        self.update_row_count()

    def clear_all(self):
        self.file_list.clear()
        self.snapshot_state()
        self.update_row_count()

    def move_items(self,dir):
        s=self.file_list.selectedItems()
        if not s:return
        rows=sorted(self.file_list.row(i) for i in s)
        if dir<0:
            if rows[0]==0:return
            new=[r-1 for r in rows]
        else:
            if rows[-1]==self.file_list.count()-1:return
            new=[r+1 for r in rows]
        items=[self.file_list.takeItem(r) for r in reversed(rows)]
        items.reverse()
        for it,pos in zip(items,new):
            self.file_list.insertItem(pos,it)
        for p in new:
            self.file_list.item(p).setSelected(True)
        self.snapshot_state()
        self.update_row_count()

    def move_to_extreme(self,top):
        s=self.file_list.selectedItems()
        if not s:return
        rows=sorted(self.file_list.row(i) for i in s)
        items=[self.file_list.takeItem(r) for r in reversed(rows)]
        items.reverse()
        if top:
            for i,it in enumerate(items):
                self.file_list.insertItem(i,it)
                self.file_list.item(i).setSelected(True)
        else:
            base=self.file_list.count()
            for i,it in enumerate(items):
                self.file_list.insertItem(base+i,it)
                self.file_list.item(base+i).setSelected(True)
        self.snapshot_state()
        self.update_row_count()

    def sort_list(self,asc=True):
        arr=[self.file_list.item(i).data(Qt.UserRole) for i in range(self.file_list.count())]
        arr=sorted(arr,key=lambda p:os.path.basename(p).lower(),reverse=not asc)
        self.file_list.clear()
        for p in arr:
            self.file_list.addItem(self._make_item(os.path.basename(p),p))
        self.snapshot_state()
        self.update_row_count()

    def preview_selected(self):
        it=self.file_list.selectedItems()
        if not it:
            QMessageBox.information(self,"Preview","Select a file first.");return
        p=it[0].data(Qt.UserRole)
        d,e=detect_delimiter_and_encoding(p)
        try:df=pd.read_csv(p,sep=d,encoding=e,nrows=200)
        except:df=pd.read_csv(p,nrows=200,encoding='latin1')
        PreviewDialog(df,os.path.basename(p)).exec_()

    def preview_merged(self):
        if self.file_list.count()==0:
            QMessageBox.information(self,"Preview","No files to merge.");return
        try:
            dfs=[]
            for i in range(self.file_list.count()):
                p=self.file_list.item(i).data(Qt.UserRole)
                d,e=detect_delimiter_and_encoding(p)
                try:df=pd.read_csv(p,sep=d,encoding=e,nrows=500)
                except:df=pd.read_csv(p,nrows=500,encoding='latin1')
                dfs.append(df)
            if self.checkbox_aligncols.isChecked():
                cols=sorted({c for x in dfs for c in x.columns})
                dfs=[x.reindex(columns=cols) for x in dfs]
            m=pd.concat(dfs,ignore_index=True)
            if self.checkbox_dedupe.isChecked():m=m.drop_duplicates()
            sc=[c.strip() for c in self.sort_input.text().split(",") if c.strip()]
            if sc:m=m.sort_values(by=sc,ascending=(self.sort_dir.currentText()=="asc"))
            PreviewDialog(m.head(1000),"Merged Preview").exec_()
        except Exception as e:
            QMessageBox.critical(self,"Preview Error",str(e))

    def keyPressEventOverride(self,e):
        if e.modifiers()&Qt.ControlModifier:
            if e.key()==Qt.Key_Up:self.move_items(-1);return
            if e.key()==Qt.Key_Down:self.move_items(1);return
            if e.key()==Qt.Key_Z:self.undo();return
            if e.key()==Qt.Key_Y:self.redo();return
            if e.key()==Qt.Key_A:self.file_list.selectAll();return
            if e.key()==Qt.Key_S:self.merge_csv();return
        if e.key()==Qt.Key_Delete:self.remove_selected();return
        QListWidget.keyPressEvent(self.file_list,e)

    def snapshot_state(self):
        s=[self.file_list.item(i).data(Qt.UserRole) for i in range(self.file_list.count())]
        self.undo_stack.append(list(s))
        self.redo_stack.clear()
        self.update_status()

    def undo(self):
        if len(self.undo_stack)<=1:return
        cur=self.undo_stack.pop()
        self.redo_stack.append(cur)
        prev=self.undo_stack[-1]
        self._restore_state(prev)
        self.update_row_count()

    def redo(self):
        if not self.redo_stack:return
        nxt=self.redo_stack.pop()
        self.undo_stack.append(nxt)
        self._restore_state(nxt)
        self.update_row_count()

    def _restore_state(self,a):
        self.file_list.clear()
        for p in a:self.file_list.addItem(self._make_item(os.path.basename(p),p))
        self.update_status()

    def save_list(self):
        if self.file_list.count()==0:
            QMessageBox.information(self,"Save List","No files to save.");return
        p,_=QFileDialog.getSaveFileName(self,"Save File List","filelist.json","JSON (*.json)")
        if not p:return
        arr=[self.file_list.item(i).data(Qt.UserRole) for i in range(self.file_list.count())]
        with open(p,'w',encoding='utf-8')as f:json.dump(arr,f,indent=2)
        QMessageBox.information(self,"Saved",f"List saved to {p}")

    def load_list(self):
        p,_=QFileDialog.getOpenFileName(self,"Load File List","","JSON (*.json)")
        if not p:return
        try:
            with open(p,'r',encoding='utf-8')as f:arr=json.load(f)
            self.file_list.clear()
            for x in arr:
                if os.path.exists(x):self.file_list.addItem(self._make_item(os.path.basename(x),x))
            self.snapshot_state()
            self.update_row_count()
        except Exception as e:
            QMessageBox.critical(self,"Load Error",str(e))

    def update_row_count(self):
        paths=[self.file_list.item(i).data(Qt.UserRole) for i in range(self.file_list.count())]
        if not paths:
            self.row_label.setText("Total Rows: 0")
            self.details_label.setText("Files: 0 | Selected: 0")
            return
        total=0
        for i,p in enumerate(paths):
            rc=fast_count_rows(p);total+=rc
            it=self.file_list.item(i)
            it.setText(f"{os.path.basename(p)} ({rc} rows)")
            it.setData(Qt.UserRole+1,rc)
        self.row_label.setText(f"Total Rows: {total}")
        self.details_label.setText(f"Files: {len(paths)} | Selected: {len(self.file_list.selectedItems())}")
        self.status.showMessage(f"{len(paths)} files, {total} rows",5000)

    def update_status(self):
        self.details_label.setText(f"Files: {self.file_list.count()} | Selected: {len(self.file_list.selectedItems())}")

    def open_context_menu(self,pos):
        m=QMenu()
        a1=QAction("Open File",self);a1.triggered.connect(self.open_file);m.addAction(a1)
        a2=QAction("Open Containing Folder",self);a2.triggered.connect(self.open_folder);m.addAction(a2)
        a3=QAction("Remove",self);a3.triggered.connect(self.remove_selected);m.addAction(a3)
        a4=QAction("Move Up",self);a4.triggered.connect(lambda:self.move_items(-1));m.addAction(a4)
        a5=QAction("Move Down",self);a5.triggered.connect(lambda:self.move_items(1));m.addAction(a5)
        a6=QAction("Preview",self);a6.triggered.connect(self.preview_selected);m.addAction(a6)
        m.exec_(self.file_list.mapToGlobal(pos))

    def open_file(self):
        it=self.file_list.selectedItems()
        if not it:return
        p=it[0].data(Qt.UserRole)
        try:os.startfile(p)
        except:os.system(f'xdg-open "{p}"')

    def open_folder(self):
        it=self.file_list.selectedItems()
        if not it:return
        p=os.path.dirname(it[0].data(Qt.UserRole))
        try:os.startfile(p)
        except:os.system(f'xdg-open "{p}"')

    def build_merged_filename(self,t,r,c):
        n=datetime.now()
        t=t.replace("[ROWCOUNT]",str(r))
        t=t.replace("[COUNT]",str(c))
        t=t.replace("[DATE]",n.strftime("%Y%m%d"))
        t=t.replace("[TIME]",n.strftime("%H%M%S"))
        return t

    def merge_csv(self):
        if self.file_list.count()==0:
            QMessageBox.warning(self,"No Files","Add files first.");return
        files=[self.file_list.item(i).data(Qt.UserRole)for i in range(self.file_list.count())]
        total=sum(self.file_list.item(i).data(Qt.UserRole+1)for i in range(self.file_list.count()))
        c=len(files)
        t=self.template_input.text().strip()or"merged_[ROWCOUNT].csv"
        sug=self.build_merged_filename(t,total,c)
        out,_=QFileDialog.getSaveFileName(self,"Save Merged CSV",sug,"CSV (*.csv);;GZip (*.gz)")
        if not out:return
        if out.endswith(".gz")and not self.chk_compress.isChecked():self.chk_compress.setChecked(True)
        try:
            self.progress.setValue(0)
            dfs=[]
            for i,p in enumerate(files):
                d,e=detect_delimiter_and_encoding(p)
                try:x=pd.read_csv(p,sep=d,encoding=e)
                except:x=pd.read_csv(p,encoding='latin1')
                dfs.append(x)
                self.progress.setValue(int((i+1)/len(files)*50))
                QApplication.processEvents()
            if self.checkbox_aligncols.isChecked():
                cols=sorted({c for x in dfs for c in x.columns})
                dfs=[x.reindex(columns=cols)for x in dfs]
            m=pd.concat(dfs,ignore_index=True)
            if self.checkbox_dedupe.isChecked():m=m.drop_duplicates()
            sc=[c.strip()for c in self.sort_input.text().split(",")if c.strip()]
            if sc and all(c in m.columns for c in sc):
                m=m.sort_values(by=sc,ascending=(self.sort_dir.currentText()=="asc"))
            self.progress.setValue(75)
            chunk=self.split_spin.value()
            b,e=os.path.splitext(out)
            if chunk>0:
                tot=len(m);parts=(tot+chunk-1)//chunk
                for i in range(parts):
                    part=m.iloc[i*chunk:(i+1)*chunk]
                    op=f"{b}_part{i+1}{e}"
                    if self.chk_compress.isChecked():
                        op=op if op.endswith(".gz") else op+".gz"
                        part.to_csv(op,index=False,compression='gzip')
                    else:part.to_csv(op,index=False)
                    self.progress.setValue(75+int((i+1)/parts*25))
                    QApplication.processEvents()
            else:
                if self.chk_compress.isChecked():
                    out=out if out.endswith(".gz") else out+".gz"
                    m.to_csv(out,index=False,compression='gzip')
                else:m.to_csv(out,index=False)
                self.progress.setValue(100)
            QMessageBox.information(self,"Saved","Merge complete.")
            self.status.showMessage("Merge complete",5000)
        except Exception as e:
            QMessageBox.critical(self,"Merge Error",str(e))
        finally:self.progress.setValue(0)

    def auto_merge_folder(self):
        f=QFileDialog.getExistingDirectory(self,"Select Folder")
        if not f:return
        c=[]
        for r,_,fs in os.walk(f):
            for x in fs:
                if x.lower().endswith(".csv"):
                    c.append(os.path.join(r,x))
        if not c:
            QMessageBox.information(self,"Auto Merge","No CSV found.");return
        self.file_list.clear()
        for p in sorted(c):self.file_list.addItem(self._make_item(os.path.basename(p),p))
        self.snapshot_state();self.update_row_count();self.merge_csv()

if __name__=="__main__":
    a=QApplication(sys.argv)
    w=CSV_Merger()
    w.show()
    sys.exit(a.exec_())
