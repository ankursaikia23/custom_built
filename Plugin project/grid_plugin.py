from PyQt6.QtWidgets import QTableWidget,QAbstractItemView,QHeaderView
from PyQt6.QtCore import Qt
from border_delegate import BorderDelegate

class GridPlugin:
    def __init__(self):
        self.table=QTableWidget(100,26)
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
        self.table.setItemDelegate(BorderDelegate())
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
        self.table.setVerticalHeaderLabels(
            [str(i+1) for i in range(self.table.rowCount())]
        )
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
            self.table.setSpan(row,col,1,1)
            return
        if selection.rowCount()<2 and selection.columnCount()<2:
            return
        self.table.setSpan(row,col,selection.rowCount(),selection.columnCount())