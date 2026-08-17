from PyQt6.QtWidgets import QTableWidget, QAbstractItemView, QHeaderView, QTableWidgetItem
from PyQt6.QtCore import Qt,QDate
# from PyQt6.QtGui import QMouseEvent
from datetime import datetime,timedelta
# import re

class GridTable(QTableWidget):
    def __init__(self,rows,columns):
        super().__init__(rows,columns)
        self.fill_active=False
        self.fill_start_row=-1
        self.fill_start_col=-1
        self.fill_last_row=-1
        self.fill_last_col=-1
        self.fill_source=""
        self.fill_source_type=""
        self.fill_origin_row=-1
        self.fill_origin_col=-1
        self.setMouseTracking(True)

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            index=self.indexAt(event.position().toPoint())
            if index.isValid():
                rect=self.visualRect(index)
                if self.currentRow()==index.row() and self.currentColumn()==index.column() and rect.right()-event.position().x()<=8 and rect.bottom()-event.position().y()<=8:
                    item=self.item(index.row(),index.column())
                    if item and item.text()!="":
                        self.fill_active=True
                        self.fill_origin_row=index.row()
                        self.fill_origin_col=index.column()
                        self.fill_start_row=index.row()
                        self.fill_start_col=index.column()
                        self.fill_last_row=index.row()
                        self.fill_last_col=index.column()
                        self.fill_source=item.text()
                        self.fill_source_type=self.detect_value_type(self.fill_source)
                        event.accept()
                        return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self,event):
        if self.fill_active:
            index=self.indexAt(event.position().toPoint())
            if index.isValid():
                row=index.row()
                col=index.column()
                if row!=self.fill_last_row or col!=self.fill_last_col:
                    self.fill_last_row=row
                    self.fill_last_col=col
                    self.perform_fill(row,col)
            event.accept()
            return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self,event):
        if self.fill_active and event.button()==Qt.MouseButton.LeftButton:
            index=self.indexAt(event.position().toPoint())
            if index.isValid():
                self.fill_last_row=index.row()
                self.fill_last_col=index.column()
                self.perform_fill(index.row(),index.column())
            self.fill_active=False
            self.fill_start_row=-1
            self.fill_start_col=-1
            self.fill_last_row=-1
            self.fill_last_col=-1
            self.fill_source=""
            self.fill_source_type=""
            self.fill_origin_row=-1
            self.fill_origin_col=-1
            event.accept()
            return
        super().mouseReleaseEvent(event)
    
    def detect_value_type(self,value):
        text=value.strip()
        try:
            float(text.replace(",",""))
            return "number"
        except ValueError:
            pass
        formats=["yyyy-MM-dd","dd-MM-yyyy","dd/MM/yyyy","MM/dd/yyyy","yyyy/MM/dd","dd.MM.yyyy","MM-dd-yyyy"]
        for fmt in formats:
            if QDate.fromString(text,fmt).isValid():
                return "date"
        return "text"
    
    def parse_date(self,value):
        formats=["%Y-%m-%d","%d-%m-%Y","%d/%m/%Y","%m/%d/%Y","%Y/%m/%d","%d.%m.%Y","%m-%d-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(),fmt),fmt
            except ValueError:
                pass
        return None,None
    
    def format_date(self,date_value,fmt):
        return date_value.strftime(fmt)
    
    def fill_value(self,offset):
        if self.fill_source_type=="number":
            text=self.fill_source.strip().replace(",","")
            try:
                value=float(text)
                result=value+offset
                if value.is_integer():
                    return str(int(result))
                return str(result)
            except ValueError:
                return self.fill_source
        if self.fill_source_type=="date":
            date_value,fmt=self.parse_date(self.fill_source)
            if date_value:
                return self.format_date(date_value+timedelta(days=offset),fmt)
        return self.fill_source
    
    def perform_fill(self,target_row,target_col):
        origin_row=self.fill_origin_row
        origin_col=self.fill_origin_col
        if target_row==origin_row and target_col==origin_col:
            return
        row_step=target_row-origin_row
        col_step=target_col-origin_col
        changed=False
        if abs(row_step)>=abs(col_step):
            start=min(origin_row,target_row)
            end=max(origin_row,target_row)
            for row in range(start,end+1):
                if row==origin_row:
                    continue
                offset=row-origin_row
                value=self.fill_value(offset)
                item=self.item(row,origin_col)
                if item is None:
                    item=QTableWidgetItem()
                    self.setItem(row,origin_col,item)
                if item.text()!=value:
                    item.setText(value)
                    changed=True
        else:
            start=min(origin_col,target_col)
            end=max(origin_col,target_col)
            for col in range(start,end+1):
                if col==origin_col:
                    continue
                offset=col-origin_col
                value=self.fill_value(offset)
                item=self.item(origin_row,col)
                if item is None:
                    item=QTableWidgetItem()
                    self.setItem(origin_row,col,item)
                if item.text()!=value:
                    item.setText(value)
                    changed=True
        if changed and self.parent() is not None:
            spreadsheet=getattr(self.parent(),"spreadsheet",None)
            if spreadsheet is not None:
                spreadsheet.is_modified=True
                
class GridPlugin:
    def __init__(self):
        self.table=GridTable(100,26)
        self.spreadsheet=None
        self.setup()
    
    def setup(self):
        self.table.setHorizontalHeaderLabels([chr(65+i) for i in range(26)])
        self.table.setVerticalHeaderLabels([str(i+1) for i in range(100)])
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setSortingEnabled(False)
        self.table.setUpdatesEnabled(True)
        self.table.setCornerButtonEnabled(False)
        self.table.setShowGrid(True)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.verticalHeader().setSectionsClickable(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setDefaultSectionSize(120)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.setStyleSheet("""
        QTableWidget{
        gridline-color:#d9d9d9;
        selection-background-color:#c2dbff;
        selection-color:black;
        }
        QTableWidget::item:selected{
        background:#c2dbff;
        color:black;
        }
        QHeaderView::section{
        background:#f1f3f4;
        border:1px solid #d9d9d9;
        padding:2px;
        }
        QHeaderView::section:checked{
        background:#dadce0;
        color:black;
        font-weight:bold;
        }
        """)
    
    def widget(self):
        return self.table
    
    def refresh_headers(self):
        self.table.setVerticalHeaderLabels([str(i+1) for i in range(self.table.rowCount())])
        labels=[]
        for i in range(self.table.columnCount()):
            n=i
            text=""
            while True:
                text=chr(65+n%26)+text
                n=n//26-1
                if n<0:
                    break
            labels.append(text)
        self.table.setHorizontalHeaderLabels(labels)
    
    def on_selection_changed(self):
        if hasattr(self,"selection_changed_callback") and callable(self.selection_changed_callback):
            self.selection_changed_callback()
    
    def merge_selected_cells(self):
        ranges=self.table.selectedRanges()
        if not ranges:
            return
        selection=ranges[0]
        row=selection.topRow()
        col=selection.leftColumn()
        if self.table.rowSpan(row,col)>1 or self.table.columnSpan(row,col)>1:
            return
        if selection.rowCount()<2 and selection.columnCount()<2:
            return
        self.table.setSpan(row,col,selection.rowCount(),selection.columnCount())
        
    def unmerge_selected_cells(self):
        ranges=self.table.selectedRanges()
        if not ranges:
            return
        selection=ranges[0]
        row=selection.topRow()
        col=selection.leftColumn()
        if self.table.rowSpan(row,col)>1 or self.table.columnSpan(row,col)>1:
            self.table.setSpan(row,col,1,1)
            
    def merge_unmerge_selected_cells(self):
        ranges=self.table.selectedRanges()
        if not ranges:
            return
        selection=ranges[0]
        row=selection.topRow()
        col=selection.leftColumn()
        if self.table.rowSpan(row,col)>1 or self.table.columnSpan(row,col)>1:
            self.table.setSpan(row,col,1,1)
            return
        if selection.rowCount()<2 and selection.columnCount()<2:
            return
        self.table.setSpan(row,col,selection.rowCount(),selection.columnCount())