import json
import os
import pandas as pd
from PyQt6.QtWidgets import QFileDialog,QLabel,QTableWidgetItem,QAbstractItemView
from grid_plugin import GridPlugin
from PyQt6.QtGui import QPixmap, QTextDocument
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter

class FilePlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.current_file=None

    def new_file(self):
        before=[]

        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                before.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
        self.table.clearContents()
        self.table.setRowCount(100)
        self.table.setColumnCount(26)
        after=[]

        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                after.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
        self.spreadsheet.history_plugin.push_operation(before,after)
    
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.clear()
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.clear()
    
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=False
            
    def save_table(self,table,file):
        data={"rows":table.rowCount(),"cols":table.columnCount(),"cells":[],"images":[],"pdfs":[]}
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                item=table.item(r,c)
                if item:
                    data["cells"].append({
                        "row":r,
                        "col":c,
                        "text":item.text(),
                        "formula":item.data(Qt.ItemDataRole.UserRole)
                    })
        with open(file,"w") as f:
            json.dump(data,f,indent=4)

    def save_file(self):
        tabs=self.spreadsheet.tab_plugin.all_tabs()
        if len(tabs)>1:
            folder,_=QFileDialog.getSaveFileName(
                self.spreadsheet,
                "Save Spreadsheet",
                "",
                "JSON Files (*.json)"
            )
            if not folder:
                return
            base,ext=os.path.splitext(folder)
            for index,tab in enumerate(tabs):
                file=f"{base}_Sheet{index+1}.json"
                self.save_table(tab["table"],file)
                tab["modified"]=False
            self.spreadsheet.statusbar_plugin.show_operation("All Tabs Saved")
            return
        file,_=QFileDialog.getSaveFileName(
            self.spreadsheet,
            "Save Project",
            "",
            "JSON Files (*.json)"
        )
        if not file:
            return
        self.save_table(self.table,file)
    
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=False
    
        self.spreadsheet.statusbar_plugin.show_operation("Saved")
        
    def new_tab(self):
        grid=GridPlugin()
        table=grid.widget()
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        table.clearSelection()
        table.setCurrentCell(-1,-1)
        index=len(self.spreadsheet.tab_plugin.all_tabs())+1
        self.spreadsheet.tab_plugin.add_tab(table,f"Sheet{index}")
        self.spreadsheet.tab_plugin.tabs.setCurrentIndex(index-1)

    def open_file(self):
        file,_=QFileDialog.getOpenFileName(
            self.spreadsheet,
            "Open Spreadsheet",
            "",
            "All Supported (*.json *.xlsx *.xls *.csv *.tsv *.ods);;"
            "JSON (*.json);;"
            "Excel (*.xlsx *.xls);;"
            "CSV (*.csv);;"
            "TSV (*.tsv);;"
            "OpenDocument (*.ods)"
        )
    
        if not file:
            return
    
        ext=os.path.splitext(file)[1].lower()
    
        self.new_file()
    
        if ext==".json":
            with open(file,"r") as f:
                data=json.load(f)
    
            self.table.setRowCount(data["rows"])
            self.table.setColumnCount(data["cols"])
    
            for cell in data["cells"]:
                item=QTableWidgetItem(cell["text"])
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    cell.get("formula")
                )
                self.table.setItem(
                    cell["row"],
                    cell["col"],
                    item
                )
    
            if hasattr(self.spreadsheet,"image_plugin"):
                for image in data.get("images",[]):
                    if os.path.exists(image["path"]):
                        self.spreadsheet.image_plugin.set_image(
                            image["row"],
                            image["col"],
                            image["path"]
                        )
    
            if hasattr(self.spreadsheet,"pdf_plugin"):
                for pdf in data.get("pdfs",[]):
                    if os.path.exists(pdf["path"]):
                        self.spreadsheet.pdf_plugin.set_pdf(
                            pdf["row"],
                            pdf["col"],
                            pdf["path"]
                        )
    
        else:
    
            if ext==".csv":
                df=pd.read_csv(file,header=None,dtype=str)
    
            elif ext==".tsv":
                df=pd.read_csv(file,sep="\t",header=None,dtype=str)
    
            elif ext in (".xlsx",".xls"):
                df=pd.read_excel(file,header=None,dtype=str)
    
            elif ext==".ods":
                df=pd.read_excel(file,engine="odf",header=None,dtype=str)
    
            else:
                return
    
            rows=len(df.index)
            cols=len(df.columns)
    
            self.table.setRowCount(max(rows,100))
            self.table.setColumnCount(max(cols,26))
    
            for r in range(rows):
                for c in range(cols):
                    value=df.iat[r,c]
                    if pd.isna(value):
                        continue
                    self.table.setItem(r,c,QTableWidgetItem(str(value)))
    
        self.current_file=file
        self.spreadsheet.history_plugin.undo_stack.clear()
        self.spreadsheet.history_plugin.redo_stack.clear()
    
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=False
    
        self.spreadsheet.statusbar_plugin.show_operation("Opened")

    def export_pdf(self):
        file,_=QFileDialog.getSaveFileName(self.spreadsheet,"Export PDF","","PDF Files (*.pdf)")
        if not file:
            return
        if not file.lower().endswith(".pdf"):
            file+=".pdf"
        html="<html><body><table border='1' cellspacing='0' cellpadding='4'>"
        for r in range(self.table.rowCount()):
            html+="<tr>"
            for c in range(self.table.columnCount()):
                html+="<td>"
                item=self.table.item(r,c)
                if item:
                    html+=item.text().replace("\n","<br>")
                html+="</td>"
            html+="</tr>"
        html+="</table></body></html>"
        printer=QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file)
        document=QTextDocument()
        document.setHtml(html)
        document.print(printer)
        self.spreadsheet.statusbar_plugin.show_operation("PDF Exported")
        
    def export_image(self):
        file_name,_=QFileDialog.getSaveFileName(
            self.spreadsheet,
            "Export Image",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        if not file_name:
            return
        pixmap=self.spreadsheet.table.grab()
        pixmap.save(file_name)
        self.spreadsheet.statusbar_plugin.show_operation("Image Exported")
        
    def export_file(self):
        file,_=QFileDialog.getSaveFileName(
            self.spreadsheet,
            "Export Spreadsheet",
            "",
            "CSV (*.csv);;Excel Workbook (*.xlsx);;Excel 97-2003 (*.xls);;OpenDocument Spreadsheet (*.ods);;TSV (*.tsv)"
        )
        if not file:
            return
        rows=self.table.rowCount()
        cols=self.table.columnCount()
        data=[]
        for r in range(rows):
            row=[]
            for c in range(cols):
                item=self.table.item(r,c)
                row.append(item.text() if item else "")
            data.append(row)
        df=pd.DataFrame(data)
        ext=os.path.splitext(file)[1].lower()
        if ext==".csv":
            df.to_csv(file,index=False,header=False)
        elif ext==".tsv":
            df.to_csv(file,sep="\t",index=False,header=False)
        elif ext==".xlsx":
            df.to_excel(file,index=False,header=False)
        elif ext==".xls":
            df.to_excel(file,index=False,header=False,engine="xlwt")
        elif ext==".ods":
            df.to_excel(file,index=False,header=False,engine="odf")
        else:
            return
        self.spreadsheet.statusbar_plugin.show_operation("Spreadsheet Exported")